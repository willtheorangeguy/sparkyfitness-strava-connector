"""Verify colors in a real browser after source metadata survives the image queue."""
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
pytest.importorskip('playwright.sync_api')
from playwright.sync_api import sync_playwright
from sparkyfitness_strava.media.muscles import collect
from sparkyfitness_strava.media.queue import snapshot, enqueue
from sparkyfitness_strava.media.summary import from_activity
from sparkyfitness_strava.media.render import html
from sparkyfitness_strava.state import State


def test_queued_muscles_have_primary_secondary_colors_on_both_views(tmp_path):
    config = SimpleNamespace(data_dir=tmp_path, timezone='America/Edmonton', media_units='lb')
    groups = collect([{'primary_muscles':['chest','quadriceps','abdominals'],
                       'secondary_muscles':['triceps','shoulders','glutes','hamstrings']}])
    plan = {'name':'Muscle highlight verification', 'muscles': groups,
            'payload': {'start_time':'2026-10-21T18:00:00Z', 'elapsed_time':900,
                        'sets':[{'exercise_type':'BARBELL_BENCH_PRESS','weight':40,'repetitions':8}]}}
    state = State(tmp_path)
    try:
        state.set('strava_athlete','42')
        enqueue(config, state, {'state':'exported','activity_id':'123','media':snapshot(plan,config)})
    finally:
        state.close()
    job = json.loads((tmp_path/'media/outbox/123.json').read_text())
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chromium')
        try:
            page = browser.new_page(viewport={'width':1080,'height':1080})
            page.route('**/*', lambda route: route.abort())
            page.set_content(html(from_activity(job), 'dark', 'summary'))
            page.evaluate('document.fonts.ready')
            for region in ['chest','quads','abs']:
                paths = page.locator(f'.muscle.primary[data-muscle="{region}"]')
                assert paths.count() == 2
                assert paths.first.evaluate('(e)=>getComputedStyle(e).fill') == 'rgb(90, 158, 245)'
            for region in ['triceps','shoulders','glutes','hamstrings']:
                paths = page.locator(f'.muscle.secondary[data-muscle="{region}"]')
                assert paths.count() >= 2
                assert paths.first.evaluate('(e)=>getComputedStyle(e).fill') == 'rgb(163, 206, 247)'
            assert page.locator('.muscle[data-muscle="calves"]').first.evaluate('(e)=>getComputedStyle(e).fill') == 'rgb(38, 57, 80)'
            Path('/reports').mkdir(exist_ok=True)
            page.screenshot(path='/reports/muscle-highlights.png')
        finally:
            browser.close()
