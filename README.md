# OpenAI API Tester

OpenAI API Tester is a tool designed to interact with APIs compatible with OpenAI's format. It uses the [FastAPI framework](https://github.com/fastapi/fastapi) and [HTMX](https://htmx.org) to provide a seamless interface for quickly testing various APIs. Form inputs are stored in the browser's local storage, so you can pick up where you left off.

## Installation

To install the necessary dependencies, use the `uv` package manager:

```bash
uv sync
```

## Development

To run the application in development mode, use the following command:

```bash
uv run uvicorn main:app --reload
```

## Production

To run the application in production mode, use the following command:

```bash
uv run -m src.server
```

## Usage

This project aims to provide a seamless interface for interacting with various APIs that are compatible with OpenAI's API.

## Deploy on Clever Cloud

Install Clever Tools and create a Python application:

```bash
npm i -g clever-tools
clever login

git clone https://github.com/davlgd/openai-api-tester.git
cd openai-api-tester

clever create --type python
```

Set the environment variables:

```bash
clever env set CC_RUN_COMMAND "uv run -m server"
```

Deploy the application:

```bash
clever deploy
clever open
```

## License

This project is licensed under the MIT License.
