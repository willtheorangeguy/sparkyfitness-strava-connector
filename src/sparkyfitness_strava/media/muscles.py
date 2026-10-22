"""Translate explicit source anatomy into the schematic's supported regions."""
import re
import unicodedata


def key(value):
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', ' ', value.casefold()).strip()


ALIASES = {
    'chest': ('chest', 'pectorals', 'pectoralis major', 'pectoralis'),
    'shoulders': ('shoulders', 'shoulder', 'deltoids', 'deltoid', 'anterior deltoid', 'posterior deltoid'),
    'back': ('back', 'lats', 'latissimus dorsi', 'trapezius', 'traps', 'middle back', 'upper back', 'rhomboids'),
    'lower_back': ('lower back', 'erector spinae', 'spinal erectors'),
    'biceps': ('biceps', 'biceps brachii', 'brachialis'),
    'triceps': ('triceps', 'triceps brachii'),
    'forearms': ('forearms', 'forearm', 'brachioradialis'),
    'abs': ('abs', 'abdominals', 'abdominal', 'abdominis', 'rectus abdominis'),
    'obliques': ('obliques', 'obliquus externus abdominis', 'external obliques'),
    'quads': ('quads', 'quadriceps', 'quadriceps femoris'),
    'hamstrings': ('hamstrings', 'biceps femoris', 'ischiocrural muscles'),
    'glutes': ('glutes', 'gluteals', 'gluteus', 'gluteus maximus', 'gluteus medius'),
    'calves': ('calves', 'calf', 'gastrocnemius', 'soleus'),
    'adductors': ('adductors', 'adductor', 'hip adductors', 'adductor longus'),
}
LOOKUP = {key(name): region for region, names in ALIASES.items() for name in (region, *names)}


def normalize(values):
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, (list, tuple)):
        return set(), set()
    regions, unknown = set(), set()
    for value in values:
        names = [value.get('name_en'), value.get('name')] if isinstance(value, dict) else [value]
        names = [name.strip() for name in names if isinstance(name, str) and name.strip()]
        region = next((LOOKUP[key(name)] for name in names if key(name) in LOOKUP), None)
        if region:
            regions.add(region)
        elif names:
            unknown.add(names[0])
    return regions, unknown


def collect(exercises, primary_field='primary_muscles', secondary_field='secondary_muscles'):
    primary, secondary, unknown = set(), set(), set()
    for exercise in exercises:
        if not isinstance(exercise, dict):
            continue
        main, missing_main = normalize(exercise.get(primary_field))
        extra, missing_extra = normalize(exercise.get(secondary_field))
        primary.update(main)
        secondary.update(extra)
        unknown.update(missing_main | missing_extra)
    return {'primary': sorted(primary), 'secondary': sorted(secondary - primary),
            'unmapped_muscles': sorted(unknown)}


def sparky_session(session):
    return collect((entry.get('exercise_snapshot') or entry)
                   for entry in session.get('exercises', [])
                   if any(item.get('completed_at') is not None for item in entry.get('sets', [])))
