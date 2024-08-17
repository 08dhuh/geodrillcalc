#!/usr/bin/env python
"""
This module defines a class, GeoDrillCalcInterface, that serves as an interface
for calculating wellbore parameters. It utilises the WellBoreDict class for managing
wellbore data and the CalcPipeline class for performing wellbore calculations.

Example Usage:
    geo_interface = GeoDrillCalcInterface()

    result_wbd = geo_interface.calculate_and_return_wellbore_parameters(
        is_production_well=True,
        aquifer_layer_table=aquifer_layer_table,
        initial_input_params=initial_values
    )

Note: Ensure that you provide valid depth data and initial input data
when using the 'calculate_and_return_wellbore_parameters' method.
"""
from .wellbore_dict import WellBoreDict
from .wellborecalc.wellborecalc_pipeline import CalcPipeline
from .utils.utils import getlogger
from typing import Optional

class GeoDrillCalcInterface:
    """
    A class representing the interface for calculating wellbore parameters.

    Attributes:
    - wbd: An instance of the WellBoreDict class for managing wellbore data.
    - cpl: An instance of the CalcPipeline class for performing wellbore calculations.
    - is_production_well: A boolean indicating whether the pump used is for production or injection.
    - logger: A logger for handling log messages in the GeoDrillCalcInterface class.

    Methods:
    - calculate_and_return_wellbore_parameters:
      Calculates wellbore parameters using WellBoreDict and CalcPipeline 
      and returns the WellBoreDict instance.

    - set_loglevel:
      Sets the logging level of the current instance's logger.

    Example Usage:

    geo_interface = GeoDrillCalcInterface()

    result_wbd = geo_interface.calculate_and_return_wellbore_parameters(
        is_production_well=True,
        aquifer_layer_table=aquifer_layer_table,
        initial_input_params=initial_values
    )

    Note: Ensure that you provide valid depth data and initial input data
    when using the 'calculate_and_return_wellbore_parameters' method.
    """

    def __init__(self, is_production_well: Optional[bool] = None, log_level='INFO'):
        self.wbd:WellBoreDict = None
        self.cpl:CalcPipeline = None
        self.is_production_well = is_production_well
        self.logger = getlogger(log_level)

    def calculate_and_return_wellbore_parameters(self,
                                                 is_production_well: bool,
                                                 aquifer_layer_table,
                                                 initial_input_params):
        """
        Orchestration method for inputting and calculating 
        the model parameters

        Parameters:
            is_production_well: bool
            aquifer_layer_table: pd.DataFrame
            initial_input_params: dict

        Returns:
            WellBoreDict instance containing the results

        Note:
            Make sure the inputs follow the format below:
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
        """
        self._initialise(is_production_well, aquifer_layer_table, 
                                                   initial_input_params)
        self.cpl = CalcPipeline(self.wbd)
        self.cpl.calc_pipeline()
        self._log_outcome()
        return self.wbd

    def _initialise(self, is_production_well, aquifer_layer_table, initial_input_params):
        """
        Initialises and prepares the instance for the pipeline
        """
        if self.is_production_well is None:
            self.is_production_well = is_production_well
        if self.wbd is None:
            self.wbd = WellBoreDict(is_production_well)
        self.wbd.initialise_calculation_parameters(aquifer_layer_table=aquifer_layer_table,
                                                    **initial_input_params)

    def _log_outcome(self):
        """
        Logs the outcome of the pipeline at INFO level
        """
        if not self.wbd.ready_for_calculation or not self.wbd.calculation_completed:
            return
        for key in self.wbd.output_attribute_names:
            value = getattr(self.wbd, key)
            self.logger.info(f"{key}: {value}")

    def set_loglevel(self, loglevel: int | str):
        """
        Sets the logging level of current instance's logger.
        """
        self.logger.setLevel(loglevel)

    def export_results_to_json_file(self, path:str):
        """
        Writes the output as json file to the given path

        Parameters
            path : str
        """
        json_result = self.wbd.export_results_to_json_string()
        with open(path, 'w') as f:
            f.write(json_result)
    
    def export_results_to_dict(self):
        """
        Retrieves the results from the instance's WellBoreDict attribute
        """
        return self.wbd.export_results_to_dict()
    


