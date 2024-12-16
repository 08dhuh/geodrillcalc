import pandas as pd
from ..exceptions import (
    GeodrillCalcError,
    MissingDataError,
    InvalidGroundwaterLayerError,
    ShallowLTAError,
)

def check_initial_calculation_feasibility(layer_df:pd.DataFrame,
                                          target_top_layers=None,
                                          target_layer='111lta'):
    # TODO: implement check
    """
    Perform validation checks for the geology of the layers.
    Raises exceptions When the aquifer layer data is empty,
    """
    if target_top_layers is None:
        target_top_layers = ['100qa', '102utqa']

    #data should not be empty
    layers = layer_df.index.tolist()


    if len(layers) == 0:
        raise MissingDataError("Aquifer layer data is empty.")
        #raise ValueError('Aquifer layer data is empty')
    
    #top layer validation 
    top_layer = layers[0]
    if top_layer not in target_top_layers:
        # Special case: Shallow LTA layer
        if top_layer == target_layer:
            raise ShallowLTAError(
                 f"Top layer '{top_layer}' is too shallow to be drilled."
            )
        raise InvalidGroundwaterLayerError(
            f"Top layer '{top_layer}' is invalid. Expected one of {target_top_layers}."
        )
        #raise ValueError(f'Aquifer Validation Error: Top layer is {top_layer}, which is not an aquifer layer.')

    #target layer must be present in the data
    if target_layer not in layers:
        raise InvalidGroundwaterLayerError(f'Aquifer Validation Error: {target_layer} not present in the aquifer layers: {layers}')
    
    #target layer is not the bottommost layer
    target_index=layer_df.index.get_loc(
            target_layer)
    if target_index >= len(layers) - 1:
        raise InvalidGroundwaterLayerError(
                 f"Target aquifer '{target_layer}' is the bottommost layer, which is an invalid design.")
    
    #depth_to_base values are not monotonically increasing
    if 'depth_to_base' in layer_df.columns:
        depths = layer_df['depth_to_base'].tolist()
        for i in range(1, len(depths)):
            if depths[i] <= depths[i - 1]:
                raise InvalidGroundwaterLayerError(
                    f"Depth to base is not monotonically increasing at index {i}: "
                    f"layer '{layers[i]}' has depth {depths[i]}m, "
                    f"but the previous layer '{layers[i - 1]}' has depth {depths[i - 1]}m."
                )
    else:
        raise MissingDataError("The 'depth_to_base' column is missing in the aquifer data.")
    
    return True


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



