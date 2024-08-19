#!/usr/bin/env python

# def test_imports():
#     import geodrillcalc.geodrillcalc as gdc

# def debug_pipeline():
#     import geodrillcalc.geodrillcalc as gdc
#     aquifer_layer_table = {'aquifer_layer': ['102utqa', '111lta', '114bse'], 'is_aquifer': [True, True, False], 'depth_to_base': [47.0, 507.0, 807.0]}


def test_pipeline():
    import geodrillcalc.geodrillcalc as gdc
    from geodrillcalc.wellborecost.cost_parameter_extractor import CostParameterExtractor
    from geodrillcalc.wellborecost.wellborecost_pipeline import CostCalculationPipeline

    aquifer_layer_table = {
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
    gci.set_loglevel(4)

    wbd = gci.calculate_and_return_wellbore_parameters(False, # True for production, false for injection
                                                       aquifer_layer_table,
                                    initial_values)
    #cpe = CostParameterExtractor(wbd)
    #jsonstr = wbd.export_results_to_json_string()
    #result = wbd.export_results_to_dict()
    #print(result)
    #print(wbd.casing_stage_table)
    assert wbd.ready_for_calculation
    assert wbd.calculation_completed
    #assert type(jsonstr) is str

    # atts = get_all_non_boilerplate_attributes(CostParameterExtractor)
    # for att in atts:
    #     print(cpe.__getattribute__(att))
    cpl = CostCalculationPipeline(wbd)
    print(cpl.wellbore_params)
    
