#!/usr/bin/env python
import numpy as np
import pandas as pd
import json
from .utils.utils import getlogger, validate


class WellBoreDict:
    """
    WellBoreDict is a class designed to store and manage input/output parameters
    pertaining to wellbore construction and operation.
    It provides methods for initialising parameters, storing and exporting results.

    Attributes:
    -----------
    table_attribute_names : list
        Names of data parameters required for the wellbore calculations.

    initial_param_names : list
        Names of initial parameters required for wellbore initialization.

    outcome_params : list
        Names of outcome parameters resulting from wellbore calculations.

    Various attributes for input data, calculated parameters, constants, and results.

    Methods:
    --------
    __init__(self, logger=None):
        Initializes the WellBoreDict instance with default values.

    _initialise_diameter_table(self, casing_diameter_table=None, drilling_diameter_table=None):
        Initializes diameter data for casing and drilling.

    _initialise_aquifer_layer_table(self, aquifer_layer_table):
        Initializes depth data from a given dictionary or DataFrame.

    assign_input_params(self, arg_names: list, **kwargs):
        Assigns input parameters from keyword arguments.

    _get_diameter_table(self, dataset, metric='metres', as_numpy=True):
        Retrieves diameter data in the specified metric.

    get_casing_diameters(self, metric='metres', as_numpy=True):
        Returns casing diameters as a numpy array or pandas Series.

    get_drilling_diameters(self, metric='metres', as_numpy=True):
        Returns drilling diameters as a numpy array or pandas Series.

    _initialise_casing_stage_table(self):
        Initializes the casing stage data DataFrame.

    initialise_and_validate_input_params(self, **kwargs):
        Initializes and validates the input data for wellbore calculations.

    _validate_table(self):
        Validates the essential data parameters.

    _validate_all_inputs(self):
        Performs validation checks for the initial input data.

    export_results_to_dict(self, to_json=False):
        Exports the results of the wellbore calculations to a dictionary.

    export_results_to_json_string(self):
        Exports the results of the wellbore calculations to a JSON string.
    """

    _INPUT_ATTRIBUTES = {
        # Input tables
        "casing_diameter_table": pd.DataFrame,
        "drilling_diameter_table": pd.DataFrame,
        "aquifer_layer_table": pd.DataFrame,
        # Input parameters
        "required_flow_rate": float,
        "hydraulic_conductivity": float,
        "average_porosity": float,
        "bore_lifetime_year": float,
        "groundwater_depth": float,
        "long_term_decline_rate": float,
        "allowable_drawdown": float,
        "safety_margin": float,
        "is_production_well": bool,
        "top_aquifer_layer": str,
        "target_aquifer_layer": str,
        # Derived parameters
        "depth_to_top_screen": float,
        "required_flow_rate_per_litre_sec": float,
        "required_flow_rate_per_m3_sec": float,
        "bore_lifetime_per_day": float,
        "aquifer_thickness": float,
        "depth_to_aquifer_base": float,
        # Constants
        "sand_face_velocity_production": float,
        "sand_face_velocity_injection": float,
        "net_to_gross_ratio_aquifer": float,
        "aquifer_average_porosity": float,
        "pipe_roughness_coeff": float,
    }

    _OUTPUT_ATTRIBUTES = {
        # Output parameters for production and injection holes
        "production_screen_length": float,
        "injection_screen_length": float,
        "production_screen_length_error": float,
        "injection_screen_length_error": float,
        "production_screen_diameter": float,
        "injection_screen_diameter": float,
        "production_open_hole_diameter": float,
        "injection_open_hole_diameter": float,
        "pump_inlet_depth": float,
        "minimum_pump_housing_diameter": float,
        "min_total_casing_production_screen_diameter": float,

        # Output dataframes
        "screen_stage_table": pd.DataFrame,
        "casing_stage_table": pd.DataFrame
    }

    table_attribute_names = [key for key, val in _INPUT_ATTRIBUTES.items() if val == pd.DataFrame] +\
        [key for key, val in _OUTPUT_ATTRIBUTES.items() if val == pd.DataFrame]
    # [
    #     # ----------------input
    #     "casing_diameter_table",
    #     "drilling_diameter_table",
    #     "aquifer_layer_table",
    #     # ----------------tbd by pipeline
    #     "screen_stage_table",
    #     "casing_stage_table"
    # ]

    initial_param_names = [
        key for key, val in _INPUT_ATTRIBUTES.items() if val != pd.DataFrame]
    # [
    #     # input variables
    #     "required_flow_rate",
    #     "hydraulic_conductivity",
    #     "average_porosity",
    #     "bore_lifetime_year",
    #     "groundwater_depth",
    #     "long_term_decline_rate",
    #     "allowable_drawdown",
    #     "safety_margin",
    #     # added inputs
    #     "top_aquifer_layer",
    #     "target_aquifer_layer",
    #     # Below are derived from the input parameters
    #     "depth_to_top_screen",
    #     "required_flow_rate_per_litre_sec",
    #     "required_flow_rate_per_m3_sec",
    #     "bore_lifetime_per_day",
    #     "aquifer_thickness",
    #     "depth_to_aquifer_base",
    #     # And below are params with preassigned default values
    #     "sand_face_velocity_production",
    #     "sand_face_velocity_injection",
    #     "net_to_gross_ratio_aquifer",
    #     "aquifer_average_porosity",
    #     "pipe_roughness_coeff",
    # ]

    output_param_names = [*_OUTPUT_ATTRIBUTES.keys()]
    # [
    #     "production_screen_length",
    #     "injection_screen_length",
    #     "production_screen_length_error",
    #     "injection_screen_length_error",
    #     "min_total_casing_production_screen_diameter",
    #     "production_screen_diameter",
    #     "injection_screen_diameter",
    #     "production_open_hole_diameter",
    #     "injection_open_hole_diameter",
    #     "pump_inlet_depth",
    #     "minimum_pump_housing_diameter",
    #     "screen_stage_table",
    #     "casing_stage_table"
    # ]

    def __init__(self, logger=None):
        # ----------------------------------------------------------------
        self.casing_diameter_table = pd.DataFrame(
            columns=['inches', 'metres', 'recommended_bit'])
        self.drilling_diameter_table = pd.DataFrame(
            columns=['inches', 'metres', 'recommended_screen'])
        self.aquifer_layer_table = pd.DataFrame(
            columns=["aquifer_layer", "is_aquifer", "depth_to_base"])
        # ----------------------------------------------------------------
        # input parameters
        self.required_flow_rate = None
        self.hydraulic_conductivity = None
        self.average_porosity = None
        self.bore_lifetime_year = None
        self.groundwater_depth = None
        self.long_term_decline_rate = None
        self.allowable_drawdown = None
        self.safety_margin = None
        # ----------------------------------------------------------------
        # inferred from input parameters
        self.required_flow_rate_per_litre_sec = None
        self.required_flow_rate_per_m3_sec = None
        self.bore_lifetime_per_day = None
        self.depth_to_top_screen = None
        self.aquifer_thickness = None
        self.depth_to_aquifer_base = None
        # ----------------------------------------------------------------
        # constants
        self.sand_face_velocity_production = .01
        self.sand_face_velocity_injection = .003
        self.net_to_gross_ratio_aquifer = 1
        self.aquifer_average_porosity = .25
        self.pipe_roughness_coeff = 100
        # ----------------------------------------------------------------
        # result stage
        self.production_screen_length = None
        self.injection_screen_length = None
        self.production_screen_length_error = None
        self.injection_screen_length_error = None
        self.production_screen_diameter = None
        self.injection_screen_diameter = None
        self.production_open_hole_diameter = None
        self.injection_open_hole_diameter = None
        self.pump_inlet_depth = None
        self.minimum_pump_housing_diameter = None
        self.min_total_casing_production_screen_diameter = None
        # ----------------------------------------------------------------
        # result dataframe
        self.screen_stage_table = None
        self.casing_stage_table = self._initialise_casing_stage_table()
        # ----------------------------------------------------------------
        self.is_initialised = False
        self.calculation_completed = False
        # ----------------------------------------------------------------
        self.logger = logger or getlogger()
        # ----------------------------------------------------------------
        # input added
        self.top_aquifer_layer = None
        self.target_aquifer_layer = None

    def _initialise_diameter_table(self,
                                   casing_diameter_table=None,
                                   drilling_diameter_table=None,):
        self.casing_diameter_table = casing_diameter_table or pd.DataFrame({
            'inches': [4, 4.5, 5, 5.5, 6.625, 7, 8.625, 9.625, 10.75, 13.375, 18.625, 20, 24, 30],
            'metres': [0.1016, 0.1143, 0.127, 0.1397, 0.168275, 0.1778, 0.219075, 0.244475, 0.27305, 0.339725, 0.473075, 0.508, 0.6096, 0.762],
            'recommended_bit': [0.190500, 0.215900, 0.215900, 0.228600, 0.269875, 0.269875, 0.311150, 0.349250, 0.381000, 0.444500, 0.609600, 0.609600, 0.711200, 0.914400]
        })

        self.drilling_diameter_table = drilling_diameter_table or pd.DataFrame({
            'inches': [7.5, 8.5, 9, 9.5, 10.625, 11.625, 12.25, 13.75, 15, 16, 17.5, 18.5, 20, 22, 24, 26, 28, 30, 32, 34, 36],
            'metres': [0.1905, 0.2159, 0.2286, 0.2413, 0.269875, 0.295275, 0.31115, 0.34925, 0.381, 0.4064, 0.4445, 0.4699, 0.508, 0.5588, 0.6096, 0.6604, 0.7112, 0.762, 0.8128, 0.8636, 0.9144],
            'recommended_screen': [
                0.1016, 0.1143, 0.127, 0.1397, 0.168275, 0.1778, 0.1778, 0.244475,
                0.27305, 0.27305, 0.339725, 0.339725, 0.339725, 0.339725, 0.508,
                0.508, 0.6096, 0.6096, 0.6096, 0.762, 0.762
            ]  # in metres
        })

    def _initialise_aquifer_layer_table(self, aquifer_layer_table):
        if not isinstance(aquifer_layer_table, pd.DataFrame):
            try:
                aquifer_layer_table_pd = pd.DataFrame(aquifer_layer_table)
            except ValueError as e:
                self.logger.error(e)
        else:
            aquifer_layer_table_pd = aquifer_layer_table.copy()
        columns = ["aquifer_layer", "is_aquifer", "depth_to_base"]
        aquifer_layer_table_pd.columns = columns
        self.aquifer_layer_table = aquifer_layer_table_pd.set_index(
            "aquifer_layer")  # index as the aquifer code

    def assign_input_params(self, arg_names: list, **kwargs):
        for arg_name in arg_names:
            value = kwargs.get(arg_name)
            if value is not None:
                setattr(self, arg_name, value)

    def _get_diameter_table(self, dataset, metric='metres', as_numpy=True):
        """
        dataset: self.casing_diameter_table if 'casing' else self.drilling_diameter_table
        metric: if 'metres' or 'inches', returns the corresponding column. Otherwise, returns the whole dataset
        as_numpy: if True, casts the returning dataset to numpy. This argument is ignored when metric is set to None, 
        """
        dset = self.casing_diameter_table if dataset == 'casing' else self.drilling_diameter_table
        if metric is None or metric not in dset.columns:
            return dset
        diam = dset['metres'] if metric == 'metres' else dset['inches']
        return np.array(diam) if as_numpy else diam

    def get_casing_diameters(self, metric='metres', as_numpy=True):
        """Returns as numpy array """
        return self._get_diameter_table(dataset='casing', metric=metric, as_numpy=as_numpy)

    def get_drilling_diameters(self, metric='metres', as_numpy=True):
        return self._get_diameter_table(dataset='drilling', metric=metric, as_numpy=as_numpy)

    def _initialise_casing_stage_table(self):
        casing_stages = ["pre_collar",
                         "superficial_casing",
                         "pump_chamber_casing",
                         "intermediate_casing",
                         "screen_riser",
                         "production_screen"]
        casing_columns = ['top', 'bottom', 'casing', 'drill_bit']
        nan_array = np.full((len(casing_stages), len(casing_columns)), np.nan)
        casing_df = pd.DataFrame(nan_array,
                                 columns=casing_columns).set_index(pd.Index(casing_stages, name='casing_stages'))
        return casing_df

    # TODO: The method directly accesses specific layers (LMTA, LTA, QA_UTQA) using .loc.
    def initialise_and_validate_input_params(self, **kwargs):
        """
        Initialises the WellboreDict instance with the provided depth data and initial parameters

        Parameters:
            "aquifer_layer_table": Dictionary containing aquifer layer information. Refer to the example usage below for api
            "required_flow_rate": Required flow rate in cubic metres per second (m^3/s).
            "hydraulic_conductivity": Aquifer hydraulic conductivity, K (m/day),
            "average_porosity": average reservoir porosity (0–1),
            "bore_lifetime_year": Bore/project lifetime in years,
            "groundwater_depth": Depth of the groundwater table in metres,
            "long_term_decline_rate": Long-term decline rate in water level in metres per year (dS/dt),
            "allowable_drawdown": Allowable drawdown in metres,
            "safety_margin": Safety margin in metres,
            "target_aquifer_layer": "The layer on which the screen is installed",
            "top_aquifer_layer": Top aquifer layer (qa or utqa)"

        Example Usage:
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

        wbd = WellBoreDict()
        wbd.initialise(aquifer_layer_table=aquifer_layer_table, **initial_values)

        """
        self._initialise_diameter_table()
        self._initialise_aquifer_layer_table(kwargs.get('aquifer_layer_table'))
        self.assign_input_params(self.initial_param_names, **kwargs)

        self.required_flow_rate_per_litre_sec = self.required_flow_rate / 86.4
        self.required_flow_rate_per_m3_sec = self.required_flow_rate / 86400
        self.bore_lifetime_per_day = self.bore_lifetime_year * 365

        if self.target_aquifer_layer not in self.aquifer_layer_table.index:
            raise ValueError(
                f'Target aquifer: {self.target_aquifer_layer} not present in the dataframe')
        target_index = self.aquifer_layer_table.index.get_loc(
            self.target_aquifer_layer)
        if target_index >= len(self.aquifer_layer_table.index) - 1:
            raise ValueError(
                f"Target aquifer '{self.target_aquifer_layer}' is the bottommost layer, which is not allowed.")

        self.depth_to_top_screen = self.aquifer_layer_table.loc[
            self.target_aquifer_layer]['depth_to_base']
        next_index = target_index + 1

        self.aquifer_thickness = self.aquifer_layer_table.iloc[next_index]['depth_to_base'] - \
            self.depth_to_top_screen

        if self.top_aquifer_layer not in self.aquifer_layer_table.index:
            raise ValueError(
                f'top_aquifer_layer(received:{self.top_aquifer_layer}) not present in the dataframe')
        if self.top_aquifer_layer not in ['100qa', '102utqa']:
            raise ValueError(
                f'top_aquifer_layer(received:{self.top_aquifer_layer}) should either be 100qa or 102utqa'
            )
        self.depth_to_aquifer_base = self.aquifer_layer_table.loc[
            self.top_aquifer_layer]['depth_to_base']

        self._validate_all_inputs()
        self.is_initialised = True

    def _validate_table(self):
        for arg in self.table_attribute_names:
            value = getattr(self, arg)
            if validate(value, lambda x: x.empty):
                self.logger.critical(
                    f'{self.__class__.__name__}.{self._validate_table.__name__} check failed: {arg} is an empty dataframe')
                return False
        return True

    def _validate_all_inputs(self):
        """ 
        #TODO: write in DRY util method
        Performs validation checks for the initial input data
        """

        if not isinstance(self.casing_diameter_table, pd.DataFrame) or self.casing_diameter_table.empty:
            raise ValueError("Invalid or missing casing diameter data")

        if not isinstance(self.drilling_diameter_table, pd.DataFrame) or self.drilling_diameter_table.empty:
            raise ValueError("Invalid or missing drilling diameter data")

        if not isinstance(self.aquifer_layer_table, pd.DataFrame) or self.aquifer_layer_table.empty:
            raise ValueError("Invalid or missing depth data")

        for param in self.initial_param_names:
            if getattr(self, param) is None:
                raise ValueError(
                    f"Invalid or missing initial parameter at {param}")

    def export_results_to_dict(self, to_json=False):
        """
        Export the results of the pipeline as a Python dict object

        Parameters:
            to_json: if set to True, stores the pd.DataFrame item as a json string
        """
        if not self.calculation_completed:
            self.logger.critical('Unfinished pipeline')
            return
        results = {}
        for key in self.output_param_names:
            value = getattr(self, key)
            if isinstance(value, pd.DataFrame):
                # json compatible
                value = value.replace(np.nan, None)
                if to_json:
                    results[key] = value.to_json()
                    continue
            results[key] = value
        return results

    def export_results_to_json_string(self):
        """
        Export the results of the pipeline to a json format string
        """
        results = self.export_results_to_dict(to_json=True)

        return json.dumps(results)
