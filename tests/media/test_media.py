from decimal import Decimal
import json
import os
import re
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen, Request

import pytest
pytest.importorskip('playwright.sync_api', reason='Media browser tests run in Dockerfile.media')
from playwright.sync_api import sync_playwright
from sparkyfitness_strava.media.browser import attach_mock, profile_lock, restore_session_cookies, save_session_cookies
from sparkyfitness_strava.media.comparisons import REFERENCES
from sparkyfitness_strava.media.render import html, render
from sparkyfitness_strava.media.summary import POUNDS_PER_KG, demo, formatted_volume, volume


@pytest.fixture(scope='module',autouse=True)
def reset_mock():
    with urlopen(Request(os.environ['MOCK_WEB_URL']+'/__reset',data=b'')) as response:
        assert response.status==200


def test_volume_counts_only_actual_external_load_repetitions():
    sets = [{'weight':100,'repetitions':10}, {'weight':50,'repetitions':4},
            {'repetitions':20}, {'duration':90,'weight':100}, {'weight':0,'repetitions':20}]
    assert volume(sets,'kg') == Decimal(1200)
    assert formatted_volume(sets,'lb') == '2,646'


@pytest.mark.parametrize('item', [{'weight':'NaN','repetitions':1},{'weight':-1,'repetitions':1},{'weight':10,'repetitions':'Infinity'}])
def test_invalid_volume_values(item):
    with pytest.raises(ValueError):
        volume([item])


def test_render_escapes_workout_names_and_rejects_unknown_design():
    summary = {**demo(),'title':'<script>document.cookie</script>'}
    assert '<script>' not in html(summary,'light','summary')
    with pytest.raises(ValueError):
        html(summary,'neon','summary')


def test_profile_has_exclusive_lock(tmp_path):
    with profile_lock(tmp_path):
        with pytest.raises(ValueError,match='busy'):
            with profile_lock(tmp_path):
                pass
    with profile_lock(tmp_path):
        assert tmp_path.stat().st_mode & 0o777 == 0o700


@pytest.mark.parametrize('theme',['light','dark'])
def test_headline_has_accessible_contrast(theme):
    def luminance(rgb):
        values=[channel/255 for channel in rgb]
        linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values]
        return sum(v*factor for v,factor in zip(linear,[.2126,.7152,.0722]))
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chromium')
        try:
            page=browser.new_page()
            page.set_content(html(demo(),theme,'summary'))
            colors=page.evaluate('''() => [getComputedStyle(document.querySelector('h1')).color,
                getComputedStyle(document.querySelector('.card')).backgroundColor].map(c => c.match(/\\d+/g).map(Number))''')
            light,dark=sorted(map(luminance,colors),reverse=True)
            assert (light+.05)/(dark+.05) >= 7
        finally:
            browser.close()


@pytest.fixture(scope='module')
def cards(tmp_path_factory):
    output=tmp_path_factory.mktemp('cards')
    render(output)
    return output


def sign_in(page, origin, athlete='123456'):
    page.goto(origin+'/login')
    page.get_by_label('Athlete ID').fill(athlete)
    page.get_by_role('button',name='Sign in').click()


def test_session_only_login_survives_browser_restart_and_logout_clears_saved_cookies(tmp_path):
    origin=os.environ['MOCK_WEB_URL']
    profile=tmp_path/'profile'
    with profile_lock(profile), sync_playwright() as p:
        context=p.chromium.launch_persistent_context(str(profile/'chromium'),headless=True,channel='chromium')
        try:
            page=context.new_page()
            sign_in(page,origin)
            # Match Strava's session-only authentication cookie, not Max-Age.
            cookie=next(cookie for cookie in context.cookies() if cookie['name']=='athlete')
            context.add_cookies([{**cookie,'expires':-1}])
            save_session_cookies(context,profile)
            assert (profile/'session-cookies.json').stat().st_mode & 0o777 == 0o600
        finally:
            context.close()
        context=p.chromium.launch_persistent_context(str(profile/'chromium'),headless=True,channel='chromium')
        try:
            restore_session_cookies(context,profile)
            page=context.new_page()
            page.goto(origin+'/activities/101')
            assert page.locator('[data-athlete-id]').get_attribute('data-athlete-id')=='123456'
            context.clear_cookies()
            save_session_cookies(context,profile)
            assert json.loads((profile/'session-cookies.json').read_text())==[]
        finally:
            context.close()


