#!/usr/bin/env python3
"""Interactive Google OAuth2 authentication helper for YouTube Data API v3.
Run this script once after saving credentials/youtube_client_secret.json.
It will open your default browser to grant YouTube upload permissions and save
the persistent refresh token to credentials/youtube_token.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from src.config import config, CREDENTIALS_DIR

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]


def authenticate_youtube() -> None:
    client_secrets = config.YOUTUBE_CLIENT_SECRETS_FILE
    token_file = config.YOUTUBE_TOKEN_FILE

    if not client_secrets.is_file():
        print(f"❌ Error: Client secrets file not found at: {client_secrets}")
        print("Please follow docs/SETUP_GUIDE.md Part 1 to download your client secret JSON from Google Cloud Console.")
        sys.exit(1)

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("❌ Error: google-auth-oauthlib is required.")
        print("Install dependencies with: pip install -r requirements.txt")
        sys.exit(1)

    print("🔑 Starting local OAuth2 consent flow for YouTube Shorts...")
    flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), SCOPES)
    creds = flow.run_local_server(port=8088, prompt="consent", access_type="offline")

    token_file.parent.mkdir(parents=True, exist_ok=True)
    with open(token_file, "w", encoding="utf-8") as f:
        f.write(creds.to_json())

    print(f"✅ Success! YouTube OAuth token saved to: {token_file}")
    print("You are now authorized to upload YouTube Shorts!")


if __name__ == "__main__":
    authenticate_youtube()
