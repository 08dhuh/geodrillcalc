"""
modules to associate the wellbore parameters with the cost rates to be used for calculating the overall cost
"""
import pandas as pd
import numpy as np
from ..utils.utils import getlogger 
from ..utils.cost_utils import calculate_costs_with_df, populate_margin_functions


class WellboreCostCalculator:
    def __init__(self,
                 cost_rates,
                 wellbore_params,
                 margins_dict,
                 stage_labels) -> None:
        self.logger = getlogger()
        self.cost_rates = cost_rates
        self.wellbore_params = wellbore_params
        self.stage_labels = stage_labels

        self._cost_estimation_table = None
        self.set_margin_functions(margins_dict)


    @property
    def drilling_rate_params(self):
        return self.wellbore_params['drilling_rates']

    @property
    def time_rate_params(self):
        return self.wellbore_params['time_rates']

    @property
    def material_cost_params(self):
        return self.wellbore_params['materials']

    @property
    def other_cost_params(self):
        return self.wellbore_params['others']

    @property
    def cost_estimation_table(self) -> pd.DataFrame:
        if self._cost_estimation_table is None:
            columns = ['low', 'base', 'high']
            self._cost_estimation_table = pd.DataFrame(columns=columns, index=self.stage_labels)
        return self._cost_estimation_table
    
    @property
    def margin_functions(self):
        return self._margin_functions


    @margin_functions.setter
    def margin_functions(self, margins_dict: dict):
        if self._margin_functions is None:
            margin_functions = {}
            for key, margins in margins_dict.items():
                margin_functions[key] = populate_margin_functions(margins)
            self._margin_functions = margin_functions


    # Step 1: Drilling Rates
    def calculate_base_drilling_rates(self) -> float:
        try:
            total_well_depth = self.drilling_rate_params["total_well_depth"]
            pilot_hole_rate = self.cost_rates["drilling_rates"]["pilot_hole_rate_per_meter"]
            other_drilling_rate = self.cost_rates["drilling_rates"]["other_drilling_rate"]
            error_margin = self.cost_rates["drilling_rates"]["drilling_rate_error_margin_per_meter"]

            base_cost = total_well_depth * pilot_hole_rate
            adjusted_cost = (other_drilling_rate["coefficient"] * total_well_depth +
                             other_drilling_rate["offset"] + error_margin)

            total_drilling_cost = base_cost + adjusted_cost
            return total_drilling_cost
        except KeyError as e:
            self.logger.error(f"Error in calculating drilling rates: {e}")
            return 0.0

    # Step 2: Time Rates
    def calculate_time_rates(self) -> None:
        try:
            drilling_time = self.time_rate_params["drilling_time"]
            rig_standby_rate = self.cost_rates["hourly_rates"]["rig_standby_rate"]
            accommodation_rate = self.cost_rates["hourly_rates"]["accommodation_meals_rate_per_day"]

            base_costs = {}
            # Example calculations
            base_costs['rig_standby_cost'] = drilling_time * rig_standby_rate
            base_costs['development_bail_surge_jet'] = None  # TODO:
            base_costs['accommodation_cost'] = drilling_time * accommodation_rate
            base_costs['site_telehandler_cost'] = drilling_time * self.cost_rates["hourly_rates"][
                "site_telehandler_rate_per_day"]  # Example rate
            base_costs['site_generator_fuel_cost'] = drilling_time * self.cost_rates["hourly_rates"][
                "site_generator_fuel_rate_per_day"]  # Example rate

            df = calculate_costs_with_df(base_values=base_costs,
                                         margin_functions=self.margin_functions['time_rates'],
                                         index_labels=base_costs.keys())

            # Sum the columns to calculate the final time rates
            self.cost_estimation_table['time_rates'] = df.sum(axis=1)

        except KeyError as e:
            self.logger.error(f"Error in calculating time rates: {e}")
            return 0.0

    # Step 3: Material Costs
    def calculate_material_costs(self) -> float:
        try:
            total_well_depth = self.material_cost_params["total_well_depth"]
            section_lengths = self.material_cost_params["section_lengths"]
            section_diameters = self.material_cost_params["section_diameters"]
            section_excavation_volumes = self.material_cost_params["section_excavation_volumes"]
            total_gravel_volume = self.material_cost_params["total_gravel_volume"]
            total_cement_volume = self.material_cost_params["total_cement_volume"]
            operational_section_count = self.material_cost_params["operational_section_count"]

            base_costs = {}
            # Example calculations
            base_costs['casing_cost'] = section_lengths.multiply(
                self.cost_rates["materials"]["casing_cost_per_meter"]).sum()
            base_costs['screen_cost'] = section_lengths.multiply(
                self.cost_rates["materials"]["screen_cost_per_meter"]).sum()
            base_costs['gravel_cost'] = total_gravel_volume * self.cost_rates["materials"]["gravel_cost_per_cubic_meter"]
            base_costs['cement_cost'] = total_cement_volume * self.cost_rates["materials"]["cement_cost_per_cubic_meter"]
            base_costs['drilling_bit_cost'] = operational_section_count * self.cost_rates["materials"][
                "drilling_bit_cost_per_section"]
            base_costs['excavation_cost'] = section_excavation_volumes.multiply(
                self.cost_rates["materials"]["excavation_cost_per_cubic_meter"]).sum()

            df = calculate_costs_with_df(base_values=base_costs,
                                         margin_functions=self.margin_functions['materials'],
                                         index_labels=base_costs.keys())

            # Sum the columns to calculate the final material costs
            self.cost_estimation_table['materials'] = df.sum(axis=1)

        except KeyError as e:
            self.logger.error(f"Error in calculating material costs: {e}")
            return 0.0

    # Step 4: Other Costs
    def calculate_other_costs(self) -> float:
        try:
            total_well_depth = self.other_cost_params["total_well_depth"]
            section_lengths = self.other_cost_params["section_lengths"]
            drilling_time = self.other_cost_params["drilling_time"]

            base_costs = {}
            # Example calculations
            base_costs['mobilization_cost'] = self.cost_rates["others"]["mobilization_cost"]
            base_costs['demobilization_cost'] = self.cost_rates["others"]["demobilization_cost"]
            base_costs['permits_cost'] = self.cost_rates["others"]["permits_cost"]
            base_costs['site_preparation_cost'] = self.cost_rates["others"]["site_preparation_cost"]
            base_costs['well_development_cost'] = self.cost_rates["others"]["well_development_cost"]
            base_costs['well_testing_cost'] = self.cost_rates["others"]["well_testing_cost"]
            base_costs['well_disinfection_cost'] = self.cost_rates["others"]["well_disinfection_cost"]
            base_costs['well_abandonment_cost'] = self.cost_rates["others"]["well_abandonment_cost"]
            base_costs['insurance_cost'] = self.cost_rates["others"]["insurance_cost"]
            base_costs['overhead_cost'] = self.cost_rates["others"]["overhead_cost"]
            base_costs['profit_cost'] = self.cost_rates["others"]["profit_cost"]

            df = calculate_costs_with_df(base_values=base_costs,
                                         margin_functions=self.margin_functions['others'],
                                         index_labels=base_costs.keys())

            # Sum the columns to calculate the final other costs
            self.cost_estimation_table['others'] = df.sum(axis=1)

        except KeyError as e:
            self.logger.error(f"Error in calculating other costs: {e}")
            return 0.0

    # Calculate the total cost
    def calculate_total_cost(self) -> float:
        total_drilling_rates = self.calculate_base_drilling_rates()
        self.cost_estimation_table.at['drilling_rates', 'base'] = total_drilling_rates
        self.calculate_time_rates()
        self.calculate_material_costs()
        self.calculate_other_costs()

        total_cost = self.cost_estimation_table.sum(axis=0)
        return total_cost



