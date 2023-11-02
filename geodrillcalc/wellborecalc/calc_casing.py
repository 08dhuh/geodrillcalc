#!/usr/bin/env python3

import numpy as np
import math
#import logging
from utils import getlogger, find_next_largest_value

logger = getlogger()

#================================================================
# Stage 3. Determine parameters for each casing state

#TODO: needs to read stratigraphic depths
#TODO: calculate_pre_collar_casing_diameter might need change later
#TODO: needs to query PCD corresponding to the smallest total tubing surface area
#TODO: in calculation pipeline, make sure to query the smallest production casing

def calculate_pre_collar_depths(depth_to_aquifer_base, pre_collar_top=0):
    """
    Calculates and returns the pre-collar depth as a list [top, bottom].

    Parameters:
    - depth_to_aquifer_base: (float) Depth to the base of the aquifer in metres.
    - pre_collar_top: (float, optional) Depth to the top of the pre-collar (default: 0).

    Returns:
    - pre_collar_depths: (list) A list containing the depth to the top and bottom of the pre-collar in metres.

    ----------------------------------------------------------------
    Notes:
    - The pre-collar depth is calculated based on the depth to the aquifer base.
    - If the depth to the aquifer base is between 10.9 and 21.8 metres, the pre-collar depth is calculated as
      6 times the floor value of (1 + depth_to_aquifer_base * 11/6).
    - If the depth does not fall within the specified range, a default pre-collar depth of 12 metres is used.

    """
    if 10.9 < depth_to_aquifer_base <= 21.8:
        pre_collar_depth = 6 * math.floor(1 + depth_to_aquifer_base * 11/6)
    else:
        pre_collar_depth = 12

    pre_collar_bottom = pre_collar_top + pre_collar_depth
    return [pre_collar_top, pre_collar_bottom]


def calculate_pre_collar_casing_diameter():
    """
    Calculates and returns the pre-collar casing diameter.

    Returns:
    - pre_collar_casing_diameter: (float) Pre-collar casing diameter in metres (m).

    ----------------------------------------------------------------
    Notes:
    - The pre-collar casing diameter is 0.762 metres (30 inches) and is typically used inside a 36-inch hole.
    """
    return 0.762


def is_superficial_casing_required(depth_to_aquifer_base) -> bool:
    """
    Checks if superficial casing is required based on the depth to the aquifer base.

    Parameters:
    - depth_to_aquifer_base: (float) Depth to the base of the aquifer in metres.

    Returns:
    - required: (bool) True if superficial casing is required, False otherwise.

    ----------------------------------------------------------------
    Notes:
    - Superficial casing is considered required when the depth to the aquifer base is greater than 21.8 metres.
    - The function logs whether superficial casing is required or not using the logger.

    """
    required = depth_to_aquifer_base > 21.8
    logger.debug(f"Superficial casing is {'not ' if not required else ''}required")
    return required

def calculate_superficial_casing_depths(is_superficial_casing_required: bool, depth_to_aquifer_base=None, top=0):
    """
    Calculates and returns the depth range for superficial casing installation.

    If depth_to_aquifer_base is less than or equal to 21.8 metres, superficial casing is combined with the pre-collar, 
    and no additional drilling costs are incurred.

    Parameters:
    - is_superficial_casing_required: (bool) Indicates if superficial casing is required.
    - depth_to_aquifer_base: (float, optional) Depth to the base of the aquifer in metres (metre).
    - top: (float, optional) Depth to the top of the casing (default: 0).

    Returns:
    - depths: (list) A list containing the depth range for superficial casing installation.
      - [top, top+bottom] if superficial casing is required.
      - [np.nan, np.nan] if superficial casing is not required.

    ----------------------------------------------------------------
    Notes:
    - When superficial casing is required and the depth to the aquifer base is less than or equal to 21.8 metres, 
      it is often combined with the pre-collar, starting from the same ground level.

    """
    if is_superficial_casing_required:
        bottom = 1.1 * (depth_to_aquifer_base + 5)
        return [top, top + bottom]
    else:
        return [np.nan, np.nan]  # Not required

