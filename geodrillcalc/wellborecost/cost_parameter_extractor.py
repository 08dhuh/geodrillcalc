import pandas as pd
import numpy as np

from ..data_management.wellbore_data_store import WellBoreDataStore
from ..utils.utils import getlogger

class CostParameterExtractor:
    """
    A class to extract cost parameters required for wellbore construction based on a WellBoreDataStore instance.

    Attributes
    ----------
    wbd : WellBoreDataStore
        An instance of the WellBoreDataStore class containing wellbore data.
    is_production_well : bool
        Indicates whether the well is a production well or not.
    logger : Logger
        A logger instance for logging information, warnings, and errors.
    required_flow_rate : float
        The required flow rate for the well in litres per second (L/s).

    Methods
    -------
    drilling_rates_params():
        Extracts parameters for calculating drilling rates.
    time_rates_params():
        Extracts parameters for calculating time rates.
    materials_params():
        Extracts parameters for calculating materials used in wellbore construction.
    others_params():
        Extracts parameters for calculating other miscellaneous costs.

    Example
    -------
    .. code-block:: python

        wbd = WellBoreDataStore(is_production_well=True)
        extractor = CostParameterExtractor(wbd)
        drilling_params = extractor.drilling_rates_params
    """
    def __init__(self, wbd: WellBoreDataStore) -> None:
        """
        Initialises the CostParameterExtractor with a WellBoreDataStore instance.

        Parameters
        ----------
        wbd : WellBoreDataStore
            An instance of the WellBoreDataStore class containing wellbore data.
        """
        self.wbd = wbd
        self.is_production_well = wbd.is_production_well
        self.logger = getlogger()
        self.required_flow_rate = wbd.required_flow_rate_per_litre_sec

    @property
    def drilling_rates_params(self) -> dict:
        """
        Extracts parameters required for calculating drilling rates.

        Returns
        -------
        dict
            A dictionary containing the total well depth, section lengths, and section diameters for drilling rate calculations.
        """
        return {
            "total_well_depth": self._total_well_depth,
            "section_lengths": self._section_lengths,
            "section_diameters": self._get_section_diameters(outer=True) * 1000,
        }

    @property
    def time_rates_params(self) -> dict:
        """
        Extracts parameters required for calculating time rates.

        Returns
        -------
        dict
            A dictionary containing the total well depth, required flow rate, and drilling time for time rate calculations.
        """
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
            "individual_section_lengths": self._individial_section_lengths,

            "section_diameters": self._get_section_diameters(outer=False), #casing diameter
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
            "drilling_time": self._calculate_drilling_time(),
            "total_casing_length": self._individial_section_lengths.iloc[1:].sum()
        }

    @property
    def _total_well_depth(self) -> float:
        return self._section_lengths.sum()
        #return self.wbd.depth_to_top_screen + self.wbd.screen_length

    @property
    def _individial_section_lengths(self) -> pd.Series:
        try:
            st = self.wbd.casing_stage_table
            individual_section_lengths = st['bottom'].subtract(st['top'], fill_value=0).fillna(0)
            return individual_section_lengths
        except (AttributeError, KeyError) as e:
            self.logger.error(f"Error calculating individual section lengths: {e}")
            return pd.Series(dtype='float64')

    @property
    def _section_lengths(self) -> pd.Series:
        try:
            st = self.wbd.casing_stage_table
            #fill in the section column 
            section_lengths = st['bottom'].subtract(st['top'], fill_value=0).fillna(0)
            
            if not pd.isna(st.loc['superficial_casing', 'bottom']):
                section_lengths['superficial_casing'] = st.loc['superficial_casing', 'bottom'] \
                - st.loc['pre_collar', 'bottom']
                
            if not pd.isna(st.loc['pump_chamber_casing', 'bottom']):
                section_lengths['pump_chamber_casing'] = st.loc['pump_chamber_casing', 'bottom'] \
                - max(st.loc['pre_collar', 'bottom'] , st.loc['superficial_casing','bottom']) 
            
            section_lengths['intermediate_casing'] = st.loc['intermediate_casing', 'bottom'] \
                - max(st.loc['pre_collar', 'bottom'] , 
                      st.loc['superficial_casing','bottom'], 
                      st.loc['pump_chamber_casing','bottom'])
            section_lengths['screen_riser'] = st.loc['screen_riser', 'bottom'] \
                - st.loc['intermediate_casing','bottom']
            section_lengths['screen'] = st.loc['screen', 'bottom'] \
                - st.loc['screen_riser','bottom']

            #print('section_lengths:')
            #print(section_lengths)
            return section_lengths
        except (AttributeError, KeyError) as e:
            self.logger.error(f"Error calculating section lengths: {e}")
            return pd.Series(dtype='float64')

    def _get_section_diameters(self, outer: bool) -> pd.Series:
        """
        Retrieves the diameters of different well sections.

        Parameters
        ----------
        outer : bool
            If True, returns the outer diameters; if False, returns the casing diameters.

        Returns
        -------
        pd.Series
            A pandas Series containing the diameters of each well section.
        """
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
                raise ValueError(f"Negative volume detected: {volumes[volumes < 0]}")
            return volumes
        except (AttributeError, KeyError, ValueError) as e:
            self.logger.warning(f"Error calculating section annular volumes: {e}")
            #return pd.Series(dtype='float64')
            volumes[volumes < 0 ] = 0
        finally:
            return volumes

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
        """
        Calculates the number of operational sections in the well.

        Returns
        -------
        int
            The number of operational sections in the well.
        """
        try:
            st = self.wbd.casing_stage_table
            return st['casing'][st['top'].ne(0) & st['top'].notna()].nunique()
        except (AttributeError, KeyError) as e:
            self.logger.error(f"Error calculating operational section count: {e}")
            return 0

    def _calculate_drilling_time(self, base_day: float = 3.0, drilling_rate_per_day: float = 20) -> float:
        """
        Calculates the total drilling time required for the well based on drilling rates.

        Parameters
        ----------
        base_day : float, optional
            The base number of days required for setup and initial drilling (default: 3.0).
        drilling_rate_per_day : float, optional
            The drilling rate in metres per day (default: 20).

        Returns
        -------
        float
            The total drilling time required in days.

        Raises
        ------
        AssertionError
            If the drilling rate per day is not greater than 0.
        """
        try:
            assert drilling_rate_per_day > 0
            return base_day + np.ceil(self._total_well_depth / drilling_rate_per_day)
        except AssertionError as e:
            self.logger.error(f"Drilling rate per day must be greater than 0: {e}")
            return 0
