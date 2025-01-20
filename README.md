# OpenAI API Tester

OpenAI API Tester is a tool designed to interact with APIs compatible with OpenAI's format. It uses the [FastAPI framework](https://github.com/fastapi/fastapi) and [HTMX](https://htmx.org) to provide a seamless interface for quickly testing various APIs. Form inputs are stored in the browser's local storage, so you can pick up where you left off.

## Installation

To install the necessary dependencies, use the `uv` package manager:

```bash
uv tool install openai-api-tester
openai-api-tester
```

or `pipx`:

```bash
pipx install openai-api-tester
openai-api-tester
```

You can also launch the application one-shot:

```bash
uvx  openai-api-tester
pipx run openai-api-tester
```

## Deploy on Clever Cloud

Install Clever Tools and create a Python application:

```bash
npm i -g clever-tools
clever login

clever create --type python
```

Set the environment variables:

```bash
clever env set CC_RUN_COMMAND "uvx openai-api-tester"
```

Deploy the application:

```bash
clever deploy
clever open
```

## Development

To run the application locally, clone the repository use the development script:

```bash
git clone https://github.com/davlgd/openai-api-tester.git
cd openai-api-tester

uv run dev.py
```

## License

This project is licensed under the MIT License.
