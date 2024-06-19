#!/usr/bin/env python
import numpy as np
import pandas as pd
import json
from .utils.utils import getlogger, validate


class WellBoreDict:
    """
    
    """
    data_param_names = [
        # ----------------input
        "casing_diameter_data",
        "drilling_diameter_data",
        "depth_data",
        # ----------------tbd by pipeline
        "interval_stage_data",
        "casing_stage_data"
    ]

    initial_param_names = [
        "required_flow_rate",
        "hydraulic_conductivity",
        "average_porosity",
        "bore_lifetime_year",
        "groundwater_depth",
        "long_term_decline_rate",
        "allowable_drawdown",
        "safety_margin",
        # Below are derived from the above parameters
        "depth_to_top_screen",
        "required_flow_rate_per_litre_sec",
        "required_flow_rate_per_m3_sec",
        "bore_lifetime_per_day",
        "aquifer_thickness",
        "depth_to_aquifer_base",
        # And below are params with preassigned default values
        "sand_face_velocity_production",
        "sand_face_velocity_injection",
        "net_to_gross_ratio_aquifer",
        "aquifer_average_porosity",
        "pipe_roughness_coeff"
    ]

    outcome_params = [
        "production_screen_length",
        "injection_screen_length",
        "production_screen_length_error",
        "injection_screen_length_error",
        "min_total_casing_production_screen_diameter",
        "production_screen_diameter",
        "injection_screen_diameter",
        "production_open_hole_diameter",
        "injection_open_hole_diameter",
        "pump_inlet_depth",
        "minimum_pump_housing_diameter",
        "interval_stage_data",
        "casing_stage_data"
    ]

    def __init__(self, logger=None):
        # ----------------------------------------------------------------
        self.casing_diameter_data = pd.DataFrame(
            columns=['inches', 'metres', 'recommended_bit'])
        self.drilling_diameter_data = pd.DataFrame(
            columns=['inches', 'metres', 'recommended_screen'])

        self.depth_data = pd.DataFrame(
            columns=["aquifer_layer", "is_aquifer", "depth_to_base"])
        # ----------------------------------------------------------------
        self.required_flow_rate = None
        self.hydraulic_conductivity = None
        self.average_porosity = None
        self.bore_lifetime_year = None
        self.groundwater_depth = None
        self.long_term_decline_rate = None
        self.allowable_drawdown = None
        self.safety_margin = None
        # ----------------------------------------------------------------
        self.required_flow_rate_per_litre_sec = None
        self.required_flow_rate_per_m3_sec = None
        self.bore_lifetime_per_day = None
        self.depth_to_top_screen = None
        self.aquifer_thickness = None
        self.depth_to_aquifer_base = None
        # ----------------------------------------------------------------
        self.sand_face_velocity_production = .01
        self.sand_face_velocity_injection = .003
        self.net_to_gross_ratio_aquifer = 1
        self.aquifer_average_porosity = .25
        self.pipe_roughness_coeff = 100
        # ----------------------------------------------------------------
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
        self.interval_stage_data = None
        self.casing_stage_data = self._initialise_casing_stage_data()
        # ----------------------------------------------------------------
        self.is_initialised = False
        self.calculation_completed = False
        #----------------------------------------------------------------
        self.logger = logger or getlogger()

    def _set_diameter_data(self,
                          casing_diameter_data=None,
                          drilling_diameter_data=None,):
        self.casing_diameter_data = casing_diameter_data or pd.DataFrame({
            'inches': [4, 4.5, 5, 5.5, 6.625, 7, 8.625, 9.625, 10.75, 13.375, 18.625, 20, 24, 30],
            'metres': [0.1016, 0.1143, 0.127, 0.1397, 0.168275, 0.1778, 0.219075, 0.244475, 0.27305, 0.339725, 0.473075, 0.508, 0.6096, 0.762],
            'recommended_bit': [0.190500, 0.215900, 0.215900, 0.228600, 0.269875, 0.269875, 0.311150, 0.349250, 0.381000, 0.444500, 0.609600, 0.609600, 0.711200, 0.914400]
        })

        self.drilling_diameter_data = drilling_diameter_data or pd.DataFrame({
            'inches': [7.5, 8.5, 9, 9.5, 10.625, 11.625, 12.25, 13.75, 15, 16, 17.5, 18.5, 20, 22, 24, 26, 28, 30, 32, 34, 36],
            'metres': [0.1905, 0.2159, 0.2286, 0.2413, 0.269875, 0.295275, 0.31115, 0.34925, 0.381, 0.4064, 0.4445, 0.4699, 0.508, 0.5588, 0.6096, 0.6604, 0.7112, 0.762, 0.8128, 0.8636, 0.9144],
            'recommended_screen': [
                0.1016, 0.1143, 0.127, 0.1397, 0.168275, 0.1778, 0.1778, 0.244475,
                0.27305, 0.27305, 0.339725, 0.339725, 0.339725, 0.339725, 0.508,
                0.508, 0.6096, 0.6096, 0.6096, 0.762, 0.762
            ]  # in metres
        })

    def _set_depth_data(self, depth_data):
        if not isinstance(depth_data, pd.DataFrame):
            try:
                depth_data_pd = pd.DataFrame(depth_data)
            except ValueError as e:
                self.logger.error(e)
        else:
            depth_data_pd = depth_data.copy()
        columns = ["aquifer_layer", "is_aquifer", "depth_to_base"]
        depth_data_pd.columns = columns
        self.depth_data = depth_data_pd.set_index(
            "aquifer_layer")

    def set_params(self, arg_names:list, **kwargs):
        for arg_name in arg_names:
            value = kwargs.get(arg_name)
            if value is not None:
                setattr(self, arg_name, value)


    # def set_is_production(self, is_production):
    #     self.is_production = is_production

    def _get_diameter_data(self, dataset, metric='metres', as_numpy=True):
        """
        dataset: self.casing_diameter_data if 'casing' else self.drilling_diameter_data
        metric: if 'metres' or 'inches', returns the corresponding column. Otherwise, returns the whole dataset
        as_numpy: if True, casts the returning dataset to numpy. This argument is ignored when metric is set to None, 
        """
        dset = self.casing_diameter_data if dataset == 'casing' else self.drilling_diameter_data
        if metric is None or metric not in dset.columns:
            return dset
        diam = dset['metres'] if metric == 'metres' else dset['inches']
        return np.array(diam) if as_numpy else diam

    def get_casing_diameters(self, metric='metres', as_numpy=True):
        """Returns as numpy array """
        return self._get_diameter_data(dataset='casing', metric=metric, as_numpy=as_numpy)
        # if metric == None
        # diam = self.casing_diameter_data['metres']
        # return np.array(diam) if as_numpy else diam

    def get_drilling_diameters(self, metric='metres', as_numpy=True):
        return self._get_diameter_data(dataset='drilling', metric=metric, as_numpy=as_numpy)
        # diam = self.drilling_diameter_data['metres']
        # return np.array(diam) if as_numpy else diam

    def _initialise_casing_stage_data(self):
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

    def initialise_and_validate_input_data(self, **kwargs):
        """
        Initialises the WellboreDict instance with the provided depth data and initial parameters
        
        Parameters:
            "depth_data": Dictionary containing aquifer layer information. Refer to the example usage below for api
            "required_flow_rate": Required flow rate in cubic metres per second (m^3/s).
            "hydraulic_conductivity": Aquifer hydraulic conductivity, K (m/day),
            "average_porosity": average reservoir porosity (0–1),
            "bore_lifetime_year": Bore/project lifetime in years,
            "groundwater_depth": Depth of the groundwater table in metres,
            "long_term_decline_rate": Long-term decline rate in water level in metres per year (dS/dt),
            "allowable_drawdown": Allowable drawdown in metres,
            "safety_margin": Safety margin in metres
        
        Example Usage:
            depth_data = {
                "aquifer_layer": [
                    "QA_UTQA",
                    "UTQD",
                    "UTAF",
                    "UTD",
                    "UMTA",
                    "UMTD",
                    "LMTA",
                    "LTA",
                    "BSE"
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
                "safety_margin": 25
            }
        
        wbd = WellBoreDict()
        wbd.initialise(depth_data=depth_data, **initial_values)

        """
        self._set_diameter_data()
        self._set_depth_data(kwargs.get('depth_data'))
        self.set_params(self.initial_param_names, **kwargs)

        self.required_flow_rate_per_litre_sec = self.required_flow_rate / 86.4
        self.required_flow_rate_per_m3_sec = self.required_flow_rate / 86400
        self.bore_lifetime_per_day = self.bore_lifetime_year * 365

        self.depth_to_top_screen = self.depth_data.loc['LMTA']['depth_to_base']
        self.aquifer_thickness = self.depth_data.loc['LTA']['depth_to_base'] - \
            self.depth_to_top_screen
        self.depth_to_aquifer_base = self.depth_data.loc['QA_UTQA']['depth_to_base']
        self.is_initialised = True

        self._validate_initial_inputs()

    def _validate_data(self):
        for arg in self.data_param_names:
            value = getattr(self, arg)
            if validate(value, lambda x: not isinstance(x, pd.DataFrame) or x.empty):
                self.logger.critical('validate_data failed')
                return False
        return True

    def _validate_initial_inputs(self):
        """ 
        #TODO: write in DRY util method
        Performs validation checks for the initial input data
        """
        if not self.is_initialised:
            return False

        if not isinstance(self.casing_diameter_data, pd.DataFrame) or self.casing_diameter_data.empty:
            self.logger.error("Invalid or missing casing diameter data")
            return False

        if not isinstance(self.drilling_diameter_data, pd.DataFrame) or self.drilling_diameter_data.empty:
            self.logger.error("Invalid or missing drilling diameter data")
            return False

        if not isinstance(self.depth_data, pd.DataFrame) or self.depth_data.empty:
            self.logger.error("Invalid or missing depth data")
            return False

        if not all([
            self.required_flow_rate,
            self.hydraulic_conductivity,
            self.average_porosity,
            self.bore_lifetime_year,
            self.groundwater_depth,
            self.long_term_decline_rate,
            self.allowable_drawdown,
            self.safety_margin
        ]):
            self.logger.error("Invalid or missing float input data")
            return False

        return True

    def export_results_to_dict(self,to_json=False):
        """
        Export the results of the pipeline as a Python dict object

        Parameters:
            to_json: if set to True, stores the pd.DataFrame item as a json string
        """
        if not self.calculation_completed:
            self.logger.critical('Unfinished pipeline')
            return
        results = {}
        for key in self.outcome_params:
            value = getattr(self, key)
            if isinstance(value, pd.DataFrame):
                #json compatible
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