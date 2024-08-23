import pandas as pd
import numpy as np
from ..utils.utils import getlogger
from ..utils.cost_utils import calculate_costs_with_df, populate_margin_functions

# Constants for margin calculations
# TODO: get rid of these magic numbers
PRE_COLLAR_MARGIN_RATE = 0.2  # 20% margin for pre-collar section
CENTRALISER_COST_FACTOR_LOW = 2/3
CENTRALISER_COST_FACTOR_HIGH = 1.5
CENTRALISER_DEPTH_OFFSET_LOW = -20
CENTRALISER_DEPTH_OFFSET_HIGH = 20


class CostStageCalculator:
    """
    stores calculation methods required for the cost calculation pipeline.
    """

    def __init__(self,
                 cost_rates,
                 wellbore_params,
                 margin_rates,
                 stage_labels):
        self.logger = getlogger()
        self.cost_rates = cost_rates
        self.wellbore_params = wellbore_params
        self.stage_labels = stage_labels
        self.margin_functions = self._initialise_margin_functions(margin_rates)

        self.stage_calculators = {
            'drilling_rates': self.calculate_drilling_components_cost,
            'time_rates': self.calculate_time_components_cost,
            'materials': self.calculate_material_components_cost,
            'others': self.calculate_other_components_cost
        }

    @property
    def drilling_rate_params(self):
        return self.wellbore_params['drilling_rates']

    @property
    def time_rate_params(self):
        return self.wellbore_params['time_rates']

    @property
    def material_params(self):
        return self.wellbore_params['materials']

    @property
    def other_params(self):
        return self.wellbore_params['others']

    @property
    def drilling_cost_rates(self):
        return self.cost_rates['drilling_rates']

    @property
    def time_cost_rates(self):
        return self.cost_rates['time_rates']

    @property
    def material_cost_rates(self):
        return self.cost_rates['materials']

    @property
    def other_cost_rates(self):
        return self.cost_rates['others']

    def _initialise_margin_functions(self, margins_dict) -> pd.DataFrame:
        return populate_margin_functions(margins_dict)

    def calculate_drilling_components_cost(self) -> pd.DataFrame:
        try:
            total_well_depth = self.drilling_rate_params["total_well_depth"]
            drilling_section_length_diameter = pd.concat([self.drilling_rate_params['section_lengths'],
                                                          self.drilling_rate_params['section_diameters']], axis=1)
            drilling_section_length_diameter.columns = ['length', 'diameter']

            pilot_hole_cost = total_well_depth * \
                self.drilling_cost_rates['pilot_hole_rate_per_meter']

            drilling_section_result = pd.DataFrame({
                'base': [pilot_hole_cost]
            }, index=['pilot_hole'])

            casing_stages_result = drilling_section_length_diameter.apply(
                lambda row: max(row['length'] * (
                    np.pi / 2 * row['diameter'] - self.drilling_cost_rates['diameter_based_offset']), 0), axis=1)

            casing_stages_result = pd.DataFrame({
                'base': casing_stages_result
            })
            drilling_section_result = pd.concat(
                [drilling_section_result, casing_stages_result], axis=0)

            drilling_section_result[['low', 'high']] = np.nan
            drilling_section_result = drilling_section_result[[
                'low', 'base', 'high']]

            return drilling_section_result
        except KeyError as e:
            self.logger.error(
                f"Error in calculating drilling rates: {e} at line {e.__traceback__.tb_lineno}")
            raise

    def calculate_drilling_rates_total_cost(self,
                                            base_sum) -> pd.Series:
        cost_margin = self.drilling_rate_params["total_well_depth"] * \
            self.drilling_cost_rates['drilling_rate_error_margin_per_meter']
        cost_low = base_sum - cost_margin
        cost_high = base_sum + cost_margin
        return pd.Series([cost_low, base_sum, cost_high], index=['low', 'base', 'high'])

    def calculate_time_components_cost(self) -> pd.DataFrame:
        try:
            flow_rate = self.time_rate_params["required_flow_rate"]
            drilling_time = self.time_rate_params["drilling_time"]
            base_costs = {
                'rig_standby_cost': self.time_cost_rates["rig_standby_rate"],
                'development_bail_surge_jet': flow_rate * self.time_cost_rates['development_bail_surge_jet_rate_per_hour'],
                'accommodation_cost': drilling_time * self.time_cost_rates['accommodation_meals_rate_per_day'],
                'site_telehandler_cost': drilling_time * self.time_cost_rates["site_telehandler_rate_per_day"],
                'site_generator_fuel_cost': drilling_time * self.time_cost_rates["site_generator_fuel_rate_per_day"]
            }

            time_rates_df = calculate_costs_with_df(
                base_values=base_costs,
                margin_functions=self.margin_functions.loc['time_rates'],
                index_labels=base_costs.keys()
            )

            return time_rates_df

        except (ValueError, KeyError) as e:
            self.logger.error(
                f"Error in calculating time rates: {e} at line {e.__traceback__.tb_lineno}")
            raise

    def calculate_material_components_cost(self) -> pd.DataFrame:
        try:
            total_well_depth = self.material_params["total_well_depth"]
            section_lengths = self.material_params["section_lengths"]
            section_diameters = self.material_params["section_diameters"]
            section_excavation_volumes = self.material_params["section_excavation_volumes"]
            total_excavation_volume = section_excavation_volumes.sum()
            total_gravel_volume = self.material_params["total_gravel_volume"]
            total_cement_volume = self.material_params["total_cement_volume"]
            operational_section_count = self.material_params["operational_section_count"]

            base_costs = {
                'cement': total_cement_volume * self.material_cost_rates['cement_rate_per_cubic_meter'],
                'gravel': total_gravel_volume * self.material_cost_rates['gravel_rate_per_cubic_meter'],
                'bentonite': total_excavation_volume * self.material_cost_rates['bentonite_rate_per_cubic_meter'],
                'drilling_fluid_and_lubricants': total_excavation_volume * self.material_cost_rates['drilling_fluid_and_lubricant_rate_per_cubic_meter'],
                'drilling_mud': total_excavation_volume * self.material_cost_rates['drilling_mud_rate_per_cubic_meter'],
                'bore_flange_and_valve_spec': self.material_cost_rates['bore_table_flange_gate_valve_rate'],
                'cement_shoe': self.material_cost_rates['cement_shoe_rate'],
                'packer_lowering_assembly': self.material_cost_rates['packer_lowering_assembly_rate'] * operational_section_count
            }

            material_costs_df = calculate_costs_with_df(
                base_values=base_costs,
                margin_functions=self.margin_functions.loc['materials'],
                index_labels=base_costs.keys()
            )

            bore_section_params = pd.DataFrame(
                section_lengths.multiply(section_diameters) * 1E3)
            bore_section_costs = pd.DataFrame(
                index=bore_section_params.index, columns=['base', 'low', 'high'])
            bore_section_costs['base'] = bore_section_params.apply(
                lambda row: (
                    row * self.material_cost_rates['pre_collar']['coefficient'] /
                    self.material_cost_rates['pre_collar']['divisor']
                    if row.name == 'pre_collar'
                    else (
                        row * self.material_cost_rates['screen']['coefficient'] +
                        self.material_cost_rates['screen']['offset']
                        if row.name == 'screen'
                        else row * self.material_cost_rates['other_section']['coefficient'] + self.material_cost_rates['other_section']['offset']
                    )
                ), axis=1
            )
            bore_section_costs['low'] = bore_section_costs.apply(
                lambda row: max(row['base'] - section_lengths.get(row.name)
                                * self.material_cost_rates['bore_section_margin_rate'], 0)
                if row.name != 'pre_collar' else row['base'] * (1 - PRE_COLLAR_MARGIN_RATE), axis=1
            )
            bore_section_costs['high'] = bore_section_costs.apply(
                lambda row: row['base'] + section_lengths.get(
                    row.name) * self.material_cost_rates['bore_section_margin_rate']
                if row.name != 'pre_collar' else row['base'] * (1 + PRE_COLLAR_MARGIN_RATE), axis=1
            )

            material_costs_df = pd.concat(
                [material_costs_df, bore_section_costs])

            total_well_depth_without_screen = section_lengths.iloc[:-2].sum()
            # append centraliser
            centraliser_row = {
                'low': max(self.material_cost_rates['centraliser_rate_per_meter'] * CENTRALISER_COST_FACTOR_LOW * (total_well_depth_without_screen + CENTRALISER_DEPTH_OFFSET_LOW), 0),
                'base': self.material_cost_rates['centraliser_rate_per_meter'] * total_well_depth,
                'high': self.material_cost_rates['centraliser_rate_per_meter'] * CENTRALISER_COST_FACTOR_HIGH * (total_well_depth_without_screen + CENTRALISER_DEPTH_OFFSET_HIGH)
            }
            material_costs_df = pd.concat(
                [material_costs_df, pd.DataFrame(centraliser_row, index=['centraliser'])])

            return material_costs_df
        except KeyError as e:
            self.logger.error(
                f"Error in calculating material costs: {e} at line {e.__traceback__.tb_lineno}")
            raise

    def calculate_other_components_cost(self) -> pd.DataFrame:

        try:
            total_well_depth = self.other_params["total_well_depth"]
            section_lengths = self.other_params["section_lengths"]
            drilling_time = self.other_params["drilling_time"]
            pre_collar_length = section_lengths['pre_collar']
            screen_length = section_lengths['screen']

            base_costs = {
                'disinfection_drilling_plant': self.other_cost_rates['disinfection_drilling_plant_rate'],
                'mobilisation_demobilization': self.other_cost_rates['mobilisation_demobilization_rate_per_day'] * drilling_time,
                'installation_grouting_pre_collar': self.other_cost_rates['installation_grouting_pre_collar_rate_per_meter'] * pre_collar_length,
                'wireline_logging': self.other_cost_rates['wireline_logging_rate_per_meter'] * total_well_depth,
                'fabrication_installation': self.other_cost_rates['fabrication_installation_rate_per_meter'] * (total_well_depth - pre_collar_length),
                'cement_casing': self.other_cost_rates['cement_casing_rate_per_meter'] * (total_well_depth - pre_collar_length),
                'pack_gravel': self.other_cost_rates['gravel_pack_rate_per_meter'] * screen_length,
                'subcontract_welders': self.other_cost_rates['subcontract_welders_rate_per_day'] * drilling_time
            }

            other_costs_df = calculate_costs_with_df(
                base_values=base_costs,
                margin_functions=self.margin_functions.loc['others'],
                index_labels=base_costs.keys()
            )

            return other_costs_df
        except KeyError as e:
            self.logger.error(
                f"Error in calculating other costs: {e} at line {e.__traceback__.tb_lineno}")
            raise
        except Exception as e:
            self.logger.error(
                f"Error in calculating other costs: {e} at line {e.__traceback__.tb_lineno}")
            raise
