#!/usr/bin/env python
import logging
import numpy as np
import functools


def getlogger() -> logging.Logger:
    """
    Get the pre-configured logger instance.


    """
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S %d-%m-%Y")
    logger = logging.getLogger()
    return logger


def find_nearest_value(val,
                       array,
                       larger_than_or_equal_val=True,
                       one_size_larger=False):
    """
    Finds and returns the nearest value in an array relative to the given value,
    or if one_size_larger is set to true, finds nearest value one nominal casing size larger than the given value.
    ----------------------------------------------------------------
    Input Parameters:
        val: (float) The target value to which you want to find the nearest value.
        array: (list or numpy.ndarray) The array of values in which you want to search for the nearest value.
        larger_than_or_equal_val: (bool, optional) If True, search for values larger than or equal to 'val'.
            If False, search for values strictly larger than 'val'.
        one_size_larger: (bool, optional) If True, find the nearest value one nominal casing size larger than 'val'.
            This option is only applicable when 'larger_than_or_equal_val' is True.

    ----------------------------------------------------------------
    Returns:
        (float) The nearest value in the 'array' relative to 'val'. If 'one_size_larger' is True,
        and a larger or equal value is not found, it returns the next nominal casing size larger.
    """
    # casting applied
    if larger_than_or_equal_val:
        valid_vals = array[array >
                           val] if one_size_larger else array[array >= val]
    else:
        valid_vals = array

    nearest_idx = np.argmin(np.abs(valid_vals - val))

    return valid_vals[nearest_idx]


def find_next_largest_value(val, array):
    """
    Finds the next nominal casing size larger than the given value in the array.

    ----------------------------------------------------------------
    Input Parameters:
        val: (float) The target value for which you want to find the next nominal casing size larger.
        array: (list or numpy.ndarray) The array of values in which you want to search for the next larger value.

    ----------------------------------------------------------------
    Returns:
        (float) The next nominal casing size larger than 'val' in the 'array'.
    """
    return find_nearest_value(val,
                              array,
                              one_size_larger=True)

    # TODO: read casing diameter csv, import the column in meters,
    # use round_algorithm function predefined


def validate_data(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # Check the validity of the data.
        if not self.casing_data['casing_diameter_data']:
            raise ValueError('casing_diameter_data is required.')

        if not self.depth_data:
            raise ValueError('depth_data is required.')

        # Call the decorated function.
        return func(self, *args, **kwargs)

    return wrapper


def validate(value, condition=None):
    if condition:
        return condition(value)
    return True


@classmethod
def get_all_non_boilerplate_attributes(cls):
    """Returns a list of all non-boilerplate attributes of the class.

    Returns:
        A list of strings, where each string is the name of a non-boilerplate
        attribute.
    """

    boilerplate_attribute_names = ["__class__", "__dict__", "__module__"]
    attribute_names = [attr for attr in dir(cls) if not attr.startswith(
        "__") and attr not in boilerplate_attribute_names]
    return attribute_names
