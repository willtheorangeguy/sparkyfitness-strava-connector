"""Exercise the persistent CLI watcher through a real synchronization engine."""
from datetime import datetime, timedelta, timezone

import pytest

from sparkyfitness_strava import cli
from sparkyfitness_strava.api import APIError
from sparkyfitness_strava.config import Config
from sparkyfitness_strava.engine import Engine
from sparkyfitness_strava.state import State


class Source:
    exercise_id = "963d8112-df67-41d3-adc9-3bf0809777da"

    def __init__(self, up):
        self.up, self.complete, self.closed = up, False, False
        self.day = (datetime.now(timezone.utc) - timedelta(days=2)).date().isoformat()

    def request(self, method, path):
        if not self.up:
            raise APIError(method, path)
        assert method == "GET" and path == "/api/identity/user"
        return {"authenticatedUserId": "watch-test", "activeUserId": "watch-test"}

    def sessions(self):
        return [{"type": "preset", "id": "session", "workout_preset_id": 1,
                 "entry_date": self.day, "name": "Watch test", "exercises": [{
                     "id": "entry", "exercise_id": self.exercise_id, "entry_date": self.day,
                     "entry_time": "10:00", "duration_minutes": 60,
                     "exercise_snapshot": {"modality": "weight_reps"}, "sets": [{
                         "id": 1, "set_number": 1, "reps": 8, "weight": 100,
                         "completed_at": self.day + "T10:05:00Z" if self.complete else None}]}]}]

    def close(self):
        self.closed = True


class Destination:
    def __init__(self):
        self.uploads, self.polls, self.closed = [], 0, False

    def call(self, method, path, **kwargs):
        if path == "/athlete":
            return {"id": 123}
        if method == "POST":
            assert path == "/uploads"
            self.uploads.append(kwargs)
            return {"id": 7, "external_id": kwargs["data"]["external_id"], "activity_id": None}
        assert path == "/uploads/7"
        self.polls += 1
        return {"id": 7, "external_id": self.uploads[0]["data"]["external_id"], "activity_id": 99}

    def close(self):
        self.closed = True


@pytest.mark.parametrize("initial_outage", [False, True])
def test_watch_detects_later_completion_and_exports_once_without_manual_sync(tmp_path, monkeypatch, capsys, initial_outage):
    source, destination = Source(not initial_outage), Destination()
    config = Config(tmp_path, "https://source.test", "test-key", "client", "secret", since=source.day)
    state = State(tmp_path)
    state.set("mappings", {source.exercise_id: "BARBELL_BENCH_PRESS"})
    state.close()
    monkeypatch.setattr(cli.Config, "env", lambda: config)
    monkeypatch.setattr(cli, "Engine", lambda config, state: Engine(config, state, source, destination))
    monkeypatch.setattr("sys.argv", ["connector", "watch"])
    sleeps = []

    def next_cycle(seconds):
        sleeps.append(seconds)
        if len(sleeps) == 1:
            assert not destination.uploads
            source.up = True
        elif len(sleeps) == 2:
            assert not destination.uploads
            # The source workout completes after the watcher is already running.
            source.complete = True
        elif len(sleeps) == 4:
            raise KeyboardInterrupt

    monkeypatch.setattr(cli.time, "sleep", next_cycle)
    cli.main()
    assert sleeps == [900] * 4
    assert len(destination.uploads) == 1 and destination.polls == 1
    assert source.closed and destination.closed
    output = capsys.readouterr()
    assert '"submitted": 1' in output.out
    assert ("network error" in output.err) == initial_outage
    reopened = State(tmp_path)
    try:
        assert reopened.get("last_cycle")
        assert [record["state"] for record in reopened.exports().values()] == ["exported"]
    finally:
        reopened.close()
