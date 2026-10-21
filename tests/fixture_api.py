"""Test-only write client, separate from the connector's read-only source client."""
import json
from http.cookiejar import CookieJar
from urllib.error import HTTPError
from urllib.request import Request, build_opener, HTTPCookieProcessor


class FixtureAPI:
    def __init__(self, base, api_key=None):
        self.base, self.api_key = base.rstrip("/"), api_key
        self.opener = build_opener(HTTPCookieProcessor(CookieJar()))

    def request(self, path, data=None, method=None):
        headers = {"Content-Type": "application/json", "Origin": self.base}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        request = Request(self.base + path, headers=headers, method=method or ("POST" if data is not None else "GET"),
                          data=None if data is None else json.dumps(data).encode())
        try:
            with self.opener.open(request, timeout=30) as response:
                raw = response.read()
                return json.loads(raw) if raw else None
        except HTTPError as error:
            raise RuntimeError(f"Fixture API {request.method} {path}: HTTP {error.code}") from None
