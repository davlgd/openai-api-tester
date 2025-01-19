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
from jinja2 import Environment, FileSystemLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(openapi_url="")

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
    env = Environment(loader=FileSystemLoader(str(templates_path)))
except Exception as e:
    logger.error(f"Error initializing paths: {str(e)}")
    raise

@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    template = env.get_template("index.html")
    return template.render()

@app.get("/template/{template_name}", response_class=HTMLResponse)
async def get_template(template_name: str) -> HTMLResponse:
    return read_html(f"partials/{template_name}.html")

@app.post("/api-call", response_class=HTMLResponse)
async def make_api_call(request: Request) -> HTMLResponse:
    try:
        form = await request.form()

        headers = {"Content-Type": "application/json"}
        if token := form.get("token"):
            headers["Authorization"] = f"Bearer {token}"

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.request(
                method=form.get("method", "POST"),
                url=form.get("base_url"),
                headers=headers,
                json=json.loads(form.get("body")) if form.get("method") == "POST" else None
            )
            response.raise_for_status()
            return format_json_response(response.json())
    except httpx.HTTPStatusError as http_err:
        logger.error(f"HTTP error occurred: {http_err.response.status_code} - {http_err.response.text}")
        return f"<div class='error'>HTTP error occurred: {http_err.response.status_code} - {http_err.response.text}</div>"
    except httpx.RequestError as req_err:
        logger.error(f"Request error occurred: {str(req_err)}")
        return f"<div class='error'>Request error occurred: {str(req_err)}</div>"
    except Exception as e:
        logger.error(f"Error during API call: {str(e)}")
        return f"<div class='error'>{str(e)}</div>"

def read_html(path: str) -> str:
    template_file = templates_path / path
    with open(template_file, "r") as f:
        return f.read()

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
        return f'<div class="error">{str(e)}</div>'

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)

if __name__ == "__main__":
    main()
