#!/usr/bin/env python
import logging

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
