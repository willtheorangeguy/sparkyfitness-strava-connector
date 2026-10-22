from copy import deepcopy
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx
import pytest

from sparkyfitness_strava.api import SparkyFitness
from sparkyfitness_strava.config import Config
from sparkyfitness_strava.engine import Engine
from sparkyfitness_strava.source import select_workouts
from sparkyfitness_strava.state import State
from sparkyfitness_strava.workout import build, SkipWorkout

EXERCISE = str(uuid4())
MAPPINGS = {EXERCISE: "BARBELL_BENCH_PRESS"}


def entry(**changes):
    return {"id": str(uuid4()), "type": "individual", "source": "sparky", "exercise_id": EXERCISE,
            "entry_date": "2026-07-01", "entry_time": "12:00", "duration_minutes": 45,
            "exercise_snapshot": {"modality": "weight_reps"},
            "sets": [{"id": 1, "set_number": 1, "reps": 8, "weight": 100,
                      "completed_at": "2026-07-01T18:05:00Z"}], **changes}


def workout(children=None, **changes):
    return {"id": str(uuid4()), "type": "preset", "source": "sparky", "entry_date": "2026-07-01",
            "workout_preset_id": 1, "name": "Strength", "exercises": children or [entry()], **changes}


def test_actual_metric_values_and_no_false_set_start():
    payload, missing, problems = build(workout(), MAPPINGS, "America/Edmonton")
    assert not missing and not problems
    assert payload["utc_offset"] == -21600
    assert payload["elapsed_time"] == 2700
    assert payload["sets"] == [{"exercise_type": "BARBELL_BENCH_PRESS", "repetitions": 8, "weight": 100}]


def test_reported_workout_total_takes_priority_over_overlapping_exercise_times():
    payload, missing, problems = build(workout([entry(), entry()], total_duration_minutes=55), MAPPINGS, "America/Edmonton")
    assert payload["elapsed_time"] == 3300
    assert not missing and not problems


def test_missing_start_is_estimated_from_final_completion_and_total_duration():
    child = entry(entry_time=None)
    child["sets"][0]["completed_at"] = "2026-07-01T18:45:00Z"
    payload, _, _ = build(workout([child], total_duration_minutes=45), MAPPINGS, "America/Edmonton")
    assert payload["start_time"] == "2026-07-01T18:00:00Z"
    assert payload["elapsed_time"] == 2700
    assert "start_time" not in payload["sets"][0]


def test_activity_start_is_serialized_as_utc_with_z_and_preserves_precision():
    child = entry(entry_time=None)
    child["sets"][0]["completed_at"] = "2026-07-01T12:45:00.485-06:00"
    payload, _, _ = build(workout([child], total_duration_minutes=45), MAPPINGS, "America/Edmonton")
    assert payload["start_time"] == "2026-07-01T18:00:00.485000Z"
    assert payload["elapsed_time"] == 2700
    assert payload["utc_offset"] == -21600


@pytest.mark.parametrize("source", ["garmin", "strava", "healthconnect", "unknown"])
def test_imported_workouts_and_mixed_native_groups_are_excluded(source):
    imported = workout([entry(source=source)], source=source)
    mixed = workout([entry(), entry(source=source)])
    imported_parent = workout([entry()], source=source)
    imported_plan = entry(source=source, workout_plan_assignment_id=99)
    assert list(select_workouts([imported, mixed, imported_parent, imported_plan], [])) == []
    for session in (imported, mixed, imported_parent):
        with pytest.raises(SkipWorkout, match="Only native SparkyFitness"):
            build(session, MAPPINGS, "America/Edmonton")


@pytest.mark.parametrize("source", ["sparky", "manual", "Manual"])
def test_native_source_names_are_accepted(source):
    native = workout([entry(source=source)], source=source)
    assert len(list(select_workouts([native], []))) == 1
    assert len(build(native, MAPPINGS, "America/Edmonton")[0]["sets"]) == 1


def test_workouts_without_any_source_evidence_are_excluded():
    assert list(select_workouts([workout([entry(source=None)], source=None)], [])) == []


def test_native_unfinished_sets_remain_excluded_with_reported_duration():
    child = entry(source="sparky")
    child["sets"][0]["completed_at"] = None
    with pytest.raises(SkipWorkout, match="No completed sets"):
        build(workout([child], total_duration_minutes=45), MAPPINGS, "America/Edmonton")


def test_total_duration_alone_cannot_supply_activity_date_and_time():
    child = entry(entry_time=None)
    child["sets"][0]["completed_at"] = None
    with pytest.raises(SkipWorkout, match="No completed sets"):
        build(workout([child], total_duration_minutes=45), MAPPINGS, "America/Edmonton")


