import numpy as np
import pandas as pd

def find_nearest_value(val,
                       array,
                       larger_than_or_equal_val=True,
                       one_size_larger=False):
    """
    Finds and returns the nearest value in an array relative to the given value.
    
    This function can also find the nearest value that is one nominal casing size larger than the given value, if specified.

    Parameters
    ----------
    val : float
        The target value for which the nearest value is to be found.
    array : list or numpy.ndarray
        The array of values to search for the nearest value.
    larger_than_or_equal_val : bool, optional
        If True, search for values larger than or equal to 'val'. If False, search for values strictly larger than 'val'. Default is True.
    one_size_larger : bool, optional
        If True, find the nearest value that is one nominal casing size larger than 'val'. This option is applicable only when 'larger_than_or_equal_val' is True. Default is False.

    Returns
    -------
    float
        The nearest value in the 'array' relative to 'val'. If 'one_size_larger' is True and a larger or equal value is not found, returns the next nominal casing size larger.
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

    Parameters
    ----------
    val : float
        The target value for which the next nominal casing size larger is to be found.
    array : list or numpy.ndarray
        The array of values in which to search for the next larger value.

    Returns
    -------
    float
        The next nominal casing size larger than 'val' in the 'array'.
    """
    return find_nearest_value(val,
                              array,
                              one_size_larger=True)


def query_diameter_table(val:float, 
                         table:pd.DataFrame, #wbd's drillling or casing table
                         metric_column:str='metres', #'inches' or 'metres'
                         query_param_column_id:int = 2): #2 is the default for wbd's drilling/casing table
    """
    Queries a diameter table to find a recommended bit size based on the given value.

    Parameters
    ----------
    val : float
        The value to search for in the 'metric_column' of the table.
    table : pandas.DataFrame
        A DataFrame containing drilling or casing diameter data.
    metric_column : str, optional
        The column name to query for 'val'. Default is 'metres'.
    query_param_column_id : int, optional
        The column index from which to retrieve the recommended bit size. Default is 2.

    Returns
    -------
    float
        The recommended bit size corresponding to the provided 'val'.

    Raises
    ------
    ValueError
        If no matching value is found in the 'metric_column'.
    KeyError
        If the specified 'metric_column' does not exist in the table.
    IndexError
        If the 'query_param_column_id' is out of the DataFrame's column index range.
    RuntimeError
        If an unexpected error occurs during the query.
    """
    try:
        matching_row = table[table[metric_column] == val]
        if matching_row.empty:
            raise ValueError(f"No match found for value {val} in column '{metric_column}'")
        recommended_bit = matching_row.iloc[0,query_param_column_id]
        return recommended_bit        
    except KeyError as e:
        raise KeyError(f"Column '{metric_column}' does not exist in the table. Details: {e}")
    except IndexError as e:
        raise IndexError(f"The DataFrame does not have a column {query_param_column_id+1}. Details: {e}")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {e}")


def validate(value, condition=None):
    """
    Validates a given value based on a condition.

    Parameters
    ----------
    value : Any
        The value to be validated.
    condition : callable, optional
        A function or lambda that takes a single argument and returns True or False.

    Returns
    -------
    bool
        True if the value meets the condition or if no condition is provided; False otherwise.
    """
    if condition:
        return condition(value)
    return True
