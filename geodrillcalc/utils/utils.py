#!/usr/bin/env python
import pandas as pd
import numpy as np
import logging, json

logger=None

def getlogger(log_level='INFO') -> logging.Logger:
    """
    Get the pre-configured logger instance.

    Parameters:
    - log_level: str (default: 'INFO')
        The logging level as a string. Possible values: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'.
    
    Returns:
    - logger: logging.Logger
        The configured logger instance.
    """
    global logger
    if logger is None:
        logger = logging.getLogger(__name__)
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=numeric_level, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S %d-%m-%Y")
    return logger

# def save_df_to_dict(obj, 
#                     keys,
#                     to_json:bool=True):
#     results = {}
#     for key in keys:
#         value = getattr(obj, key)
#         if isinstance(value, pd.DataFrame):
#             # json compatible
#             value = value.replace(np.nan, None)
#             if to_json:
#                 results[key] = value.to_json()
#                 continue
#         results[key] = value
#     return results

def serialize_results(obj, keys, to_json: bool = True):
    results = {}
    for key in keys:
        value = getattr(obj, key)
        if isinstance(value, pd.DataFrame):
            # Handle double-indexed (MultiIndex) DataFrame
            if isinstance(value.index, pd.MultiIndex):
                # Convert MultiIndex DataFrame to a dictionary and handle NaNs
                value_dict = value.reset_index().replace(np.nan, None).to_dict(orient='records')
                if to_json:
                    results[key] = json.dumps(value_dict)
                else:
                    results[key] = value_dict
            else:
                # Handle single-indexed DataFrame
                value = value.replace(np.nan, None)
                if to_json:
                    results[key] = value.to_json()
                else:
                    results[key] = value
        else:
            results[key] = value
    return results


def get_all_non_boilerplate_attributes(cls):
    """Returns a list of all non-boilerplate attributes of the class.

    Returns:
        A list of strings, where each string is the name of a non-boilerplate
        attribute.
    """

    boilerplate_attribute_names = ["__class__", "__dict__", "__module__"]
    attribute_names = [attr for attr in dir(cls) if not attr.startswith(
        "_") and attr not in boilerplate_attribute_names]
    return attribute_names
