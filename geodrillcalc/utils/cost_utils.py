import pandas as pd


def calculate_costs_with_df(base_values: dict, 
                            margin_functions_df: pd.DataFrame, 
                            index_labels: list) -> pd.DataFrame:

    df = pd.DataFrame(columns=['low', 'base', 'high'], index=index_labels)

    for label in index_labels:
        base_value = base_values.get(label, 0)
        df.at[label, 'base'] = base_value
        if label in margin_functions_df.index:
            low_func = margin_functions_df.at[label, 'low']
            high_func = margin_functions_df.at[label, 'high']
            df.at[label, 'low'] = low_func(base_value)
            df.at[label, 'high'] = high_func(base_value)
        else:
            df.at[label, 'low'] = base_value
            df.at[label, 'high'] = base_value

    return df

def populate_margin_functions(mar:pd.DataFrame | dict) -> pd.DataFrame:
    if isinstance(mar, dict):
        mar = pd.DataFrame(mar)
    df = pd.DataFrame()
    for label in mar.index:
        rate_or_float:bool = mar.at[label, 'rate_or_float']
        if rate_or_float: #rate
            df.at[label, 'low'] = lambda x: x * mar.at[label, 'lower']
            df.at[label, 'high'] = lambda x: x * mar.at[label, 'higher']
        else: #float
            df.at[label, 'low'] = lambda x: x + mar.at[label, 'lower'] # should be negative
            df.at[label, 'high'] = lambda x: x + mar.at[label, 'higher']

    return df