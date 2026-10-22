"""Translate logged sets into Strava strength JSON without requiring set times."""
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import hashlib
import math
from zoneinfo import ZoneInfo
from .state import encode
from .source import is_native_workout
from .mapping import EXERCISES, resolve_exercise


def stamp(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Workout timestamps must include a timezone")
    return result


def numeric(value, *, integer=False):
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        raise ValueError("Invalid logged number") from None
    if not number.is_finite() or number < 0:
        raise ValueError("Logged numbers must be finite and nonnegative")
    if integer and number != number.to_integral_value():
        raise ValueError("Strava requires whole repetitions or seconds")
    if integer:
        return int(number)
    result = float(number)
    if not math.isfinite(result):
        raise ValueError("Logged number exceeds the supported numeric range")
    return result


class SkipWorkout(ValueError):
    """A workout is ineligible, without blocking other workouts."""


def local_start(day, clock, timezone):
    if not day or not clock:
        raise SkipWorkout("Missing recorded workout start time")
    try:
        naive = datetime.fromisoformat(day + "T" + clock)
        zone = ZoneInfo(timezone)
        if naive.tzinfo is not None:
            raise ValueError("Expected local wall clock")
        first = naive.replace(tzinfo=zone, fold=0)
        second = naive.replace(tzinfo=zone, fold=1)
        if first.utcoffset() != second.utcoffset():
            raise ValueError("Ambiguous or nonexistent local time")
        return first.astimezone(ZoneInfo("UTC"))
    except (ValueError, TypeError):
        raise SkipWorkout("Invalid, ambiguous or nonexistent workout start time") from None


def build(session, mappings, timezone):
    if session.get("skip_reason"):
        raise SkipWorkout(session["skip_reason"])
    if not is_native_workout(session):
        raise SkipWorkout("Only native SparkyFitness workouts are exported")
    exercises = session.get("exercises", [])
    completed = [(entry, item) for entry in exercises for item in sorted(
        entry.get("sets", []), key=lambda s: (s.get("set_number") or 0, str(s.get("id", ""))))
        if item.get("completed_at") is not None]
    if not completed:
        raise SkipWorkout("No completed sets")
    starts, ends, completions = [], [], []
    try:
        total = numeric(session.get("total_duration_minutes") or 0)
        for entry in exercises:
            if not any(child is entry for child, _ in completed):
                continue
            duration = numeric(entry.get("duration_minutes") or 0)
            completions.extend(stamp(item["completed_at"]) for item in entry.get("sets", [])
                               if item.get("completed_at") is not None)
            if entry.get("entry_time"):
                start = local_start(entry.get("entry_date") or session.get("entry_date"), entry["entry_time"], timezone)
                starts.append(start)
                ends.append(start + timedelta(minutes=duration))
            elif not total:
                raise SkipWorkout("Missing recorded workout start time")
        if total:
            if starts:
                start = min(starts)
            elif completions:
                start = max(completions) - timedelta(minutes=total)
            else:
                raise SkipWorkout("Missing workout start time and completion timestamps")
            end = start + timedelta(minutes=total)
        else:
            start, end = min(starts), max(ends + completions)
    except SkipWorkout:
        raise
    except (ValueError, TypeError, AttributeError, OverflowError):
        raise SkipWorkout("Invalid recorded duration or completion time") from None
    if end <= start:
        raise SkipWorkout("No positive recorded workout duration")
    if starts and any(completion < start for completion in completions):
        raise SkipWorkout("Completion time precedes workout start")
    local = start.astimezone(ZoneInfo(timezone))
    sets, missing, problems = [], set(), []
    for entry, logged in completed:
        exercise = str(entry.get("exercise_id") or "")
        target, _ = resolve_exercise(entry, mappings)
        if not exercise:
            problems.append(f"Entry {entry['id']}: library exercise was deleted; mapping identity is unavailable")
            continue
        if target is None:
            missing.add(exercise)
            continue
        item = {"exercise_type": target}
        try:
            if target not in EXERCISES:
                raise ValueError("Unknown Strava exercise identifier")
            modality = (entry.get("exercise_snapshot") or {}).get("modality") or entry.get("modality")
            if modality not in {"weight_reps", "bodyweight_reps", "reps_only", "duration", "weight_duration"}:
                raise ValueError("Unsupported or unknown strength modality")
            if logged.get("distance") is not None:
                raise ValueError("Distance sets cannot be represented as strength sets")
            if modality in {"duration", "weight_duration"}:
                item["duration"] = numeric(logged.get("duration"), integer=True)
            else:
                item["repetitions"] = numeric(logged.get("reps"), integer=True)
            if not item.get("repetitions", item.get("duration", 0)):
                raise ValueError("Set has no positive actual repetitions or duration")
            if logged.get("weight") is not None:
                load = numeric(logged["weight"])
                if load or modality not in {"bodyweight_reps", "reps_only", "duration"}:
                    item["weight"] = load
            sets.append(item)
        except (ValueError, InvalidOperation, TypeError) as error:
            problems.append(f"Set {logged.get('id', logged.get('set_number'))}: {error}")
    # Strava's live JSON importer requires canonical UTC timestamps even though
    # its docs allow other ISO offsets. The UTC Z suffix is essential; fractional
    # seconds are accepted and remain intact.
    start_time = start.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")
    payload = {"version": "1.0", "start_time": start_time, "utc_offset": int(local.utcoffset().total_seconds()),
               "elapsed_time": max(1, int(round((end - start).total_seconds()))),
               "creator": {"name": "sparkyfitness-strava-connector"}, "sets": sets}
    return payload, sorted(missing), problems


def fingerprint(payload):
    return hashlib.sha256(encode(payload).encode()).hexdigest()
