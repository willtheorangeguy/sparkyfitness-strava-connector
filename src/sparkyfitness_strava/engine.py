from datetime import datetime, timedelta, timezone
import hashlib
import time
from .api import APIError, UnknownWrite, SparkyFitness, Strava
from .state import encode
from .workout import build, fingerprint, stamp, SkipWorkout
from .source import select_workouts


class Engine:
    def __init__(self, config, state, sparkyfitness=None, strava=None):
        self.config, self.state = config, state
        self.sparkyfitness = sparkyfitness or SparkyFitness(config)
        self.strava = strava or Strava(config, state)

    def close(self):
        self.sparkyfitness.close()
        self.strava.close()

    def source(self):
        if self.state.get("wger_account") is not None:
            raise ValueError("Use a separate state volume; wger state cannot be reused")
        self.state.bind("source_platform", "sparkyfitness")
        profile = self.sparkyfitness.request("GET", "/api/identity/user")
        user = profile.get("activeUserId")
        if not user or user != profile.get("authenticatedUserId"):
            raise ValueError("SparkyFitness must return the API key owner's user identity")
        identity = {"url": self.config.sparkyfitness_url, "user": str(user)}
        self.state.bind("sparkyfitness_account", identity)
        return identity

    def preview(self):
        identity = self.source()
        since = self.config.since or self.state.get("export_since") or datetime.now(timezone.utc).date().isoformat()
        self.state.set("export_since", since)
        mappings = self.state.get("mappings", {})
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=self.config.settle)
        sessions = list(self.sparkyfitness.sessions())
        plans = self.sparkyfitness.request("GET", "/api/workout-plan-templates") if any(
            s.get("workout_plan_assignment_id") is not None or any(
                e.get("workout_plan_assignment_id") is not None for e in s.get("exercises", []))
            for s in sessions) else []
        output = []
        exports = self.state.exports()
        for session in select_workouts(sessions, plans):
            if session.get("entry_date") and session["entry_date"] < since:
                continue
            key = session["key"]
            try:
                payload, missing, problems = build(session, mappings, self.config.timezone)
                end = stamp(payload["start_time"]) + timedelta(seconds=payload["elapsed_time"])
                if end > cutoff:
                    continue
                state = "blocked" if missing or problems else "ready"
                reason = None
            except SkipWorkout as error:
                payload, missing, problems = {}, [], []
                state, reason = "skipped", str(error)
            content = {"payload": payload, "name": session.get("name") or "SparkyFitness strength workout",
                       "notes": session.get("notes") or ""}
            current = fingerprint(content)
            previous = self.state.export(key)
            regrouped = False
            source_entries = sorted(str(e["id"]) for e in session.get("exercises", []))
            if previous is None:
                overlapping = [record for record in exports.values()
                               if set(source_entries).intersection(record.get("source_entries", []))]
                if overlapping:
                    previous = overlapping[0]
                    regrouped = True
                    # Moving a plan session or regrouping its entries is a source edit,
                    # never a new export intent. Keep unresolved jobs held as well.
                    state = "changed" if previous["state"] == "exported" else previous["state"]
            if previous:
                state = previous["state"]
                if state == "exported" and (regrouped or previous["fingerprint"] != current):
                    state = "changed"
            account = hashlib.sha256(encode(identity).encode()).hexdigest()[:16]
            external = hashlib.sha256(key.encode()).hexdigest()[:32]
            output.append({"session": key, "state": state, "missing": missing, "problems": problems,
                           "source_entries": source_entries,
                           "reason": reason, "fingerprint": current,
                           "external_id": f"sparkyfitness-{account}-{external}.json", **content})
        return output

    def check(self):
        identity = self.source()
        athlete = self.strava.call("GET", "/athlete")
        self.state.bind("strava_athlete", str(athlete["id"]))
        return {"sparkyfitness": identity, "strava_athlete": str(athlete["id"])}

    def finish(self, session, record, upload):
        if str(upload.get("external_id")) != record["external_id"]:
            raise ValueError("Strava upload external ID does not match this session")
        if upload.get("error"):
            record["state"] = "failed"
            # Never persist untrusted HTML error messages from Strava.
            record["reason"] = "Strava rejected the upload; inspect the upload on Strava"
        elif upload.get("activity_id"):
            record["state"] = "exported"
            record["activity_id"] = str(upload["activity_id"])
        else:
            record["state"] = "processing"
        self.state.save(session, record)

    def sync(self):
        if self.state.get("cooldown", 0) > time.time():
            return {"state": "rate_limited", "retry_at": self.state.get("cooldown")}
        self.check()
        # Poll previous jobs first, even if their source was subsequently edited/deleted.
        for session, record in self.state.exports().items():
            if record["state"] == "processing":
                upload = self.strava.call("GET", "/uploads/" + record["upload_id"])
                self.finish(session, record, upload)
        plans = self.preview()
        submitted = 0
        for plan in plans:
            if plan["state"] != "ready" or submitted >= self.config.batch:
                continue
            record = {key: plan[key] for key in ("fingerprint", "external_id", "source_entries")}
            record["state"] = "uncertain"
            # Commit intent before the POST: a crash or lost reply must not cause another upload.
            self.state.save(plan["session"], record)
            try:
                upload = self.strava.call("POST", "/uploads", data={
                    "data_type": "json", "sport_type": "WeightTraining", "trainer": "1",
                    "name": plan["name"], "description": ("Exported from SparkyFitness.\n" + plan["notes"])[:10000],
                    "external_id": plan["external_id"]},
                    files={"file": (plan["external_id"], encode(plan["payload"]).encode(), "application/json")})
                if not isinstance(upload, dict) or not (upload.get("id_str") or upload.get("id")):
                    raise UnknownWrite("POST", "/api/v3/uploads")
                record["upload_id"] = str(upload.get("id_str") or upload["id"])
                # Save ID before interpreting the remainder, so restart can poll it.
                record["state"] = "processing"
                self.state.save(plan["session"], record)
                self.finish(plan["session"], record, upload)
                submitted += 1
            except UnknownWrite:
                # Remains uncertain; no automatic POST retry even across process restarts.
                raise
            except APIError as error:
                if error.status == 429 or error.status == 401:
                    # Explicit rejection, not an ambiguous transport failure.
                    self.state.db.execute("DELETE FROM exports WHERE session=?", (plan["session"],))
                    self.state.db.commit()
                else:
                    record["state"] = "failed"
                    record["reason"] = str(error)
                    self.state.save(plan["session"], record)
                raise
        return {"submitted": submitted, "exports": self.state.exports(),
                "blocked": [{k: p[k] for k in ("session", "missing", "problems")} for p in plans if p["state"] == "blocked"],
                "changed": [p["session"] for p in plans if p["state"] == "changed"],
                "skipped": [{"session": p["session"], "reason": p["reason"]} for p in plans if p["state"] == "skipped"]}

    def reconcile(self, session, upload_id):
        self.check()
        record = self.state.export(session)
        if not record or record["state"] not in {"uncertain", "processing", "failed"}:
            raise ValueError("Session must have an unresolved upload")
        upload = self.strava.call("GET", "/uploads/" + str(int(upload_id)))
        if upload.get("external_id") != record["external_id"]:
            raise ValueError("Upload does not belong to this sparkyfitness session")
        record["upload_id"] = str(upload.get("id_str") or upload["id"])
        self.finish(session, record, upload)
        return self.state.export(session)

    def reconcile_activity(self, session, activity_id):
        self.check()
        record = self.state.export(session)
        if not record or record["state"] not in {"uncertain", "processing", "failed"}:
            raise ValueError("Session must have an unresolved upload")
        activity = self.strava.call("GET", "/activities/" + str(int(activity_id)))
        if activity.get("external_id") != record["external_id"]:
            raise ValueError("Activity does not belong to this sparkyfitness session")
        record.update(state="exported", activity_id=str(activity["id"]))
        self.state.save(session, record)
        return record
