import base64
import hashlib
import secrets
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

import requests

PROVIDER_CONFIG: Dict[str, Dict[str, Any]] = {
    "google": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://openidconnect.googleapis.com/v1/userinfo",
    },
    "facebook": {
        "auth_url": "https://www.facebook.com/v18.0/dialog/oauth",
        "token_url": "https://graph.facebook.com/v18.0/oauth/access_token",
        "userinfo_url": "https://graph.facebook.com/me",
        "userinfo_token_param": "access_token",
        "userinfo_params": {"fields": "id,name,email"},
    },
    "github": {
        "auth_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "token_headers": {"Accept": "application/json"},
        "userinfo_url": "https://api.github.com/user",
        "userinfo_headers": {"Accept": "application/vnd.github+json"},
    },
    "x": {
        "auth_url": "https://twitter.com/i/oauth2/authorize",
        "token_url": "https://api.twitter.com/2/oauth2/token",
        "token_auth": "basic",
        "userinfo_url": "https://api.twitter.com/2/users/me",
    },
    "linkedin": {
        "auth_url": "https://www.linkedin.com/oauth/v2/authorization",
        "token_url": "https://www.linkedin.com/oauth/v2/accessToken",
        "userinfo_url": "https://api.linkedin.com/v2/userinfo",
        "pkce": False,  # requires opt-in via LinkedIn support
    },
    "microsoft": {
        "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "userinfo_url": "https://graph.microsoft.com/oidc/userinfo",
    },
    "apple": {
        "auth_url": "https://appleid.apple.com/auth/authorize",
        "token_url": "https://appleid.apple.com/auth/token",
        "userinfo_url": None,
        "extra_auth_params": {"response_mode": "form_post"},
    },
    "discord": {
        "auth_url": "https://discord.com/api/oauth2/authorize",
        "token_url": "https://discord.com/api/oauth2/token",
        "userinfo_url": "https://discord.com/api/users/@me",
    },
    "slack": {
        "auth_url": "https://slack.com/openid/connect/authorize",
        "token_url": "https://slack.com/api/openid.connect.token",
        "userinfo_url": "https://slack.com/api/openid.connect.userInfo",
    },
}


def build_pkce_verifier() -> str:
    """Create a PKCE code verifier."""
    return secrets.token_urlsafe(64)


def build_pkce_challenge(verifier: str) -> str:
    """Create a PKCE S256 code challenge from a verifier."""
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("utf-8")


def build_authorize_url(
    provider: str,
    client_id: str,
    redirect_uri: str,
    scope: Optional[str] = None,
    state: Optional[str] = None,
    response_type: str = "code",
    code_challenge: Optional[str] = None,
    code_challenge_method: str = "S256",
    extra_params: Optional[Dict[str, str]] = None,
) -> str:
    """Build an OAuth authorization URL for the given provider."""
    config = PROVIDER_CONFIG.get(provider)
    if not config:
        raise ValueError(f"Unsupported provider: {provider}")

    if not client_id or not redirect_uri:
        raise ValueError("client_id and redirect_uri are required")

    params: Dict[str, str] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": response_type,
    }

    if scope:
        params["scope"] = scope

    if state:
        params["state"] = state

    if code_challenge:
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = code_challenge_method

    if config.get("extra_auth_params"):
        params.update(config["extra_auth_params"])

    if extra_params:
        params.update(extra_params)

    return f"{config['auth_url']}?{urlencode(params)}"


def exchange_code_for_tokens(
    provider: str,
    code: str,
    redirect_uri: str,
    client_id: str,
    client_secret: Optional[str] = None,
    code_verifier: Optional[str] = None,
    extra_params: Optional[Dict[str, str]] = None,
    timeout: int = 10,
) -> Dict[str, Any]:
    """Exchange an OAuth authorization code for tokens."""
    config = PROVIDER_CONFIG.get(provider)
    if not config:
        raise ValueError(f"Unsupported provider: {provider}")

    use_basic_auth = config.get("token_auth") == "basic"

    data: Dict[str, str] = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }

    # Only put client_id in body when not using Basic Auth (avoid duplicate credentials)
    if not use_basic_auth:
        data["client_id"] = client_id

    if code_verifier:
        data["code_verifier"] = code_verifier

    if extra_params:
        data.update(extra_params)

    headers = dict(config.get("token_headers", {}))

    auth = None
    if use_basic_auth:
        auth = (client_id, client_secret or "")
    elif client_secret:
        data["client_secret"] = client_secret

    resp = requests.post(config["token_url"], data=data, headers=headers, auth=auth, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def fetch_userinfo(
    provider: str,
    access_token: str,
    extra_params: Optional[Dict[str, str]] = None,
    timeout: int = 10,
) -> Optional[Dict[str, Any]]:
    """Fetch user profile info from the provider if supported."""
    config = PROVIDER_CONFIG.get(provider)
    if not config:
        raise ValueError(f"Unsupported provider: {provider}")

    userinfo_url = config.get("userinfo_url")
    if not userinfo_url:
        return None

    headers = dict(config.get("userinfo_headers", {}))
    params: Dict[str, str] = dict(config.get("userinfo_params", {}))

    token_param = config.get("userinfo_token_param")
    if token_param:
        params[token_param] = access_token
    else:
        headers["Authorization"] = f"Bearer {access_token}"

    if extra_params:
        params.update(extra_params)

    resp = requests.get(userinfo_url, headers=headers, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def verify_oauth_callback(
    provider: str,
    code: str,
    redirect_uri: str,
    client_id: str,
    client_secret: Optional[str] = None,
    code_verifier: Optional[str] = None,
    extra_token_params: Optional[Dict[str, str]] = None,
    extra_userinfo_params: Optional[Dict[str, str]] = None,
    timeout: int = 10,
) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    """Exchange code for tokens and optionally fetch userinfo."""
    tokens = exchange_code_for_tokens(
        provider=provider,
        code=code,
        redirect_uri=redirect_uri,
        client_id=client_id,
        client_secret=client_secret,
        code_verifier=code_verifier,
        extra_params=extra_token_params,
        timeout=timeout,
    )

    access_token = tokens.get("access_token")
    userinfo = None
    if access_token:
        userinfo = fetch_userinfo(
            provider=provider,
            access_token=access_token,
            extra_params=extra_userinfo_params,
            timeout=timeout,
        )

    return tokens, userinfo
