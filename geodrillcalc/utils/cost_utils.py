import pandas as pd
import os

def calculate_costs_with_df(base_values: dict, 
                            margin_functions: pd.DataFrame, 
                            index_labels: list) -> pd.DataFrame:
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
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, '..', 'data')
    return os.path.join(data_dir, filename)
