# backend/app/services/acled_client.py

from __future__ import annotations

import os
import time
from typing import Any, Dict, Iterable, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()


class ACLEDApiError(RuntimeError):
    """Raised when the ACLED API responds with a non-200 or malformed response."""
    pass


class ACLEDClient:
    """
    Thin ACLED API client using OAuth2 password grant and JSON responses.

    - Auth:
        POST https://acleddata.com/oauth/token
        body: username, password, grant_type=password, client_id=acled

    - Data:
        GET https://acleddata.com/api/acled/read
        params example:
            terms=accept
            country=Sudan
            event_date=2024-01-01
            event_date_where=AFTER
            _format=json
            page=1
            limit=1000
    """

    TOKEN_URL = "https://acleddata.com/oauth/token"
    BASE_URL = "https://acleddata.com/api/acled/read"

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        base_url: Optional[str] = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.username = username or os.getenv("ACLED_USERNAME")
        self.password = password or os.getenv("ACLED_PASSWORD")

        if not self.username or not self.password:
            raise RuntimeError(
                "ACLED_USERNAME and ACLED_PASSWORD must be set in environment."
            )

        self.base_url = base_url or self.BASE_URL
        self.session = session or requests.Session()

        self.access_token: Optional[str] = None
        self.token_expiry: float = 0.0  # unix timestamp

        # Authenticate immediately
        self._authenticate()

    # ------------------------------------------------------------------ #
    # Auth helpers                                                       #
    # ------------------------------------------------------------------ #

    def _authenticate(self) -> None:
        """
        Fetch a fresh access token from ACLED using the password grant.

        On success, sets self.access_token, self.token_expiry, and
        updates session headers with the Bearer token.
        """
        data = {
            "username": self.username,
            "password": self.password,
            "grant_type": "password",
            "client_id": "acled",
        }

        resp = self.session.post(self.TOKEN_URL, data=data, timeout=30)
        if resp.status_code != 200:
            body = resp.text[:300].replace("\n", " ")
            raise ACLEDApiError(
                f"ACLED token request failed: {resp.status_code} {body}..."
            )

        try:
            payload = resp.json()
        except Exception as e:
            raise ACLEDApiError(f"Failed to parse ACLED token JSON: {e}") from e

        token = payload.get("access_token")
        if not token:
            raise ACLEDApiError("ACLED token response missing 'access_token' field.")

        expires_in = int(payload.get("expires_in", 86400))
        # refresh 60s before expiry
        self.token_expiry = time.time() + expires_in - 60
        self.access_token = token

        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def _ensure_token(self) -> None:
        """Refresh the token if it is close to expiring."""
        if not self.access_token or time.time() >= self.token_expiry:
            self._authenticate()

    # ------------------------------------------------------------------ #
    # Low-level request helper                                           #
    # ------------------------------------------------------------------ #

    def _get_json_page(
        self,
        params: Dict[str, Any],
        page: int,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Make a single paged GET request to ACLED and return a list of dict rows.

        If there are no rows for this page, returns [].
        Raises ACLEDApiError on non-200 or malformed responses.
        """
        self._ensure_token()

        query_params = dict(params)  # shallow copy
        query_params.setdefault("terms", "accept")
        query_params.setdefault("_format", "json")
        query_params["page"] = page
        query_params["limit"] = limit

        resp = self.session.get(self.base_url, params=query_params, timeout=60)

        if resp.status_code != 200:
            body = resp.text[:300].replace("\n", " ")
            print("⚠️ ACLED API non-200 response")
            print(f"   URL:    {resp.url}")
            print(f"   Status: {resp.status_code}")
            print(f"   Body:   {body}...")
            raise ACLEDApiError(
                f"ACLED read failed (page {page}): {resp.status_code} {body}"
            )

        try:
            data = resp.json()
        except Exception as e:
            body = resp.text[:200].replace("\n", " ")
            raise ACLEDApiError(
                f"Failed to parse ACLED JSON (page {page}): {e}; body starts: {body}..."
            ) from e

        # New ACLED API seems to return a bare JSON array: []
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]

        # Defensive: if they ever wrap in an object
        if isinstance(data, dict):
            # Try common keys
            for key in ("data", "results", "items"):
                val = data.get(key)
                if isinstance(val, list):
                    return [row for row in val if isinstance(row, dict)]
            # If no recognizable structure, just bail
            raise ACLEDApiError(
                f"Unexpected ACLED JSON structure (page {page}): top-level keys={list(data.keys())}"
            )

        # Anything else is unexpected
        raise ACLEDApiError(
            f"Unexpected ACLED JSON type (page {page}): {type(data)}"
        )

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #

    def fetch_events_dicts(
        self,
        params: Dict[str, Any],
        max_pages: int = 10,
        per_page: int = 1000,
    ) -> Iterable[Dict[str, Any]]:
        """
        Yield ACLED event rows as dicts across pages.

        Example params:
            {
                "country": "Sudan",
                "event_date": "2024-01-01",
                "event_date_where": "AFTER",
                "terms": "accept",
            }

        Yields:
            dict rows directly compatible with pandas.DataFrame(list(rows)).
        """
        for page in range(1, max_pages + 1):
            rows = self._get_json_page(params=params, page=page, limit=per_page)

            if not rows:
                # No rows for this page -> we are done
                break

            for row in rows:
                yield row

            # If fewer rows than per_page, there are no further pages
            if len(rows) < per_page:
                break
