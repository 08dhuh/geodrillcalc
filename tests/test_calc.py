#!/usr/bin/env python

def test_imports():
    import geodrillcalc.geodrillcalc as gdc


def test_pipeline():
    import geodrillcalc.geodrillcalc as gdc
    import geodrillcalc.wellbore_dict as wbdict
    depth_data = {
        "aquifer_layer": [
            '100qa',
            '103utqd',
            '105utaf',
            '106utd',
            '107umta',
            '108umtd',
            '109lmta',
            '111lta',
            '114bse'
        ],
        "is_aquifer": [
            True,
            False,
            True,
            False,
            True,
            False,
            True,
            True,
            False
        ],
        "depth_to_base": [
            3,
            53,
            112,
            150,
            150,
            1000,
            1000,
            1221,
            1421
        ]
    }

    initial_values = {
        "required_flow_rate": 4320,
        "hydraulic_conductivity": 5,
        "average_porosity": 0.25,
        "bore_lifetime_year": 30,
        "groundwater_depth": 25,
        "long_term_decline_rate": 1,
        "allowable_drawdown": 25,
        "safety_margin": 25,
        "target_aquifer_layer": "109lmta",
        "top_aquifer_layer": "100qa"
    }

    gci = gdc.GeoDrillCalcInterface()
    wbd = gci.calculate_and_return_wellbore_parameters(True,
                                                       depth_data,
                                                       initial_values)
    jsonstr = wbd.export_results_to_json_string()
    assert wbd.is_initialised
    assert wbd.calculation_completed
    assert type(jsonstr) is str
