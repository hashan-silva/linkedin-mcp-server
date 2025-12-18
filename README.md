# LinkedIn MCP Server (Python, stdio)
[![SonarCloud analysis](https://github.com/hashan-silva/linkedin-mcp-server/actions/workflows/sonarcloud.yml/badge.svg)](https://github.com/hashan-silva/linkedin-mcp-server/actions/workflows/sonarcloud.yml)

Minimal Model Context Protocol (MCP) server that speaks JSON-over-stdio for use with Codex CLI. It wraps LinkedIn REST endpoints so an agent can fetch your profile.

> You will need a valid LinkedIn OAuth access token with the appropriate scopes. Tokens are **not** handled here; provide them via env vars.

## Features
- Get profile

## Project layout
```
src/
  linkedin_client.py    # HTTP wrapper around LinkedIn REST
  mcp_server.py         # JSON-RPC/stdio MCP server exposing tools
requirements.txt        # Python deps (requests)
Dockerfile
```

## Run locally (stdio)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export LINKEDIN_ACCESS_TOKEN="<your-token>"
# optional: override API base
# export LINKEDIN_BASE_URL="https://api.linkedin.com"
python -m src.mcp_server
```

The server stays attached to stdio. Configure Codex CLI to use the stdio command (see below).

### Built-in OAuth helper (fetch token on start)
If you have a LinkedIn app client ID/secret and want the server to launch a local redirect catcher:
```bash
export LINKEDIN_CLIENT_ID="your-client-id"
export LINKEDIN_CLIENT_SECRET="your-client-secret"
export LINKEDIN_REDIRECT_URI="http://127.0.0.1:8765/callback"  # must match your app config
# optional: scopes (space-separated)
# export LINKEDIN_SCOPE="r_liteprofile w_member_social"
python -m src.mcp_server --auth
```
It will print an authorization URL; open it in a browser, approve, and the server will start with the fetched access token. You can still provide LINKEDIN_ACCESS_TOKEN directly if you already have one.

## Docker
Build and run:
```bash
docker build -t linkedin-mcp-server .
docker run --rm -e LINKEDIN_ACCESS_TOKEN="$LINKEDIN_ACCESS_TOKEN" linkedin-mcp-server
```

Run with an alternate base URL (e.g., sandbox or proxy):
```bash
docker run --rm -e LINKEDIN_ACCESS_TOKEN=... -e LINKEDIN_BASE_URL=https://api.linkedin.com linkedin-mcp-server
```

**Public image guidance:** Do not bake secrets into the image. Pass creds at runtime via `-e` or a bind-mounted `.env`:
```bash
docker run --rm --env-file .env linkedin-mcp-server
```
An example env file is provided in `.env.example`. Never commit your filled-in `.env`.

OAuth in Docker (fetch token on start):
```bash
docker run --rm \
  -p 8765:8765 \  # expose redirect port
  -e LINKEDIN_CLIENT_ID=... \
  -e LINKEDIN_CLIENT_SECRET=... \
  -e LINKEDIN_REDIRECT_URI=http://127.0.0.1:8765/callback \
  linkedin-mcp-server python -m src.mcp_server --auth
```
Open the printed URL, approve, and the container will start the MCP server with the token.

## Codex CLI config (stdio server)
Add to your `~/.config/codex/mcp.json` (adjust paths as needed):
```json
{
  "servers": {
    "linkedin": {
      "command": "python",
      "args": ["-m", "src.mcp_server"],          // or ["-m", "src.mcp_server", "--auth"] to drive OAuth
      "env": {
        "LINKEDIN_ACCESS_TOKEN": "<your-token>",
        "LINKEDIN_BASE_URL": "https://api.linkedin.com"
      }
    }
  }
}
```
Ensure the working directory is this repo (or set `cwd` field if supported by your CLI).

## Exposed tools
- `get_profile` – fetch current profile

## Notes
- This is a lightweight JSON-RPC loop for MCP stdio. Validation is minimal; LinkedIn API errors are returned to the caller.
- Be mindful of LinkedIn API rate limits and scopes (e.g., r_liteprofile, etc.).
- No persistence beyond the LinkedIn API itself.

## Backlog / Future Work
- Public distribution without exposing secrets: deliver a brokered-token service (you host LinkedIn client secret and issue short-lived access tokens) or a managed MCP endpoint you run. Avoid embedding client secrets in public images or repos.
