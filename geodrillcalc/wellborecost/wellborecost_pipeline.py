from ..wellbore_dict import WellBoreDict

from  .cost_parameter_extractor import CostParameterExtractor
from .stage4_calc_cost import WellboreCostCalculator
from ..utils.utils import getlogger

logger = getlogger()


class CostCalculationPipeline:
    """
    A class designed to estimate wellbore installation cost based on the wellbore model parameters calculated in the previous stages.

    cost calculation
    comprises of 4 separate steps

    """

    def __init__(self, 
                 wbd:WellBoreDict,
                 cost_rates,
                 margins=None) -> None:
        self.wbd = wbd
        self.stage_labels = ['drilling_rates',
                             'time_rates',
                             'materials',
                             'others']
        self._wellbore_params = None
        self.cost_rates = cost_rates
        self.margins = margins

    @property	
    def wellbore_params(self):
        if not self._wellbore_params:
            cpe = CostParameterExtractor(self.wbd)
            param_dict = {}		
            for label in self.stage_labels:
                param_dict[label] = getattr(cpe, f"{label}_params")
            self._wellbore_params = param_dict
        return self._wellbore_params


    def calc_pipeline(self):
        """
        Executes the cost calculation pipeline, returning the total cost table and cost estimation table.
        """
        wellbore_cost_calculator = WellboreCostCalculator(
            cost_rates=self.cost_rates,
            wellbore_params=self.wellbore_params,
            margins_dict=self.margins,
            stage_labels=self.stage_labels
        )
        wellbore_cost_calculator.calculate_total_cost()
        return wellbore_cost_calculator.total_cost_table, wellbore_cost_calculator.cost_estimation_table
