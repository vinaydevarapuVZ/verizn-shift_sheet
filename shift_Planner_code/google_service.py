from __future__ import annotations

import os
from typing import Optional

import gspread
from google.oauth2 import service_account


SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


def open_google_sheet(sheet_url: Optional[str] = None, credentials_json: Optional[str] = None):
    """Open the Google Sheet using a service account JSON private key."""
    if gspread is None:
        raise ModuleNotFoundError("Install dependencies: pip install gspread google-auth")

    resolved_path = credentials_json or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not resolved_path:
        raise FileNotFoundError(
            "Service account JSON not found. Set GOOGLE_SERVICE_ACCOUNT_JSON or pass --credentials-json."
        )

    creds = service_account.Credentials.from_service_account_file(
        resolved_path,
        scopes=SCOPES,
    )
    client = gspread.authorize(creds)

    resolved_url = sheet_url or os.getenv("GOOGLE_SHEET_URL")
    if not resolved_url:
        raise ValueError(
            "No Google Sheet URL found. Set GOOGLE_SHEET_URL or pass --sheet-url."
        )

    return client.open_by_url(resolved_url)
