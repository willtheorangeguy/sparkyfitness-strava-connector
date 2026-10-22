"""Select logged preset/plan instances, never the prescribed template sets."""
from .state import encode


def is_native_workout(session):
    # "manual"/"Manual" are the API defaults for native entries; the app also uses
    # "sparky". Check children too so imported sets cannot enter a native group.
    sources = {str(entry["source"]).strip().lower() for entry in [session, *session.get("exercises", [])]
               if entry.get("source")}
    return bool(sources) and sources <= {"sparky", "manual"}


def select_workouts(sessions, plans):
    assignments = {}
    for plan in plans:
        for assignment in plan.get("assignments", []):
            assignments[str(assignment["id"])] = (plan, assignment)
    groups = {}
    for session in sessions:
        if not is_native_workout(session):
            continue
        if session["type"] == "preset":
            children = session.get("exercises", [])
            if session.get("workout_preset_id") is None and session.get("workout_plan_assignment_id") is None and not any(
                child.get("workout_plan_assignment_id") is not None for child in children
            ):
                continue
            yield {**session, "key": "preset:" + str(session["id"]),
                   "notes": "\n".join(filter(None, [session.get("description"), session.get("notes"),
                                                    *(child.get("notes") for child in children)]))}
            continue
        assignment_id = session.get("workout_plan_assignment_id")
        if assignment_id is None:
            continue
        resolved = assignments.get(str(assignment_id))
        if resolved is None:
            yield {**session, "key": "unresolved:" + str(session["id"]), "exercises": [session],
                   "skip_reason": "Plan assignment is unavailable; cannot identify its session"}
            continue
        plan, assignment = resolved
        slot = assignment.get("session_index")
        schedule = "sequence" if slot is not None else "weekday"
        slot = slot if slot is not None else assignment.get("day_of_week")
        if slot is None:
            yield {**session, "key": "unresolved:" + str(session["id"]), "exercises": [session],
                   "skip_reason": "Plan assignment has no scheduled session identity"}
            continue
        key = "plan:" + encode([str(plan["id"]), schedule, slot, session.get("entry_date")])
        group = groups.setdefault(key, {"key": key, "entry_date": session.get("entry_date"),
                                      "name": assignment.get("session_name") or plan.get("plan_name"),
                                      "exercises": [], "notes": ""})
        group["exercises"].append({**session, "sort_order": assignment.get("sort_order") or 0})
    for group in groups.values():
        group["exercises"].sort(key=lambda e: (e.get("entry_time") or "", e.get("sort_order") or 0, str(e["id"])))
        group["notes"] = "\n".join(e["notes"] for e in group["exercises"] if e.get("notes"))
        yield group
