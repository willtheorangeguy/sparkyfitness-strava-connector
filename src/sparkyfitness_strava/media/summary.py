"""Image facts derived from actual exported sets, with no invented body weight."""
from decimal import Decimal, ROUND_HALF_UP

POUNDS_PER_KG = Decimal('2.2046226218487757')


def volume(sets, units='lb'):
    if units not in {'lb', 'kg'}:
        raise ValueError('Summary units must be lb or kg')
    total = Decimal(0)
    for item in sets:
        if 'repetitions' in item and item.get('weight') is not None:
            weight, reps = Decimal(str(item['weight'])), Decimal(str(item['repetitions']))
            if not weight.is_finite() or not reps.is_finite() or weight < 0 or reps < 0:
                raise ValueError('Summary loads and repetitions must be finite and nonnegative')
            total += weight * reps
    return total * POUNDS_PER_KG if units == 'lb' else total


def demo():
    return {'title': 'Upper body', 'date': 'TUESDAY, OCTOBER 20', 'duration': '53:08',
            'exercise_count': 8, 'set_count': 26, 'volume': '12,000', 'units': 'lb',
            'primary': ['chest', 'back', 'shoulders'], 'secondary': ['biceps', 'triceps'],
            'volume_kg': Decimal(12000) / POUNDS_PER_KG}


def formatted_volume(sets, units='lb'):
    return f"{volume(sets, units).quantize(Decimal('1'), rounding=ROUND_HALF_UP):,}"
