#!/usr/bin/env python
import numpy as np
import pandas as pd
import json
from .utils.utils import getlogger


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
    Refer to example usage for details

    Methods:
    --------
    __init__(self, is_production_well:bool, logger=None):
        Instantiates and initialises the WellBoreDict instance with pre-defined values.

    initialise_and_validate_input_params(self, **kwargs):
        Initializes and validates the input data for wellbore calculations.

    export_results_to_dict(self, to_json=False):
        Exports the results of the wellbore calculations to a dictionary.

    export_results_to_json_string(self):
        Exports the results of the wellbore calculations to a JSON string.
    
    get_casing_diameters(self, metric='metres', as_numpy=True):
        Returns casing diameters as a numpy array or pandas Series.

    get_drilling_diameters(self, metric='metres', as_numpy=True):
        Returns drilling diameters as a numpy array or pandas Series.

    """
    #--------base attributes----------------------
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
        # "is_production_well": bool,
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

    _OUTPUT_DEFAULT_ATTRIBUTES = {
        "screen_length": float,
        "screen_length_error": float,
        "screen_diameter": float,
        "open_hole_diameter": float,

        "pump_inlet_depth": float,
        "minimum_pump_housing_diameter": float,

        "casing_stage_table": pd.DataFrame
    }

    _OUTPUT_PRODUCTION_ATTRIBUTES = {
        "min_total_casing_production_screen_diameter": float,
        "screen_stage_table": pd.DataFrame,
    }


    def __init__(self, is_production_well:bool, logger=None):
        self.is_production_well = is_production_well       
        self._setup_calc_attributes(is_production_well)
        self._assign_default_attributes()
        self.ready_for_calculation = False
        self.calculation_completed = False
        # ----------------------------------------------------------------
        self.logger = logger or getlogger()
        # ----------------------------------------------------------------

    def initialise_calculation_parameters(self, **kwargs):
        self._assign_input_params(self.initial_param_names, **kwargs)
        self.required_flow_rate_per_litre_sec = self.required_flow_rate / 86.4
        self.required_flow_rate_per_m3_sec = self.required_flow_rate / 86400
        self.bore_lifetime_per_day = self.bore_lifetime_year * 365

        self._initialise_aquifer_layer_table(kwargs.get('aquifer_layer_table'))
        
        # Validate and assign target aquifer layer
        self._validate_aquifer_layer(self.target_aquifer_layer, "Target aquifer")
        target_index = self._validate_target_aquifer_layer()
        self.depth_to_top_screen = self.aquifer_layer_table.loc[self.target_aquifer_layer]['depth_to_base']
        self.aquifer_thickness = self.aquifer_layer_table.iloc[target_index + 1]['depth_to_base'] - self.depth_to_top_screen

        # Validate and assign top aquifer layer
        self._validate_aquifer_layer(self.top_aquifer_layer, "Top aquifer layer")
        self._validate_top_aquifer_layer()
        self.depth_to_aquifer_base = self.aquifer_layer_table.loc[self.top_aquifer_layer]['depth_to_base']

        # Final validation before calculation
        self._validate_initial_inputs()
        self.ready_for_calculation = True

#------export utils----------------------
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
        for key in self.output_attribute_names:
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


#------------initialisation utility private methods----------------------------------------
    def _setup_calc_attributes(self, is_production_well: bool):
        self._all_attributes = self._INPUT_ATTRIBUTES | self._OUTPUT_DEFAULT_ATTRIBUTES | \
            (self._OUTPUT_PRODUCTION_ATTRIBUTES if is_production_well else {})
        self.initial_param_names = [
            key for key, val in self._INPUT_ATTRIBUTES.items() if val != pd.DataFrame]
        self.table_attribute_names = [
            key for key, val in self._all_attributes.items() if val == pd.DataFrame]
        self.output_attribute_names = [*self._OUTPUT_DEFAULT_ATTRIBUTES.keys()]
        if is_production_well:
            self.output_attribute_names += [*self._OUTPUT_PRODUCTION_ATTRIBUTES.keys()]
        self.attributes_assigned = True
        
    def _assign_default_attributes(self):
        if not self.attributes_assigned:
            raise RuntimeError("Attributes must be initialised before setting default values."+ 
                               "Call '_setup_calc_attributes()' first.")
        for attr in self._all_attributes:
            setattr(self, attr, None)
        # ----------------------------------------------------------------
        # table initialisation
        self.casing_diameter_table = pd.DataFrame(
            columns=['inches', 'metres', 'recommended_bit'])
        self.drilling_diameter_table = pd.DataFrame(
            columns=['inches', 'metres', 'recommended_screen'])
        self.aquifer_layer_table = pd.DataFrame(
            columns=["aquifer_layer", "is_aquifer", "depth_to_base"])
        # ----------------------------------------------------------------
        # constants initialisation
        self.sand_face_velocity_production = .01
        self.sand_face_velocity_injection = .003
        self.net_to_gross_ratio_aquifer = 1
        self.aquifer_average_porosity = .25
        self.pipe_roughness_coeff = 100
        # ----------------------------------------------------------------
        self.casing_stage_table = self._initialise_casing_stage_table()
        # ----------------------------------------------------------------
        self.initialise_diameter_tables()

    def initialise_diameter_tables(self,
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

    def _initialise_casing_stage_table(self):
        casing_stages = ["pre_collar",
                         "superficial_casing",
                         "pump_chamber_casing",
                         "intermediate_casing",
                         "screen_riser",
                         "screen"]
        casing_columns = ['top', 'bottom', 'casing', 'drill_bit']
        nan_array = np.full((len(casing_stages), len(casing_columns)), np.nan)
        casing_df = pd.DataFrame(nan_array,
                                 columns=casing_columns).set_index(pd.Index(casing_stages, name='casing_stages'))
        return casing_df

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

    def _assign_input_params(self, arg_names: list, **kwargs):
        for arg_name in arg_names:
            value = kwargs.get(arg_name)
            if value is not None:
                setattr(self, arg_name, value)

    # TODO: The method directly accesses specific layers (LMTA, LTA, QA_UTQA) using .loc.

#-----validation private methods----------------------

    def _validate_aquifer_layer(self, layer_name: str, context: str):
        if layer_name not in self.aquifer_layer_table.index:
            raise ValueError(f"{context}: '{layer_name}' not found in the aquifer layer table.")
        return True

    def _validate_target_aquifer_layer(self):
        target_index = self.aquifer_layer_table.index.get_loc(self.target_aquifer_layer)
        if target_index >= len(self.aquifer_layer_table.index) - 1:
            raise ValueError(f"Target aquifer '{self.target_aquifer_layer}' is the bottommost layer, which is not allowed.")
        return target_index

    def _validate_top_aquifer_layer(self):
        #TODO: Improve the logic after discussion
        if self.top_aquifer_layer not in ['100qa', '102utqa']:
            raise ValueError(f"Top aquifer layer must be either '100qa' or '102utqa', but received '{self.top_aquifer_layer}'.")

    def _validate_initial_inputs(self):
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

#-------diameter table utils-----------------------
    def _get_diameter_table(self, casing_or_drilling:str, metric='metres', as_numpy=True):
        """
        casing_or_drilling: self.casing_diameter_table if 'casing' else self.drilling_diameter_table
        metric: if 'metres' or 'inches', returns the corresponding column. Otherwise, returns the whole dataset
        as_numpy: if True, casts the returning dataset to numpy. This argument is ignored when metric is set to None, 
        """
        dset = self.casing_diameter_table if casing_or_drilling == 'casing' else self.drilling_diameter_table
        if metric is None or metric not in dset.columns:
            return dset
        diam = dset['metres'] if metric == 'metres' else dset['inches']
        return np.array(diam) if as_numpy else diam

    def get_casing_diameters(self, metric='metres', as_numpy=True):
        """Returns as numpy array """
        return self._get_diameter_table(casing_or_drilling='casing', metric=metric, as_numpy=as_numpy)

    def get_drilling_diameters(self, metric='metres', as_numpy=True):
        return self._get_diameter_table(casing_or_drilling='drilling', metric=metric, as_numpy=as_numpy)

