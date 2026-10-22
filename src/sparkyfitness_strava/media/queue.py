"""Immutable export snapshots; browser work never holds the connector database lock."""
import hashlib
import json
import os
import tempfile
from pathlib import Path


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.pending-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        if os.name != "nt":
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def snapshot(plan, config):
    return {'payload': plan['payload'], 'title': plan['name'],
            'timezone': config.timezone, 'units': config.media_units,
            'primary': list(plan.get('muscles', {}).get('primary', [])),
            'secondary': list(plan.get('muscles', {}).get('secondary', [])),
            'unmapped_muscles': list(plan.get('muscles', {}).get('unmapped_muscles', []))}


def enqueue(config, state, record):
    if record.get('state') != 'exported' or not record.get('media'):
        return
    activity = str(record['activity_id'])
    athlete = str(state.get('strava_athlete'))
    if not activity.isdigit() or not athlete.isdigit():
        raise ValueError('Invalid media destination')
    job = {**record['media'], 'activity_id': activity, 'athlete_id': athlete}
    job['fingerprint'] = hashlib.sha256(json.dumps(job, sort_keys=True).encode()).hexdigest()
    path = config.data_dir / 'media' / 'outbox' / (activity + '.json')
    if path.exists():
        if json.loads(path.read_text()) != job:
            raise ValueError('Media job changed after export')
    else:
        atomic(path, job)