def test_four_cards_are_exact_size_and_render_deterministically(cards,tmp_path):
    render(tmp_path)
    individual = [path for path in cards.glob('*.png') if path.stem.startswith(('light-', 'dark-'))]
    for path in individual:
        raw=path.read_bytes()
        assert struct.unpack('>II',raw[16:24]) == (1080,1080)
        assert raw == (tmp_path/path.name).read_bytes()
    assert len(individual) == 4
    assert (cards/'concepts.png').read_bytes() == (tmp_path/'concepts.png').read_bytes()
    assert (cards/'comparison-catalog.png').read_bytes() == (tmp_path/'comparison-catalog.png').read_bytes()


def test_selected_dark_layout_and_all_comparison_subjects_fit():
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chromium')
        try:
            page=browser.new_page(viewport={'width':1080,'height':1080})
            page.set_content(html(demo(),'dark','summary'))
            page.evaluate('document.fonts.ready')
            assert page.locator('.footer').count()==0
            diagram=page.locator('.figure svg').first.bounding_box()
            assert diagram['height'] >= 500
            assert page.locator('.muscle-list').bounding_box()['y'] < 1020
            for reference in REFERENCES:
                pounds=Decimal(reference.kg)*POUNDS_PER_KG
                facts={**demo(),'volume_kg':Decimal(reference.kg),'volume':f'{pounds:,.0f}'}
                page.set_content(html(facts,'dark','comparison'))
                page.evaluate('document.fonts.ready')
                assert page.locator('h1').inner_text()==reference.name
                assert page.locator('.animal svg').count()==1
                assert page.locator('.footer').count()==0
                assert page.locator('.hero-number').evaluate('(e) => e.scrollWidth <= e.clientWidth'), reference.key
                assert page.locator('h1').evaluate('(e) => e.scrollHeight <= e.clientHeight'), reference.key
                assert page.locator('.sub').bounding_box()['y']+page.locator('.sub').bounding_box()['height'] < 540, reference.key
            # The largest catalog total must fit the summary's narrower column too.
            page.set_content(html(facts,'dark','summary'))
            page.evaluate('document.fonts.ready')
            assert page.locator('.metric .value').first.evaluate('(e) => e.scrollWidth <= e.clientWidth')
        finally:
            browser.close()


def test_browser_upload_persists_after_restart_and_never_repeats(cards,tmp_path):
    origin=os.environ['MOCK_WEB_URL']
    images=[cards/'light-summary.png',cards/'light-comparison.png']
    journal=tmp_path/'upload.json'
    with sync_playwright() as p:
        context=p.chromium.launch_persistent_context(str(tmp_path/'profile'),headless=True,channel='chromium')
        page=context.new_page()
        sign_in(page,origin)
        record=attach_mock(page,origin,101,123456,images,journal)
        assert record['state']=='attached'
        context.close()
        context=p.chromium.launch_persistent_context(str(tmp_path/'profile'),headless=True,channel='chromium')
        try:
            page=context.new_page()
            page.goto(origin+'/activities/101')
            assert page.locator('#photos img').count()==2
            assert attach_mock(page,origin,101,123456,images,journal)['state']=='attached'
            state=json.load(urlopen(origin+'/state'))
            assert state['posts']['101']==1
            with pytest.raises(ValueError,match='different activity'):
                attach_mock(page,origin,999,123456,images,journal)
        finally:
            context.close()