@pytest.mark.parametrize("duration", [-1, "NaN", "Infinity", "bad", "1e1000"])
def test_invalid_reported_total_skips_workout(duration):
    with pytest.raises(SkipWorkout, match="Invalid recorded duration"):
        build(workout(total_duration_minutes=duration), MAPPINGS, "America/Edmonton")


@pytest.mark.parametrize("modality,values,expected", [
    ("bodyweight_reps", {"weight": 0}, {"repetitions": 8}),
    ("bodyweight_reps", {"weight": 20}, {"repetitions": 8, "weight": 20}),
    ("reps_only", {"weight": None}, {"repetitions": 8}),
    ("duration", {"weight": None, "duration": 90}, {"duration": 90}),
    ("weight_duration", {"weight": 15, "duration": 45}, {"duration": 45, "weight": 15}),
])
def test_supported_set_modalities(modality, values, expected):
    child = entry(exercise_snapshot={"modality": modality})
    child["sets"][0].update(values)
    payload, missing, problems = build(workout([child]), MAPPINGS, "America/Edmonton")
    assert not missing and not problems
    assert payload["sets"] == [{"exercise_type": "BARBELL_BENCH_PRESS", **expected}]


@pytest.mark.parametrize("values", [{"reps": None}, {"reps": 1.5}, {"reps": 0}, {"reps": -1},
                                    {"weight": "NaN"}, {"weight": "Infinity"}, {"weight": "1e1000"}, {"weight": -10},
                                    {"distance": 1}])
def test_invalid_completed_sets_block_workout(values):
    child = entry()
    child["sets"][0].update(values)
    payload, missing, problems = build(workout([child]), MAPPINGS, "America/Edmonton")
    assert problems and not payload["sets"]


def test_only_completed_sets_need_values_and_mappings():
    done = entry()
    done["sets"].append({"set_number": 2, "reps": 100, "weight": 200, "completed_at": None})
    planned = entry(exercise_id=str(uuid4()), entry_time=None, sets=[{"completed_at": None}])
    payload, missing, problems = build(workout([done, planned]), MAPPINGS, "America/Edmonton")
    assert not missing and not problems and len(payload["sets"]) == 1
    assert build(workout([done]), {}, "America/Edmonton")[1] == [EXERCISE]
    assert build(workout([done]), {EXERCISE: "INVALID"}, "America/Edmonton")[2]


@pytest.mark.parametrize("changes", [{"entry_time": None}, {"entry_date": None, "entry_time": "invalid"},
                                     {"duration_minutes": -1}, {"sets": [{"completed_at": None}]}])
def test_missing_or_invalid_timing_and_unperformed_workouts_skip(changes):
    with pytest.raises(SkipWorkout):
        build(workout([entry(**changes)]), MAPPINGS, "America/Edmonton")


@pytest.mark.parametrize("day,clock", [("2025-03-09", "02:30"), ("2025-11-02", "01:30")])
def test_dst_ambiguous_and_nonexistent_starts_skip(day, clock):
    with pytest.raises(SkipWorkout, match="Ambiguous|ambiguous"):
        build(workout([entry(entry_date=day, entry_time=clock)]), MAPPINGS, "America/Edmonton")


def test_selection_excludes_unlinked_and_keeps_preset_instances_separate():
    first, second = workout(), workout()
    unlinked = workout(workout_preset_id=None)
    selected = list(select_workouts([entry(), unlinked, first, second], []))
    assert [w["key"] for w in selected] == ["preset:" + first["id"], "preset:" + second["id"]]


@pytest.mark.parametrize("schedule", ["weekly", "sequential"])
def test_plan_session_groups_assignments_without_merging_dates_or_sessions(schedule):
    slot = "day_of_week" if schedule == "weekly" else "session_index"
    plans = [{"id": 1, "plan_name": "Plan", "assignments": [
        {"id": 10, slot: 1}, {"id": 11, slot: 1}, {"id": 12, slot: 2}]}]
    children = [entry(workout_plan_assignment_id=n) for n in [10, 11, 12]]
    children.append(entry(workout_plan_assignment_id=10, entry_date="2026-07-02"))
    selected = list(select_workouts(children, plans))
    assert len(selected) == 3
    assert sorted(len(s["exercises"]) for s in selected) == [1, 1, 2]
    # Explicit grouped plan workouts are never duplicated by assignment grouping.
    grouped = workout([children[0]], workout_preset_id=None)
    assert len(list(select_workouts([grouped], plans))) == 1


