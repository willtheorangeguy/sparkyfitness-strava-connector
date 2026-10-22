"""Real Chromium proof of the production attachment flow against intercepted web routes."""
import json
from pathlib import Path
import pytest
pytest.importorskip('playwright.sync_api', reason='Media browser tests run in Dockerfile.media')
from playwright.sync_api import sync_playwright
from sparkyfitness_strava.media.worker import attach, run

PIXEL = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII='


@pytest.mark.parametrize('lose_reply', [False, True])
def test_production_media_upload_is_saved_once_or_held(tmp_path, lose_reply, monkeypatch):
    saved = []
    selections = []
    job = {'activity_id': '123', 'athlete_id': '42', 'fingerprint': 'immutable'}
    journal = tmp_path / 'receipt.json'
    images = []
    for name in ['summary', 'comparison']:
        path = tmp_path / (name + '.png')
        import base64
        path.write_bytes(base64.b64decode(PIXEL.split(',')[1]))
        images.append(path)
    def route(request):
        url = request.request.url
        if url.endswith('/saved'):
            saved.append(True)
            request.fulfill(body='ok')
        elif url.endswith('/selected'):
            selections.append(True)
            request.fulfill(body='ok')
        elif url.endswith('/edit'):
            photos = ''.join(f'<img class="Thumbnail--thumbnail-image" src="{PIXEL}#{i}">' for i in range(2)) if saved else ''
            request.fulfill(content_type='text/html', body=f'''<form>
              <input name="activity[name]" value="Mock workout"><input type="radio" name="activity[visibility]" value="only_me" checked>
              <button type="button" onclick="fetch('/saved',{{method:'POST'}}).then(()=>location.href='/activities/123')">Save</button>
              <div id="photos">{photos}</div>
              {'' if saved else '<button type="button" onclick="document.querySelector(\'input[type=file]\').click()">Drag and drop media</button>'}
              <input type="file" multiple hidden onchange="fetch('/selected',{{method:'POST'}});for(let i=0;i<this.files.length;i++){{let img=document.createElement('img');img.className='Thumbnail--thumbnail-image';let reader=new FileReader();reader.onload=()=>img.src=reader.result;reader.readAsDataURL(this.files[i]);document.querySelector('#photos').append(img)}}">
            </form>''')
        else:
            request.fulfill(content_type='text/html', body='<a class="nav-link" href="/athletes/42">Me</a><a class="minimal" href="/athletes/42">Owner</a><a href="/activities/123/edit">Edit</a>')
    if lose_reply:
        from sparkyfitness_strava.media import worker
        original_editor = worker.editor
        calls = []
        def lost_verification(page, job):
            calls.append(True)
            if len(calls) > 1:
                raise RuntimeError('Verification reply lost after Save committed')
            return original_editor(page, job)
        monkeypatch.setattr(worker, 'editor', lost_verification)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chromium')
        context = browser.new_context()
        context.route('https://www.strava.com/**', route)
        errors = []
        context.on('page', lambda page: page.on('pageerror', lambda error: errors.append(str(error))))
        context.set_default_navigation_timeout(30000)
        try:
            if lose_reply:
                with pytest.raises(Exception):
                    attach(context, job, images, journal, tmp_path / 'evidence')
                assert json.loads(journal.read_text())['state'] == 'uncertain'
            else:
                attach(context, job, images, journal, tmp_path / 'evidence')
                assert json.loads(journal.read_text())['state'] == 'attached'
            with pytest.raises(ValueError, match='Existing media intent'):
                attach(context, job, images, journal, tmp_path / 'evidence')
            assert len(saved) == len(selections) == 1
            assert not errors
        finally:
            browser.close()


def test_worker_skips_attached_and_uncertain_jobs_without_opening_browser(tmp_path):
    for key, state in [('123','attached'), ('456','uncertain')]:
        outbox = tmp_path / 'media/outbox' / (key + '.json')
        result = tmp_path / 'media/results' / (key + '.json')
        outbox.parent.mkdir(parents=True, exist_ok=True)
        result.parent.mkdir(parents=True, exist_ok=True)
        outbox.write_text('{}')
        result.write_text(json.dumps({'state': state}))
    run(tmp_path, tmp_path / 'unused-profile')
    assert not (tmp_path / 'unused-profile').exists()
