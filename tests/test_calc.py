#!/usr/bin/env python3

import geodrillcalc.wellbore_param_calc as wpc

def test_working():
    print(wpc.assign_pump_diameter(5))
    assert 1==1
    return True