def test_missing_plan_assignment_is_skipped_and_not_guessed():
    selected = list(select_workouts([entry(workout_plan_assignment_id=99)], []))
    with pytest.raises(SkipWorkout, match="assignment"):
        build(selected[0], MAPPINGS, "America/Edmonton")


def test_api_key_pagination_and_read_only_source(tmp_path):
    calls = []
    def handler(request):
        calls.append(request)
        assert request.headers["x-api-key"] == "key"
        assert "authorization" not in request.headers
        number = int(request.url.params["page"])
        return httpx.Response(200, json={"sessions": [{"id": str(number), "type": "preset"}],
                                         "pagination": {"page": number, "hasMore": number == 1}})
    source = SparkyFitness(Config(tmp_path, "https://source.test", "key", "client", "secret"),
                          transport=httpx.MockTransport(handler))
    try:
        assert len(list(source.sessions())) == 2
        with pytest.raises(ValueError, match="read-only"):
            source.request("POST", "/anything")
        assert len(calls) == 2
    finally:
        source.close()


class Source:
    def __init__(self, sessions):
        self.data = sessions

    def request(self, method, path):
        assert method == "GET"
        if path == "/api/identity/user":
            return {"authenticatedUserId": "user", "activeUserId": "user"}
        return []

    def sessions(self):
        return deepcopy(self.data)

    def close(self):
        pass


class Destination:
    def __init__(self):
        self.uploads = []

    def call(self, method, path, **kwargs):
        if path == "/athlete":
            return {"id": 1}
        assert method == "POST" and path == "/uploads"
        self.uploads.append(kwargs)
        return {"id": len(self.uploads), "activity_id": 99, "external_id": kwargs["data"]["external_id"]}

    def close(self):
        pass


def test_preview_explains_missing_mappings_and_includes_sets_after_mapping(tmp_path):
    child = entry(exercise_snapshot={"name": "Custom Bench Movement", "modality": "weight_reps"})
    state = State(tmp_path)
    config = Config(tmp_path, "https://source.test", "key", "client", "secret", timezone="America/Edmonton", since="2026-01-01")
    destination = Destination()
    engine = Engine(config, state, Source([workout([child])]), destination)
    try:
        blocked = engine.preview()[0]
        assert blocked["state"] == "blocked" and blocked["payload"]["sets"] == []
        assert blocked["reason"] == "Missing Strava exercise mappings for 1 exercise(s)"
        assert blocked["missing_exercises"] == [{"id": EXERCISE, "name": "Custom Bench Movement"}]
        state.set("mappings", MAPPINGS)
        ready = engine.preview()[0]
        assert ready["state"] == "ready" and ready["reason"] is None
        assert ready["missing_exercises"] == [] and ready["missing"] == []
        assert ready["payload"]["sets"] == [{"exercise_type": "BARBELL_BENCH_PRESS", "repetitions": 8, "weight": 100}]
        assert destination.uploads == []
    finally:
        engine.close()
        state.close()


def test_sync_ignores_garmin_even_with_completed_sets_and_existing_mappings(tmp_path):
    native = workout()
    imported = workout([entry(source="garmin")], source="garmin")
    state = State(tmp_path)
    state.set("mappings", MAPPINGS)
    config = Config(tmp_path, "https://source.test", "key", "client", "secret", timezone="America/Edmonton", since="2026-01-01")
    destination = Destination()
    engine = Engine(config, state, Source([native, imported]), destination)
    try:
        assert [item["session"] for item in engine.preview()] == ["preset:" + native["id"]]
        assert engine.sync()["submitted"] == 1
        assert len(destination.uploads) == 1
        assert "preset:" + imported["id"] not in state.exports()
    finally:
        engine.close()
        state.close()


def test_automatic_mapping_uploads_native_workout_once_without_saving_overrides(tmp_path):
    child = entry(exercise_snapshot={"name": "Seated Cable Rows", "modality": "weight_reps"})
    native = workout([child])
    imported = workout([entry(source="garmin")], source="garmin")
    state = State(tmp_path)
    config = Config(tmp_path, "https://source.test", "key", "client", "secret", timezone="America/Edmonton", since="2026-01-01")
    destination = Destination()
    engine = Engine(config, state, Source([native, imported]), destination)
    try:
        preview = engine.preview()
        assert len(preview) == 1 and preview[0]["state"] == "ready"
        assert preview[0]["exercise_mappings"] == [{"id": EXERCISE, "name": "Seated Cable Rows",
                                                    "strava_type": "SEATED_CABLE_ROW", "method": "alias"}]
        assert preview[0]["payload"]["sets"] == [{"exercise_type": "SEATED_CABLE_ROW", "repetitions": 8, "weight": 100}]
        assert engine.sync()["submitted"] == 1
        assert state.get("mappings", {}) == {}
    finally:
        engine.close()
        state.close()
    state = State(tmp_path)
    engine = Engine(config, state, Source([native, imported]), destination)
    try:
        assert engine.sync()["submitted"] == 0
        assert len(destination.uploads) == 1
    finally:
        engine.close()
        state.close()


