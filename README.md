# dash-social-signin

Social sign-in for Dash, made simple. Drop-in OAuth buttons and server-side helpers for authorization and token verification.

## Supported providers

Google · Facebook · GitHub · X (Twitter) · LinkedIn · Microsoft · Apple · Discord · Slack

## Why use it?

**Built for Dash** — Most OAuth libraries are generic and don't account for Dash's layout system or asset pipeline. This package is built specifically for Dash.

**One consistent API for all providers** — Every provider has quirks. Facebook uses a different token endpoint format. X requires PKCE. Apple requires a JWT as the client secret. This package smooths all of that over so you call the same functions regardless of provider.

**Security built in** — PKCE prevents authorization code interception. A state token is generated per login attempt, stored server-side, and verified on callback. Tokens are never exposed to the browser — all exchange happens on your Flask/Dash backend.

**Flexible** — Use the built-in `build_container()` for a ready-made UI, or skip it entirely and build your own buttons. The backend helpers work either way.

---

## Installation

```bash
pip install dash-social-signin
```

Store your provider credentials in a `.env` file. Use [.env.example](.env.example) as the template. See [docs/PROVIDERS.md](docs/PROVIDERS.md) for step-by-step credential setup for all 9 providers.

---

## Quick Start

The setup is split into three sections depending on your integration needs:

- **Section A** — Using the default pre-styled buttons
- **Section B** — Building your own custom buttons
- **Section C** — The mandatory backend routes (required by both A and B)

---

## Section A — Using the Default Buttons

The package ships ready-to-use styled OAuth buttons. Two steps to get them into your layout.

**Step 1 — Copy assets into your app**

```python
from dash_social_signin import install_assets

install_assets("./assets")
```

**Step 2 — Mount the container in your layout**

```python
import os
from dash import Dash, html
from dash_social_signin import build_container
from dotenv import load_dotenv

load_dotenv()

app = Dash(__name__)
app.server.secret_key = os.environ.get("DASH_SOCIAL_SIGNIN_SECRET", "change-me")

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8050")

app.layout = html.Div([
    build_container(
        {
            "providers": {
                "google": {
                    "clientId": os.environ.get("GOOGLE_CLIENT_ID"),
                    "redirectUri": f"{BASE_URL}/auth/callback?provider=google",
                    "authUrl": f"{BASE_URL}/auth/start",
                    "extraParams": {"provider": "google"},
                    "scope": "openid email profile",
                },
                "github": {
                    "clientId": os.environ.get("GITHUB_CLIENT_ID"),
                    "redirectUri": f"{BASE_URL}/auth/callback?provider=github",
                    "authUrl": f"{BASE_URL}/auth/start",
                    "extraParams": {"provider": "github"},
                    "scope": "read:user user:email",
                },
            }
        },
        id="social-signin",
    )
])
```

The JS renders the buttons into the container automatically. `authUrl` points to your `/auth/start` backend route — see Section C.

---

## Section B — Building Custom Buttons

You can skip `install_assets()` and `build_container()` entirely and design your own layout. The only requirement is that your buttons link to `/auth/start` with the right query parameters.

This example uses `dash-bootstrap-components` and Font Awesome:

```python
import os
import dash
import dash_bootstrap_components as dbc
from dash import html
from dotenv import load_dotenv

load_dotenv()

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME]
)
app.server.secret_key = os.environ.get("DASH_SOCIAL_SIGNIN_SECRET", "change-me")

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8050")

app.layout = html.Div([
    html.H3("Sign in to your account"),
    html.A(
        dbc.Button(
            [html.I(className="fab fa-google me-2"), "Continue with Google"],
            color="danger",
            outline=True,
            className="d-flex align-items-center px-4 py-2",
        ),
        href=f"/auth/start?provider=google&scope=openid email profile&redirectUri={BASE_URL}/auth/callback?provider=google",
        style={"textDecoration": "none"},
    )
], className="d-flex flex-column align-items-center justify-content-center vh-100")
```

Any button or link that hits `/auth/start?provider=<name>&scope=<scopes>` will work.

---

## Section C — The Mandatory Backend Routes

Both Section A and Section B rely on the same two server-side routes. These handle state generation, PKCE, and token exchange.

### 1. `/auth/start` — Initiate the login

Generates a PKCE verifier and a CSRF state token, stores them in the session, then redirects the user to the provider.

