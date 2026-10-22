import json
from types import SimpleNamespace
from sparkyfitness_strava.media.muscles import collect, sparky_session
from sparkyfitness_strava.media.queue import snapshot
from sparkyfitness_strava.media.summary import from_activity
from sparkyfitness_strava.media.render import html


def test_normalizes_source_anatomy_and_primary_wins_across_exercises():
    groups = collect([
        {'primary_muscles': ['Quadriceps', 'lower_back'], 'secondary_muscles': ['GLUTES', 'hamstrings']},
        {'primary_muscles': ['gluteus maximus'], 'secondary_muscles': ['quadriceps', 'hip adductors', 'Unknown custom muscle']},
    ])
    assert groups == {'primary': ['glutes', 'lower_back', 'quads'],
                      'secondary': ['adductors', 'hamstrings'], 'unmapped_muscles': ['Unknown custom muscle']}


def test_wger_english_and_latin_names_ignore_ids_and_unknown_regions():
    assert collect([{'muscles': [{'id': 4, 'name_en': '', 'name': 'Pectoralis major'}],
                     'muscles_secondary': [{'name_en': 'Triceps', 'name': 'Triceps brachii'}, 99]}],
                   'muscles', 'muscles_secondary') == {
                       'primary': ['chest'], 'secondary': ['triceps'], 'unmapped_muscles': []}
    assert collect([{'primary_muscles': ['Unrecognized muscle'], 'secondary_muscles': None}]) == {
        'primary': [], 'secondary': [], 'unmapped_muscles': ['Unrecognized muscle']}


def test_only_completed_exercises_reach_snapshot_and_rendered_highlights():
    groups = sparky_session({'exercises': [
        {'exercise_snapshot': {'primary_muscles': ['chest'], 'secondary_muscles': ['triceps']},
         'sets': [{'completed_at': '2026-10-21T15:00:00Z'}]},
        {'exercise_snapshot': {'primary_muscles': ['quadriceps']}, 'sets': [{'completed_at': None}]},
    ]})
    plan = {'name': 'Bench', 'muscles': groups, 'payload': {
        'start_time': '2026-10-21T14:00:00Z', 'elapsed_time': 900,
        'sets': [{'exercise_type': 'BARBELL_BENCH_PRESS', 'weight': 40, 'repetitions': 8}]}}
    job = json.loads(json.dumps(snapshot(plan, SimpleNamespace(timezone='America/Edmonton', media_units='lb'))))
    summary = from_activity(job)
    assert summary['primary'] == ['chest'] and summary['secondary'] == ['triceps']
    markup = html(summary, 'dark', 'summary')
    assert 'class="muscle primary" data-muscle="chest"' in markup
    assert 'class="muscle secondary" data-muscle="triceps"' in markup
    assert 'class="muscle inactive" data-muscle="quads"' in markup
