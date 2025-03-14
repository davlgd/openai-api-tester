import asyncio
import html
import json
import httpx
import logging
import os
import ssl

import certifi

from pathlib import Path
from importlib import resources
from urllib.parse import urlparse

from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from jinja2 import Environment, FileSystemLoader, select_autoescape

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(openapi_url="")

ALLOWED_METHODS = {"GET", "POST", "DELETE"}

# Only these Host headers are served. Without it, a page on an attacker's
# domain that resolves to this instance would pass the same-origin check on
# /api-call, since its Origin and Host would agree with each other.
DEFAULT_ALLOWED_HOSTS = "localhost,127.0.0.1"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", DEFAULT_ALLOWED_HOSTS).split(",")
    if host.strip()
] or DEFAULT_ALLOWED_HOSTS.split(",")

app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
logger.info(f"Serving requests for hosts: {', '.join(ALLOWED_HOSTS)}")
ERROR_BODY_LIMIT = 20000

def get_package_paths():
    try:
        package_path = resources.files("src")
        static_test = package_path / "static"

        try:
            static_test.joinpath('test').stat()
            return package_path
        except (TypeError, FileNotFoundError):
            raise ModuleNotFoundError
    except (ModuleNotFoundError, AttributeError):
        src_path = Path(__file__).parent
        if not (src_path / "static").exists():
            raise RuntimeError("Static directory not found in development mode")
        return src_path

try:
    package_path = get_package_paths()
    static_path = package_path / "static"
    templates_path = package_path / "templates"

    try:
        if isinstance(static_path, Path):
            if not static_path.exists():
                raise RuntimeError(f"Static directory not found at {static_path}")
        if isinstance(templates_path, Path):
            if not templates_path.exists():
                raise RuntimeError(f"Templates directory not found at {templates_path}")
    except AttributeError:
        pass  # Skip existence check for MultiplexedPath

    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    env = Environment(
        loader=FileSystemLoader(str(templates_path)),
        autoescape=select_autoescape(["html"])
    )
except Exception as e:
    logger.error(f"Error initializing paths: {str(e)}")
    raise

def format_error(message: str, detail: str = "") -> str:
    """Render an error panel. Everything interpolated here can come from the
    remote server, so it is escaped and shown as text, never as markup."""
    block = f'<div class="error-title">{html.escape(message)}</div>'
    if detail and detail.strip():
        # Shown exactly as the server sent it: only truncated, never trimmed.
        body = detail
        if len(body) > ERROR_BODY_LIMIT:
            body = body[:ERROR_BODY_LIMIT] + "\n\u2026 (truncated)"
        # The text sits in a <code> child: a newline straight after a <pre>
        # start tag is swallowed by the HTML parser, which would drop the
        # response's first blank line.
        block += f'<pre class="error-body"><code>{html.escape(body)}</code></pre>'
    return f'<div class="error">{block}</div>'


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    template = env.get_template("index.html")
    return template.render()

@app.get("/template/{template_name}", response_class=HTMLResponse)
async def get_template(template_name: str) -> HTMLResponse:
    template = env.get_template(f"partials/{template_name}.html")
    return template.render()

def _require_regular_file(path: str, label: str) -> None:
    """Reject anything that is not a plain file.

    A FIFO passes exists() and then blocks OpenSSL indefinitely, which would
    hang the request before httpx's timeout can apply to it.
    """
    candidate = Path(path)
    if not candidate.exists():
        raise ValueError(f"{label} not found at {path}")
    if not candidate.is_file():
        raise ValueError(f"{label} at {path} is not a regular file")


def _reject_encrypted_key() -> str:
    """Password callback for load_cert_chain.

    Raising here is what stops OpenSSL from prompting for a passphrase on
    stdin, which would hang the event loop inside an async handler.
    """
    raise ValueError(
        "Client key is encrypted: point CLIENT_KEY_PATH at a decrypted key file"
    )


