import os
import secrets

from dotenv import load_dotenv
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
from dash_social_signin.oauth import PROVIDER_CONFIG

HERE = os.path.dirname(__file__)
load_dotenv(os.path.join(HERE, ".env"))
ASSETS_DIR = os.path.join(HERE, "assets")

install_assets(ASSETS_DIR)

app = Dash(__name__, assets_folder=ASSETS_DIR)
app.server.secret_key = os.environ.get("DASH_SOCIAL_SIGNIN_SECRET", "dev-only")

CLIENT_IDS = {
    provider: os.environ.get(env[0], "")
    for provider, env in {
        "google": ("GOOGLE_CLIENT_ID", ""),
        "facebook": ("FACEBOOK_CLIENT_ID", ""),
        "github": ("GITHUB_CLIENT_ID", ""),
        "x": ("X_CLIENT_ID", ""),
        "linkedin": ("LINKEDIN_CLIENT_ID", ""),
        "microsoft": ("MICROSOFT_CLIENT_ID", ""),
        "apple": ("APPLE_CLIENT_ID", ""),
        "discord": ("DISCORD_CLIENT_ID", ""),
        "slack": ("SLACK_CLIENT_ID", ""),
    }.items()
}

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8050")

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


@app.server.route("/auth/callback", methods=["GET", "POST"])
def auth_callback():
    # Apple sends form_post (POST); all other providers send GET
    get_param = lambda k: request.args.get(k) or request.form.get(k)
    provider = get_param("provider")
    code = get_param("code")
    if not provider or not code:
        return "Missing provider or code", 400

    client_id, client_secret = _get_creds(provider)
    if not client_id:
        return "Missing client ID", 400

    redirect_uri = f"{BASE_URL}/auth/callback?provider={provider}"
    code_verifier = session.pop(f"pkce_verifier:{provider}", None)

    try:
        tokens, userinfo = verify_oauth_callback(
            provider=provider,
            code=code,
            redirect_uri=redirect_uri,
            client_id=client_id,
            client_secret=client_secret,
            code_verifier=code_verifier,
        )
    except Exception as e:
        body = getattr(getattr(e, "response", None), "text", None)
        return jsonify({"error": str(e), "response_body": body, "code_verifier_present": code_verifier is not None}), 400

    # Apple has no userinfo endpoint — decode the id_token instead.
    # Note: this skips signature verification. In production, verify against
    # Apple's public keys: https://appleid.apple.com/auth/keys
    if userinfo is None and tokens.get("id_token"):
        try:
            import jwt
            userinfo = jwt.decode(tokens["id_token"], options={"verify_signature": False})
        except Exception:
            pass

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

    redirect_uri = f"{BASE_URL}/auth/callback?provider={provider}"
    scope = request.args.get("scope")
    state = request.args.get("state") or secrets.token_urlsafe(16)
    response_type = request.args.get("response_type", "code")

    use_pkce = PROVIDER_CONFIG.get(provider, {}).get("pkce", True)
    challenge = None
    if use_pkce:
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
                        "clientId": CLIENT_IDS["google"],
                        "redirectUri": f"{BASE_URL}/auth/callback?provider=google",
                        "authUrl": f"{BASE_URL}/auth/start",
                        "extraParams": {"provider": "google"},
                        "scope": "openid email profile",
                        "state": "abc123",
                    },
                    "facebook": {
                        "clientId": CLIENT_IDS["facebook"],
                        "redirectUri": f"{BASE_URL}/auth/callback?provider=facebook",
                        "authUrl": f"{BASE_URL}/auth/start",
                        "extraParams": {"provider": "facebook"},
                        "scope": "public_profile,email",
                    },
                    "github": {
                        "clientId": CLIENT_IDS["github"],
                        "redirectUri": f"{BASE_URL}/auth/callback?provider=github",
                        "authUrl": f"{BASE_URL}/auth/start",
                        "extraParams": {"provider": "github"},
                        "scope": "read:user user:email",
                    },
                    "x": {
                        "clientId": CLIENT_IDS["x"],
                        "redirectUri": f"{BASE_URL}/auth/callback?provider=x",
                        "authUrl": f"{BASE_URL}/auth/start",
                        "extraParams": {"provider": "x"},
                        "scope": "tweet.read users.read",
                    },
                    "linkedin": {
                        "clientId": CLIENT_IDS["linkedin"],
                        "redirectUri": f"{BASE_URL}/auth/callback?provider=linkedin",
                        "authUrl": f"{BASE_URL}/auth/start",
                        "extraParams": {"provider": "linkedin"},
                        "scope": "openid profile email",
                    },
                    "microsoft": {
                        "clientId": CLIENT_IDS["microsoft"],
                        "redirectUri": f"{BASE_URL}/auth/callback?provider=microsoft",
                        "authUrl": f"{BASE_URL}/auth/start",
                        "extraParams": {"provider": "microsoft"},
                        "scope": "openid email profile",
                    },
                    "apple": {
                        "clientId": CLIENT_IDS["apple"],
                        "redirectUri": f"{BASE_URL}/auth/callback?provider=apple",
                        "authUrl": f"{BASE_URL}/auth/start",
                        "extraParams": {"provider": "apple"},
                        "scope": "name email",
                    },
                    "discord": {
                        "clientId": CLIENT_IDS["discord"],
                        "redirectUri": f"{BASE_URL}/auth/callback?provider=discord",
                        "authUrl": f"{BASE_URL}/auth/start",
                        "extraParams": {"provider": "discord"},
                        "scope": "identify email",
                    },
                    "slack": {
                        "clientId": CLIENT_IDS["slack"],
                        "redirectUri": f"{BASE_URL}/auth/callback?provider=slack",
                        "authUrl": f"{BASE_URL}/auth/start",
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
    app.run(debug=True)
