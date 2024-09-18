import pandas as pd
import json
from ..wellbore_data_store import WellBoreDataStore
from .cost_parameter_extractor import CostParameterExtractor
from .cost_stage_calculator import CostStageCalculator
from ..utils.utils import getlogger
from ..utils.cost_utils import get_data_path

logger = getlogger()
#TODO: upgrade validation logics for margin and cost rates

class CostPipeline:
    """
    A class designed to estimate wellbore installation cost based on the wellbore model parameters calculated in the previous stages.

    This pipeline performs cost calculations in four stages: 
    drilling rates, time rates, materials, and others.
    It uses cost rates and margin rates to estimate costs for each stage.
    
    Attributes
    ----------
    wbd : WellBoreDataStore
        The WellBoreDataStore object containing wellbore parameters.
    cost_stage_calculator : CostStageCalculator or None
        An instance of the CostStageCalculator class for performing cost calculations.
    cost_rates : dict
        Dictionary containing cost rates for each stage.
    margin_rates : dict
        Dictionary containing margin rates for each stage.
    stage_labels : list
        List of stage labels used in the cost calculation ['drilling_rates', 'time_rates', 'materials', 'others'].
    estimate_levels : list
        List of estimate levels used in cost calculation ['low', 'base', 'high'].
    inputs_valid : bool
        Boolean flag indicating if the input rates are valid.
    
    Methods
    -------
    __init__(self, wbd: WellBoreDataStore, cost_rates: dict, margin_rates: dict):
        Initialises the CostPipeline class with wellbore data, cost rates, and margin rates.
    _validate_inputs(self) -> bool:
        Validates the cost and margin rates inputs.
    _validate_cost_rates(self) -> bool:
        Validates the cost rates input.
    _validate_margin_rates(self) -> bool:
        Validates the margin rates input.
    _validate_outputs(self, tables: list) -> bool:
        Validates the output tables to ensure they are non-empty DataFrames.
    wellbore_params(self) -> dict:
        Extracts cost parameters from the WellBoreDataStore object.
    _load_fallback_rates(self, filename: str, target_attribute: str):
        Loads fallback cost rates or margin rates from a JSON file.
    calc_pipeline(self):
        Executes the cost calculation pipeline and saves the results to the WellBoreDataStore instance.
    build_cost_estimation_table(self, cost_stage_calculator: CostStageCalculator) -> pd.DataFrame:
        Builds the cost estimation table for each stage of the cost calculation.
    build_total_cost_table(self, cost_stage_calculator: CostStageCalculator, cost_estimation_table: pd.DataFrame) -> pd.DataFrame:
        Builds the total cost table by aggregating costs from the cost estimation table.
    """

    def __init__(self, wbd: WellBoreDataStore, cost_rates: dict, margin_rates: dict):
        """
        Initialises the CostPipeline class with wellbore data, cost rates, and margin rates.

        Parameters
        ----------
        wbd : WellBoreDataStore
            The WellBoreDataStore object containing wellbore parameters.
        cost_rates : dict
            Dictionary containing cost rates for each stage.
        margin_rates : dict
            Dictionary containing margin rates for each stage.
        """
        self.stage_labels = ['drilling_rates', 'time_rates', 'materials', 'others']
        self.estimate_levels = ['low', 'base', 'high']

        self.wbd = wbd
        self.cost_stage_calculator = None
        self.cost_rates = cost_rates
        self.margin_rates = margin_rates
        
        self.inputs_valid = False 

    #validations
    def _validate_inputs(self):
        """
        Validates the cost and margin rates inputs.

        Returns
        -------
        bool
            True if both cost rates and margin rates are valid, False otherwise.
        """
        return self._validate_cost_rates() and self._validate_margin_rates()

    def _validate_cost_rates(self):
        return self.cost_rates is not None and isinstance(self.cost_rates, dict)

    def _validate_margin_rates(self):
        return self.margin_rates is not None and isinstance(self.margin_rates, dict)
    
    def _validate_outputs(self, tables):
        """
        Validates the output tables to ensure they are non-empty DataFrames.

        Parameters
        ----------
        tables : list
            A list of tables (DataFrames) to validate.

        Returns
        -------
        bool
            True if all tables are valid, False otherwise.
        """
        return all(isinstance(table, pd.DataFrame) and not table.empty for table in tables)


    #properties
    @property
    def wellbore_params(self):
        """
        Extracts cost parameters from the WellBoreDataStore object.

        Returns
        -------
        dict
            A dictionary containing wellbore parameters for each stage.
        """
        if not hasattr(self, '_wellbore_params'):
            cpe = CostParameterExtractor(self.wbd)
            self._wellbore_params = {
                label: getattr(cpe, f"{label}_params") for label in self.stage_labels
            }
        return self._wellbore_params

    def _load_fallback_rates(self, filename: str, target_attribute: str):
        """
        Loads fallback cost rates or margin rates from a JSON file.

        Parameters
        ----------
        filename : str
            Name of the JSON file containing fallback rates.
        target_attribute : str
            Name of the attribute to update (e.g., 'cost_rates', 'margin_rates').

        Notes
        -----
        If the fallback file is not found, a warning is logged.
        """
        try:
            with open(filename, 'r') as f:
                fallback_rates = json.load(f)
            setattr(self, target_attribute, fallback_rates)
            logger.info(f"Using fallback {target_attribute} from {filename}")
        except FileNotFoundError:
            logger.warning(f"Fallback file '{filename}' not found.")


    def calc_pipeline(self):
        """
        Executes the cost calculation pipeline and saves the results to the WellBoreDataStore instance.

        This method performs validations, loads fallback rates if necessary, calculates costs for each stage, 
        and updates the WellBoreDataStore instance with the cost outputs.
        
        Notes
        -----
        If the inputs are invalid or the fallback rates fail to load, the cost calculation pipeline does not run.
        """
        self.inputs_valid = self._validate_inputs()
        if not self.inputs_valid:
            logger.warning("Invalid cost rates or margin rates. Cost calculation pipeline cannot run with invalid inputs.")

            if not self._validate_cost_rates():
                self._load_fallback_rates(get_data_path('fallback_cost_rates.json'), 'cost_rates')

            if not self._validate_margin_rates():
                self._load_fallback_rates(get_data_path(
                    'fallback_margin_rates.json'), 'margin_rates')

            self.inputs_valid = self._validate_inputs() #try again

            if not self.inputs_valid:
                logger.warning("Fallback failed. Cost calculation pipeline cannot run with invalid inputs.")


        #load the calculator with initial parameters
        self.cost_stage_calculator = CostStageCalculator(
            cost_rates=self.cost_rates,
            wellbore_params=self.wellbore_params,
            margin_rates=self.margin_rates,
            stage_labels=self.stage_labels
        )

        outputs = {}
        outputs["cost_estimation_table"] = self.build_cost_estimation_table(self.cost_stage_calculator)
        outputs["total_cost_table"] = self.build_total_cost_table(
            self.cost_stage_calculator,
            outputs["cost_estimation_table"])


        self.wbd.ready_for_cost_output = self._validate_outputs(outputs.values())
        
        if self.wbd.ready_for_cost_output:
            self.wbd.assign_parameters(stage='cost',
                                       **outputs
                                   )
        else:
            logger.error("Cost calculation failed.")


    def build_cost_estimation_table(self, 
                                    cost_stage_calculator:CostStageCalculator) -> pd.DataFrame:
        """
        Builds the cost estimation table for each stage of the cost calculation.

        Parameters
        ----------
        cost_stage_calculator : CostStageCalculator
            The CostStageCalculator object used to perform stage-specific cost calculations.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the cost estimation for each component of each stage.

        Raises
        ------
        KeyError
            If there is an error accessing the cost parameters or calculation results.
        ValueError
            If there is an error in the data or calculations.
        """
        try:
            cost_estimation_table = pd.DataFrame(
                columns=self.estimate_levels,
                index=pd.MultiIndex.from_product(
                    [self.stage_labels, []], names=['stage', 'components'])
            )
            for stage_name, stage_method in cost_stage_calculator.stage_calculators.items():
                stage_result = stage_method() 
                for component, component_costs in stage_result.iterrows():
                    cost_estimation_table.loc[(
                        stage_name, component), self.estimate_levels] = component_costs

            return cost_estimation_table
        except (KeyError, ValueError) as e:
            logger.error(f"Error in building cost estimation table: {e}")
            cost_estimation_table = None
            raise

            
    def build_total_cost_table(self, 
                               cost_stage_calculator:CostStageCalculator,
                               cost_estimation_table:pd.DataFrame) -> pd.DataFrame:
        """
        Builds the total cost table by aggregating costs from the cost estimation table.

        Parameters
        ----------
        cost_stage_calculator : CostStageCalculator
            The CostStageCalculator object used to perform stage-specific cost calculations.
        cost_estimation_table : pd.DataFrame
            The DataFrame containing the cost estimations for each stage.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the total costs for each stage and the grand total.

        Raises
        ------
        Exception
            If there is an error in aggregating the cost data.
        """
        try:
            total_cost_table = cost_estimation_table.groupby(level=[0]).sum()
            total_cost_table.loc['drilling_rates'] = \
                cost_stage_calculator.calculate_drilling_rates_total_cost(total_cost_table.at['drilling_rates', 'base'])
            grand_total = total_cost_table.sum(axis=0)
            total_cost_table.loc['total_cost'] = grand_total
            print('\n Total cost:')
            print(total_cost_table)
            return total_cost_table

        except Exception as e:
            logger.error(f"Error in building total cost table: {e}")
            raise



