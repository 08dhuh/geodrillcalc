#!/usr/bin/env python

def test_pipeline():
    import geodrillcalc.geodrillcalc_interface as gdc
    from geodrillcalc.wellborecost.cost_parameter_extractor import CostParameterExtractor
    from geodrillcalc.wellborecost.wellborecost_pipeline import CostPipeline
    from geodrillcalc.wellborecost.cost_stage_calculator import CostStageCalculator
    import json

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
    gci.set_loglevel(0)

    wbd = gci.calculate_and_return_wellbore_parameters(False, # True for production, false for injection
                                                       aquifer_layer_table,
                                    initial_values)
    #js = wbd.export_installation_results_to_json_string()
    #assert isinstance(js, str)
    assert wbd.ready_for_calculation
    assert wbd.ready_for_installation_output
    assert wbd.ready_for_cost_output

    result = wbd.export_results_to_dict()
    print(result)
    #print(js)

    # with open('geodrillcalc/data/fallback_cost_rates.json') as f:
    #     cost_rates = json.load(f)
    # with open('geodrillcalc/data/fallback_margin_rates.json') as f:
    #     md = json.load(f)

    #print(cpl.wellbore_params)


    # Test WellboreCostCalculator
    # wellbore_cost_calculator = WellboreCostCalculator(
    #     cost_rates=cost_rates,
    #     wellbore_params=cpl.wellbore_params,
    #     margin_rates=md,  
    #     stage_labels=['drilling_rates', 'time_rates', 'materials', 'others']
    # )

    #print(wellbore_cost_calculator.margin_functions)

    # Calculate total cost

    # total_cost_table = wellbore_cost_calculator.calculate_total_cost()
    # print(total_cost_table)
    # print(wellbore_cost_calculator.cost_estimation_table)
    #assert not total_cost_table.empty


    #assert not wellbore_cost_calculator.cost_estimation_table.empty