def calculate_pump_chamber_depths(is_pump_chamber_required: bool, pump_inlet_depth=None, top=0):
    """
    Calculates and returns the depths of the pump chamber, including the top and bottom depths.

    If a pump chamber is present, the bottom depth is the same as the pump inlet depth.

    Parameters:
    - is_pump_chamber_required: (bool) Indicates if a pump chamber is required.
    - pump_inlet_depth: (float, optional) Depth of the pump inlet in metres (m). Required if a pump chamber is present.
    - top: (float, optional) Depth to the top of the pump chamber (default: 0).

    Returns:
    - depths: (list) A list containing the top and bottom depths of the pump chamber.
      - [top, top + pump_inlet_depth] if a pump chamber is required.
      - [np.nan, np.nan] if a pump chamber is not required.

    ----------------------------------------------------------------
    Notes:
    - If a pump chamber is present, the bottom depth is the same as the pump inlet depth.

    """
    if is_pump_chamber_required:
        if pump_inlet_depth is None:
            raise ValueError('Missing argument: Pump inlet depth')
        return [top, top + pump_inlet_depth]
    return [np.nan, np.nan]

def calculate_intermediate_casing_diameter(screen_diameter, smallest_production_casing_diameter, casing_diameter_data):
    """
    Calculates the intermediate casing diameter based on the given parameters.

    This high-level function compares one case size larger than the injection or production screen diameter with the Production Casing Diameter (PCD) corresponding to the smallest total tubing surface area.

    Parameters:
    - screen_diameter: (float) Production or injection screen diameter in metres (m).
    - smallest_production_casing_diameter: (float) Smallest production casing diameter in metres (m).
    - casing_diameter_data: (list) Data containing various casing diameters.

    Returns:
    - intermediate_casing_diameter: (float) The intermediate casing diameter in metres (m).

    ----------------------------------------------------------------
    Notes:
    - Before passing arguments to this function, smallest production casing diameter must be queried as corresponding to the smallest total tubing surface area. 
    - The intermediate casing diameter is determined as the maximum value between the next largest casing diameter and the smallest production casing diameter.

    """
    intermediate_casing_diameter = max(find_next_largest_value(screen_diameter, casing_diameter_data), smallest_production_casing_diameter)
    return intermediate_casing_diameter

def is_separate_pump_chamber_required(is_production_well, intermediate_casing_diameter=None, minimum_pump_housing_diameter=None):
    """
    Determines whether a separate pump chamber is required for a well.

    Parameters:
    - is_production_well: (bool) True for production wells, False for injection wells.
    - intermediate_casing_diameter: (float, optional) Intermediate casing diameter in metres (m).
      - Will raise an error if not present for production wells. Default is None.
    - minimum_pump_housing_diameter: (float, optional) Minimum pump housing diameter in metres (m).
      - Will raise an error if not present for production wells. Default is None.

    Returns:
    - required: (bool) True if the pump chamber is required, False otherwise.

    ----------------------------------------------------------------
    Notes:
    - This function determines whether a separate pump chamber is required based on the type of well (production or injection).
    - For production wells, it checks if the minimum pump housing diameter is greater than the intermediate casing diameter to decide if a separate pump chamber is needed.

    """
    try:
        required = is_production_well and (minimum_pump_housing_diameter > intermediate_casing_diameter)
        return required
    except (TypeError, ValueError) as e:
        logger.exception(e)
        return False


def calculate_pump_chamber_diameter(minumum_pump_housing_diameter, casing_diameter_data):
    """
    Calculates the pump chamber diameter based on the minimum pump housing diameter and an array of nominal casing diameters.

    Parameters:
    - minumum_pump_housing_diameter: (float) Minimum pump housing diameter in metres (m).
    - casing_diameter_data: (list) An array of nominal casing diameters.

    Returns:
    - pump_chamber_diameter: (float) The pump chamber diameter in metres (m).

    ----------------------------------------------------------------
    Notes:
    - This function calculates the pump chamber diameter by finding the next largest value in the array of nominal casing diameters.

    """
    pump_chamber_diameter = find_next_largest_value(minumum_pump_housing_diameter, casing_diameter_data)
    return pump_chamber_diameter


def calculate_intermediate_casing_depths(depth_to_top_screen, is_separate_pump_chamber_required, intermediate_casing_top=None):
    """
    Calculates and returns the depth range for the intermediate casing.

    This high-level function determines the intermediate casing depth based on various conditions.

    Parameters:
    - depth_to_top_screen: (float) Depth to the top of the screen in metres (m).
    - is_separate_pump_chamber_required: (bool) Indicates if a separate pump chamber is required.
    - intermediate_casing_top: (float, optional) Depth to the top of the intermediate casing (default: None).

    Returns:
    - depths: (list) A list containing the top and bottom depths of the intermediate casing.

    ----------------------------------------------------------------
    Notes:
    - If a separate pump chamber is required, the intermediate casing starts at the depth determined during pump chamber calculations.
    - If no pump chamber is required, the intermediate casing starts at the surface (depth 0).

    """
    if intermediate_casing_top is None:
        if is_separate_pump_chamber_required:
            raise ValueError('Pump chamber required. Please pass pump inlet depth as the intermediate_casing_top argument')
        else:
            intermediate_casing_top = 0

    return [intermediate_casing_top, depth_to_top_screen - 10]


