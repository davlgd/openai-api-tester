import json
import httpx
import logging

from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.styles import get_style_by_name
from pygments.formatters import HtmlFormatter

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

env = Environment(loader=FileSystemLoader("templates"))

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

        async with httpx.AsyncClient(timeout=30.0) as client:
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
    with open(f"templates/{path}", "r") as f:
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
