import pandas as pd

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

    # Pre-allocate the DataFrame with the correct MultiIndex
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

# def populate_margin_functions(margin_dict: dict) -> dict:
#     if isinstance(margin_dict, dict):
#         mar_dic = {}
#         for key, item in margin_dict.items():
#             mar_dic[key] = pd.DataFrame(item, index=[key])
#     df = {}
#     for key, item in mar_dic.items():
#         mar = mar_dic[key] #dataframe
#         df_label = pd.DataFrame(columns=['low','high'], index=item.index)
#         for col in df_label.columns: #col: low, high
#             df_label[col] = mar.apply( lambda row: \
#                               lambda x: x * row[col] if row['is_rate_based'] 
#                               else lambda x: x + row[col] 
#                            ,axis=1)
#         df[key] = df_label
#     return df

