"""Contract fixture for browser behavior; no Strava credentials or forwarding."""
from email.parser import BytesParser
from email.policy import default
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from http.cookies import SimpleCookie
from urllib.parse import parse_qs

PHOTOS = {}
COUNTS = {}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def respond(self, body, content_type='text/html', status=200):
        body = body.encode() if isinstance(body, str) else body
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/health':
            return self.respond('ok')
        if self.path == '/state':
            return self.respond(json.dumps({'photos':{key:list(value) for key,value in PHOTOS.items()}, 'posts':COUNTS}), 'application/json')
        if self.path == '/login':
            return self.respond('<form method="POST" action="/login"><label>Athlete ID<input name="athlete" value="123456"></label><button>Sign in</button></form>')
        cookies = SimpleCookie(self.headers.get('Cookie',''))
        if 'athlete' not in cookies:
            self.send_response(303)
            self.send_header('Location','/login')
            return self.end_headers()
        athlete = cookies['athlete'].value
        parts = self.path.split('/')
        activity = parts[2] if len(parts) >= 3 else ''
        if self.path.startswith('/photos/'):
            _, _, activity, name = self.path.split('/', 3)
            return self.respond(PHOTOS[activity][name], 'image/png')
        if self.path.endswith('/edit'):
            return self.respond(f'''<h1>Edit activity</h1><form method="POST" action="/activities/{activity}" enctype="multipart/form-data">
              <label>Media<input type="file" name="photos" multiple accept="image/png"></label>
              <button type="submit">Save</button></form>''')
        photos = ''.join(f'<img width="350" alt="{escape(name)}" src="/photos/{activity}/{escape(name)}">' for name in PHOTOS.get(activity, {}))
        return self.respond(f'''<header data-athlete-id="{escape(athlete)}">Signed in as synthetic athlete {escape(athlete)}</header>
          <main data-owner-id="123456"><h1>Upper body</h1><a href="/activities/{activity}/edit">Edit activity</a>
          <div id="photos">{photos}</div></main>''')

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get('Content-Length', '0')))
        if self.path == '/__reset':
            PHOTOS.clear()
            COUNTS.clear()
            return self.respond('reset')
        if self.path == '/login':
            athlete = parse_qs(raw.decode())['athlete'][0]
            if not athlete.isdigit():
                return self.respond('Invalid athlete', status=400)
            self.send_response(303)
            self.send_header('Set-Cookie', f'athlete={athlete}; Path=/; Max-Age=86400; HttpOnly; SameSite=Lax')
            self.send_header('Location','/activities/101')
            return self.end_headers()
        if 'athlete=' not in self.headers.get('Cookie',''):
            return self.respond('Login required',status=401)
        message = BytesParser(policy=default).parsebytes(b'Content-Type: '+self.headers['Content-Type'].encode()+b'\r\n\r\n'+raw)
        activity = self.path.split('/')[2]
        COUNTS[activity] = COUNTS.get(activity,0) + 1
        photos = PHOTOS.setdefault(activity, {})
        for part in message.iter_parts():
            if part.get_filename():
                name = part.get_filename()
                data = part.get_payload(decode=True)
                if not data.startswith(b'\x89PNG\r\n\x1a\n'):
                    return self.respond('Expected PNG', status=400)
                photos[name] = data
        self.send_response(303)
        self.send_header('Location', '/activities/'+activity)
        self.end_headers()


if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0',8080),Handler).serve_forever()
