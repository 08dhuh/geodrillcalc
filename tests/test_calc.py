#!/usr/bin/env python

def test_pipeline():
    import geodrillcalc.geodrillcalc as gdc
    from geodrillcalc.wellborecost.cost_parameter_extractor import CostParameterExtractor
    from geodrillcalc.wellborecost.wellborecost_pipeline import CostCalculationPipeline
    from geodrillcalc.wellborecost.stage4_calc_cost import WellboreCostCalculator
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

    wbd = gci.calculate_and_return_wellbore_parameters(True, # True for production, false for injection
                                                       aquifer_layer_table,
                                    initial_values)

    assert wbd.ready_for_calculation
    assert wbd.calculation_completed
    with open('geodrillcalc/data/fallback_cost_rates.json') as f:
        cost_rates = json.load(f)
    cpl = CostCalculationPipeline(wbd, cost_rates)


    with open('geodrillcalc/data/fallback_margin_rates.json') as f:
        md = json.load(f)

    # Test WellboreCostCalculator
    wellbore_cost_calculator = WellboreCostCalculator(
        cost_rates=cost_rates,
        wellbore_params=cpl.wellbore_params,
        margins_dict=md,  
        stage_labels=['drilling_rates', 'time_rates', 'materials', 'others']
    )


    # Calculate total cost

    total_cost_table = wellbore_cost_calculator.calculate_total_cost()
    print(total_cost_table)
    print(wellbore_cost_calculator.cost_estimation_table)

