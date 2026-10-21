"""Interactive headless-server login; upload proof restricted to the local mock."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import secrets
import signal
import subprocess
import tempfile
import threading
import time
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright


@contextmanager
def profile_lock(profile):
    profile.mkdir(parents=True, exist_ok=True)
    profile.chmod(0o700)
    with (profile / '.session.lock').open('a+b') as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Browser profile is busy; stop the login service or worker first') from None
        yield


def restore_session_cookies(context, profile):
    """Chromium does not normally reload cookies without an expiry on restart."""
    path = profile / 'session-cookies.json'
    if path.exists():
        context.add_cookies(json.loads(path.read_text(encoding='utf-8')))


def save_session_cookies(context, profile):
    """Save browser-session cookies privately and atomically beside the profile."""
    cookies = [cookie for cookie in context.cookies() if cookie.get('expires') == -1]
    descriptor, temporary = tempfile.mkstemp(prefix='.session-cookies-', dir=profile)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(cookies, stream)
        os.replace(temporary, profile / 'session-cookies.json')
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def login(profile, url='https://www.strava.com/login', stop=None):
    """A real browser displayed through localhost-only noVNC, with manual MFA."""
    processes = []
    stop = stop or threading.Event()
    with profile_lock(profile), tempfile.TemporaryDirectory() as temp:
        password = secrets.token_urlsafe(8)[:8]
        password_file = Path(temp) / 'vnc-password'
        password_file.write_text(password + '\n', encoding='utf-8')
        password_file.chmod(0o600)
        # Chromium's crash reporter also needs writable XDG directories. Keep
        # these private to the profile instead of depending on a shared HOME.
        for directory in ('config', 'cache'):
            (profile / directory).mkdir(exist_ok=True, mode=0o700)
        environment = {**os.environ, 'DISPLAY': ':99',
                       'XDG_CONFIG_HOME': str(profile / 'config'),
                       'XDG_CACHE_HOME': str(profile / 'cache')}
        try:
            processes.append(subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1280x900x24', '-nolisten', 'tcp'], env=environment))
            for _ in range(100):
                if Path('/tmp/.X11-unix/X99').exists():
                    break
                if processes[0].poll() is not None:
                    raise ValueError('Virtual display did not start')
                time.sleep(.1)
            else:
                raise ValueError('Virtual display did not become ready')
            processes.append(subprocess.Popen(['x11vnc', '-display', ':99', '-localhost', '-rfbport', '5900',
                '-forever', '-shared', '-loop', '-passwdfile', str(password_file)], env=environment,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
            processes.append(subprocess.Popen(['websockify', '--web=/usr/share/novnc/', '6080', '127.0.0.1:5900'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
            print('Open http://localhost:6080/vnc.html (remote server: use an SSH tunnel).', flush=True)
            print('Temporary viewer password: ' + password, flush=True)
            print('Sign into Strava manually, then stop this service to save and release the profile.', flush=True)
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(str(profile / 'chromium'), channel='chromium', headless=False,
                    env=environment, viewport={'width':1280,'height':900})
                try:
                    restore_session_cookies(context, profile)
                    page = context.pages[0] if context.pages else context.new_page()
                    page.goto(url, wait_until='domcontentloaded')
                    while not stop.is_set():
                        failed = next((process for process in processes if process.poll() is not None), None)
                        if failed:
                            raise ValueError(f'Login helper {Path(failed.args[0]).name} stopped (exit {failed.returncode})')
                        page.wait_for_timeout(1000)
                finally:
                    try:
                        save_session_cookies(context, profile)
                    finally:
                        context.close()
        finally:
            for process in reversed(processes):
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


def attach_mock(page, origin, activity_id, athlete_id, images, journal):
    """Proof of file upload/save/reopen behavior; NOT a verified Strava adapter."""
    parsed = urlsplit(origin)
    if parsed.scheme != 'http' or parsed.hostname not in {'mock-strava-web', '127.0.0.1', 'localhost'}:
        raise ValueError('Upload prototype is restricted to the local mock website')
    activity_id, athlete_id = str(int(activity_id)), str(int(athlete_id))
    if len(images) != 2 or any(not path.is_file() for path in images):
        raise ValueError('Exactly two existing image files are required')
    identity = {'activity_id':activity_id, 'athlete_id':athlete_id,
                'images':{path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in images}}
    if len(identity['images']) != 2:
        raise ValueError('Image filenames must be different')
    if journal.exists():
        prior = json.loads(journal.read_text())
        if any(prior.get(key) != value for key,value in identity.items()):
            raise ValueError('Journal belongs to a different activity, athlete or image revision')
        if prior['state'] == 'attached':
            return prior
        raise ValueError('Prior upload outcome is uncertain; inspect the activity before another attempt')
    page.goto(origin + '/activities/' + activity_id)
    if urlsplit(page.url).path == '/login':
        raise ValueError('Browser needs login; reconnect using the login viewer')
    if page.locator('[data-athlete-id]').get_attribute('data-athlete-id') != athlete_id:
        raise ValueError('Browser account does not match the expected Strava athlete')
    if page.locator('[data-owner-id]').get_attribute('data-owner-id') != athlete_id:
        raise ValueError('Activity belongs to a different athlete')
    page.get_by_role('link', name='Edit activity', exact=True).click()
    record = {**identity, 'state':'uncertain'}
    journal.parent.mkdir(parents=True, exist_ok=True)
    journal.write_text(json.dumps(record), encoding='utf-8')
    # Record intent before selecting files: even selection can begin remote uploads.
    page.get_by_label('Media', exact=True).set_input_files([str(path) for path in images])
    page.get_by_role('button', name='Save', exact=True).click()
    page.goto(origin + '/activities/' + activity_id)
    for path in images:
        if page.get_by_alt_text(path.name, exact=True).count() != 1:
            raise ValueError('Saved media could not be verified; upload outcome is uncertain')
    record['state'] = 'attached'
    journal.write_text(json.dumps(record), encoding='utf-8')
    return record


def main():
    stop = threading.Event()
    def shutdown(*_):
        stop.set()
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('login')
    args = parser.parse_args()
    try:
        if args.command == 'login':
            url = os.environ.get('MEDIA_LOGIN_URL', 'https://www.strava.com/login')
            if url != 'https://www.strava.com/login':
                parsed = urlsplit(url)
                if parsed.scheme != 'http' or parsed.hostname not in {'mock-strava-web','localhost','127.0.0.1'}:
                    raise ValueError('Login URL must be Strava or the local mock website')
            login(Path(os.environ.get('BROWSER_PROFILE', '/browser-profile')), url, stop)
    except KeyboardInterrupt:
        pass
    except ValueError as error:
        parser.exit(1, str(error)+'\n')


if __name__ == '__main__':
    main()
