import pandas as pd
import numpy as np

from ..wellbore_dict import WellBoreDict
from ..utils.utils import getlogger

class CostParameterExtractor:
    def __init__(self, wbd: WellBoreDict) -> None:
        self.wbd = wbd
        self.is_production_well = wbd.is_production_well
        self.logger = getlogger()
        self.required_flow_rate = wbd.required_flow_rate_per_litre_sec

    @property
    def drilling_rates_params(self) -> dict:
        return {
            "total_well_depth": self._total_well_depth,
            "section_lengths": self._section_lengths,
            "section_diameters": self._get_section_diameters(outer=True) * 1000,
        }

    @property
    def time_rates_params(self) -> dict:
        return {
            "total_well_depth": self._total_well_depth,
            "required_flow_rate": self.required_flow_rate,
            "drilling_time": self._calculate_drilling_time()
        }

    @property
    def materials_params(self) -> dict:
        return {
            "total_well_depth": self._total_well_depth,
            "section_lengths": self._section_lengths,
            "section_diameters": self._get_section_diameters(outer=True),
            "section_excavation_volumes": self._section_excavation_volumes,
            "total_gravel_volume": self._total_gravel_volume,
            "total_cement_volume": self._total_cement_volume,
            "operational_section_count": self._operational_section_count
        }

    @property
    def others_params(self) -> dict:
        return {
            "total_well_depth": self._total_well_depth,
            "section_lengths": self._section_lengths,
            "drilling_time": self._calculate_drilling_time()
        }

    @property
    def _total_well_depth(self) -> float:
        return self.wbd.depth_to_top_screen + self.wbd.screen_length

    @property
    def _section_lengths(self) -> pd.Series:
        try:
            st = self.wbd.casing_stage_table
            return st['bottom'].subtract(st['top'], fill_value=0).fillna(0)
        except (AttributeError, KeyError) as e:
            self.logger.error(f"Error calculating section lengths: {e}")
            return pd.Series(dtype='float64')

    def _get_section_diameters(self, outer: bool) -> pd.Series:
        try:
            st = self.wbd.casing_stage_table
            return st['drill_bit'] if outer else st['casing']
        except (AttributeError, KeyError) as e:
            self.logger.error(f"Error retrieving section diameters: {e}")
            return pd.Series(dtype='float64')

    @property
    def _section_excavation_volumes(self) -> pd.Series:
        try:
            lengths = self._section_lengths
            radii = self._get_section_diameters(outer=True) / 2
            return np.pi * radii**2 * lengths
        except (AttributeError, KeyError) as e:
            self.logger.error(f"Error calculating section volumes: {e}")
            return pd.Series(dtype='float64')

    @property
    def _section_annular_volumes(self) -> pd.Series:
        try:
            lengths = self._section_lengths
            outer_radii = self._get_section_diameters(outer=True) / 2
            inner_radii = self._get_section_diameters(outer=False) / 2
            volumes = np.pi * (outer_radii**2 - inner_radii**2) * lengths
            if volumes.min() < 0:
                raise ValueError(f"Negative volume detected: {volumes.min()}")
            return volumes
        except (AttributeError, KeyError, ValueError) as e:
            self.logger.error(f"Error calculating section annular volumes: {e}")
            return pd.Series(dtype='float64')

    @property
    def _total_cement_volume(self) -> float:
        try:
            return self._section_annular_volumes.drop(['screen_riser', 'screen'], errors='ignore').sum()
        except (AttributeError, KeyError) as e:
            self.logger.error(f"Error calculating gravel volumes: {e}")
            return 0

    @property
    def _total_gravel_volume(self) -> float:
        try:
            return self._section_annular_volumes.get('screen', 0)
        except (AttributeError, KeyError) as e:
            self.logger.error(f"Error calculating cement volumes: {e}")
            return 0

    @property
    def _operational_section_count(self) -> int:
        try:
            st = self.wbd.casing_stage_table
            return st['casing'][st['top'].ne(0) & st['top'].notna()].nunique()
        except (AttributeError, KeyError) as e:
            self.logger.error(f"Error calculating operational section count: {e}")
            return 0

    def _calculate_drilling_time(self, base_day: float = 3.0, drilling_rate_per_day: float = 20) -> float:
        try:
            assert drilling_rate_per_day > 0
            return base_day + self._total_well_depth / drilling_rate_per_day
        except AssertionError as e:
            self.logger.error(f"Drilling rate per day must be greater than 0: {e}")
            return 0
