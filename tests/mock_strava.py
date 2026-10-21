"""Local-only Strava contract double. Never forwards requests to the Internet."""
from email.parser import BytesParser
from email.policy import default
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import time
from urllib.parse import parse_qs

STATE = {}


def reset():
    STATE.clear()
    STATE.update({"uploads": {}, "requests": [], "refreshes": 0, "refresh_token": "mock-refresh-0"})


reset()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            return self.reply({"healthy": True})
        if self.path == "/__state":
            return self.reply(STATE)
        if self.headers.get("Authorization") != "Bearer mock-access":
            return self.reply({"message": "Unauthorized"}, 401)
        if self.path == "/api/v3/athlete":
            return self.reply({"id": 123456})
        if self.path.startswith("/api/v3/activities/"):
            identity = int(self.path.rsplit("/", 1)[1])
            upload = STATE["uploads"].get(str(identity - 900000))
            if upload:
                return self.reply({"id": identity, "external_id": upload["external_id"]})
            return self.reply({}, 404)
        if self.path.startswith("/api/v3/uploads/"):
            upload = STATE["uploads"].get(self.path.rsplit("/", 1)[1])
            if not upload:
                return self.reply({}, 404)
            upload["polls"] += 1
            return self.reply({"id": upload["id"], "id_str": str(upload["id"]), "external_id": upload["external_id"],
                               "error": None, "activity_id": 900000 + upload["id"], "status": "Your activity is ready."})
        self.reply({}, 404)

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        if self.path == "/__reset":
            reset()
            return self.reply({"reset": True})
        if self.path == "/oauth/token":
            values = {k: v[0] for k, v in parse_qs(raw.decode()).items()}
            if values.get("client_id") != "mock-client" or values.get("client_secret") != "mock-secret":
                return self.reply({}, 401)
            if values.get("grant_type") == "refresh_token":
                if values.get("refresh_token") != STATE["refresh_token"]:
                    return self.reply({"error": "invalid_grant"}, 400)
                STATE["refreshes"] += 1
                STATE["refresh_token"] = f"mock-refresh-{STATE['refreshes']}"
            elif values.get("code") != "mock-code":
                return self.reply({}, 400)
            return self.reply({"access_token": "mock-access", "refresh_token": STATE["refresh_token"],
                               "expires_at": int(time.time()) + 21600, "athlete": {"id": 123456}})
        if self.path != "/api/v3/uploads":
            return self.reply({}, 404)
        if self.headers.get("Authorization") != "Bearer mock-access":
            return self.reply({}, 401)
        message = BytesParser(policy=default).parsebytes(
            b"Content-Type: " + self.headers["Content-Type"].encode() + b"\r\nMIME-Version: 1.0\r\n\r\n" + raw)
        fields = {}
        for part in message.iter_parts():
            name = part.get_param("name", header="content-disposition")
            fields[name] = part.get_payload(decode=True).decode()
        payload = json.loads(fields["file"])
        assert fields["sport_type"] == "WeightTraining" and fields["data_type"] == "json"
        assert payload["version"] == "1.0" and payload["sets"] and payload["elapsed_time"] > 0
        assert all("exercise_type" in s and ("repetitions" in s or "duration" in s) for s in payload["sets"])
        for upload in STATE["uploads"].values():
            if upload["external_id"] == fields["external_id"]:
                return self.reply({"error": "Duplicate upload"}, 400)
        identity = len(STATE["uploads"]) + 1
        STATE["uploads"][str(identity)] = {"id": identity, "external_id": fields["external_id"], "payload": payload,
                                           "polls": 0, "name": fields["name"], "description": fields["description"]}
        STATE["requests"].append({"method": "POST", "path": self.path})
        return self.reply({"id": identity, "id_str": str(identity), "external_id": fields["external_id"],
                           "error": None, "activity_id": None, "status": "Your activity is still being processed."}, 201)


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
