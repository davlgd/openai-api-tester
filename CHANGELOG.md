# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/spec/v2.0.0.html). Dates are the UTC publication dates of the GitHub releases.

## [Unreleased]

## [0.2.0] - 2026-09-13

### Added

- Responses API: `POST /v1/responses`, `POST /v1/responses/compact`, `GET` and `DELETE /v1/responses/{response_id}`.
- TLS settings from the environment: `SKIP_TLS_VERIFY`, `CUSTOM_CA_BUNDLE`, `CLIENT_CERT_PATH`, `CLIENT_KEY_PATH`.
- `ALLOWED_HOSTS` to declare which `Host` headers are served.
- Responsive layout.
- `LICENSE` file (Apache-2.0, already the declared licence).

### Changed

- **Deployment change**: `ALLOWED_HOSTS` defaults to `localhost,127.0.0.1`, so LAN and deployed hostnames return `400` until listed. Whatever fronts the application must preserve the public `Host`. See the deployment section of the README.
- htmx 4.0, served locally; browser assets no longer depend on a CDN.
- Versioned script and stylesheet URLs, with conditional revalidation of static files.
- The request method follows the selected endpoint, not the loaded template.
- Upstream errors are shown as escaped text instead of being rendered as markup.
- Font Awesome replaced by inline SVG icons.
- Browser request timeout raised to 95s, above the server's 90s.
- All dependencies refreshed.

### Fixed

- Switching endpoint mid-request silently lost the response.
- Switching Responses endpoints could send `DELETE` while `GET` was selected.
- Send stayed disabled after a network error.
- The copy button did nothing.
- Long endpoint labels overflowed the sidebar.
- Missing accessible names on the copy button and the response id field.

### Security

- Templates autoescape, and error panels escape upstream content.
- Host and origin checks for browser submissions to `/api-call`.

## [0.1.5] - 2025-01-20

### Fixed

- Packaging: templates and static files missing from the distribution.

## [0.1.4] - 2025-01-19

### Added

- `dev.py` script to run the application locally.

## [0.1.3] - 2025-01-19

### Added

- `uvx` support.

## [0.1.0] - 2025-01-19

### Added

- Initial release: `GET /v1/models`, `POST /v1/chat/completions`, `POST /v1/embeddings`.

[Unreleased]: https://github.com/davlgd/openai-api-tester/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/davlgd/openai-api-tester/compare/v0.1.5...v0.2.0
[0.1.5]: https://github.com/davlgd/openai-api-tester/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/davlgd/openai-api-tester/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/davlgd/openai-api-tester/compare/v0.1.0...v0.1.3
[0.1.0]: https://github.com/davlgd/openai-api-tester/releases/tag/v0.1.0
