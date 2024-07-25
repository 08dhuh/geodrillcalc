#!/usr/bin/env python
import numpy as np
import pandas as pd
from .wellbore_dict import WellBoreDict
from .wellborecalc import calc_casing as cc, calc_interval as ci, calc_pump as cp
from .utils.utils import getlogger, find_next_largest_value


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
    1. _interval_pipeline: Calculates interval parameters.
    2. _pump_pipeline: Calculates pump parameters.
    3. _casing_pipeline: Calculates casing parameters. 
        Requires a boolean argument (True for production pump, False for injection pump).
    4. calc_pipeline: Encapsulates the pipeline methods in a single method

    Usage Example:
    wbd = WellBoreDict()
    wbd.initialise_and_validate_input_data(depth_data=depth_data, **initial_values)  
    # Refer to WellBoreDict.__doc__ for the required keyword arguments.

    calc_injectionpipe = CalcPipeline(wbd)
    calc_injectionpipe.calc_pipeline(is_production_pump=True)
    """

    def __init__(self, wellboredict: WellBoreDict, logger=None):
        self.wbd = wellboredict  # wellboredict must be a fully initialised instance
        self.casing_diameters_in_metres = self.wbd.get_casing_diameters()
        self.drilling_diameters_in_metres = self.wbd.get_drilling_diameters()
        self.logger = logger or getlogger()

    def calc_pipeline(self, is_production_pump):
        logger = self.logger
        try:
            setattr(self.wbd,'calculation_completed',False)            
            self._interval_pipeline()
            self._pump_pipeline()
            self._casing_pipeline(is_production_pump)
            setattr(self.wbd,'calculation_completed',True)
            #self.wbd.calculation_completed = True
        except ValueError as e:
            logger.error(f"An error occurred during calculation: {str(e)}")
            raise ValueError from e
        except ZeroDivisionError as e:
            logger.error(f"Zero division error occurred in interval calculations: {str(e)}")
            raise ValueError from e
        
    def _interval_pipeline(self):
        """
        Determines and updates WellboreDict instance Interval parameters

        """
        wbd = self.wbd  # fully initialised wellboredict instance
        interval_df = pd.DataFrame(self.casing_diameters_in_metres,
                                   columns=['prod_casing_diameters'])
        ir = {}

        ir['production_screen_length'], ir['production_screen_length_error'] = \
            ci.calculate_minimum_screen_length(wbd.required_flow_rate,
                                               wbd.hydraulic_conductivity,
                                               wbd.bore_lifetime_per_day,
                                               wbd.aquifer_thickness,
                                               False)
        ir['injection_screen_length'], ir['injection_screen_length_error'] = \
            ci.calculate_minimum_screen_length(wbd.required_flow_rate,
                                               wbd.hydraulic_conductivity,
                                               wbd.bore_lifetime_per_day,
                                               wbd.aquifer_thickness,
                                               True)
        interval_df['casing_frictions'] = \
            ci.calculate_casing_friction(wbd.depth_to_top_screen,
                                         wbd.required_flow_rate_per_m3_sec,
                                         self.casing_diameters_in_metres,
                                         wbd.pipe_roughness_coeff)
        interval_df['production_minimum_screen_diameters'] = \
            ci.calculate_minimum_screen_diameter(interval_df['casing_frictions'].to_numpy(),
                                                 screen_length=ir['production_screen_length'],
                                                 req_flow_rate=wbd.required_flow_rate_per_m3_sec,
                                                 pipe_roughness_coeff=wbd.pipe_roughness_coeff
                                                 )

        interval_df['production_screen_diameters'] = \
            interval_df.apply(lambda row: find_next_largest_value
                              (row['production_minimum_screen_diameters'],
                               self.casing_diameters_in_metres)
                              if not np.isnan(row['production_minimum_screen_diameters'])
                              else np.nan,
                              axis=1)
        interval_df['total_casing'] =\
            interval_df.apply(lambda row: ci.calculate_total_casing(row['prod_casing_diameters'],
                                                                    row['production_screen_diameters'],
                                                                    wbd.depth_to_top_screen-10,
                                                                    ir['production_screen_length']),
                              axis=1)
        ohd_min_production = ci.calculate_minimum_open_hole_diameter(wbd.required_flow_rate_per_m3_sec,
                                                                     ir['production_screen_length'],
                                                                     wbd.sand_face_velocity_production,
                                                                     wbd.aquifer_average_porosity,
                                                                     wbd.net_to_gross_ratio_aquifer)
        ohd_min_injection = ci.calculate_minimum_open_hole_diameter(wbd.required_flow_rate_per_m3_sec,
                                                                    ir['injection_screen_length'],
                                                                    wbd.sand_face_velocity_injection,
                                                                    wbd.aquifer_average_porosity,
                                                                    wbd.net_to_gross_ratio_aquifer)

        ir['production_open_hole_diameter'] = find_next_largest_value(
            ohd_min_production, self.drilling_diameters_in_metres)
        ir['injection_open_hole_diameter'] = find_next_largest_value(
            ohd_min_injection, self.drilling_diameters_in_metres)
        min_total_casing_production_screen_diameter = \
            interval_df.iloc[interval_df['total_casing'].argmin(
                skipna=True)]['production_screen_diameters']
        ir['min_total_casing_production_screen_diameter'] = min_total_casing_production_screen_diameter
        ir['production_screen_diameter'] = max(
            min_total_casing_production_screen_diameter, self.casing_diameters_in_metres[0])
        ir['injection_screen_diameter'] = \
            wbd.drilling_diameter_data.loc[wbd.drilling_diameter_data['metres']
                                           == ir['injection_open_hole_diameter']]['recommended_screen'].iloc[0]
        wbd.set_params(ir.keys(), **ir)
        # for key, value in ir.items():
        #     print(f"{key}: {value}")
        setattr(self.wbd, 'interval_stage_data', interval_df)

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
        wbd.set_params(pr.keys(), **pr)
        # for key, value in pr.items():
        #     print(f"{key}: {value}")

    def _casing_pipeline(self, is_production_pump):
        """
        casing_stages = ["pre_collar",
                         "superficial_casing",
                         "pump_chamber_casing",
                         "intermediate_casing",
                         "screen_riser",
                         "production_screen"]
        """
        wbd = self.wbd
        logger = self.logger
        casing_stage_data = wbd.casing_stage_data.copy().drop(
            ['drill_bit'], axis=1)
        # print(casing_stage_data)
        screen_diameter = wbd.production_screen_diameter if is_production_pump \
            else wbd.injection_screen_diameter
        screen_length = wbd.production_screen_length if is_production_pump \
            else wbd.injection_screen_length
        # ------pre-collar
        pre_collar = [
            *cc.calculate_pre_collar_depths(wbd.depth_to_aquifer_base),
            cc.calculate_pre_collar_casing_diameter()
        ]
        # print(pre_collar)
        casing_stage_data.loc['pre_collar'] = pre_collar
        # ------superficial_casing
        superficial_casing_required = cc.is_superficial_casing_required(
            wbd.depth_to_aquifer_base)
        logger.info(
            f'superficial_casing_required: {superficial_casing_required}')
        if superficial_casing_required:
            casing_stage_data.loc['superficial_casing'] = \
                [*cc.calculate_superficial_casing_depths(superficial_casing_required,
                                                         wbd.depth_to_aquifer_base),
                 cc.calculate_superficial_casing_diameter(superficial_casing_required)]
        # ------intermediate_casing
        intermediate_casing_diameter = screen_diameter
        separate_pump_chamber_required = cc.is_separate_pump_chamber_required(True,
                                                                              intermediate_casing_diameter,
                                                                              wbd.minimum_pump_housing_diameter)
        logger.info(
            f'separate_pump_chamber_required: {separate_pump_chamber_required}')
        if separate_pump_chamber_required:
            pump_chamber = [*cc.calculate_pump_chamber_depths(separate_pump_chamber_required,
                                                              wbd.pump_inlet_depth),
                            cc.calculate_pump_chamber_diameter(wbd.minimum_pump_housing_diameter,
                                                               self.casing_diameters_in_metres)]
            casing_stage_data.loc['pump_chamber_casing'] = pump_chamber
        intermediate_casing = [*cc.calculate_intermediate_casing_depths(wbd.depth_to_top_screen,
                                                                        separate_pump_chamber_required,
                                                                        casing_stage_data.loc['pump_chamber_casing']['bottom']),
                               cc.calculate_intermediate_casing_diameter(screen_diameter,
                                                                         wbd.min_total_casing_production_screen_diameter,
                                                                         self.casing_diameters_in_metres
                                                                         )]
        casing_stage_data.loc['intermediate_casing'] = intermediate_casing
        casing_stage_data.loc['screen_riser'] = [*cc.calculate_screen_riser_depths(wbd.depth_to_top_screen),
                                                 cc.calculate_screen_riser_diameter(screen_diameter)]
        casing_stage_data.loc['production_screen'] = [*cc.calculate_screen_depths(wbd.depth_to_top_screen,
                                                                                  screen_length,
                                                                                  wbd.aquifer_thickness),
                                                      screen_diameter]
        casing_stage_data['drill_bit'] =\
            casing_stage_data.apply(lambda row: cc.calculate_drill_bit_diameter
                                    (row['casing'],
                                     wbd.casing_diameter_data) if not np.isnan(row['casing']) else row['casing'],
                                    axis=1)
        # print(casing_stage_data)
        setattr(wbd, 'casing_stage_data', casing_stage_data)
