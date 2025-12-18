# Repository Guidelines

## Project Structure & Module Organization
- `src/` – Python implementation of the MCP stdio server and LinkedIn REST client (`mcp_server.py`, `linkedin_client.py`, `oauth.py`).
- `requirements.txt` – Python dependencies (requests).
- `Dockerfile` – Container build for running the server.
- `resources/` – Static assets (e.g., logo).
- `.env.example` – Template for runtime env vars; do not commit real secrets.
- `.gitignore` – Keeps virtualenvs, caches, and secrets out of git.

## Build, Test, and Development Commands
- Local stdio run: `python -m src.mcp_server` (requires `LINKEDIN_ACCESS_TOKEN`).
- OAuth-assisted run: `python -m src.mcp_server --auth` (requires `LINKEDIN_CLIENT_ID/SECRET`; prints an auth URL, captures code on localhost).
- Docker build: `docker build -t linkedin-mcp-server .`
- Docker run: `docker run --rm -e LINKEDIN_ACCESS_TOKEN=... linkedin-mcp-server`
- Docker + OAuth: expose redirect port, pass client creds, and run `python -m src.mcp_server --auth` inside the container.

## MCP Quality Checks (run after every code change)
- The SonarQube MCP server is already configured via Codex CLI (`docker run --rm -i -e SONARQUBE_TOKEN -e SONARQUBE_ORG mcp/sonarqube`).
- After editing code, use Codex CLI to query the server and ensure quality gates stay green:
  - `codex mcp call sonarqube get_project_quality_gate_status '{"projectKey":"hashan-silva_linkedin-mcp-server"}'`
  - `codex mcp call sonarqube search_sonar_issues_in_projects '{"projects":["hashan.silva:linkedin-mcp-server"],"severities":["HIGH","BLOCKER"]}'`
- Resolve any reported violations before submitting PRs. Re-run these SonarQube MCP tools until the project is clean.

## Coding Style & Naming Conventions
- Language: Python 3.11+. Prefer typing annotations and small, focused functions.
- Formatting: keep imports grouped stdlib/third-party/local; 4-space indentation.
- Naming: snake_case for functions/variables; PascalCase for classes; env vars in UPPER_SNAKE.
- Comments: brief, only where intent is non-obvious.

## Testing Guidelines
- No test suite is bundled yet. Add lightweight unit tests under `tests/` using `pytest`.
- Aim to mock network calls to LinkedIn APIs; avoid real HTTP in tests.
- Suggested pattern: `tests/test_<module>.py` with clear, isolated cases.

## Commit & Pull Request Guidelines
- Commits: concise, present-tense summaries (e.g., “Add OAuth helper for token exchange”).
- PRs: include what changed, why, and how to verify. Link related issues. Note any auth scope or env var changes.
- Screenshots/terminal logs are helpful when altering runtime behavior or setup instructions.

## Security & Configuration Tips
- Never commit secrets. Use `.env` locally or `--env-file` with Docker; `.env.example` is safe to share.
- Required envs: `LINKEDIN_ACCESS_TOKEN` or `LINKEDIN_CLIENT_ID/SECRET` with `--auth`; optional `LINKEDIN_BASE_URL`, `LINKEDIN_REDIRECT_URI`, `LINKEDIN_SCOPE`.
- Keep scope minimal (e.g., `r_liteprofile w_member_social`) and rotate tokens regularly.