def test_mismatched_browser_account_cannot_upload(cards,tmp_path):
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chromium')
        try:
            page=browser.new_page()
            sign_in(page,os.environ['MOCK_WEB_URL'],'999')
            with pytest.raises(ValueError,match='Browser account'):
                attach_mock(page,os.environ['MOCK_WEB_URL'],102,123456,
                            [cards/'dark-summary.png',cards/'dark-comparison.png'],tmp_path/'job.json')
            assert not (tmp_path/'job.json').exists()
        finally:
            browser.close()


def test_ambiguous_save_is_held_instead_of_uploading_again(cards,tmp_path):
    journal=tmp_path/'job.json'
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chromium')
        try:
            page=browser.new_page()
            page.set_default_timeout(3000)
            origin=os.environ['MOCK_WEB_URL']
            sign_in(page,origin)
            page.route('**/activities/103',lambda route: route.abort() if route.request.method=='POST' else route.continue_())
            with pytest.raises(Exception):
                attach_mock(page,origin,103,123456,[cards/'light-summary.png',cards/'light-comparison.png'],journal)
            assert json.loads(journal.read_text())['state']=='uncertain'
            with pytest.raises(ValueError,match='uncertain'):
                attach_mock(page,origin,103,123456,[cards/'light-summary.png',cards/'light-comparison.png'],journal)
        finally:
            browser.close()


def test_prototype_will_not_target_live_strava(cards,tmp_path):
    with pytest.raises(ValueError,match='restricted'):
        attach_mock(None,'https://www.strava.com',101,123456,
                    [cards/'light-summary.png',cards/'light-comparison.png'],tmp_path/'job.json')


def test_expired_login_pauses_before_selecting_files(cards,tmp_path):
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chromium')
        try:
            page=browser.new_page()
            sign_in(page,os.environ['MOCK_WEB_URL'])
            page.context.clear_cookies()
            with pytest.raises(ValueError,match='needs login'):
                attach_mock(page,os.environ['MOCK_WEB_URL'],104,123456,
                            [cards/'light-summary.png',cards/'light-comparison.png'],tmp_path/'job.json')
            assert not (tmp_path/'job.json').exists()
        finally:
            browser.close()


def test_login_viewer_runs_without_a_host_display_as_nonroot():
    # Only the local mock is opened. A real Strava sign-in still needs a human.
    with tempfile.TemporaryDirectory(prefix='media-viewer-') as root:
        root=Path(root)
        root.chmod(0o755)
        # The non-root process owns its profile; the parent only owns the log FD.
        profile=root/'profile'
        profile.mkdir()
        os.chown(profile,10001,10001)
        # Reproduce a shared HOME made unwritable by earlier root-run browsers.
        shared_home=root/'shared-home'
        shared_home.mkdir(mode=0o755)
        (shared_home/'.config').mkdir(mode=0o755)
        environment={**os.environ,'BROWSER_PROFILE':str(profile),'MEDIA_LOGIN_URL':os.environ['MOCK_WEB_URL']+'/login',
                     'HOME':str(shared_home)}
        with (root/'viewer.log').open('w') as log:
            process=subprocess.Popen([sys.executable,'-m','sparkyfitness_strava.media.browser','login'],env=environment,
                                     stdout=log,stderr=log,user=10001,group=10001)
            try:
                for _ in range(100):
                    if process.poll() is not None:
                        details=(root/'viewer.log').read_text()[-6000:]
                        details=re.sub(r'Temporary viewer password: .*','Temporary viewer password: [redacted]',details)
                        pytest.fail('Login viewer exited during startup:\n'+details)
                    try:
                        with urlopen('http://127.0.0.1:6080/vnc.html',timeout=1) as response:
                            ready=response.status==200 and (profile/'chromium/Default/Preferences').exists()
                    except OSError:
                        ready=False
                    if ready:
                        break
                    time.sleep(.2)
                else:
                    pytest.fail('Headless login viewer did not become ready')
            finally:
                process.terminate()
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    pytest.fail('Login viewer did not shut down cleanly')
        assert process.returncode==0
