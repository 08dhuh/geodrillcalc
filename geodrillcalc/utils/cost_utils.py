import importlib.resources
import pandas as pd
import os

def calculate_costs_with_df(base_values: dict, 
                            margin_functions: pd.DataFrame, 
                            index_labels: list) -> pd.DataFrame:
    """
    Calculates the costs for different components using base values and margin functions.

    This function generates a DataFrame with cost estimates for each component, including
    low, base, and high estimates based on provided margin functions.

    Parameters
    ----------
    base_values : dict
        A dictionary containing base cost values for each component. Keys are component names, 
        and values are the base costs.
    margin_functions : pandas.DataFrame
        A DataFrame containing margin functions for calculating low and high cost estimates.
        The DataFrame should have a MultiIndex with 'stage' and 'component' and columns 'low' and 'high'.
    index_labels : list
        A list of component names to be used as the index for the resulting DataFrame.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing the low, base, and high cost estimates for each component.
        The index of the DataFrame corresponds to the components, and columns are 'low', 'base', and 'high'.

    Notes
    -----
    If a component does not have an associated margin function, the low and high costs will 
    default to the base cost value.
    """
    df = pd.DataFrame(columns=['low', 'base', 'high'], index=index_labels)

    for label in index_labels:
        base_value = base_values.get(label, 0)
        df.at[label, 'base'] = base_value
        if label in margin_functions.index:
            low_func = margin_functions.at[label, 'low']
            high_func = margin_functions.at[label, 'high']
            df.at[label, 'low'] = low_func(base_value)
            df.at[label, 'high'] = high_func(base_value)
        else:
            df.at[label, 'low'] = base_value
            df.at[label, 'high'] = base_value

    return df

def populate_margin_functions(margin_dict: dict) -> pd.DataFrame:
    """
    Creates a DataFrame of margin functions based on the provided margin dictionary.

    This function builds a DataFrame that stores lambda functions for calculating 
    low and high margins for cost estimates based on the input dictionary.

    Parameters
    ----------
    margin_dict : dict
        A dictionary where keys are stages and values are dictionaries. Each inner dictionary 
        contains components as keys and a dictionary with margin calculation parameters as values.
        Margin calculation parameters include 'low', 'high', and 'is_rate_based' indicating whether 
        the margin is a rate or a fixed amount.

    Returns
    -------
    pandas.DataFrame
        A DataFrame indexed by a MultiIndex of 'stage' and 'component', with 'low' and 'high' 
        columns containing lambda functions for calculating margins.

    Notes
    -----
    The lambda functions stored in the DataFrame are used to calculate the low and high cost estimates
    based on whether the margin is rate-based or an absolute value.
    """
    stages = list(margin_dict.keys())
    components = [list(inner_dict.keys()) for inner_dict in margin_dict.values()]

    # Pre-allocate the DataFrame with the correct MultiIndex for better performance
    index = pd.MultiIndex.from_tuples(
        [(stage, component) for stage, components_list in zip(stages, components) for component in components_list],
        names=["stage", "component"]
    )
    pd1 = pd.DataFrame(index=index, columns=['low', 'high'])

    for stage, inner_dict in margin_dict.items():
        for component, values in inner_dict.items():
            for col in ['low', 'high']:
                pd1.loc[(stage, component), col] = (
                    lambda x, r=values, c=col: x * r[c] if r['is_rate_based'] else x + r[c]
                )

    return pd1


def get_data_path(filename: str) -> str:
    """
    Constructs a full file path for a given filename within the data directory.

    This function returns the absolute path to a file located in the 'data' directory,
    which is assumed to be one level above the directory of this script.

    Parameters
    ----------
    filename : str
        The name of the file for which the path is to be constructed.

    Returns
    -------
    str
        The absolute path to the specified file in the 'data' directory.

    Notes
    -----
    This function assumes that the 'data' directory is located one level above the directory
    where this script is located.
    """
    try:
        data_path = importlib.resources.files('geodrillcalc.data') / filename
        if not data_path.exists():
            raise FileNotFoundError
        return str(data_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"The file '{filename}' was not found in the 'data' directory.") from e
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred while trying to access '{filename}'.") from e
