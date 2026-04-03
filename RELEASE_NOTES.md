# Release Notes

## 2026-04-03

This maintenance release focuses on security, container reliability, and repository hygiene.

### Highlights

- Upgraded `requests` and explicitly pinned `urllib3` to address the dependency vulnerabilities reported on the default branch.
- Upgraded the rest of the runtime dependencies to current releases that match the project structure.
- Updated the Docker image so Playwright installs Chromium during build, which makes automatic token retrieval usable in containers.
- Reworked the GitHub Actions Docker workflow so pull requests build-check only, while `main` pushes publish Docker images.
- Simplified container startup by removing shell-based `.env` parsing and running the app directly.
- Added repository-level change tracking with `CHANGELOG.md`.

### Operator Notes

- Existing `.env` files remain compatible.
- `docker build` will take longer than before because Chromium and its system dependencies are installed at build time.
- If you only use a valid `Authorization`, local development can still skip Playwright until automatic login is needed.

### Suggested Verification

- Run `python3 -m compileall main.py`.
- Run `python3 main.py --help`.
- Build the image with `docker build -t autodl-keeper .`.
- If Playwright login is needed, run the container with valid `AUTODL_PHONE` and `AUTODL_PASSWORD`.
