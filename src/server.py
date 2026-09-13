import html
import json
import httpx
import logging

from pathlib import Path
from importlib import resources

from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(openapi_url="")

ALLOWED_METHODS = {"GET", "POST", "DELETE"}
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

@app.post("/api-call", response_class=HTMLResponse)
async def make_api_call(request: Request) -> HTMLResponse:
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

        async with httpx.AsyncClient(timeout=90.0) as client:
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
