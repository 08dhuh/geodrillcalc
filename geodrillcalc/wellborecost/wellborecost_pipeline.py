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
		wellbore_cost_summary = {
			'base': None,
			'error_margins': {
				'low': None,
				'high': None
			}
		}
		return wellbore_cost_summary
