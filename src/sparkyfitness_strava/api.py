from email.utils import parsedate_to_datetime
import time
from urllib.parse import urlsplit
import httpx


class APIError(RuntimeError):
    def __init__(self, method, path, status=None):
        self.status = status
        super().__init__(f"{method} {urlsplit(path).path}: " + (f"HTTP {status}" if status else "network error"))


class UnknownWrite(APIError):
    pass


class API:
    def __init__(self, base, state=None, headers=None, transport=None):
        self.base, self.state = base, state
        self.client = httpx.Client(headers=headers, transport=transport, timeout=30, follow_redirects=False, trust_env=False)

    def close(self):
        self.client.close()

    def request(self, method, path, **kwargs):
        url = path if path.startswith(("http://", "https://")) else self.base + path
        if urlsplit(url)[:2] != urlsplit(self.base)[:2]:
            raise ValueError("Refusing pagination outside the configured API origin")
        if self.state and self.state.get("cooldown", 0) > time.time():
            raise APIError(method, path, 429)
        try:
            response = self.client.request(method, url, **kwargs)
        except httpx.TransportError:
            raise (UnknownWrite if method != "GET" else APIError)(method, path) from None
        if response.status_code == 429:
            delay = 900
            retry = response.headers.get("Retry-After")
            if retry:
                try:
                    delay = max(delay, float(retry))
                except ValueError:
                    try:
                        delay = max(delay, parsedate_to_datetime(retry).timestamp() - time.time())
                    except (ValueError, TypeError):
                        pass
            # A daily exhaustion must wait until the next UTC day, not 15 minutes.
            for prefix in ["X-RateLimit", "X-ReadRateLimit"]:
                try:
                    limit = [int(x) for x in response.headers[prefix + "-Limit"].split(",")]
                    usage = [int(x) for x in response.headers[prefix + "-Usage"].split(",")]
                    if usage[1] >= limit[1]:
                        delay = max(delay, 86400 - time.time() % 86400 + 1)
                except (KeyError, IndexError, ValueError):
                    pass
            if self.state:
                self.state.set("cooldown", time.time() + delay)
        if not response.is_success:
            error = UnknownWrite if method != "GET" and response.status_code >= 500 else APIError
            raise error(method, path, response.status_code)
        try:
            return response.json()
        except ValueError:
            raise (UnknownWrite if method != "GET" else APIError)(method, path, response.status_code) from None


class SparkyFitness(API):
    def __init__(self, config, **kwargs):
        if not config.sparkyfitness_api_key:
            raise ValueError("Set SPARKYFITNESS_API_KEY to your SparkyFitness API key")
        super().__init__(config.sparkyfitness_url, headers={"x-api-key": config.sparkyfitness_api_key}, **kwargs)

    def request(self, method, path, **kwargs):
        if method != "GET":
            raise ValueError("The SparkyFitness source client is read-only")
        return super().request(method, path, **kwargs)

    def sessions(self):
        number = 1
        seen = set()
        while True:
            page = self.request("GET", "/api/v2/exercise-entries/history", params={"page": number, "pageSize": 100})
            if not isinstance(page, dict) or not isinstance(page.get("sessions"), list):
                raise ValueError("Invalid SparkyFitness exercise history response")
            pagination = page.get("pagination", {})
            if pagination.get("page") != number or not isinstance(pagination.get("hasMore"), bool):
                raise ValueError("Invalid SparkyFitness history pagination")
            fresh = 0
            for session in page["sessions"]:
                identity = (session["type"], str(session["id"]))
                if identity not in seen:
                    seen.add(identity)
                    fresh += 1
                    yield session
            if not pagination["hasMore"]:
                return
            if not fresh:
                raise ValueError("Repeated or empty SparkyFitness history page")
            number += 1


class Strava(API):
    def __init__(self, config, state, **kwargs):
        super().__init__(config.strava_url, state, **kwargs)
        self.config = config

    @staticmethod
    def credentials(result):
        if not isinstance(result, dict) or any(not isinstance(result.get(k), str) or not result[k] for k in ("access_token", "refresh_token")):
            raise ValueError("Strava returned an invalid OAuth token response; authorize again")
        if not isinstance(result.get("expires_at"), int) or result["expires_at"] <= 0:
            raise ValueError("Strava returned an invalid token expiry; authorize again")
        return {key: result[key] for key in ("access_token", "refresh_token", "expires_at")}

    def token(self):
        token = self.state.get("oauth")
        if not token:
            raise ValueError("Authorize Strava first with auth-url and auth-complete")
        self.state.bind("strava_app", {"url": self.base, "client": self.config.client_id})
        if token["expires_at"] > time.time() + 120:
            return token["access_token"]
        if self.state.get("refresh_uncertain"):
            raise ValueError("OAuth refresh outcome is uncertain; authorize again")
        self.state.set("refresh_uncertain", True)
        try:
            result = self.request("POST", "/oauth/token", data={
                "client_id": self.config.client_id, "client_secret": self.config.client_secret,
                "grant_type": "refresh_token", "refresh_token": token["refresh_token"]})
        except UnknownWrite:
            raise
        except APIError:
            self.state.set("refresh_uncertain", False)
            raise
        # Persist the newest token before any other API calls; never reuse .env tokens.
        updated = {**token, **self.credentials(result)}
        self.state.set("oauth", updated)
        self.state.set("refresh_uncertain", False)
        return updated["access_token"]

    def call(self, method, path, **kwargs):
        return self.request(method, "/api/v3" + path, headers={"Authorization": "Bearer " + self.token()}, **kwargs)

    def authorize(self, code, scopes):
        if not self.config.client_id or not self.config.client_secret:
            raise ValueError("Set STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET")
        if not {"read", "activity:write", "activity:read_all"} <= set(scopes.replace(",", " ").split()):
            raise ValueError("Strava authorization must grant read, activity:write and activity:read_all")
        self.state.bind("strava_app", {"url": self.base, "client": self.config.client_id})
        result = self.request("POST", "/oauth/token", data={
            "client_id": self.config.client_id, "client_secret": self.config.client_secret,
            "grant_type": "authorization_code", "code": code})
        credentials = self.credentials(result)
        if not isinstance(result.get("athlete"), dict) or not result["athlete"].get("id"):
            raise ValueError("Strava did not return the authorized athlete ID")
        athlete = str(result["athlete"]["id"])
        self.state.bind("strava_athlete", athlete)
        self.state.set("oauth", credentials)
        self.state.set("refresh_uncertain", False)
        self.state.set("oauth_scopes", scopes)
        return athlete
