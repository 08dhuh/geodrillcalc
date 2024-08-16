from ..wellbore_dict import WellBoreDict

from ..utils.utils import getlogger


class CostParameterExtractor:

    def __init__(self,
                 wbd: WellBoreDict,
                 is_production_well: bool) -> None:
        self.wbd = wbd
        self.is_production_well = is_production_well
        self.logger = getlogger()

    # step 1. drilling rates
    def get_drilling_rate_params(self):
        """
        Extracts parameters needed for calculating drilling costs.

        Returns:
            dict: A dictionary containing drilling cost parameters.
        """
        drilling_params = {}
        return drilling_params

    # step 2. time rates
    def get_time_rate_params(self):
        time_params = {}
        return time_params

    # step 3. material costs
    def get_material_cost_params(self):
        meterial_params = {}
        return meterial_params

    # step 4. other costs
    def get_other_cost_params(self):
        other_params = {}
        return other_params
