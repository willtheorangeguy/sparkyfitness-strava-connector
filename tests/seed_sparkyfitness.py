"""Create isolated real API fixtures. No Strava credentials or uploads."""
from copy import deepcopy
from datetime import date, timedelta
import json
from fixture_api import FixtureAPI


def seed(base, email, password, journal):
    api = FixtureAPI(base)
    api.request("/api/auth/sign-up/email", {"email": email, "password": password, "name": "Connector integration"})
    api.request("/api/auth/sign-in/email", {"email": email, "password": password})
    key = api.request("/api/identity/user/generate-api-key", {"name": "connector-test", "scope": "full"})
    api.api_key = key["apiKey"]["key"]
    fixture = {"email": email, "api_key": api.api_key, "mappings": {}, "sessions": []}
    journal.write_text(json.dumps(fixture), encoding="utf-8")
    exercises = []
    for name, category, modality, target in [
        ("Test Bench", "strength", "weight_reps", "BARBELL_BENCH_PRESS"),
        ("Test Plank", "isometric", "duration", "PLANK_GENERIC")]:
        result = api.request("/api/exercises", {"exerciseData": json.dumps({
            "name": name, "category": category, "modality": modality, "calories_per_hour": 240,
            "source": "custom", "is_custom": True, "shared_with_public": False,
            "primary_muscles": ["chest"], "secondary_muscles": [], "equipment": ["barbell"]})})
        exercises.append(result["id"])
        fixture["mappings"][result["id"]] = target
    day = str(date.today() - timedelta(days=7))
    children = [
        {"exercise_id": exercises[0], "entry_time": "10:00", "sort_order": 0, "duration_minutes": 45,
         "sets": [{"set_number": n, "reps": 8, "weight": 61.23,
                   "completed_at": day + f"T10:{n*5:02d}:00Z"} for n in range(1, 4)]},
        {"exercise_id": exercises[1], "entry_time": "10:20", "sort_order": 1, "duration_minutes": 10,
         "sets": [{"set_number": 1, "duration": 90, "completed_at": day + "T10:25:00Z"},
                  {"set_number": 2, "duration": 999, "completed_at": None}]}]
    preset = api.request("/api/workout-presets", {"name": "Integration preset", "exercises": [
        {"exercise_id": exercise, "sets": [{"set_number": 1, "reps": 999, "weight": 200}]} for exercise in exercises]})
    grouped = api.request("/api/exercise-preset-entries", {"workout_preset_id": preset["id"], "entry_date": day,
        "name": "Integration preset", "notes": "Synthetic SparkyFitness workout", "exercises": children})
    fixture["sessions"].append(grouped["id"])
    plan = api.request("/api/workout-plan-templates", {"plan_name": "Integration plan", "schedule_type": "weekly",
        "start_date": day, "is_active": True, "assignments": [
            {"day_of_week": 1, "exercise_id": exercise, "sort_order": n,
             "sets": [{"set_number": 1, "reps": 999, "weight": 200}]} for n, exercise in enumerate(exercises)]})
    for child, assignment in zip(children, plan["assignments"]):
        api.request("/api/exercise-entries", {**child, "entry_date": day,
            "workout_plan_assignment_id": assignment["id"], "calories_burned": 0})
    # Exclusion controls: unrelated standalone entry, freeform grouped workout,
    # unperformed preset, missing-time preset, and future preset.
    api.request("/api/exercise-entries", {**children[0], "entry_date": day, "calories_burned": 0})
    api.request("/api/exercise-preset-entries", {"entry_date": day, "name": "Unlinked freeform", "exercises": children})
    pending = deepcopy(children)
    for child in pending:
        for logged in child["sets"]: logged["completed_at"] = None
    api.request("/api/exercise-preset-entries", {"workout_preset_id": preset["id"], "entry_date": day, "exercises": pending})
    missing = deepcopy(children)
    for child in missing: child["entry_time"] = None
    api.request("/api/exercise-preset-entries", {"workout_preset_id": preset["id"], "entry_date": day, "exercises": missing})
    future_day = str(date.today() + timedelta(days=2))
    future = deepcopy(children)
    for child in future:
        for logged in child["sets"]:
            if logged["completed_at"]: logged["completed_at"] = logged["completed_at"].replace(day, future_day)
    api.request("/api/exercise-preset-entries", {"workout_preset_id": preset["id"], "entry_date": future_day, "exercises": future})
    fixture["day"] = day
    journal.write_text(json.dumps(fixture), encoding="utf-8")
    return fixture
