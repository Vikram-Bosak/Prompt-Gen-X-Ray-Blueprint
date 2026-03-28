#!/usr/bin/env python3
"""Create .env file from environment variables for GitHub Actions."""

import os
import json
import base64


def create_env():
    """Create api_keys/.env file from environment variables."""
    secrets = {
        "NVIDIA_API_KEY": os.environ.get("NVIDIA_API_KEY", ""),
        "GOOGLE_SHEET_ID": os.environ.get("GOOGLE_SHEET_ID", ""),
        "GOOGLE_DRIVE_FOLDER_ID": os.environ.get("GOOGLE_DRIVE_FOLDER_ID", ""),
        "TELEGRAM_BOT_TOKEN": os.environ.get("TELEGRAM_BOT_TOKEN", ""),
        "TELEGRAM_CHAT_ID": os.environ.get("TELEGRAM_CHAT_ID", ""),
        "SERVICE_ACCOUNT_JSON": os.environ.get("SERVICE_ACCOUNT_JSON", ""),
    }

    os.makedirs("api_keys", exist_ok=True)

    # Decode base64 if needed and re-encode as base64 for .env storage
    sa_json = secrets.get("SERVICE_ACCOUNT_JSON", "")
    if sa_json:
        try:
            decoded = base64.b64decode(sa_json.encode()).decode()
            json.loads(decoded)  # Verify it's valid JSON
            # Store as base64 in .env file (no escaping issues)
            secrets["SERVICE_ACCOUNT_JSON"] = base64.b64encode(
                decoded.encode()
            ).decode()
            print("SERVICE_ACCOUNT_JSON: decoded and stored as base64")
        except Exception as e:
            print(f"SERVICE_ACCOUNT_JSON: keeping as-is (decode failed: {e})")

    with open("api_keys/.env", "w") as f:
        for key, value in secrets.items():
            f.write(f"{key}={value}\n")

    # Verify SERVICE_ACCOUNT_JSON (unescape first)
    with open("api_keys/.env") as f:
        for line in f:
            if line.startswith("SERVICE_ACCOUNT_JSON="):
                json_str = line.split("=", 1)[1].strip()
                # Unescape for verification
                json_str_unescaped = json_str.replace("\\n", "\n")
                try:
                    data = json.loads(json_str_unescaped)
                    print(f"Valid! Project: {data.get('project_id')}")
                    print(f"Has private key: {'private_key' in data}")
                except Exception as e:
                    print(f"JSON Error: {e}")
                    print(f"First 100 chars: {json_str[:100]}")
                break

    print("Created api_keys/.env")


if __name__ == "__main__":
    create_env()