```python
import os
import secrets
from flask import redirect, request, session
from dash_social_signin import build_authorize_url, build_pkce_challenge, build_pkce_verifier
from dash_social_signin.oauth import PROVIDER_CONFIG

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8050")

@app.server.route("/auth/start")
def auth_start():
    provider = request.args.get("provider")
    if not provider or provider not in PROVIDER_CONFIG:
        return "Invalid provider", 400

    state = secrets.token_urlsafe(16)
    session[f"oauth_state:{provider}"] = state

    verifier = build_pkce_verifier()
    session[f"pkce_verifier:{provider}"] = verifier
    challenge = build_pkce_challenge(verifier)

    auth_url = build_authorize_url(
        provider=provider,
        client_id=os.environ.get(f"{provider.upper()}_CLIENT_ID"),
        redirect_uri=f"{BASE_URL}/auth/callback?provider={provider}",
        scope=request.args.get("scope"),
        state=state,
        code_challenge=challenge,
    )

    return redirect(auth_url)
```

### 2. `/auth/callback` — Handle the provider redirect

Validates the state, exchanges the authorization code for tokens, and fetches the user's profile.

```python
import os
from flask import jsonify, request, session
from dash_social_signin import verify_oauth_callback

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8050")

@app.server.route("/auth/callback", methods=["GET", "POST"])
def auth_callback():
    # Apple sends a POST; all other providers send a GET
    get_param = lambda k: request.args.get(k) or request.form.get(k)

    provider = get_param("provider")
    code = get_param("code")
    if not provider or not code:
        return "Missing provider or code", 400

    # CSRF check
    returned_state = get_param("state")
    expected_state = session.pop(f"oauth_state:{provider}", None)
    if expected_state and returned_state != expected_state:
        return "Invalid state", 400

    code_verifier = session.pop(f"pkce_verifier:{provider}", None)

    tokens, userinfo = verify_oauth_callback(
        provider=provider,
        code=code,
        redirect_uri=f"{BASE_URL}/auth/callback?provider={provider}",
        client_id=os.environ.get(f"{provider.upper()}_CLIENT_ID"),
        client_secret=os.environ.get(f"{provider.upper()}_CLIENT_SECRET"),
        code_verifier=code_verifier,
    )

    # At this point you have the user's profile.
    # Save to your database, set a session cookie, redirect to your dashboard.
    return jsonify({"provider": provider, "userinfo": userinfo})
```

---

## Security features

**PKCE** — Before redirecting the user, a random verifier is generated and stored server-side. A SHA-256 hash of it (the challenge) is sent to the provider. When the code comes back, the verifier is sent with the token request. The provider checks they match — an intercepted code is useless without the verifier.

**CSRF protection via state** — A random token is generated per login attempt and stored in the session. The provider echoes it back in the callback. If it doesn't match, the request is rejected.

**Tokens stay on the server** — The browser never sees your client secret or access tokens. In production, store tokens in your database and give the user a session cookie — never return raw tokens to the frontend.

---

## Running your app

```python
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=True)
```

---

## Deployment

Set these environment variables before deploying (Use [.env.example](.env.example) as the template):

```bash
BASE_URL=https://your-domain.com
DASH_SOCIAL_SIGNIN_SECRET=a-long-random-string
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
# etc.
```

Register your callback URL in each provider's developer console. The pattern is always:

```
https://your-domain.com/auth/callback?provider=PROVIDER_NAME
```

For local development replace with `http://localhost:8050`.

| Provider  | Redirect URI                                                   |
|-----------|----------------------------------------------------------------|
| Google    | `https://your-domain.com/auth/callback?provider=google`     |
| Facebook  | `https://your-domain.com/auth/callback?provider=facebook`   |
| GitHub    | `https://your-domain.com/auth/callback?provider=github`     |
| X         | `https://your-domain.com/auth/callback?provider=x`          |
| LinkedIn  | `https://your-domain.com/auth/callback?provider=linkedin`   |
| Microsoft | `https://your-domain.com/auth/callback?provider=microsoft`  |
| Apple     | `https://your-domain.com/auth/callback?provider=apple`      |
| Discord   | `https://your-domain.com/auth/callback?provider=discord`    |
| Slack     | `https://your-domain.com/auth/callback?provider=slack`      |

---

## What this package does NOT do

It handles OAuth. What you do after that — saving users to a database, managing sessions, handling logout, registration flows — is up to you. This is intentional. Every app has different requirements, and this package shouldn't force a database or session library on you.

After `verify_oauth_callback()` returns `userinfo`, you have the user's name, email, and profile picture. The rest is your app's business logic.

---

## Example app

See [examples/app.py](examples/app.py) for a full runnable demo covering all 9 providers.

```bash
pip install "dash-social-signin[examples]"
python examples/app.py
```

---

## Provider credential setup

Full step-by-step setup guides for all 9 providers: [docs/PROVIDERS.md](docs/PROVIDERS.md)

---

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

- [Report a bug](.github/ISSUE_TEMPLATE/bug_report.md)
- [Request a feature](.github/ISSUE_TEMPLATE/feature_request.md)

## Connect

- PyPI: https://pypi.org/project/dash-social-signin
- LinkedIn: https://www.linkedin.com/in/budescode
- PayPal: https://www.paypal.com/paypalme/omonbudeemma

## License

MIT
