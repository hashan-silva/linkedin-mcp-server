# LinkedIn MCP Server
[![SonarCloud analysis](https://github.com/hashan-silva/linkedin-mcp-server/actions/workflows/sonarcloud.yml/badge.svg)](https://github.com/hashan-silva/linkedin-mcp-server/actions/workflows/sonarcloud.yml)
[![Docker publish](https://github.com/hashan-silva/linkedin-mcp-server/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/hashan-silva/linkedin-mcp-server/actions/workflows/docker-publish.yml)

![LinkedIn MCP Server Logo](resources/logo.png)

If you spend enough time around AI agents, you hear the same promise over and over: agents will not just answer questions, they will do work.

That promise is only partly true if the model cannot safely and reliably interact with real systems.

An agent that cannot use tools is mostly a good conversationalist. An agent that can discover tools, understand their inputs, and execute real actions starts becoming useful.

That is where MCP comes in.

This project is a LinkedIn MCP server that exposes LinkedIn capabilities through a clean tool interface. Instead of asking a model to guess how to call LinkedIn APIs, the server gives the model a structured set of operations for profile lookup, content publishing, image posting, and article sharing.

GitHub repository: `https://github.com/hashan-silva/linkedin-mcp-server`  
Docker image: `hashan0314/linkedin-mcp-server`

> You will need a valid LinkedIn OAuth access token with the appropriate scopes. Tokens are not stored in this project; provide them through environment variables or use the built-in OAuth flow.

![LinkedIn MCP Server architecture diagram](resources/architect-diagram.png)

## What MCP Is

MCP stands for Model Context Protocol.

The simplest way to think about it is this: MCP gives AI agents a standard way to use tools.

Without MCP, developers often end up describing APIs in prompts and hoping the model follows those instructions exactly. That approach is fragile. Models can invent parameters, skip required fields, or misuse an API shape they only partially understand.

MCP replaces that guesswork with structure.

An MCP server tells an agent:

- what tools exist
- what each tool does
- what inputs are required
- how results come back

In this project, the server reads JSON messages from standard input and writes JSON responses to standard output. The transport is intentionally lightweight, but the interface is explicit and reliable.

```python
while True:
    line = await reader.readline()
    if not line:
        break

    message = json.loads(line.decode())
    response = await self.handle_message(message)

    if response is not None:
        writer.write((json.dumps(response) + "\n").encode())
        await writer.drain()
```

That is the basic shape of an MCP server: receive a structured request, route it, return a structured response.

## Why MCP Matters for Agent AI

The real value of MCP is not that it gives agents access. It gives them disciplined access.

That matters because an agent needs more than intelligence. It needs dependable ways to interact with external systems. MCP helps with that in a few important ways.

### It makes tool use explicit

Instead of hoping the model remembers how LinkedIn posting works, you expose a tool like `create_text_post` or `create_article_post`.

One of the tool definitions in this project looks like this:

```python
{
    "name": "create_article_post",
    "description": "Create a LinkedIn article post with an external article link.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "author": {"type": "string"},
            "commentary": {"type": "string"},
            "articleSource": {"type": "string"},
            "articleTitle": {"type": "string"},
            "articleDescription": {"type": "string"},
        },
        "required": [
            "author",
            "commentary",
            "articleSource",
            "articleTitle",
            "articleDescription",
        ],
    },
}
```

That is much more dependable than burying API instructions inside a prompt.

### It separates reasoning from execution

The model decides what it wants to do. The server handles how it gets done.

That means the agent can focus on decisions like:

- Should I fetch the profile first?
- Should I create a text post or an article post?
- Do I need to initialize an image upload before publishing media?

The server then takes care of the rest:

- headers and auth
- LinkedIn API endpoints
- payload construction
- upload flow
- error handling

### It makes agents easier to govern

A focused MCP server exposes only the actions you want the agent to perform.

That is safer than giving a model broad network freedom and hoping it behaves correctly. In this project, the model can only use the LinkedIn operations that the server explicitly exposes.

### It makes integrations reusable

Once a capability is wrapped as MCP, more than one agent can use it. The same server can be plugged into Codex CLI, local workflows, or containerized environments.

That is when an integration stops being a prompt trick and starts becoming infrastructure.

## What This Server Does

At a high level, the LinkedIn MCP Server does three things:

- exposes LinkedIn-related tools to an AI agent
- translates tool calls into LinkedIn REST API requests
- handles authentication through either an access token or a built-in OAuth flow

The architecture is intentionally simple. One layer exposes tools, one layer talks to LinkedIn, and one helper handles OAuth.

## Exposed Tools

- `get_profile`
- `get_verification_report`
- `get_userinfo`
- `create_text_post`
- `create_reshare`
- `initialize_image_upload`
- `upload_image_binary`
- `create_image_post`
- `create_multi_image_post`
- `create_article_post`

The server dispatches tool calls directly into the LinkedIn client:

```python
if name == "get_profile":
    return self.client.get_profile()

if name == "create_text_post":
    return self.client.create_post(
        author=args.get("author", ""),
        commentary=args.get("commentary", ""),
        visibility=args.get("visibility", "PUBLIC"),
    )

if name == "create_article_post":
    return self.client.create_article_post(
        author=args.get("author", ""),
        commentary=args.get("commentary", ""),
        article_source=args.get("articleSource", ""),
        article_title=args.get("articleTitle", ""),
        article_description=args.get("articleDescription", ""),
    )
```

That directness is one of the strengths of the project. MCP does not have to be complicated to be useful.

## LinkedIn Functionality

This server supports meaningful LinkedIn workflows rather than just exposing a toy demo.

### Profile and identity lookups

The server can retrieve:

- the current member profile
- the verification report
- OpenID Connect user information

The profile lookup is a direct call to LinkedIn's identity endpoint:

```python
resp = self.session.get(
    self._url("/rest/identityMe"),
    headers={"LinkedIn-Version": "202510.03"},
)
```

This gives an agent context before it starts acting on behalf of a user.

### Text post creation

The `create_text_post` tool lets an agent publish a standard text-only LinkedIn post.

The payload includes the author, commentary, visibility, distribution settings, and lifecycle state:

```python
return {
    "author": author_value,
    "commentary": commentary_value,
    "visibility": visibility,
    "distribution": distribution or {
        "feedDistribution": "MAIN_FEED",
        "targetEntities": [],
        "thirdPartyDistributionChannels": [],
    },
    "lifecycleState": lifecycle_state,
    "isReshareDisabledByAuthor": is_reshare_disabled_by_author,
}
```

The agent does not need to know LinkedIn's payload shape. It just calls the tool with the right intent and arguments.

### Reshares

The `create_reshare` tool allows the agent to reshare an existing LinkedIn post with optional commentary.

The payload includes a `reshareContext` that points at the parent post:

```python
payload = {
    "author": author_value,
    "visibility": visibility,
    "distribution": distribution or {
        "feedDistribution": "MAIN_FEED",
        "targetEntities": [],
        "thirdPartyDistributionChannels": [],
    },
    "lifecycleState": lifecycle_state,
    "isReshareDisabledByAuthor": is_reshare_disabled_by_author,
    "reshareContext": {"parent": parent_value},
}
```

### Image uploads and image posts

Media posting is intentionally modeled as a multi-step workflow:

1. Initialize the upload
2. Receive an upload URL and image URN
3. Upload the image binary
4. Create the final post that references the uploaded media

The upload initialization step looks like this:

```python
resp = self.session.post(
    self._url("/rest/images?action=initializeUpload"),
    json={"initializeUploadRequest": {"owner": owner_value}},
    headers={"LinkedIn-Version": linkedin_version},
)
```

The binary upload is then sent directly to the provided upload URL:

```python
with path.open("rb") as handle:
    resp = requests.put(
        url_value,
        data=handle,
        headers={"Content-Type": "application/octet-stream"},
    )
```

This mirrors the real LinkedIn flow instead of hiding it behind an unrealistic one-step abstraction.

### Multi-image posts

The `create_multi_image_post` tool lets the agent publish a post with multiple uploaded images by building a `multiImage` content structure:

```python
return {
    "author": author_value,
    "commentary": commentary_value,
    "visibility": visibility,
    "distribution": distribution or {
        "feedDistribution": "MAIN_FEED",
        "targetEntities": [],
        "thirdPartyDistributionChannels": [],
    },
    "lifecycleState": lifecycle_state,
    "isReshareDisabledByAuthor": is_reshare_disabled_by_author,
    "content": {"multiImage": {"images": image_items}},
}
```

### Article posts

The `create_article_post` tool is especially useful for longer-form content workflows. It lets an agent publish a LinkedIn post that links to an external article, such as a Medium post.

```python
return {
    "author": author_value,
    "commentary": commentary_value,
    "visibility": visibility,
    "lifecycleState": lifecycle_state,
    "content": {
        "article": {
            "source": source_value,
            "title": title_value,
            "description": description_value,
        }
    },
    "distribution": distribution or {"feedDistribution": "MAIN_FEED"},
}
```

This is a strong example of MCP turning a messy external API capability into a clean tool an agent can use.

## Authentication

Authentication is where many demos become unrealistic. This project handles it in a practical way.

You can either:

- provide `LINKEDIN_ACCESS_TOKEN` directly
- start the server with `--auth` and complete an OAuth flow

The authorization URL is built like this:

```python
params = {
    "response_type": "code",
    "client_id": client_id,
    "redirect_uri": redirect_uri,
    "scope": scope,
    "state": state,
}
```

The server then waits for the redirect, captures the authorization code, and exchanges it for an access token. That built-in OAuth helper makes the project much easier to use in practice.

## Features

- Get profile
- Get verification report
- Get userinfo
- Create text-only post
- Create reshare post
- Create image post
- Create multi-image post
- Create article post

## Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export LINKEDIN_ACCESS_TOKEN="<your-token>"
# optional: override API base
# export LINKEDIN_BASE_URL="https://api.linkedin.com"
python -m src.mcp_server
```

The server stays attached to stdio and can be configured as an MCP server in a compatible client.

### Built-In OAuth Helper

If you have a LinkedIn app client ID and secret, you can start the server with OAuth-assisted authentication:

```bash
export LINKEDIN_CLIENT_ID="your-client-id"
export LINKEDIN_CLIENT_SECRET="your-client-secret"
export LINKEDIN_REDIRECT_URI="http://127.0.0.1:8765/callback"
# optional: scopes
# export LINKEDIN_SCOPE="r_liteprofile w_member_social"
python -m src.mcp_server --auth
```

The server prints an authorization URL, waits for the redirect, exchanges the code for an access token, and then starts the MCP loop.

## Docker

Build and run:

```bash
docker build -t linkedin-mcp-server .
docker run --rm -e LINKEDIN_ACCESS_TOKEN="$LINKEDIN_ACCESS_TOKEN" linkedin-mcp-server
```

Run with an alternate base URL:

```bash
docker run --rm -e LINKEDIN_ACCESS_TOKEN=... -e LINKEDIN_BASE_URL=https://api.linkedin.com linkedin-mcp-server
```

Use the published image directly:

```bash
docker run --rm -i -e LINKEDIN_ACCESS_TOKEN=... hashan0314/linkedin-mcp-server
```

Do not bake secrets into the image. Pass credentials at runtime with environment variables or `--env-file`.

OAuth in Docker:

```bash
docker run --rm \
  -p 8765:8765 \
  -e LINKEDIN_CLIENT_ID=... \
  -e LINKEDIN_CLIENT_SECRET=... \
  -e LINKEDIN_REDIRECT_URI=http://127.0.0.1:8765/callback \
  hashan0314/linkedin-mcp-server python -m src.mcp_server --auth
```

## Codex CLI Example

Add a stdio MCP server entry to `~/.codex/config.toml`:

```toml
[mcp_servers.linkedin]
command = "docker"
args = ["run", "--rm", "-i", "-e", "LINKEDIN_ACCESS_TOKEN", "hashan0314/linkedin-mcp-server"]
env = {"LINKEDIN_ACCESS_TOKEN"="<your_token>"}
startup_timeout_ms = 30000
```

## Notes

- Validation is intentionally minimal; LinkedIn API errors are surfaced back to the caller.
- Be mindful of LinkedIn rate limits and token scopes.
- If you see a 401 or 403, your token may be expired or missing required scopes.
- No persistence is implemented beyond the LinkedIn API itself.

## Why This Project Is Useful

This project is small enough to understand quickly but real enough to demonstrate why MCP matters.

It shows:

- a real stdio MCP transport
- explicit tool definitions
- structured tool inputs
- a clean separation between protocol and API execution
- a practical authentication story
- read and write workflows that an agent can actually use

If you are trying to understand why MCP matters for agent AI, this is the core idea: give the model structured tools, keep execution logic outside the prompt, and let the agent work through stable interfaces instead of improvisation.