def calculate_screen_riser_depths(depth_to_top_screen):
    """
    Calculates and returns the depth range for the screen riser.

    Parameters:
    - depth_to_top_screen: (float) Depth to the top of the screen in metres (m).

    Returns:
    - depths: (list) A list containing the top and bottom depths of the screen riser.

    ----------------------------------------------------------------
    Notes:
    - This function calculates the depth range for the screen riser, which extends from 20 metres below the top of the screen to the top of the screen itself.
    """
    return [depth_to_top_screen - 20, depth_to_top_screen]

def calculate_screen_riser_diameter(screen_diameter):
    """
    Returns the diameter of the screen riser.
    The diameter of the screen riser is the same as the production or injection diameter.

    Parameters:
    - screen_diameter: (float) Diameter of the screen riser in metres (m).

    Returns:
    - screen_riser_diameter: (float) Diameter of the screen riser, which is the same as the production/injection diameter.

    """
    return screen_diameter

def calculate_superficial_casing_diameter(is_superficial_casing_required, diameter=None, casing_diameter_data=None):
    """
    Calculates the diameter of superficial casing based on whether it is required.

    If a pump chamber is present, the superficial casing diameter is determined by finding the next nominal standard casing larger than the pump chamber diameter. If no pump chamber is present, the superficial casing diameter is determined based on the intermediate casing diameter.

    Parameters:
    - is_superficial_casing_required: (bool) Indicates if superficial casing is required.
    - diameter: (float, optional) Diameter of the pump chamber or intermediate casing, depending on the presence of a pump chamber.
    - casing_diameter_data: (list) A list of usual casing diameters.

    Returns:
    - superficial_casing_diameter: (float) Diameter of the superficial casing.
      Returns np.nan if superficial casing is not required.

    ----------------------------------------------------------------
    Notes:
    - The determination of whether a pump chamber is required should be made in the pipeline stage.
    - When a pump chamber is present, the superficial casing diameter is the next nominal standard casing larger than the pump chamber diameter.
    - When no pump chamber is present, the superficial casing diameter is the next nominal standard casing larger than the intermediate casing diameter.

    """
    if is_superficial_casing_required:
        return find_next_largest_value(diameter, casing_diameter_data)
    else:
        return np.nan

def calculate_drill_bit_diameter(casing_stage_diameter: float, 
                                 casing_recommended_bit_dataframe):
    """
    Calculates the recommended drill bit diameter based on the casing stage diameter.

    Parameters:
    - casing_stage_diameter: (float) Diameter of the casing stage.
    - casing_recommended_bit_dataframe: DataFrame containing diameters and their corresponding recommended bits.

    Returns:
    - drill_bit_diameter: (float) Recommended drill bit diameter.

    ----------------------------------------------------------------
    Notes:
    - This function looks up the recommended drill bit diameter from the provided DataFrame based on the casing stage diameter.
    - If a matching diameter is found in the DataFrame, the corresponding recommended bit diameter is returned.
    - If there are missing or non-matching values, an error is logged, and the function returns np.nan.

    """
    col1, col2 = casing_recommended_bit_dataframe.columns
    value = casing_recommended_bit_dataframe.loc[casing_recommended_bit_dataframe[col1] == casing_stage_diameter][col2].values
    if len(value) > 0:
        return value[0]
    else:
        logger.error("Missing or non-matching values. Check arguments of calculate_drill_bit_diameter")
        return np.nan

def calculate_screen_depths(depth_to_top_screen, screen_length, aquifer_thickness):
    """
    Calculates and returns the top and bottom depths of the screen.

    Parameters:
    - depth_to_top_screen: (float) Depth to the top of the screen in metres (m).
    - screen_length: (float) Production or injection screen length in metres (m).
    - aquifer_thickness: (float) Depth difference between the Lower Tertiary Aquifer (LTA) and Lower mid-Tertiary Aquifer (LMTA) in metres (m).

    Returns:
    - depths: (list) A list containing the top and bottom depths of the screen.

    ----------------------------------------------------------------
    Notes:
    - This function calculates the top and bottom depths of the screen.
    - It checks whether the screen length is larger than the aquifer thickness and raises an error if the condition is not met.

    """
    if aquifer_thickness < screen_length:
        raise ValueError("aquifer thickness should be smaller than the screen length")
    return [depth_to_top_screen, round(depth_to_top_screen + screen_length)]

