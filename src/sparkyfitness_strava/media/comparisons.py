"""Illustrative reference masses supplied for the workout-card design (kg).

These are approximate examples, not specifications for a particular animal or
vehicle. Pounds are always calculated from kg rather than rounded independently.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from .summary import POUNDS_PER_KG


@dataclass(frozen=True)
class Reference:
    key: str
    name: str
    kg: int


REFERENCES = (
    Reference('hippo', 'Hippopotamus', 1600),
    Reference('container', 'Empty shipping container (20 ft)', 2300),
    Reference('pickup', 'Pickup truck', 2500),
    Reference('forklift', 'Forklift', 4000),
    Reference('orca', 'Orca', 5000),
    Reference('elephant', 'African elephant', 6000),
    Reference('tractor', 'Semi-truck tractor', 8000),
    Reference('bus', 'School bus', 10000),
    Reference('bell', 'Big Ben bell', 13700),
    Reference('whale_shark', 'Whale shark', 15000),
    Reference('excavator', 'Excavator', 20000),
    Reference('stonehenge', 'Large Stonehenge stone', 25000),
    Reference('humpback', 'Humpback whale', 30000),
    Reference('semi', 'Loaded semi-truck', 36000),
    Reference('subway', 'Subway railcar', 38000),
    Reference('blue_whale', 'Blue whale', 150000),
    Reference('locomotive', 'Freight locomotive', 190000),
    Reference('liberty', 'Statue of Liberty (without pedestal)', 254000),
    Reference('iss', 'International Space Station', 419725),
    Reference('a380', 'Airbus A380 (maximum takeoff weight)', 575000),
    Reference('mining_truck', 'Loaded Caterpillar mining truck', 623690),
    Reference('saturn_v', 'Saturn V rocket (fully fueled)', 2800000),
    Reference('bunker_hill', 'Bunker Hill Monument', 6350000),
    Reference('eiffel', 'Eiffel Tower', 10100000),
    Reference('pisa', 'Leaning Tower of Pisa', 14453000),
    Reference('washington', 'Washington Monument (with foundation)', 90700000),
    Reference('carrier', 'Loaded aircraft carrier', 100000000),
    Reference('empire_state', 'Empire State Building', 331000000),
    Reference('golden_gate', 'Golden Gate Bridge (including anchorages and approaches)', 804700000),
    Reference('pyramid', 'Great Pyramid of Giza', 6000000000),
)


def compare(total, units='kg'):
    """Choose the nearest reference mass; show a fraction/multiple honestly.

    Ties prefer the lighter reference. Selection uses unrounded kg so changing
    display units does not change the subject. Zero load has no equivalence.
    """
    if units not in {'kg', 'lb'}:
        raise ValueError('Comparison units must be lb or kg')
    mass = Decimal(str(total))
    if not mass.is_finite() or mass < 0:
        raise ValueError('Comparison load must be finite and nonnegative')
    kg = mass / POUNDS_PER_KG if units == 'lb' else mass
    if not kg:
        return {'object': None, 'name': 'No external load recorded',
                'equivalent': '', 'reference': 'Bodyweight and timed sets do not add external load.'}
    reference = min(REFERENCES, key=lambda item: abs(kg - item.kg))
    ratio = kg / reference.kg
    if ratio < Decimal('.1'):
        percent = ratio * 100
        amount = percent.quantize(Decimal('.1'), rounding=ROUND_HALF_UP)
        equivalent = 'Less than 0.1% of this weight' if not amount else f'About {amount}% of this weight'
    else:
        amount = ratio.quantize(Decimal('.1'), rounding=ROUND_HALF_UP)
        equivalent = f'About {amount:,.1f}× this weight'
    reference_mass = Decimal(reference.kg) * (POUNDS_PER_KG if units == 'lb' else 1)
    rounded = reference_mass.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return {'object': reference.key, 'name': reference.name, 'equivalent': equivalent,
            'reference': f'Approx. {rounded:,} {units} reference weight'}
