import time
from urllib.parse import urlencode
import httpx
import pytest
from sparkyfitness_strava.api import API, APIError, Strava, UnknownWrite
from sparkyfitness_strava.cli import complete_callback
from sparkyfitness_strava.config import Config
from sparkyfitness_strava.state import State
from sparkyfitness_strava.workout import EXERCISES, build


def test_state_is_durable_bound_and_exclusive(tmp_path):
    state = State(tmp_path)
    try:
        state.bind("account", {"id": 1})
        with pytest.raises(ValueError, match="Account"):
            state.bind("account", {"id": 2})
        state.save("session", {"state": "uncertain"})
        with pytest.raises(ValueError, match="Another connector"):
            State(tmp_path)
    finally:
        state.close()
    reopened = State(tmp_path)
    try:
        assert reopened.export("session") == {"state": "uncertain"}
    finally:
        reopened.close()


def test_pagination_origin_does_not_leak_auth():
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={})
    api = API("https://sparkyfitness.test", headers={"Authorization": "Token test"}, transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ValueError):
            api.request("GET", "https://attacker.test/steal")
        assert not requests
    finally:
        api.close()


@pytest.mark.parametrize("status,error", [(400, APIError), (401, APIError), (500, UnknownWrite), (503, UnknownWrite)])
def test_post_never_retries_and_errors_do_not_include_secrets(status, error):
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(status, json={"secret": "private-token-value"})
    api = API("https://strava.test", transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(error) as failure:
            api.request("POST", "/api/v3/uploads", json={})
        assert "private-token-value" not in str(failure.value)
        assert len(requests) == 1
    finally:
        api.close()


def test_daily_rate_limit_is_persisted_without_retrying(tmp_path):
    state = State(tmp_path)
    api = API("https://strava.test", state=state, transport=httpx.MockTransport(lambda request: httpx.Response(
        429, headers={"Retry-After": "120", "X-RateLimit-Limit": "200,2000", "X-RateLimit-Usage": "200,2000"}, json={})))
    try:
        with pytest.raises(APIError):
            api.request("POST", "/api/v3/uploads")
        assert state.get("cooldown") >= time.time() + 86400 - time.time() % 86400 - 1
    finally:
        api.close()
        state.close()


def test_oauth_callback_checks_nonce_expiry_and_consent(tmp_path):
    state = State(tmp_path)
    try:
        state.set("authorization", {"state": "good", "expires": time.time() + 60})
        good = "http://localhost/strava/callback?" + urlencode({"state": "good", "code": "code", "scope": "read,activity:write"})
        assert complete_callback(state, good) == ("code", "read,activity:write")
        with pytest.raises(ValueError, match="state"):
            complete_callback(state, good.replace("good", "wrong"))
        with pytest.raises(ValueError, match="declined"):
            complete_callback(state, "http://localhost/?state=good&error=access_denied")
        state.set("authorization", {"state": "good", "expires": 0})
        with pytest.raises(ValueError, match="expired"):
            complete_callback(state, good)
    finally:
        state.close()


def test_oauth_refresh_rotation_is_durable_and_not_repeated(tmp_path):
    config = Config(tmp_path, "https://sparkyfitness.test", "token", "client", "secret", "https://strava.test")
    state = State(tmp_path)
    calls = []
    state.set("oauth", {"access_token": "old", "refresh_token": "refresh-old", "expires_at": 0})
    def handler(request):
        calls.append(request)
        assert b"refresh_token=refresh-old" in request.content
        return httpx.Response(200, json={"access_token": "new", "refresh_token": "refresh-new", "expires_at": int(time.time())+3600})
    api = Strava(config, state, transport=httpx.MockTransport(handler))
    try:
        assert api.token() == api.token() == "new"
        assert len(calls) == 1 and state.get("oauth")["refresh_token"] == "refresh-new"
        state.set("refresh_uncertain", True)
        state.set("oauth", {"access_token": "old", "refresh_token": "refresh-old", "expires_at": 0})
        with pytest.raises(ValueError, match="uncertain"):
            api.token()
    finally:
        api.close()
        state.close()


def test_refresh_lost_reply_blocks_reuse_after_restart(tmp_path):
    config = Config(tmp_path, "https://sparkyfitness.test", "token", "client", "secret", "https://strava.test")
    state = State(tmp_path)
    state.set("oauth", {"access_token": "old", "refresh_token": "refresh-old", "expires_at": 0})
    def lost(request):
        raise httpx.ReadTimeout("lost", request=request)
    api = Strava(config, state, transport=httpx.MockTransport(lost))
    try:
        with pytest.raises(UnknownWrite):
            api.token()
        assert state.get("refresh_uncertain")
    finally:
        api.close()
        state.close()
    reopened = State(tmp_path)
    api = Strava(config, reopened, transport=httpx.MockTransport(lost))
    try:
        with pytest.raises(ValueError, match="uncertain"):
            api.token()
    finally:
        api.close()
        reopened.close()


@pytest.mark.parametrize("response", [{}, {"access_token": "sensitive", "refresh_token": "sensitive", "expires_at": None}])
def test_invalid_token_responses_fail_without_revealing_credentials(response):
    with pytest.raises(ValueError) as error:
        Strava.credentials(response)
    assert "sensitive" not in str(error.value)


@pytest.mark.parametrize("url", ["file:///etc/passwd", "https://token@host", "https://host?key=token"])
def test_reject_credential_bearing_or_invalid_base_urls(tmp_path, url):
    with pytest.raises(ValueError):
        Config(tmp_path, url, "token", "client", "secret")
