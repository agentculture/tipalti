# Changelog

All notable changes to this project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/). This project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.1] - 2026-05-01

### Added

- Initial scaffold: `tipalti learn`, `tipalti explain`, `tipalti whoami` verbs
- afi-cli agent-first CLI structure (`cli/_errors.py`, `cli/_output.py`, `cli/_commands/`)
- CI: `tests.yml` (pytest + lint + version-check), `publish.yml` (PyPI Trusted Publishing, TestPyPI dev builds on PRs)
- Vendored skills from steward: `version-bump`, `pr-review`, `run-tests`, `gh-issues`, `pypi-maintainer`, `notebooklm`, `sonarclaude`
