#!/usr/bin/env python
"""
This module defines a class, GeoDrillCalcInterface, that serves as an interface
for calculating wellbore parameters. It utilises the WellBoreDict class for managing
wellbore data and the CalcPipeline class for performing wellbore calculations.

Example Usage:
    geo_interface = GeoDrillCalcInterface()

    result_wbd = geo_interface.calculate_and_return_wellbore_parameters(
        is_production_pump=True,
        depth_data=depth_data,
        initial_input_data=initial_values
    )

Note: Ensure that you provide valid depth data and initial input data
when using the 'calculate_and_return_wellbore_parameters' method.
"""
from .wellbore_dict import WellBoreDict
from .calc_pipeline import CalcPipeline
from .utils.utils import getlogger

class GeoDrillCalcInterface:
    """
    A class representing the interface for calculating wellbore parameters.

    Attributes:
    - wbd: An instance of the WellBoreDict class for managing wellbore data.
    - cpl: An instance of the CalcPipeline class for performing wellbore calculations.
    - is_production_pump: A boolean indicating whether the pump used is for production or injection.
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
        is_production_pump=True,
        depth_data=depth_data,
        initial_input_data=initial_values
    )

    Note: Ensure that you provide valid depth data and initial input data
    when using the 'calculate_and_return_wellbore_parameters' method.
    """

    def __init__(self, is_production_pump: bool = None):
        self.wbd = None
        self.cpl = None
        self.is_production_pump = is_production_pump or None
        self.logger = getlogger()

    def calculate_and_return_wellbore_parameters(self,
                                                 is_production_pump: bool,
                                                 depth_data,
                                                 initial_input_data):
        """
        Orchestration method for inputting and calculating 
        the model parameters

        Parameters:
            is_production_pump: bool
            depth_data: pd.DataFrame
            initial_input_data: dict

        Returns:
            WellBoreDict instance containing the results

        Note:
            Make sure the inputs follow the format below:
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
        """
        self._initialise(depth_data, initial_input_data)
        self.cpl = CalcPipeline(self.wbd)
        self.cpl.calc_pipeline(is_production_pump)
        self._log_outcome()
        return self.wbd

    def _initialise(self, depth_data, initial_input_data):
        """
        Initialises and prepares the instance for the pipeline
        """
        if self.wbd is None:
            self.wbd = WellBoreDict()
        self.wbd.initialise_and_validate_input_data(depth_data=depth_data,
                                                    **initial_input_data)

    def _log_outcome(self):
        """
        Logs the outcome of the pipeline at INFO level
        """
        if not self.wbd.is_initialised or not self.wbd.calculation_completed:
            return
        for key in self.wbd.outcome_params:
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
    