class RetryDestination(Destination):
    def __init__(self, external_id, *, error="Error Processing Data", activity_id=None):
        super().__init__()
        self.prior = {"external_id": external_id, "error": error, "activity_id": activity_id}

    def call(self, method, path, **kwargs):
        if path == "/uploads/7":
            return self.prior
        return super().call(method, path, **kwargs)


def failed_upload(plan):
    return {**{k: plan[k] for k in ("external_id", "fingerprint", "source_entries")},
            "state": "failed", "upload_id": "7", "reason": "Strava rejected the upload"}


def test_explicit_retry_uses_new_file_id_preserves_history_and_survives_restart(tmp_path):
    source = Source([workout()])
    state = State(tmp_path)
    state.set("mappings", MAPPINGS)
    config = Config(tmp_path, "https://source.test", "key", "client", "secret", timezone="America/Edmonton", since="2026-01-01")
    engine = Engine(config, state, source, Destination())
    original = engine.preview()[0]
    failed = failed_upload(original)
    state.save(original["session"], failed)
    destination = RetryDestination(original["external_id"])
    engine.strava = destination
    try:
        assert engine.retry(original["session"])["attempt"] == 1
        retry = engine.preview()[0]
        assert retry["state"] == "ready"
        assert retry["external_id"] == original["external_id"].removesuffix(".json") + ".retry1.json"
    finally:
        engine.close()
        state.close()
    state = State(tmp_path)
    engine = Engine(config, state, source, destination)
    try:
        assert engine.preview()[0]["external_id"] == retry["external_id"]
        assert engine.sync()["submitted"] == 1
        exported = state.export(original["session"])
        assert exported["state"] == "exported" and exported["attempt"] == 1
        assert exported["attempts"] == [{k: failed[k] for k in ("external_id", "upload_id", "state", "reason")}]
        assert engine.sync()["submitted"] == 0 and len(destination.uploads) == 1
    finally:
        engine.close()
        state.close()


@pytest.mark.parametrize("error,activity_id", [(None, None), (None, 99), ("stale error", 99)])
def test_retry_refuses_remote_success_or_still_processing_upload(tmp_path, error, activity_id):
    state = State(tmp_path)
    state.set("mappings", MAPPINGS)
    config = Config(tmp_path, "https://source.test", "key", "client", "secret", timezone="America/Edmonton", since="2026-01-01")
    engine = Engine(config, state, Source([workout()]), Destination())
    try:
        plan = engine.preview()[0]
        original = failed_upload(plan)
        state.save(plan["session"], original)
        engine.strava = RetryDestination(plan["external_id"], error=error, activity_id=activity_id)
        with pytest.raises(ValueError, match="reconcile"):
            engine.retry(plan["session"])
        assert state.export(plan["session"]) == original
    finally:
        engine.close()
        state.close()


def test_retry_does_not_bypass_current_source_validation(tmp_path):
    source = Source([workout()])
    state = State(tmp_path)
    state.set("mappings", MAPPINGS)
    config = Config(tmp_path, "https://source.test", "key", "client", "secret", timezone="America/Edmonton", since="2026-01-01")
    engine = Engine(config, state, source, Destination())
    try:
        plan = engine.preview()[0]
        state.save(plan["session"], failed_upload(plan))
        destination = RetryDestination(plan["external_id"])
        engine.strava = destination
        engine.retry(plan["session"])
        source.data[0]["exercises"][0]["sets"][0]["reps"] = None
        assert engine.preview()[0]["state"] == "blocked"
        assert engine.sync()["submitted"] == 0 and destination.uploads == []
    finally:
        engine.close()
        state.close()


