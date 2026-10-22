import json
from decimal import Decimal
from types import SimpleNamespace
import pytest
from sparkyfitness_strava.media.queue import enqueue, snapshot
from sparkyfitness_strava.media.summary import from_activity
from sparkyfitness_strava.state import State


def fixture():
    return {'name': 'Test workout', 'payload': {'start_time': '2026-10-22T01:30:00Z', 'elapsed_time': 900,
            'sets': [{'exercise_type': 'BARBELL_BENCH_PRESS', 'weight': 40, 'repetitions': 8},
                     {'exercise_type': 'BARBELL_BENCH_PRESS', 'weight': 40.8233133, 'repetitions': 6},
                     {'exercise_type': 'AIR_SQUAT', 'repetitions': 10},
                     {'exercise_type': 'PLANK_GENERIC', 'duration': 45}]}}


def test_summary_uses_exported_load_and_local_date():
    config = SimpleNamespace(timezone='America/Edmonton', media_units='lb')
    summary = from_activity(snapshot(fixture(), config))
    assert summary['volume_kg'] == Decimal('564.9398798')
    assert summary['volume'] == '1,245'
    assert summary['date'] == 'WEDNESDAY, OCTOBER 21'
    assert summary['duration'] == '15:00'
    assert summary['exercise_count'] == 3 and summary['set_count'] == 4
    assert summary['primary'] == []  # Never invent unavailable muscle metadata.


def test_queue_requires_success_and_never_replaces_changed_job(tmp_path):
    config = SimpleNamespace(data_dir=tmp_path, timezone='America/Edmonton', media_units='lb')
    state = State(tmp_path)
    try:
        state.set('strava_athlete', '42')
        record = {'state': 'processing', 'activity_id': '123', 'media': snapshot(fixture(), config)}
        enqueue(config, state, record)
        assert not list(tmp_path.glob('media/outbox/*.json'))
        record['state'] = 'exported'
        enqueue(config, state, record)
        path = tmp_path / 'media/outbox/123.json'
        original = path.read_bytes()
        enqueue(config, state, record)
        assert path.read_bytes() == original
        assert json.loads(original)['athlete_id'] == '42'
        record['media']['title'] = 'Changed'
        with pytest.raises(ValueError, match='changed'):
            enqueue(config, state, record)
        assert path.read_bytes() == original
    finally:
        state.close()


def test_image_queue_failure_keeps_successful_workout_export(tmp_path):
    from sparkyfitness_strava.engine import Engine
    engine = Engine.__new__(Engine)
    engine.state = State(tmp_path)
    try:
        engine.state.set('strava_athlete', '42')
        unavailable = tmp_path / 'unavailable'
        unavailable.write_text('file, not a directory')
        engine.config = SimpleNamespace(data_dir=unavailable)
        record = {'state': 'exported', 'activity_id': '123', 'media': {'payload': {}}}
        engine.queue_media('workout', record)
        saved = engine.state.export('workout')
        assert saved['state'] == 'exported' and saved['activity_id'] == '123'
        assert saved['media_error']
    finally:
        engine.state.close()