def build_tls_options() -> ssl.SSLContext:
    """Build the SSL context for outgoing calls from the environment.

    Returned as a single context because `verify=<SSLContext>` is the form
    httpx 0.28 supports: `verify=<str>` and `cert=...` are both deprecated
    there, and passing a CA bundle path as `verify` makes httpx return before
    it ever loads `cert`, silently dropping the client certificate when both
    are configured.

    Raises ValueError with a user-facing message when a configured file is
    missing, unreadable or the combination is incomplete, so a misconfiguration
    is reported instead of silently falling back to the defaults.
    """
    raw_skip = os.environ.get("SKIP_TLS_VERIFY", "").strip()
    skip_verify = raw_skip.lower() == "true"
    if raw_skip and raw_skip.lower() not in ("true", "false"):
        logger.warning(
            f"SKIP_TLS_VERIFY={raw_skip!r} is not a boolean: read as false, "
            "certificate verification stays on"
        )
    ca_bundle = os.environ.get("CUSTOM_CA_BUNDLE")
    client_cert = os.environ.get("CLIENT_CERT_PATH")
    client_key = os.environ.get("CLIENT_KEY_PATH")

    if client_key and not client_cert:
        raise ValueError(
            "CLIENT_KEY_PATH is set but CLIENT_CERT_PATH is not: set both, or neither"
        )

    try:
        if skip_verify:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            logger.warning("TLS verification disabled via SKIP_TLS_VERIFY")
            if ca_bundle:
                logger.warning("CUSTOM_CA_BUNDLE ignored because SKIP_TLS_VERIFY is set")
        elif ca_bundle:
            bundle = Path(ca_bundle)
            if not bundle.exists():
                raise ValueError(f"Custom CA bundle not found at {ca_bundle}")
            if not bundle.is_dir():
                _require_regular_file(ca_bundle, "Custom CA bundle")
            context = (
                ssl.create_default_context(capath=ca_bundle)
                if bundle.is_dir()
                else ssl.create_default_context(cafile=ca_bundle)
            )
            logger.info(f"Using custom CA bundle: {ca_bundle}")
        else:
            # Mirror httpx's own default chain. Building the context ourselves
            # must not quietly drop the two standard OpenSSL variables.
            ssl_cert_file = os.environ.get("SSL_CERT_FILE")
            ssl_cert_dir = os.environ.get("SSL_CERT_DIR")
            if ssl_cert_file:
                context = ssl.create_default_context(cafile=ssl_cert_file)
            elif ssl_cert_dir:
                context = ssl.create_default_context(capath=ssl_cert_dir)
            else:
                context = ssl.create_default_context(cafile=certifi.where())
    except (ssl.SSLError, OSError) as ca_err:
        raise ValueError(f"Could not load the CA certificates: {ca_err}") from ca_err

    if client_cert:
        for label, path in (("Client certificate", client_cert),
                            ("Client key", client_key)):
            if path:
                _require_regular_file(path, label)
        try:
            # A lone certificate file is allowed: it may carry the key as well.
            context.load_cert_chain(client_cert, client_key,
                                    password=_reject_encrypted_key)
        except (ssl.SSLError, OSError) as cert_err:
            raise ValueError(
                f"Could not load the client certificate: {cert_err}"
            ) from cert_err
        logger.info(f"Using client certificate: {client_cert}")

    return context


def is_from_tester_ui(request: Request) -> bool:
    """Whether the submission came from this application's own page.

    /api-call performs an outgoing call with whatever TLS identity the instance
    is configured with, so a third-party page must not be able to trigger it.
    A cross-origin HTML form cannot set a request header, and a cross-origin
    fetch that sets one is stopped by the preflight this server never answers.
    """
    if request.headers.get("HX-Request", "").lower() != "true":
        return False

    # Checked independently of Sec-Fetch-Site, which a proxy may strip and an
    # older client may never send. "null", sent by a sandboxed iframe, matches
    # nothing and is rejected here.
    origin = request.headers.get("Origin")
    if origin is not None:
        host = request.headers.get("Host")
        # Compared on host alone: behind a TLS-terminating proxy the browser
        # sends an https origin while the app itself sees http, and comparing
        # schemes would reject every legitimate request.
        if not host or urlparse(origin).netloc != host:
            return False

    fetch_site = request.headers.get("Sec-Fetch-Site")
    return fetch_site is None or fetch_site == "same-origin"


@app.post("/api-call", response_class=HTMLResponse)
async def make_api_call(request: Request) -> HTMLResponse:
    if not is_from_tester_ui(request):
        logger.warning(
            "Rejected a cross-origin /api-call submission from origin %s",
            request.headers.get("Origin", "<none>"),
        )
        return format_error("This endpoint only accepts requests from the tester page")

    try:
        form = await request.form()

        headers = {"Content-Type": "application/json"}
        if token := form.get("token"):
            headers["Authorization"] = f"Bearer {token}"

        method = form.get("method", "POST")
        if method not in ALLOWED_METHODS:
            return format_error(f"Unsupported method: {method}")

        body = form.get("body")
        json_body = json.loads(body) if method == "POST" and body else None

        try:
            # Off the event loop: reading and parsing the CA bundle and the
            # client key is blocking file I/O, and a slow or contended disk
            # would otherwise stall every concurrent request.
            ssl_context = await asyncio.to_thread(build_tls_options)
        except ValueError as tls_err:
            logger.error(f"TLS configuration error: {tls_err}")
            return format_error("TLS configuration error", str(tls_err))

        async with httpx.AsyncClient(timeout=90.0, verify=ssl_context) as client:
            response = await client.request(
                method=method,
                url=form.get("base_url"),
                headers=headers,
                json=json_body
            )
            response.raise_for_status()
            return format_json_response(response.json())
    except httpx.HTTPStatusError as http_err:
        status = http_err.response.status_code
        logger.error(f"HTTP error occurred: {status} - {http_err.response.text}")
        reason = http_err.response.reason_phrase
        title = f"HTTP {status} {reason}".strip()
        return format_error(title, http_err.response.text)
    except httpx.RequestError as req_err:
        logger.error(f"Request error occurred: {str(req_err)}")
        return format_error("Request failed", str(req_err))
    except Exception as e:
        logger.error(f"Error during API call: {str(e)}")
        return format_error("Error during API call", str(e))

def format_json_response(data: any) -> str:
    try:
        formatted_json = json.dumps(data, indent=2)
        formatter = HtmlFormatter(style="github-dark")
        highlighted = highlight(formatted_json, JsonLexer(), formatter)
        css = formatter.get_style_defs()

        return (
            f'<style>{css}</style>'
            f'<div class="response-area" style="white-space: pre;">{highlighted}</div>'
        )
    except Exception as e:
        logger.error(f"Error formatting JSON response: {str(e)}")
        return format_error("Could not format the response", str(e))

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)

if __name__ == "__main__":
    main()