def test_partial_export_later_completion_and_missing_timing_do_not_duplicate(tmp_path):
    good = workout()
    good["exercises"][0]["sets"].append({"id": 2, "set_number": 2, "reps": 10, "weight": 110, "completed_at": None})
    source = Source([good, workout([entry(entry_time=None)])])
    destination = Destination()
    config = Config(tmp_path, "https://source.test", "key", "client", "secret", timezone="America/Edmonton", since="2026-01-01")
    state = State(tmp_path)
    state.set("mappings", MAPPINGS)
    engine = Engine(config, state, source, destination)
    try:
        assert engine.sync()["submitted"] == 1
        assert len(engine.sync()["skipped"]) == 1
        source.data[0]["exercises"][0]["sets"][1]["completed_at"] = "2026-07-01T18:10:00Z"
        result = engine.sync()
        assert result["submitted"] == 0 and result["changed"] == ["preset:" + good["id"]]
        # A moved/regrouped session still contains the same source entries.
        source.data[0]["id"] = str(uuid4())
        assert engine.sync()["submitted"] == 0
        assert engine.sync()["changed"] == ["preset:" + source.data[0]["id"]]
        assert len(destination.uploads) == 1
    finally:
        engine.close()
        state.close()


def test_regrouping_without_content_change_remains_a_source_change(tmp_path):
    source, destination = Source([workout()]), Destination()
    config = Config(tmp_path, "https://source.test", "key", "client", "secret", timezone="America/Edmonton", since="2026-01-01")
    state = State(tmp_path)
    state.set("mappings", MAPPINGS)
    engine = Engine(config, state, source, destination)
    try:
        assert engine.sync()["submitted"] == 1
        source.data[0]["id"] = str(uuid4())
        result = engine.sync()
        assert result["submitted"] == 0 and result["changed"]
        assert len(destination.uploads) == 1
    finally:
        engine.close()
        state.close()


def test_pagination_repeated_page_cannot_loop_forever(tmp_path):
    def handler(request):
        return httpx.Response(200, json={"sessions": [{"id": "same", "type": "preset"}],
            "pagination": {"page": int(request.url.params["page"]), "hasMore": True}})
    source = SparkyFitness(Config(tmp_path, "https://source.test", "key", "client", "secret"),
                          transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ValueError, match="Repeated"):
            list(source.sessions())
    finally:
        source.close()


def test_future_and_recent_completions_wait(tmp_path):
    now = datetime.now(timezone.utc)
    child = entry(entry_date=now.date().isoformat(), entry_time=now.strftime("%H:%M"), duration_minutes=0)
    child["sets"][0]["completed_at"] = now.isoformat()
    state = State(tmp_path)
    config = Config(tmp_path, "https://source.test", "key", "client", "secret", since="2026-01-01")
    engine = Engine(config, state, Source([workout([child])]), Destination())
    try:
        assert engine.preview() == []
        child["sets"][0]["completed_at"] = (now + timedelta(days=1)).isoformat()
        engine.sparkyfitness.data = [workout([child])]
        assert engine.preview() == []
    finally:
        engine.close()
        state.close()


def test_reported_total_does_not_bypass_settling_after_recent_completion(tmp_path):
    now = datetime.now(timezone.utc)
    child = entry(entry_date=(now - timedelta(days=1)).date().isoformat(), entry_time="00:00")
    child["sets"][0]["completed_at"] = now.isoformat()
    state = State(tmp_path)
    config = Config(tmp_path, "https://source.test", "key", "client", "secret", since="2026-01-01")
    engine = Engine(config, state, Source([workout([child], total_duration_minutes=10)]), Destination())
    try:
        assert engine.preview() == []
    finally:
        engine.close()
        state.close()


def test_wger_state_is_rejected(tmp_path):
    state = State(tmp_path)
    state.set("wger_account", {"url": "old", "user": "old"})
    engine = Engine(Config(tmp_path, "https://source.test", "key", "client", "secret"), state, Source([]), Destination())
    try:
        with pytest.raises(ValueError, match="wger state"):
            engine.source()
    finally:
        engine.close()
        state.close()


def test_export_preserves_completed_muscle_metadata_in_durable_image_job(tmp_path):
    import json
    child = entry(exercise_snapshot={'name':'Barbell Bench Press','modality':'weight_reps',
                                     'primary_muscles':['chest'], 'secondary_muscles':['triceps','shoulders']})
    pending = entry(exercise_snapshot={'name':'Barbell Squat','modality':'weight_reps',
                                      'primary_muscles':['quadriceps']}, sets=[])
    state = State(tmp_path)
    config = Config(tmp_path, 'https://source.test', 'key', 'client', 'secret',
                    timezone='America/Edmonton', since='2026-01-01', media_enabled=True)
    destination = Destination()
    engine = Engine(config, state, Source([workout([child,pending])]), destination)
    try:
        assert engine.sync()['submitted'] == 1
        job = json.loads((tmp_path/'media/outbox/99.json').read_text())
        assert job['primary'] == ['chest']
        assert job['secondary'] == ['shoulders','triceps']
        assert engine.sync()['submitted'] == 0
    finally:
        engine.close()
        state.close()
