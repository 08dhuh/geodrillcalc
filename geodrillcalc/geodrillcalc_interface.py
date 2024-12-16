#!/usr/bin/env python
"""
This module defines a class, GeoDrillCalcInterface, that serves as an interface
for calculating wellbore parameters. It utilises the WellBoreDataStore class for managing
wellbore data and the CalcPipeline class for performing wellbore calculations.

Example Usage:
--------------
.. code-block:: python

    geo_interface = GeoDrillCalcInterface()

    result_wbd = geo_interface.calculate_and_return_wellbore_parameters(
        is_production_well=True,
        aquifer_layer_table=aquifer_layer_table,
        initial_input_params=initial_values
    )

Note:
-----
Ensure that you provide valid depth data and initial input data
when using the 'calculate_and_return_wellbore_parameters' method.
"""
from .data_management.wellbore_data_store import WellBoreDataStore
from .wellborecalc.wellborecalc_pipeline import CalcPipeline

from .wellborecost.wellborecost_pipeline import CostPipeline

from .utils.utils import getlogger
from .utils.validation import check_initial_calculation_feasibility
from .utils.data_preparation import initialise_aquifer_layer_table
from typing import Optional



#TODO: add a check to ensure that essential parameters like aquifer_layer_table and initial_input_params are valid before proceeding
class GeoDrillCalcInterface:
    """
    A class representing the interface for calculating wellbore parameters.

    Attributes
    ----------
    wbd : WellBoreDataStore
        An instance of the WellBoreDataStore class for managing wellbore data.
    calcpl : CalcPipeline
        An instance of the CalcPipeline class for performing wellbore calculations.
    costpl : CostPipeline
        An instance of the CostPipeline class for performing wellbore cost calculations.
    is_production_well : bool
        A boolean indicating whether the pump used is for production or injection.
    logger : Logger
        A logger for handling log messages in the GeoDrillCalcInterface class.

    Methods
    -------
    calculate_and_return_wellbore_parameters(is_production_well, aquifer_layer_table, initial_input_params, cost_rates=None, margin_rates=None)
        Calculates wellbore parameters and returns the WellBoreDataStore instance.
    set_loglevel(loglevel)
        Sets the logging level of the current instance's logger.
    
    Example
    -------
    .. code-block:: python

        geo_interface = GeoDrillCalcInterface()

        result_wbd = geo_interface.calculate_and_return_wellbore_parameters(
            is_production_well=True,
            aquifer_layer_table=aquifer_layer_table,
            initial_input_params=initial_values
        )

    Note
    ----
    Ensure that you provide valid depth data and initial input data
    when using the 'calculate_and_return_wellbore_parameters' method.
    """

    def __init__(self, is_production_well: Optional[bool] = None, log_level='INFO'):
        self.wbd:WellBoreDataStore = None
        self.calcpl:CalcPipeline = None
        self.costpl:CostPipeline = None
        self.is_production_well = is_production_well
        self.logger = getlogger(log_level)


    def calculate_and_return_wellbore_parameters(self,
                                                 is_production_well: bool,
                                                 aquifer_layer_table,
                                                 initial_input_params,
                                                 cost_rates=None,
                                                 margin_rates=None):
        """
        Orchestration method for inputting and calculating the model parameters.

        Parameters
        ----------
        is_production_well : bool
            Indicates whether the pump used is for production or injection.
        aquifer_layer_table : pandas.DataFrame
            A pandas DataFrame containing aquifer layer data.
        initial_input_params : dict
            A dictionary containing initial input parameters.
        cost_rates : dict, optional
            An optional dictionary containing cost rates for wellbore construction.
        margin_rates : dict, optional
            An optional dictionary containing margin rates for wellbore construction.

        Returns
        -------
        WellBoreDataStore
            An instance containing the results.
        """
        try:
            self._initialise_wbd(is_production_well, 
                            aquifer_layer_table,                                                    
                            initial_input_params,
                            )
            # Run the calculation pipeline to process wellbore parameters
            self.calcpl = CalcPipeline(self.wbd)
            self.calcpl.calc_pipeline()

            # Run the cost calculation pipeline (must be done after the CalcPipeline)
            self.costpl = CostPipeline(self.wbd, cost_rates, margin_rates)
            self.costpl.calc_pipeline()
            
            self._log_outcome()
            return self.wbd
        except ValueError as e:
            raise e
        except Exception as e:
            self.logger.exception("Wellbore calculation failed")
            raise e

    
    
    def _initialise_wbd(self, is_production_well, aquifer_layer_table, initial_input_params):
        """
        Initialises and prepares the instance for the pipeline.

        Parameters
        ----------
        is_production_well : bool
            Indicates whether the pump used is for production or injection.
        aquifer_layer_table : pandas.DataFrame
            A pandas DataFrame containing aquifer layer data.
        initial_input_params : dict
            A dictionary containing initial input parameters.
        """
        aquifer_pd = initialise_aquifer_layer_table(aquifer_layer_table)
        check_initial_calculation_feasibility(aquifer_pd)
        if self.is_production_well is None:
            self.is_production_well = is_production_well
        if self.wbd is None:
            self.wbd = WellBoreDataStore(is_production_well)
        self.wbd._initialise_calculation_parameters(aquifer_layer_table=aquifer_layer_table,
                                                    **initial_input_params)


    def _log_outcome(self):
        """
        Logs the outcome of the pipeline.
        """
        if not self.wbd.ready_for_calculation or not self.wbd.ready_for_installation_output:
            return
        for key in self.wbd.installation_output_attribute_names:
            value = getattr(self.wbd, key)
            self.logger.info(f"{key}: {value}")

    def set_loglevel(self, loglevel: int | str):
        """
        Sets the logging level of the current instance's logger.

        Parameters
        ----------
        loglevel : int or str
            The logging level to set.
        """
        self.logger.setLevel(loglevel)

    def export_installation_results_to_dict(self, to_json=False):
        """
        Retrieves the installation specification results from the instance's WellBoreDataStore attribute.

        Parameters
        ----------
        to_json : bool, optional
            If True, returns the results as a JSON string. Defaults to False.

        Returns
        -------
        dict or str
            A dictionary containing the combined results from both stages, or a JSON string if `to_json` is True.
        """
        return self.wbd.export_installation_results_to_dict(to_json=to_json)
    
    def export_cost_results_to_dict(self):
        """
        Retrieves the installation cost results from the instance's WellBoreDataStore attribute.

        Parameters
        ----------
        to_json : bool, optional
            If True, returns the results as a JSON string. Defaults to False.

        Returns
        -------
        dict or str
            A dictionary containing the combined results from both stages, or a JSON string if `to_json` is True.
        """
        return self.wbd.export_cost_results_to_dict()

    #TODO: disable support for json outputs
    def export_results_to_dict(self):
        """
        Retrieves the calculated results from the instance's WellBoreDataStore attribute.

        Parameters
        ----------
        to_json : bool, optional
            If True, returns the results as a JSON string. Defaults to False.

        Returns
        -------
        dict or str
            A dictionary containing the installation specification results, or a JSON string if `to_json` is True.
        """
        combined_results = {}

        try:
            combined_results["installation_results"] = self.wbd.export_installation_results_to_dict()
        except Exception as e:
            self.logger.error(f"Failed to retrieve installation results: {e}")
            combined_results["installation_results"] = None
            raise RuntimeError from e

        try:
            combined_results["cost_results"] = self.wbd.export_cost_results_to_dict()
        except Exception as e:
            self.logger.error(f"Failed to retrieve cost results: {e}")
            combined_results["cost_results"] = None
            raise RuntimeError from e

        
        return combined_results
    


