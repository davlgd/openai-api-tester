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
clever env set ALLOWED_HOSTS "your-app.cleverapps.io"
```

`ALLOWED_HOSTS` is required: the application only answers requests whose `Host` header it lists, and it defaults to `localhost,127.0.0.1`, so a deployed instance returns `400 Invalid host header` until its public domain is set. Give the hostname alone, without a scheme or port, and list every domain the application is served under. Whatever sits in front of the application must pass the public `Host` through unchanged — `X-Forwarded-Host` is not used. Redeploy or restart after changing the value.

Deploy the application:

```bash
clever deploy
clever open
```

### Reaching it from another device

The server listens on all interfaces, so a phone or another machine on the same network can use it — but its `Host` must be listed too, alongside the loopback names you keep for local use:

```bash
export ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.42,workstation.local
```

## Development

To run the application locally, clone the repository use the development script:

```bash
git clone https://github.com/davlgd/openai-api-tester.git
cd openai-api-tester

uv run dev.py
```

## TLS configuration

Outgoing calls verify TLS certificates against [certifi](https://pypi.org/project/certifi/) by default. Four optional environment variables cover private CAs and mutual TLS:

| Variable | Effect |
|---|---|
| `SKIP_TLS_VERIFY` | `true` (case-insensitive, surrounding spaces ignored) disables certificate verification entirely; anything else is read as `false`, and a value that is neither is logged as invalid |
| `CUSTOM_CA_BUNDLE` | CA bundle used to verify the server: a PEM file, or an OpenSSL hashed directory |
| `CLIENT_CERT_PATH` | Client certificate for mutual TLS |
| `CLIENT_KEY_PATH` | Client key, when it is not already inside the certificate file |

`ALLOWED_HOSTS`, described under [Deploy on Clever Cloud](#deploy-on-clever-cloud), applies whether or not any of these TLS settings are used.

```bash
export ALLOWED_HOSTS=openai.example.com
export CUSTOM_CA_BUNDLE=/path/to/ca-bundle.pem
export CLIENT_CERT_PATH=/path/to/client-cert.pem
export CLIENT_KEY_PATH=/path/to/client-key.pem
```

The CA in use is resolved in this order: `SKIP_TLS_VERIFY`, then `CUSTOM_CA_BUNDLE`, then the standard `SSL_CERT_FILE` and `SSL_CERT_DIR`, then certifi. Directory paths, for `CUSTOM_CA_BUNDLE` as well as `SSL_CERT_DIR`, need OpenSSL's hash links: run `openssl rehash /path/to/certs` first, otherwise verification fails even though the certificates are there. A misconfiguration — a missing file, a path that is not a regular file, a key without its certificate, an encrypted key — is reported in the response panel rather than silently ignored. `CLIENT_CERT_PATH` alone is valid if that file also carries the key; the key itself must not be passphrase-protected.

**These settings are global to the instance, and the application has no authentication.** `/api-call` accepts any destination from anyone who can reach it, so a client certificate configured here is an identity that every visitor can use, against any host they choose. Set `CLIENT_CERT_PATH` only on an instance whose access you control — not on a public deployment.

Network access control is not by itself enough: a page on another site can make a visitor's browser submit a form to an instance that browser can reach, including one bound to loopback. `/api-call` therefore rejects submissions that do not come from the tester's own page, and the application only answers requests whose `Host` header is in `ALLOWED_HOSTS` — which is what stops a hostile domain resolving to this instance from satisfying that same-origin check. Neither authenticates anyone who can open the page themselves.

Disabling verification while a client certificate is configured is allowed, since testing an unverified endpoint is the point of `SKIP_TLS_VERIFY`. Be aware of what it means: the peer is not authenticated, so it receives the certificate and a handshake proof — not the private key, and not a token it could replay elsewhere — while an interceptor can read and alter both the request and its response, including any application tokens they carry.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
