import pytest

from sparkyfitness_strava import mapping
from sparkyfitness_strava.mapping import ALIASES, EXERCISES, resolve_exercise


@pytest.mark.parametrize("name,target", [
    ("Barbell Squat", "BARBELL_SQUAT"),
    ("Seated Leg Curl", "MACHINE_LEG_CURL_SEATED"),
    ("Seated Calf Raise", "SEATED_CALF_RAISE"),
    ("Close-Grip Front Lat Pulldown", "CABLE_LAT_PULLDOWN_CLOSE_GRIP"),
    ("Seated Cable Rows", "SEATED_CABLE_ROW"),
    ("Straight-Arm Dumbbell Pullover", "DUMBBELL_PULLOVER"),
    ("Lat Static Stretch", "LAT_STRETCH"),
    ("Face Pull", "FACE_PULL"),
    ("Machine Preacher Curls", "PREACHER_CURL_MACHINE"),
    ("Barbell Bench Press - Medium Grip", "BARBELL_BENCH_PRESS"),
    ("Leverage Chest Press", "MACHINE_CHEST_PRESS"),
    ("Arnold Dumbbell Press", "ARNOLD_PRESS"),
    ("Dumbbell Flyes", "DUMBBELL_FLYE"),
    ("Pec Static Stretch", "STRETCH"),
    ("Side Lateral Raise", "LATERAL_RAISE_GENERIC"),
    ("Reverse Grip Triceps Pushdown", "CABLE_TRICEPS_PUSHDOWN"),
    ("Cable Rope Overhead Triceps Extension", "CABLE_OVERHEAD_TRICEPS_EXTENSION"),
    ("Cable One Arm Tricep Extension", "TRICEPS_EXTENSION_GENERIC"),
    ("Plank", "PLANK_GENERIC"),
    ("  bArBeLl__bench PRESS  ", "BARBELL_BENCH_PRESS"),
    ("Barbell Bench Press—Medium Grip", "BARBELL_BENCH_PRESS"),
    ("Bench Press", "BENCH_PRESS_GENERIC"),
])
def test_automatic_matching_for_catalog_names_and_library_aliases(name, target):
    entry = {"exercise_id": "exercise", "exercise_snapshot": {"name": name}}
    actual, method = resolve_exercise(entry, {})
    assert actual == target and method in {"catalog", "alias"}
    assert actual in EXERCISES


def test_aliases_only_reference_supported_exercises():
    assert set(ALIASES.values()) <= EXERCISES


@pytest.mark.parametrize("name", [None, "", "Unknown", "Custom Bench Movement", "Barbell Bench Pres", "Not a squat"])
def test_unknown_names_do_not_receive_a_similar_but_wrong_exercise(name):
    assert resolve_exercise({"exercise_id": "exercise", "name": name}, {}) == (None, None)


def test_deleted_exercise_does_not_gain_an_identity_from_name_matching():
    assert resolve_exercise({"exercise_snapshot": {"name": "Barbell Squat"}}, {}) == (None, None)


def test_snapshot_name_has_priority_over_entry_name_and_manual_override_has_priority_over_both():
    entry = {"exercise_id": "exercise", "name": "Barbell Squat", "exercise_snapshot": {"name": "Face Pull"}}
    assert resolve_exercise(entry, {}) == ("FACE_PULL", "catalog")
    assert resolve_exercise(entry, {"exercise": "SQUAT_GENERIC"}) == ("SQUAT_GENERIC", "manual")
    assert resolve_exercise(entry, {"exercise": "INVALID"}) == ("INVALID", "manual")


def test_catalog_normalization_collisions_do_not_choose_arbitrarily(monkeypatch):
    monkeypatch.setattr(mapping, "EXERCISES", frozenset({"EXAMPLE", "EXAMPLE_GENERIC"}))
    assert "example" not in mapping.catalog_index()
