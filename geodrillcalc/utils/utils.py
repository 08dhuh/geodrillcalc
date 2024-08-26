#!/usr/bin/env python
import pandas as pd
import numpy as np
import logging, json

logger=None

def getlogger(log_level='INFO') -> logging.Logger:
    """
    Gets a pre-configured logger instance.

    Parameters
    ----------
    log_level : str, optional
        The logging level as a string, default is 'INFO'. Possible values include 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'.

    Returns
    -------
    logger : logging.Logger
        The configured logger instance.

    Notes
    -----
    The logger instance is globally defined and will be re-used across multiple calls to avoid re-configuration.
    """
    global logger
    if logger is None:
        logger = logging.getLogger(__name__)
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=numeric_level, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S %d-%m-%Y")
    return logger


def serialize_results(obj, keys, to_json: bool = True):
    """
    Serialises the specified attributes of an object.

    This function serialises specified attributes of an object, converting them to either a JSON string or 
    a Python dictionary. It handles both single-indexed and MultiIndex pandas DataFrames, converting them 
    appropriately.

    Parameters
    ----------
    obj : object
        The object from which attributes will be serialized.
    keys : list
        A list of attribute names to be serialized.
    to_json : bool, optional
        If True, the function converts DataFrames to JSON strings. If False, it returns dictionaries, 
        by default True.

    Returns
    -------
    results : dict
        A dictionary containing the serialized attributes.

    Notes
    -----
    - The function replaces NaN values with None to ensure JSON compatibility.
    - MultiIndex DataFrames are flattened and converted into a list of dictionaries.
    """
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

    Parameters
    ----------
    cls : class
        The class from which attributes are to be extracted.

    Returns
    -------
    list
        A list of strings, where each string is the name of a non-boilerplate attribute.

    Notes
    -----
    - The function excludes attributes starting with an underscore and certain standard attributes like '__class__' and '__module__'.
    """
    boilerplate_attribute_names = ["__class__", "__dict__", "__module__"]
    attribute_names = [attr for attr in dir(cls) if not attr.startswith(
        "_") and attr not in boilerplate_attribute_names]
    return attribute_names
