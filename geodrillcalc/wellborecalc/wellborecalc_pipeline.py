#!/usr/bin/env python
import numpy as np
import pandas as pd
from ..wellbore_dict import WellBoreDict
from . import stage1_calc_screen as ci, stage2_calc_pump as cp, stage3_calc_casing as cc
from ..utils.utils import getlogger, find_next_largest_value


class CalcPipeline:
    """
    A class designed to calculate wellbore model parameters using a WellBoreDict instance.

    This class requires a fully instantiated and initialised WellBoreDict instance, 
    achieved through the WellBoreDict.initialise method.
    The WellBoreDict instance attributes are updated in three consecutive calls to the class methods.

    The CalcPipeline class is intended to be used in conjunction with the WellBoreDict instance, 
    collaborating to calculate wellbore parameters.
    All calculations operate on WellBoreDict's internal class attributes, initialised in advance. 
    Results are stored within the same WellBoreDict instance.

    For the casing stage, an additional argument is required, 
    distinguishing between production and injection pumps 

    Method Overview:
    1. _screen_pipeline: Calculates interval parameters.
    2. _pump_pipeline: Calculates pump parameters.
    3. _casing_pipeline: Calculates casing parameters. 
        Requires a boolean argument (True for production pump, False for injection pump).
    4. calc_pipeline: Encapsulates the pipeline methods in a single method

    Required Parameters:
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

    Usage Example:
    wbd = WellBoreDict()
    wbd.initialise_and_validate_input_params(aquifer_layer_table=aquifer_layer_table, **initial_values)  
    
    calc_injectionpipe = CalcPipeline(wbd)
    calc_injectionpipe.calc_pipeline(is_production_well=True)
    """

    def __init__(self, wellboredict: WellBoreDict, logger=None):
        self.wbd = wellboredict  # wellboredict must be a fully initialised instance
        if not self.wbd.ready_for_calculation:
            raise RuntimeError(f"Input parameters must be assigned to WellBoreDict object before calling the current class {self.__name__}")
        self.casing_diameters_in_metres = self.wbd.get_casing_diameters()
        self.drilling_diameters_in_metres = self.wbd.get_drilling_diameters()
        self.logger = logger or getlogger()

    def calc_pipeline(self):
        logger = self.logger
        try:
            setattr(self.wbd,'calculation_completed',False)            
            self._screen_pipeline()
            self._pump_pipeline()
            self._casing_pipeline()
            setattr(self.wbd,'calculation_completed',True)
        except ValueError as e:
            logger.error(f"An error occurred during calculation: {str(e)}")
            raise ValueError from e
        except ZeroDivisionError as e:
            logger.error(f"Zero division error occurred in interval calculations: {str(e)}")
            raise ValueError from e
        
    def _screen_pipeline(self):
        """
        Determines and updates WellboreDict instance Interval parameters
        "screen_length": float,
        "screen_length_error": float,
        "screen_diameter": float,
        "open_hole_diameter": float,

        if is_production_well:
        "min_total_casing_production_screen_diameter": float,
        "screen_stage_table": pd.DataFrame,
        """
        wbd = self.wbd  # fully initialised wellboredict instance
        ir = {}

        ir['screen_length'], ir['screen_length_error'] = \
            ci.calculate_minimum_screen_length(wbd.required_flow_rate,
                                               wbd.hydraulic_conductivity,
                                               wbd.bore_lifetime_per_day,
                                               wbd.aquifer_thickness,
                                               wbd.is_production_well)
        ohd_min = ci.calculate_minimum_open_hole_diameter(wbd.required_flow_rate_per_m3_sec,
                                                                     ir['screen_length'],
                                                                     wbd.sand_face_velocity_production if wbd.is_production_well else wbd.sand_face_velocity_injection,
                                                                     wbd.aquifer_average_porosity,
                                                                     wbd.net_to_gross_ratio_aquifer)
        
        ir['open_hole_diameter'] = find_next_largest_value(
            ohd_min, self.drilling_diameters_in_metres)


        if wbd.is_production_well:
            #define and populates 3 associated parameters
            screen_df = pd.DataFrame(self.casing_diameters_in_metres,
                                    columns=['production_casing_diameters'])
            screen_df['production_casing_frictions'] = \
                ci.calculate_casing_friction(wbd.depth_to_top_screen,
                                            wbd.required_flow_rate_per_m3_sec,
                                            self.casing_diameters_in_metres,
                                            wbd.pipe_roughness_coeff)
            
            screen_df['production_minimum_screen_diameters'] = \
                ci.calculate_minimum_screen_diameter(screen_df['production_casing_frictions'].to_numpy(),
                                                    screen_length=ir['screen_length'],
                                                    req_flow_rate=wbd.required_flow_rate_per_m3_sec,
                                                    pipe_roughness_coeff=wbd.pipe_roughness_coeff
                                                    )

            screen_df['production_screen_diameters'] = \
                screen_df.apply(lambda row: find_next_largest_value
                                (row['production_minimum_screen_diameters'],
                                self.casing_diameters_in_metres)
                                if not np.isnan(row['production_minimum_screen_diameters'])
                                else np.nan,
                                axis=1)
            screen_df['total_casing'] =\
                screen_df.apply(lambda row: ci.calculate_total_casing(row['production_casing_diameters'],
                                                                        row['production_screen_diameters'],
                                                                        wbd.depth_to_top_screen-10,
                                                                        ir['screen_length']),
                                axis=1)
            min_total_casing_production_screen_diameter = \
            screen_df.iloc[screen_df['total_casing'].argmin(
                skipna=True)]['production_screen_diameters']
            ir['min_total_casing_production_screen_diameter'] = min_total_casing_production_screen_diameter
            ir['screen_diameter'] = max(
            min_total_casing_production_screen_diameter, self.casing_diameters_in_metres[0])
            #stores the screen stage parameter table to wbd
            setattr(self.wbd, 'screen_stage_table', screen_df)
        else: #injection_screen_diameter
            ir['screen_diameter'] = \
            wbd.drilling_diameter_table.loc[wbd.drilling_diameter_table['metres']
                                           == ir['injection_open_hole_diameter']]['recommended_screen'].iloc[0]
        
        wbd._assign_input_params(ir.keys(), **ir)
        # for key, value in ir.items():
        #     print(f"{key}: {value}")
        

    def _pump_pipeline(self):
        # pump_results
        wbd = self.wbd
        pr = {}  # param_name: None for param_name in wbd.pump_param_names}
        pr['pump_inlet_depth'] = cp.calculate_pump_inlet_depth(wbd.groundwater_depth,
                                                               wbd.allowable_drawdown,
                                                               wbd.safety_margin,
                                                               wbd.long_term_decline_rate,
                                                               wbd.bore_lifetime_year)
        pump_diameter = cp.assign_pump_diameter(
            wbd.required_flow_rate_per_litre_sec)
        pr['minimum_pump_housing_diameter'] =\
            cp.calculate_minimum_pump_housing_diameter(wbd.required_flow_rate_per_m3_sec,
                                                       pump_diameter
                                                       )
        wbd._assign_input_params(pr.keys(), **pr)
        # for key, value in pr.items():
        #     print(f"{key}: {value}")

    def _casing_pipeline(self):
        """
        casing_stages = ["pre_collar",
                         "superficial_casing",
                         "pump_chamber_casing",
                         "intermediate_casing",
                         "screen_riser",
                         "screen"]
        """
        wbd = self.wbd
        logger = self.logger
        casing_stage_table = wbd.casing_stage_table.copy().drop(
            ['drill_bit'], axis=1) #drill_bit column will be added in the last part
        is_production_well = wbd.is_production_well
        # print(casing_stage_table)

        screen_diameter = wbd.screen_diameter
        screen_length = wbd.screen_length

        # ------pre-collar section
        pre_collar = [
            *cc.calculate_pre_collar_depths(wbd.depth_to_aquifer_base),
            cc.calculate_pre_collar_casing_diameter()
        ]
        casing_stage_table.loc['pre_collar'] = pre_collar

        # ------superficial casing section
        superficial_casing_required = cc.is_superficial_casing_required(
            wbd.depth_to_aquifer_base)
        logger.info(
            f'superficial_casing_required: {superficial_casing_required}')
        if superficial_casing_required:
            casing_stage_table.loc['superficial_casing'] = \
                [*cc.calculate_superficial_casing_depths(superficial_casing_required,
                                                         wbd.depth_to_aquifer_base),
                 cc.calculate_superficial_casing_diameter(superficial_casing_required)]
        
        # ------pump chamber casing section
        intermediate_casing_diameter = screen_diameter
        separate_pump_chamber_required = cc.is_separate_pump_chamber_required(is_production_well, #this is always false for injection wells
                                                                              intermediate_casing_diameter,
                                                                              wbd.minimum_pump_housing_diameter)
        logger.info(
            f'separate_pump_chamber_required: {separate_pump_chamber_required}')
        if separate_pump_chamber_required:
            pump_chamber = [*cc.calculate_pump_chamber_depths(separate_pump_chamber_required,
                                                              wbd.pump_inlet_depth),
                            cc.calculate_pump_chamber_diameter(wbd.minimum_pump_housing_diameter,
                                                               self.casing_diameters_in_metres)]
            casing_stage_table.loc['pump_chamber_casing'] = pump_chamber
        
        # ------intermediate_casing section
        intermediate_casing = [*cc.calculate_intermediate_casing_depths(wbd.depth_to_top_screen,
                                                                        separate_pump_chamber_required,
                                                                        casing_stage_table.loc['pump_chamber_casing']['bottom']),
                               cc.calculate_intermediate_casing_diameter(screen_diameter,
                                                                         self.casing_diameters_in_metres,
                                                                         wbd.min_total_casing_production_screen_diameter,
                                                                         )]
        casing_stage_table.loc['intermediate_casing'] = intermediate_casing
        # ------screen riser section
        casing_stage_table.loc['screen_riser'] = [*cc.calculate_screen_riser_depths(wbd.depth_to_top_screen),
                                                 cc.calculate_screen_riser_diameter(screen_diameter)]
        # ------screen section
        casing_stage_table.loc['screen'] = [*cc.calculate_screen_depths(wbd.depth_to_top_screen,
                                                                                  screen_length,
                                                                                  wbd.aquifer_thickness),
                                                      screen_diameter]
        
        casing_stage_table['drill_bit'] =\
            casing_stage_table.apply(lambda row: cc.calculate_drill_bit_diameter
                                    (row['casing'],
                                     wbd.casing_diameter_table) if not np.isnan(row['casing']) else row['casing'],
                                    axis=1)

        setattr(wbd, 'casing_stage_table', casing_stage_table)
