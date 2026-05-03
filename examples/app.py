import os
from dash import Dash, html
from flask import jsonify, redirect, request, session

from dash_social_signin import (
    build_authorize_url,
    build_container,
    build_pkce_challenge,
    build_pkce_verifier,
    install_assets,
    verify_oauth_callback,
)

HERE = os.path.dirname(__file__)
ASSETS_DIR = os.path.join(HERE, "assets")

install_assets(ASSETS_DIR)

app = Dash(__name__, assets_folder=ASSETS_DIR)
app.server.secret_key = os.environ.get("DASH_SOCIAL_SIGNIN_SECRET", "dev-only")

PROVIDER_ENV = {
    "google": ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"),
    "facebook": ("FACEBOOK_CLIENT_ID", "FACEBOOK_CLIENT_SECRET"),
    "github": ("GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET"),
    "x": ("X_CLIENT_ID", "X_CLIENT_SECRET"),
    "linkedin": ("LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET"),
    "microsoft": ("MICROSOFT_CLIENT_ID", "MICROSOFT_CLIENT_SECRET"),
    "apple": ("APPLE_CLIENT_ID", "APPLE_CLIENT_SECRET"),
    "discord": ("DISCORD_CLIENT_ID", "DISCORD_CLIENT_SECRET"),
    "slack": ("SLACK_CLIENT_ID", "SLACK_CLIENT_SECRET"),
}


def _get_creds(provider: str):
    env = PROVIDER_ENV.get(provider)
    if not env:
        return None, None
    return os.environ.get(env[0]), os.environ.get(env[1])


@app.server.route("/auth/callback")
def auth_callback():
    provider = request.args.get("provider")
    code = request.args.get("code")
    if not provider or not code:
        return "Missing provider or code", 400

    client_id, client_secret = _get_creds(provider)
    if not client_id:
        return "Missing client ID", 400

    redirect_uri = f"http://localhost:8050/auth/callback?provider={provider}"
    code_verifier = session.pop(f"pkce_verifier:{provider}", None)

    tokens, userinfo = verify_oauth_callback(
        provider=provider,
        code=code,
        redirect_uri=redirect_uri,
        client_id=client_id,
        client_secret=client_secret,
        code_verifier=code_verifier,
    )

    # Demo only: do not return tokens in production.
    return jsonify({"provider": provider, "tokens": tokens, "userinfo": userinfo})


@app.server.route("/auth/start")
def auth_start():
    provider = request.args.get("provider")
    if not provider:
        return "Missing provider", 400

    client_id, _client_secret = _get_creds(provider)
    if not client_id:
        return "Missing client ID", 400

    redirect_uri = f"http://localhost:8050/auth/callback?provider={provider}"
    scope = request.args.get("scope")
    state = request.args.get("state")
    response_type = request.args.get("response_type", "code")

    verifier = build_pkce_verifier()
    session[f"pkce_verifier:{provider}"] = verifier
    challenge = build_pkce_challenge(verifier)

    auth_url = build_authorize_url(
        provider=provider,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
        state=state,
        response_type=response_type,
        code_challenge=challenge,
    )

    return redirect(auth_url)

app.layout = html.Div(
    [
        html.H2("Social Sign-in Demo"),
        build_container(
            {
                "providers": {
                    "google": {
                        "clientId": "YOUR_GOOGLE_CLIENT_ID",
                        "redirectUri": "http://localhost:8050/auth/callback?provider=google",
                        "authUrl": "http://localhost:8050/auth/start",
                        "extraParams": {"provider": "google"},
                        "scope": "openid email profile",
                        "state": "abc123",
                    },
                    "facebook": {
                        "clientId": "YOUR_FACEBOOK_CLIENT_ID",
                        "redirectUri": "http://localhost:8050/auth/callback?provider=facebook",
                        "authUrl": "http://localhost:8050/auth/start",
                        "extraParams": {"provider": "facebook"},
                        "scope": "public_profile,email",
                    },
                    "github": {
                        "clientId": "YOUR_GITHUB_CLIENT_ID",
                        "redirectUri": "http://localhost:8050/auth/callback?provider=github",
                        "authUrl": "http://localhost:8050/auth/start",
                        "extraParams": {"provider": "github"},
                        "scope": "read:user user:email",
                    },
                    "x": {
                        "clientId": "YOUR_X_CLIENT_ID",
                        "redirectUri": "http://localhost:8050/auth/callback?provider=x",
                        "authUrl": "http://localhost:8050/auth/start",
                        "extraParams": {"provider": "x"},
                        "scope": "tweet.read users.read offline.access",
                    },
                    "linkedin": {
                        "clientId": "YOUR_LINKEDIN_CLIENT_ID",
                        "redirectUri": "http://localhost:8050/auth/callback?provider=linkedin",
                        "authUrl": "http://localhost:8050/auth/start",
                        "extraParams": {"provider": "linkedin"},
                        "scope": "r_liteprofile r_emailaddress",
                    },
                    "microsoft": {
                        "clientId": "YOUR_MICROSOFT_CLIENT_ID",
                        "redirectUri": "http://localhost:8050/auth/callback?provider=microsoft",
                        "authUrl": "http://localhost:8050/auth/start",
                        "extraParams": {"provider": "microsoft"},
                        "scope": "openid email profile",
                    },
                    "apple": {
                        "clientId": "YOUR_APPLE_CLIENT_ID",
                        "redirectUri": "http://localhost:8050/auth/callback?provider=apple",
                        "authUrl": "http://localhost:8050/auth/start",
                        "extraParams": {"provider": "apple"},
                        "scope": "name email",
                    },
                    "discord": {
                        "clientId": "YOUR_DISCORD_CLIENT_ID",
                        "redirectUri": "http://localhost:8050/auth/callback?provider=discord",
                        "authUrl": "http://localhost:8050/auth/start",
                        "extraParams": {"provider": "discord"},
                        "scope": "identify email",
                    },
                    "slack": {
                        "clientId": "YOUR_SLACK_CLIENT_ID",
                        "redirectUri": "http://localhost:8050/auth/callback?provider=slack",
                        "authUrl": "http://localhost:8050/auth/start",
                        "extraParams": {"provider": "slack"},
                        "scope": "openid profile email",
                    },
                }
            },
            id="social-signin",
        ),
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True)
