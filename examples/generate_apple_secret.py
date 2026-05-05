"""
Generate an Apple client secret (JWT) for Sign In with Apple.

Usage:
    python generate_apple_secret.py

Requirements:
    pip install PyJWT cryptography

The generated secret is valid for up to 6 months. Regenerate it before it expires
and update APPLE_CLIENT_SECRET in your .env file.
"""

import time
import os
import sys

try:
    import jwt
except ImportError:
    sys.exit("Missing dependency. Run: pip install PyJWT cryptography")

from dotenv import load_dotenv

HERE = os.path.dirname(__file__)
load_dotenv(os.path.join(HERE, ".env"))

TEAM_ID   = os.environ.get("APPLE_TEAM_ID", "")
CLIENT_ID = os.environ.get("APPLE_CLIENT_ID", "")
KEY_ID    = os.environ.get("APPLE_KEY_ID", "")
P8_FILE   = os.environ.get("APPLE_P8_FILE", "")

def generate_secret(team_id, client_id, key_id, p8_file, expiry_days=180):
    p8_path = p8_file if os.path.isabs(p8_file) else os.path.join(HERE, p8_file)
    if not os.path.exists(p8_path):
        sys.exit(f"Cannot find .p8 file at: {p8_path}")

    private_key = open(p8_path).read()
    now = int(time.time())

    payload = {
        "iss": team_id,
        "iat": now,
        "exp": now + 86400 * expiry_days,
        "aud": "https://appleid.apple.com",
        "sub": client_id,
    }

    return jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": key_id})


if __name__ == "__main__":
    missing = [k for k, v in {"TEAM_ID": TEAM_ID, "CLIENT_ID": CLIENT_ID, "KEY_ID": KEY_ID, "P8_FILE": P8_FILE}.items() if not v]
    if missing:
        sys.exit(f"Missing in .env: {', '.join(missing)}. Set APPLE_TEAM_ID, APPLE_CLIENT_ID, APPLE_KEY_ID, APPLE_P8_FILE.")

    secret = generate_secret(TEAM_ID, CLIENT_ID, KEY_ID, P8_FILE)
    print("\nYour APPLE_CLIENT_SECRET:\n")
    print(secret)
    print("\nAdd this to your .env file as APPLE_CLIENT_SECRET=<value above>")
    print("It expires in 180 days — regenerate before then.\n")
