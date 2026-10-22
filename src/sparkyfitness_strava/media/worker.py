"""Attach queued cards to Strava, with durable intent before any media mutation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import signal

from playwright.sync_api import sync_playwright
from .browser import profile_lock, restore_session_cookies, save_session_cookies
from .queue import atomic
from .render import html
from .summary import from_activity


def fields(page):
    return page.locator('form input:not([type=hidden]):not([type=file]):not([type=submit]),form select,form textarea').evaluate_all(
        "items => items.map(e => ({name:e.name,type:e.type,value:e.value,checked:e.type==='checkbox'||e.type==='radio'?e.checked:null}))")


def thumbnails(page):
    return page.locator('img[class*="Thumbnail--thumbnail-image"]').evaluate_all(
        'items => items.map(e => ({src:e.currentSrc||e.src,loaded:e.complete&&e.naturalWidth>0}))')


def editor(page, job):
    activity, athlete = job['activity_id'], job['athlete_id']
    if not activity.isdigit() or not athlete.isdigit():
        raise ValueError('Invalid destination identity')
    url = 'https://www.strava.com/activities/' + activity
    page.goto(url, wait_until='domcontentloaded')
    page.locator(f'a.nav-link[href="/athletes/{athlete}"]').first.wait_for()
    if not page.locator(f'a.minimal[href="/athletes/{athlete}"]').count():
        raise ValueError('Activity owner does not match queued athlete')
    page.locator(f'a[href="/activities/{activity}/edit"]').first.click()
    page.get_by_role('button', name='Save', exact=True).first.wait_for()
    page.locator('input[name="activity[visibility]"]:checked').wait_for(state='attached')
    page.wait_for_timeout(2000)
    return url


def attach(context, job, images, journal, evidence):
    if journal.exists():
        raise ValueError('Existing media intent; inspect before any further upload')
    page = context.new_page()
    try:
        url = editor(page, job)
        before = fields(page)
        existing = thumbnails(page)
        if existing:
            atomic(journal, {'state': 'held', 'fingerprint': job['fingerprint'], 'reason': 'Activity already has photos'})
            raise ValueError('Activity already has photos; held for review')
        receipt = {'state': 'uncertain', 'phase': 'selecting', 'fingerprint': job['fingerprint'],
                   'activity_id': job['activity_id'], 'fields': before,
                   'images': [hashlib.sha256(p.read_bytes()).hexdigest() for p in images]}
        # File selection itself may upload. No automatic second selection after this point.
        atomic(journal, receipt)
        with page.expect_file_chooser() as chooser:
            page.get_by_text('Drag and drop media', exact=False).click()
        chooser.value.set_files([str(p) for p in images])
        print('Media files selected for ' + job['activity_id'], flush=True)
        page.wait_for_function("() => {let a=[...document.querySelectorAll('img[class*=\"Thumbnail--thumbnail-image\"]')];return a.length===2&&a.every(e=>e.complete&&e.naturalWidth>0)}", timeout=60000)
        page.wait_for_timeout(3000)
        if fields(page) != before:
            raise ValueError('Activity fields changed before save')
        receipt['phase'] = 'saving'
        atomic(journal, receipt)
        print('Saving media for ' + job['activity_id'], flush=True)
        page.get_by_role('button', name='Save', exact=True).first.click()
        page.wait_for_url(url, timeout=60000)
        editor(page, job)
        page.wait_for_function("() => {let a=[...document.querySelectorAll('img[class*=\"Thumbnail--thumbnail-image\"]')];return a.length===2&&a.every(e=>e.complete&&e.naturalWidth>0)}", timeout=60000)
        photos = thumbnails(page)
        if len(photos) != 2 or not all(p['loaded'] for p in photos) or len({p['src'] for p in photos}) != 2:
            raise ValueError('Could not verify two saved photos')
        if fields(page) != before:
            raise ValueError('Saved activity fields changed')
        evidence.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(evidence / 'persisted.png'), full_page=True)
        receipt.update(state='attached', photos=photos)
        atomic(journal, receipt)
    except Exception:
        evidence.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(evidence / 'inspection-needed.png'), full_page=True)
        raise
    finally:
        page.close()


def run(data, profile):
    root = data / 'media'
    jobs = sorted((root / 'outbox').glob('*.json'))
    pending = [p for p in jobs if not (root / 'results' / p.name).exists()]
    if not pending:
        return
    with profile_lock(root / 'worker-lock'), profile_lock(profile), sync_playwright() as p:
        environment = {**os.environ, 'XDG_CONFIG_HOME': str(profile / 'config'), 'XDG_CACHE_HOME': str(profile / 'cache')}
        context = p.chromium.launch_persistent_context(str(profile / 'chromium'), channel='chromium', headless=True,
                    env=environment, viewport={'width':1280,'height':1000})
        context.set_default_navigation_timeout(90000)
        try:
            restore_session_cookies(context, profile)
            for path in pending:
                job = json.loads(path.read_text())
                journal = root / 'results' / path.name
                if journal.exists():
                    continue
                expected = hashlib.sha256(json.dumps({k:v for k,v in job.items() if k != 'fingerprint'}, sort_keys=True).encode()).hexdigest()
                if expected != job['fingerprint']:
                    raise ValueError('Media job fingerprint mismatch')
                if not job['activity_id'].isdigit() or not job['athlete_id'].isdigit():
                    raise ValueError('Invalid media identity')
                cards = root / 'cards' / job['activity_id']
                cards.mkdir(parents=True, exist_ok=True)
                page = context.new_page()
                try:
                    page.set_viewport_size({'width':1080,'height':1080})
                    page.route('**/*', lambda route: route.abort())
                    images = []
                    for kind in ('summary', 'comparison'):
                        page.set_content(html(from_activity(job), 'dark', kind))
                        page.evaluate('document.fonts.ready')
                        image = cards / (kind + '.png')
                        page.screenshot(path=str(image))
                        images.append(image)
                finally:
                    page.close()
                try:
                    attach(context, job, images, journal, cards)
                    (root / 'errors' / path.name).unlink(missing_ok=True)
                    print(json.dumps({'activity_id': job['activity_id'], 'state': 'attached'}), flush=True)
                except Exception as error:
                    # Before intent: safe to retry login/network failures. After intent: held.
                    atomic(root / 'errors' / path.name, {'error': type(error).__name__, 'detail': str(error)[:1000], 'held': journal.exists()})
                    print(json.dumps({'activity_id': job['activity_id'], 'state': 'held' if journal.exists() else 'pending', 'error': type(error).__name__}), flush=True)
        finally:
            save_session_cookies(context, profile)
            context.close()


def main():
    def stop(signum, frame):
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, stop)
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['once', 'watch', 'status'])
    parser.add_argument('--data', type=Path, default=Path(os.environ.get('DATA_DIR', '/data')))
    parser.add_argument('--profile', type=Path, default=Path('/browser-profile'))
    args = parser.parse_args()
    if args.command == 'status':
        for path in sorted((args.data / 'media' / 'outbox').glob('*.json')):
            result = args.data / 'media' / 'results' / path.name
            print(path.stem, json.loads(result.read_text())['state'] if result.exists() else 'pending')
        return
    while True:
        try:
            run(args.data, args.profile)
        except Exception as error:
            print('Media worker: ' + type(error).__name__, flush=True)
            if args.command == 'once':
                raise
        if args.command == 'once':
            return
        time.sleep(60)


if __name__ == '__main__':
    main()
