# Changelog

All notable changes to this project will be documented in this file.

## [2026-04-03] Maintenance And Security Update

### Added

- Added `.dockerignore` to avoid packaging local secrets, Git metadata, and transient files into Docker build contexts.
- Added `CHANGELOG.md` and `RELEASE_NOTES.md` to keep repository history and release summaries easier to review.
- Added a safer Docker image workflow mode where pull requests only validate builds and main-branch runs publish images.

### Changed

- Refreshed `README.md` to match the current single-file implementation and runtime behavior.
- Updated Docker runtime setup to use `python:3.11-slim` and run the app directly with `python main.py`.

### Fixed

- Moved Playwright imports to runtime so `python main.py --help` works even when Playwright is not installed yet.
- Installed Chromium during Docker image builds so Playwright-based login can work inside containers.
- Removed the brittle shell-based `.env` export step from Docker startup.
- Updated the GitHub Actions Docker workflow to current action versions and removed unsupported legacy image targets.

### Security

- Upgraded Python dependencies to current safe versions.
- Pinned `urllib3==2.6.3` to enforce a non-vulnerable resolver outcome alongside `requests==2.33.1`.
