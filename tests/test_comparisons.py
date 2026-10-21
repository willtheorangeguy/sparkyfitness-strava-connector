from decimal import Decimal
from xml.etree import ElementTree

import pytest

from sparkyfitness_strava.media.comparisons import REFERENCES, compare
from sparkyfitness_strava.media.comparison_art import illustration
from sparkyfitness_strava.media.summary import POUNDS_PER_KG


@pytest.mark.parametrize('reference', REFERENCES, ids=lambda item: item.key)
def test_each_reference_is_reachable_and_unit_independent(reference):
    kg = compare(reference.kg)
    lb = compare(Decimal(reference.kg) * POUNDS_PER_KG, 'lb')
    assert kg['object'] == lb['object'] == reference.key
    assert kg['equivalent'] == lb['equivalent'] == 'About 1.0× this weight'


def test_nearest_reference_boundaries_and_ties():
    assert compare(2399)['object'] == 'container'
    assert compare(2400)['object'] == 'container'
    assert compare(2401)['object'] == 'pickup'
    assert compare(12000, 'lb')['object'] == 'orca'


def test_extremes_report_fractions_and_multiples_without_inventing_load():
    assert compare(0)['object'] is None
    assert compare(1)['equivalent'] == 'About 0.1% of this weight'
    assert compare('.001')['equivalent'] == 'Less than 0.1% of this weight'
    assert compare(800)['equivalent'] == 'About 0.5× this weight'
    assert compare(12000000000)['equivalent'] == 'About 2.0× this weight'


@pytest.mark.parametrize('value,units', [(-1,'kg'), ('NaN','kg'), ('Infinity','lb'), (12,'oz')])
def test_invalid_comparison_loads_are_rejected(value, units):
    with pytest.raises(ValueError):
        compare(value, units)


def test_every_subject_has_valid_local_svg_without_stray_path_text():
    for reference in REFERENCES:
        root=ElementTree.fromstring(illustration(reference.key, reference.name))
        assert root.attrib['role']=='img'
        assert reference.name in root.attrib['aria-label']
        assert not ''.join(root.itertext()).strip(), reference.key
        assert 'href=' not in ElementTree.tostring(root, encoding='unicode')
