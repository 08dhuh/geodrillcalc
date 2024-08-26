#!/usr/bin/env python
import numpy as np
import pandas as pd

from geodrillcalc.utils.calc_utils import find_next_largest_value, query_diameter_table
from ..wellbore_data_store import WellBoreDataStore
from . import casing_calculation as cc, pump_calculation as cp, screen_calculation as ci
from ..utils.utils import getlogger 



class CalcPipeline:
    """
    A class designed to calculate wellbore model parameters using a WellBoreDataStore instance.

    This class requires a fully instantiated and initialised WellBoreDataStore instance, 
    achieved through the WellBoreDataStore.initialise method.
    The WellBoreDataStore instance attributes are updated in three consecutive calls to the class methods.

    The CalcPipeline class is intended to be used in conjunction with the WellBoreDataStore instance, 
    collaborating to calculate wellbore parameters.
    All calculations operate on WellBoreDataStore's internal class attributes, initialised in advance. 
    Results are stored within the same WellBoreDataStore instance.

    For the casing stage, an additional argument is required, 
    distinguishing between production and injection pumps 

    Method Overview
    ---------------
    1. _screen_pipeline: Calculates interval parameters.
    2. _pump_pipeline: Calculates pump parameters.
    3. _casing_pipeline: Calculates casing parameters. Requires a boolean argument (True for production pump, False for injection pump).
    4. calc_pipeline: Encapsulates the pipeline methods in a single method.

    Parameters
    ----------
    aquifer_layer_table : dict
        A dictionary containing details about aquifer layers.
    
    initial_values : dict
        A dictionary containing initial values for wellbore calculations.

    Example
    -------
    .. code-block:: python

        wbd = WellBoreDataStore()
        wbd.initialise_and_validate_input_params(aquifer_layer_table=aquifer_layer_table, **initial_values)
        calc_injectionpipe = CalcPipeline(wbd)
        calc_injectionpipe.calc_pipeline(is_production_well=True)
    """

    def __init__(self, wellboredict: WellBoreDataStore, logger=None):
        """
        Initialises the CalcPipeline class with a WellBoreDataStore instance.

        Parameters
        ----------
        wellboredict : WellBoreDataStore
            An initialised instance of the WellBoreDataStore class, ready for calculations.
        logger : Logger, optional
            A logger instance to handle logging within the pipeline. Defaults to None.
        
        Raises
        ------
        RuntimeError
            If the WellBoreDataStore instance is not ready for calculation.
        """
        self.wbd = wellboredict  # wellboredict must be a fully initialised instance
        if not self.wbd.ready_for_calculation:
            raise RuntimeError(f"Input parameters must be assigned to WellBoreDataStore object before calling the current class {self.__name__}")
        self.casing_diameters_in_metres = self.wbd.get_casing_diameters()
        self.drilling_diameters_in_metres = self.wbd.get_drilling_diameters()
        self.logger = logger or getlogger()

    def calc_pipeline(self):
        """
        Executes the complete calculation pipeline for wellbore data.

        This method sequentially calls the _screen_pipeline, _pump_pipeline, and _casing_pipeline
        methods to perform all necessary calculations on the WellBoreDataStore instance.

        Raises
        ------
        ValueError
            If an error occurs during any calculation stage.
        ZeroDivisionError
            If a zero division error occurs during interval calculations.
        """
        logger = self.logger
        try:
            self.wbd.ready_for_installation_output = False         
            self._screen_pipeline()
            self._pump_pipeline()
            self._casing_pipeline()
            self.wbd.ready_for_installation_output = True
        except ValueError as e:
            logger.error(f"An error occurred during calculation: {str(e)}")
            raise ValueError from e
        except ZeroDivisionError as e:
            logger.error(f"Zero division error occurred in interval calculations: {str(e)}")
            raise ValueError from e
        
    def _screen_pipeline(self):
        """
        Calculates and the following screen parameters in the WellBoreDataStore instance.

        Attributes
        ----------
        screen_length : float
            The calculated screen length for the wellbore.
        screen_length_error : float
            The error margin in the calculated screen length.
        screen_diameter : float
            The diameter of the screen used in the wellbore.
        open_hole_diameter : float
            The diameter of the open hole in the wellbore.
        min_total_casing_production_screen_diameter : float, optional
            The minimum total casing production screen diameter, calculated for production wells.
        screen_stage_table : pd.DataFrame, optional
            A DataFrame containing the screen stage details, calculated for production wells.

        Notes
        -----
        For production wells, additional parameters such as `min_total_casing_production_screen_diameter`
        and `screen_stage_table` are also calculated.
        """

        wbd = self.wbd  # fully initialised wellboredict instance
        ir = {}
        drilling_diameter_list = wbd.get_drilling_diameters()

        ir['screen_length'], ir['screen_length_error'] = \
            ci.calculate_minimum_screen_length(wbd.required_flow_rate,
                                               wbd.hydraulic_conductivity,
                                               wbd.bore_lifetime_per_day,
                                               wbd.aquifer_thickness,
                                               wbd.is_production_well)
        
        if wbd.is_production_well: #production pipeline
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
            setattr(self.wbd, 'screen_stage_table', screen_df) #stores the screen stage table to wbd
            
            screen_diameter = max(min_total_casing_production_screen_diameter, self.casing_diameters_in_metres[0])
            ohd_min = ci.calculate_minimum_open_hole_diameter(wbd.required_flow_rate_per_m3_sec,
                                                                     ir['screen_length'],
                                                                     wbd.sand_face_velocity_production,
                                                                     wbd.aquifer_average_porosity,
                                                                     wbd.net_to_gross_ratio_aquifer)        
            ohd = ci.calculate_open_hole_diameter(ohd_min, drilling_diameter_list)
            ohd = ci.calibrate_open_hole_diameter(ohd, screen_diameter, wbd.casing_diameter_table)
        else: #injection pipeline
            #for the injection wells, the screen diameter depends on the open hole diameter
            ohd_min = ci.calculate_minimum_open_hole_diameter(wbd.required_flow_rate_per_m3_sec,
                                                                     ir['screen_length'],
                                                                     wbd.sand_face_velocity_injection,
                                                                     wbd.aquifer_average_porosity,
                                                                     wbd.net_to_gross_ratio_aquifer)            
            ohd = ci.calculate_open_hole_diameter(ohd_min, drilling_diameter_list)
            screen_diameter = query_diameter_table(ohd, wbd.drilling_diameter_table)
            #screen_diameter of the injection well guaranteed to be greater than its open hole diameter
        
        ir['screen_diameter'] = screen_diameter
        ir['open_hole_diameter'] = ohd
        wbd.assign_parameters('installation', **ir)

        

    def _pump_pipeline(self):
        """
        Calculates and updates pump parameters in the WellBoreDataStore instance.

        Attributes
        ----------
        pump_inlet_depth : float
            The depth at which the pump inlet is positioned within the wellbore.
        minimum_pump_housing_diameter : float
            The minimum diameter required for the pump housing.

        Notes
        -----
        This method updates the WellBoreDataStore instance with the calculated pump parameters.
        """

        wbd = self.wbd
        pr = {}  
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
        wbd.assign_parameters('installation', **pr)


    def _casing_pipeline(self):
        """
        Calculates and updates casing parameters in the WellBoreDataStore instance.

        Attributes
        ----------
        casing_stage_table : pd.DataFrame
            A DataFrame that holds the calculated casing parameters for different wellbore stages.

        Casing Sections
        -----------------
        pre_collar :
            Contains parameters for the pre-collar section, which stabilises the top portion of the wellbore.
        superficial_casing :
            Contains parameters for the superficial casing section, providing surface protection.
        pump_chamber_casing : dict
            Contains parameters for the pump chamber casing section, where the pump will be installed.
        intermediate_casing : dict
            Contains parameters for the intermediate casing section, stabilising the wellbore between surface and target depths.
        screen_riser : dict
            Contains parameters for the screen riser section, connecting the pump chamber to the screen.
        screen : dict
            Contains parameters for the screen section, where the wellbore interacts with the aquifer.

        Notes
        -----
        This method computes and updates various casing parameters necessary for wellbore construction
        based on the WellBoreDataStore instance.
        """
        wbd = self.wbd
        logger = self.logger
        casing_stage_table = wbd.casing_stage_table.copy().drop(
            ['drill_bit'], axis=1) #drill_bit column will be added in the last part
        is_production_well = wbd.is_production_well

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
                                                                         wbd.min_total_casing_production_screen_diameter if is_production_well else 0,
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
