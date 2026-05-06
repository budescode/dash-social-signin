# Dash Social Signin

A streamlined social sign-in toolkit for Dash. This package includes high-performance vanilla JS/CSS assets for rendering OAuth provider buttons and comprehensive server-side helpers for managing authorization endpoints and token verification. Designed to be lightweight, framework-agnostic on the frontend, and easy to integrate with existing Dash layouts.

> Note: OAuth requires a backend to exchange the authorization `code` for tokens. In Dash, the backend is your Dash server (Flask).

## Install

```bash
pip install dash-social-signin
```

## Supported providers

- Google
- Facebook
- GitHub
- X (Twitter)
- LinkedIn
- Microsoft
- Apple
- Discord
- Slack

Note: Some providers do not return userinfo. Apple returns `None` for userinfo.

## Quick start

1) Copy assets into your Dash app's `assets/` folder:

```python
from dash_social_signin import install_assets

# Point this to your Dash app's assets directory
install_assets("./assets")
```

2) Add a container with configuration:

```python
from dash import Dash, html
from dash_social_signin import build_container

app = Dash(__name__)

app.layout = html.Div(
    build_container(
        {
            "providers": {
                "google": {
                    "clientId": "YOUR_GOOGLE_CLIENT_ID",
                    "redirectUri": "https://your.app/auth/callback",
                    "scope": "openid email profile",
                    "state": "abc123"
                },
                "github": {
                    "clientId": "YOUR_GITHUB_CLIENT_ID",
                    "redirectUri": "https://your.app/auth/callback",
                    "scope": "read:user user:email"
                }
            }
        },
        id="social-signin"
    )
)

if __name__ == "__main__":
    app.run_server(debug=True)
```

3) Add your social credentials to a `.env` file and use `.env.example` as the template.

The JS will render buttons into the container automatically.

## Example app

See [examples/app.py](examples/app.py) for a runnable demo.

The example includes placeholders for all supported providers.

Install example extras:

```bash
pip install "dash-social-signin[examples]"
```

Set provider credentials as environment variables before running the example:

```bash
export GOOGLE_CLIENT_ID="your-google-client-id"
export GOOGLE_CLIENT_SECRET="your-google-client-secret"
```

You can also use a `.env` file. Use `.env.example` as a guide.

Use the same pattern for other providers, e.g. `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET`.

If you use the PKCE start route, set `DASH_SOCIAL_SIGNIN_SECRET` to enable Flask sessions. See .env.example for the full list.

Set `BASE_URL` to match your deployment origin. Defaults to `http://localhost:8050` if not set:

```bash
# local dev
BASE_URL=http://localhost:8050

# tunnel or production
BASE_URL=https://your-tunnel-or-domain.com
```

```bash
python examples/app.py
```

## Minimal backend callback example (Flask, Google)

This is the smallest possible server-side route that receives the authorization `code` and exchanges it for tokens with Google.
It includes optional PKCE support (recommended) and a simple userinfo fetch.

```python
import base64
import hashlib
import os
import secrets
import requests
from flask import request, redirect, session

def build_pkce_verifier() -> str:
    return secrets.token_urlsafe(64)

def build_pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("utf-8")

@app.server.route("/auth/callback")
def auth_callback():
    code = request.args.get("code")
    if not code:
        return "Missing code", 400

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "https://your.app/auth/callback",
        "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
    }

    # Optional PKCE: store the verifier in session before the auth redirect
    # and send it here. If you did not use PKCE, remove this field.
    code_verifier = session.get("pkce_verifier")
    if code_verifier:
        data["code_verifier"] = code_verifier

    resp = requests.post(token_url, data=data, timeout=10)
    resp.raise_for_status()
    tokens = resp.json()

    userinfo = requests.get(
        "https://openidconnect.googleapis.com/v1/userinfo",
        headers={"Authorization": f"Bearer {tokens.get('access_token')}"},
        timeout=10,
    ).json()

    # TODO: create a session / set cookies, then redirect into the app
    return redirect("/")
```

## Verification helpers (Dash server)

These helpers run on the same Dash server process to exchange the `code` for tokens and fetch a user profile when supported.

Store provider credentials in environment variables (or your secrets manager) and pass them into the helper.

```python
from flask import request
from dash_social_signin import verify_oauth_callback

@app.server.route("/auth/callback")
def auth_callback():
    provider = request.args.get("provider")
    code = request.args.get("code")
    if not provider or not code:
        return "Missing provider or code", 400

    tokens, userinfo = verify_oauth_callback(
        provider=provider,
        code=code,
        redirect_uri=f"https://your.app/auth/callback?provider={provider}",
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
    )

    # TODO: create a session / set cookies, then redirect into the app
    return "Signed in"
```

## PKCE start route (Dash server)

Use a small server route to generate a PKCE verifier and redirect to the provider. Then point `authUrl` to this route.

```python
from flask import redirect, request, session
from dash_social_signin import build_authorize_url, build_pkce_challenge, build_pkce_verifier

@app.server.route("/auth/start")
def auth_start():
    provider = request.args.get("provider")
    if not provider:
        return "Missing provider", 400

    verifier = build_pkce_verifier()
    session[f"pkce_verifier:{provider}"] = verifier
    challenge = build_pkce_challenge(verifier)

    auth_url = build_authorize_url(
        provider=provider,
        client_id="YOUR_CLIENT_ID",
        redirect_uri=f"https://your.app/auth/callback?provider={provider}",
        scope=request.args.get("scope"),
        state=request.args.get("state"),
        response_type=request.args.get("response_type", "code"),
        code_challenge=challenge,
    )

    return redirect(auth_url)
```

## Provider config

Each provider accepts:

- `clientId` (required)
- `redirectUri` (required)
- `scope` (optional, provider specific)
- `state` (optional)
- `responseType` (optional, default `code`)
- `extraParams` (optional dict of additional query params)
- `userinfoParams` (optional dict of params to send to your backend start route)
- `authUrl` (optional override)

When using a backend start route (like `/auth/start`), `userinfoParams` is serialized to
the `userinfo_params` query param. The example app reads this value, stores it in the
session, and passes it into `verify_oauth_callback` as `extra_userinfo_params`.

## Backend exchange

After the redirect, your Dash server should handle the `code` query param and exchange it for tokens using the provider's OAuth token endpoint.

## Connect and contribute

- PayPal: https://www.paypal.com/paypalme/omonbudeemma
- LinkedIn: https://www.linkedin.com/in/budescode

## License

MIT

## Provider credential setup

Full step-by-step instructions live in [docs/PROVIDERS.md](docs/PROVIDERS.md).
