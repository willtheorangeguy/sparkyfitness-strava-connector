import argparse
from uuid import UUID
from datetime import datetime, timezone
import json
import secrets
import sys
import time
from urllib.parse import parse_qs, urlencode, urlsplit
from .api import Strava, APIError
from .config import Config
from .engine import Engine
from .state import State
from .workout import EXERCISES


def complete_callback(state, callback):
    query = parse_qs(urlsplit(callback).query)
    pending = state.get("authorization")
    if not pending or pending["expires"] < time.time() or not secrets.compare_digest(query.get("state", [""])[0], pending["state"]):
        raise ValueError("Authorization state is missing, expired or does not match; run auth-url again")
    if query.get("error") or not query.get("code"):
        raise ValueError("Strava authorization was declined or no code was returned")
    return query["code"][0], query.get("scope", [""])[0]


def main():
    parser = argparse.ArgumentParser(description="Export completed sparkyfitness workouts and structured sets to Strava")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("auth-url", help="Print a Strava consent link")
    commands.add_parser("auth-complete", help="Read the complete browser callback URL from stdin")
    commands.add_parser("exercises", help="List supported Strava exercise identifiers")
    mapping = commands.add_parser("map", help="Approve a sparkyfitness exercise ID -> Strava identifier mapping")
    mapping.add_argument("exercise")
    mapping.add_argument("strava_type", choices=sorted(EXERCISES))
    commands.add_parser("mappings")
    commands.add_parser("preview")
    commands.add_parser("check")
    commands.add_parser("sync")
    commands.add_parser("watch")
    commands.add_parser("status")
    reconcile = commands.add_parser("reconcile", help="Attach a known Strava upload ID to an unresolved session")
    reconcile.add_argument("session")
    reconcile.add_argument("upload_id", type=int)
    activity = commands.add_parser("reconcile-activity", help="Recover using a Strava activity ID, including private activities")
    activity.add_argument("session")
    activity.add_argument("activity_id", type=int)
    retry = commands.add_parser("retry", help="Allow a new attempt ONLY after checking Strava for duplicates")
    retry.add_argument("session")
    retry.add_argument("--confirm-no-activity", action="store_true", required=True)
    args = parser.parse_args()
    state = engine = strava = None
    try:
        config = Config.env()
        if args.command == "exercises":
            print("\n".join(sorted(EXERCISES)))
            return
        state = State(config.data_dir)
        if state.get("wger_account") is not None:
            raise ValueError("Use a separate state volume; wger state cannot be reused")
        state.bind("source_platform", "sparkyfitness")
        result = None
        if args.command == "auth-url":
            if not config.client_id:
                raise ValueError("Set STRAVA_CLIENT_ID")
            nonce = secrets.token_urlsafe(32)
            state.set("authorization", {"state": nonce, "expires": time.time() + 900})
            result = config.strava_url + "/oauth/authorize?" + urlencode({
                "client_id": config.client_id, "redirect_uri": "http://localhost/strava/callback",
                "response_type": "code", "approval_prompt": "force", "scope": "read,activity:write,activity:read_all", "state": nonce})
        elif args.command == "auth-complete":
            print("Paste the complete callback URL from your browser, then press Enter:", file=sys.stderr)
            code, scopes = complete_callback(state, sys.stdin.readline().strip())
            strava = Strava(config, state)
            result = {"authorized_athlete": strava.authorize(code, scopes)}
            state.set("authorization", None)
        elif args.command == "map":
            try:
                exercise_id = str(UUID(args.exercise))
            except ValueError:
                raise ValueError("SparkyFitness exercise IDs must be UUIDs") from None
            mappings = state.get("mappings", {})
            mappings[exercise_id] = args.strava_type
            state.set("mappings", mappings)
            result = mappings
        elif args.command == "mappings":
            result = state.get("mappings", {})
        elif args.command == "status":
            result = {"authorized": bool(state.get("oauth")), "athlete": state.get("strava_athlete"),
                      "sparkyfitness": state.get("sparkyfitness_account"), "exports": state.exports(), "cooldown": state.get("cooldown")}
        elif args.command == "retry":
            record = state.export(args.session)
            if not record or record["state"] not in {"uncertain", "failed"}:
                raise ValueError("Only uncertain or failed uploads can be retried")
            state.db.execute("DELETE FROM exports WHERE session=?", (args.session,))
            state.db.commit()
            result = {"retry_allowed": args.session}
        else:
            engine = Engine(config, state)
            if args.command == "watch":
                while True:
                    try:
                        print(json.dumps(engine.sync()), flush=True)
                        state.set("last_cycle", time.time())
                    except (APIError, ValueError) as error:
                        print(str(error), file=sys.stderr, flush=True)
                    time.sleep(config.interval)
            elif args.command == "reconcile":
                result = engine.reconcile(args.session, args.upload_id)
            elif args.command == "reconcile-activity":
                result = engine.reconcile_activity(args.session, args.activity_id)
            else:
                result = getattr(engine, args.command)()
        print(result if isinstance(result, str) else json.dumps(result, indent=2, ensure_ascii=False))
    except (APIError, ValueError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from None
    except KeyboardInterrupt:
        pass
    finally:
        if engine:
            engine.close()
        if strava:
            strava.close()
        if state:
            state.close()


if __name__ == "__main__":
    main()
