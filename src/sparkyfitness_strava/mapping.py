"""Deterministic exercise matching against the bundled Strava catalog."""
from importlib.resources import files
import json
import re
import unicodedata


EXERCISES = frozenset(json.loads(files("sparkyfitness_strava").joinpath("exercises.json").read_text(encoding="utf-8")))


def normalize(name):
    if not isinstance(name, str):
        return ""
    name = "".join(" " if unicodedata.category(char) == "Pd" else char for char in name)
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", plain).split())


def catalog_index():
    candidates = {}
    for exercise in EXERCISES:
        for label in {exercise, exercise.removesuffix("_GENERIC")}:
            candidates.setdefault(normalize(label), set()).add(exercise)
    # Never break a normalization collision by catalog iteration order.
    return {name: next(iter(targets)) for name, targets in candidates.items() if len(targets) == 1}


CATALOG = catalog_index()

# Common SparkyFitness/library names with different Strava wording. Broader
# supported categories are intentional when Strava lacks the named variation.
# Keep these explicit: similarity alone cannot distinguish exercise variants.
ALIASES = {
    "barbell bench press medium grip": "BARBELL_BENCH_PRESS",
    "seated leg curl": "MACHINE_LEG_CURL_SEATED",
    "seated leg curls": "MACHINE_LEG_CURL_SEATED",
    "close grip front lat pulldown": "CABLE_LAT_PULLDOWN_CLOSE_GRIP",
    "seated cable rows": "SEATED_CABLE_ROW",
    "straight arm dumbbell pullover": "DUMBBELL_PULLOVER",
    "lat static stretch": "LAT_STRETCH",
    "machine preacher curl": "PREACHER_CURL_MACHINE",
    "machine preacher curls": "PREACHER_CURL_MACHINE",
    "leverage chest press": "MACHINE_CHEST_PRESS",
    "arnold dumbbell press": "ARNOLD_PRESS",
    "dumbbell flyes": "DUMBBELL_FLYE",
    "dumbbell flies": "DUMBBELL_FLYE",
    "pec static stretch": "STRETCH",
    "side lateral raise": "LATERAL_RAISE_GENERIC",
    "reverse grip triceps pushdown": "CABLE_TRICEPS_PUSHDOWN",
    "cable rope overhead triceps extension": "CABLE_OVERHEAD_TRICEPS_EXTENSION",
    "cable one arm tricep extension": "TRICEPS_EXTENSION_GENERIC",
    "cable one arm triceps extension": "TRICEPS_EXTENSION_GENERIC",
    "triceps pushdown": "CABLE_TRICEPS_PUSHDOWN",
    "tricep pushdown": "CABLE_TRICEPS_PUSHDOWN",
    "triceps extension": "TRICEPS_EXTENSION_GENERIC",
    "bicep curl": "CURL_GENERIC",
    "biceps curl": "CURL_GENERIC",
    "barbell curl": "BARBELL_BICEPS_CURL",
    "dumbbell bicep curl": "CURL_GENERIC",
    "plank": "PLANK_GENERIC",
    "push up": "PUSH_UP_GENERIC",
    "push ups": "PUSH_UP_GENERIC",
    "pull up": "PULL_UP_GENERIC",
    "pull ups": "PULL_UP_GENERIC",
}


def resolve_exercise(entry, overrides):
    exercise = str(entry.get("exercise_id") or "")
    if not exercise:
        return None, None
    if exercise in overrides:
        return overrides[exercise], "manual"
    name = (entry.get("exercise_snapshot") or {}).get("name") or entry.get("name")
    normalized = normalize(name)
    if normalized in ALIASES:
        return ALIASES[normalized], "alias"
    if normalized in CATALOG:
        return CATALOG[normalized], "catalog"
    return None, None
