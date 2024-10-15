import pandas as pd
from .utils import getlogger

logger = getlogger()

def initialise_aquifer_layer_table(aquifer_layer_table):
        if not isinstance(aquifer_layer_table, pd.DataFrame):
            try:
                aquifer_layer_table_pd = pd.DataFrame(aquifer_layer_table)
            except ValueError as e:
                logger.error(e)
                raise e
        else:
            aquifer_layer_table_pd = aquifer_layer_table.copy()
        columns = ["aquifer_layer", "is_aquifer", "depth_to_base"]
        aquifer_layer_table_pd.columns = columns
        aquifer_layer_table_pd = aquifer_layer_table_pd.set_index(
            "aquifer_layer")
        return aquifer_layer_table_pd