from geodrillcalc.utils.calc_utils import find_next_largest_value

def test_find_next_largest_value():
    values = [0.1, 0.2, 0.3, 0.5]
    assert find_next_largest_value(0.25, values) == 0.3

