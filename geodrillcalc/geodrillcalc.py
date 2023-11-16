#!/usr/bin/env python
from .wellbore_dict import WellBoreDict
from .calc_pipeline import CalcPipeline
from .utils.utils import getlogger


class GeoDrillCalcInterface:
    """
    A class representing the interface for calculating wellbore parameters.

    Attributes:
    - wbd: An instance of the WellBoreDict class for managing wellbore data.
    - cpl: An instance of the CalcPipeline class for performing wellbore calculations.
    - is_production_pump: A boolean indicating whether the pump used is for production (True) or injection (False).
    - logger: A logger for handling log messages in the GeoDrillCalcInterface class.

    Methods:
    - calculate_and_return_wellbore_parameters(self, is_production_pump: bool, depth_data, initial_input_data):
      Calculates wellbore parameters using WellBoreDict and CalcPipeline and returns the WellBoreDict instance.

    Example Usage:

    geo_interface = GeoDrillCalcInterface()

    result_wbd = geo_interface.calculate_and_return_wellbore_parameters(
        is_production_pump=True,
        depth_data=depth_data,
        initial_input_data=initial_values
    )

    Note: Ensure that you provide valid depth data and initial input data
    when using the 'calculate_and_return_wellbore_parameters' method.
    """

    def __init__(self, is_production_pump: bool = None):
        self.wbd = None
        self.cpl = None
        self.is_production_pump = is_production_pump or None
        self.logger = getlogger()

    def calculate_and_return_wellbore_parameters(self,
                                                 is_production_pump: bool,
                                                 depth_data,
                                                 initial_input_data):
        self._initialise(depth_data, initial_input_data)
        self.cpl = CalcPipeline(self.wbd)
        self.cpl.calc_pipeline(is_production_pump)
        self._log_outcome()
        return self.wbd

    def _initialise(self, depth_data, initial_input_data):
        if self.wbd is None:
            self.wbd = WellBoreDict()
        self.wbd.initialise_and_validate_input_data(depth_data=depth_data,
                                                    **initial_input_data)

    def _log_outcome(self):
        if not self.wbd.is_initialised or not self.wbd.calculation_completed:
            return
        for key in self.wbd.outcome_params:
            value = getattr(self.wbd, key)
            self.logger.info(f"{key}: {value}")


# if __name__ == "__main__":
#     depth_data = {
#         "aquifer_layer": [
#             "QA_UTQA",
#             "UTQD",
#             "UTAF",
#             "UTD",
#             "UMTA",
#             "UMTD",
#             "LMTA",
#             "LTA",
#             "BSE"
#         ],
#         "is_aquifer": [
#             True,
#             False,
#             True,
#             False,
#             True,
#             False,
#             True,
#             True,
#             False
#         ],
#         "depth_to_base": [
#             3,
#             53,
#             112,
#             150,
#             150,
#             1000,
#             1000,
#             1221,
#             1421
#         ]
#     }

#     initial_values = {
#         "required_flow_rate": 4320,
#         "hydraulic_conductivity": 5,
#         "average_porosity": 0.25,
#         "bore_lifetime_year": 30,
#         "groundwater_depth": 25,
#         "long_term_decline_rate": 1,
#         "allowable_drawdown": 25,
#         "safety_margin": 25
#     }
#     gdc = GeoDrillCalcInterface()
#     print("loading success")
#     gdc.calculate_and_return_wellbore_parameters(True,
#                                                  depth_data,
#                                                  initial_values)