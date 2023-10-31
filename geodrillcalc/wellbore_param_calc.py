import numpy as np
import math
#import logging
from utils import getlogger, find_next_largest_value

logger = getlogger()


def is_water_corrosive(temperature_k:float, 
                       pH:float, 
                       calcium_ion_concentration:float,
                       carbonate_ion_concentration:float,
                       total_dissolved_solids:float) -> float:
    """
    Calculates the Langelier Saturation Index (LSI) of geothermal water.
    
    --------------------------------------------------------
    Input Parameters
        temperature_k: (float) temperature of the water as Kelvin, must be in the range of 273 <= T <=363
        pH: (float) pH of the water
        calcium_ion_concentration: (float) calcium ion concentration as ppm
        carbonate_ion_concentration: (float) carbonate ion concentration as
        total_dissolved_solids: (float) TDS (ppm)

    --------------------------------------------------------
    Returns:
        LSI: (float) Langelier saturation index(LSI)
    """
    #TODO: Check if the temperature input is in the valid range
    
    K_potenz = lambda coeff, t: np.dot(coeff, [1, t, -1/t,-np.log10(t), 1/t**2])
    pK2_coeff = [107.8871, .03252849, 5151.79, 38.92561, 563713.9]
    pKsc_coeff = [171.9065,0.077993,2839.319,71.595,0]
    
    pK2 = K_potenz(pK2_coeff, temperature_k)
    logger.info(f'pk2: {pK2}')
    pKsc = K_potenz(pKsc_coeff, temperature_k)
    logger.info(f'pKsc: {pKsc}')
    pCa2 = -np.log10(calcium_ion_concentration/(1000*40.08))
    pHCO3 = -np.log10(carbonate_ion_concentration/(1000*61.0168))
    ionic_strength = total_dissolved_solids/40000
    dielectric_stength = 60954/(temperature_k+116) - 68.937
    alkalinity = 1.82*10**6*(dielectric_stength*temperature_k)**(-1.5)
    pfm = alkalinity*(np.sqrt(ionic_strength)/(1+np.sqrt(ionic_strength))-.31) #activity coefficient for monovalent species at the specified temperature
    pHs = pK2 - pKsc + pCa2 + pHCO3 + 5*pfm #pH of saturation, or the pH at which water is saturated with CaCO3
    LSI = pH - pHs

    return LSI

#================================================================
# Stage 1. Define parameters for screened interval
#TODO: test with the whole casing diameter list

def calculate_minimum_screen_length(req_flow_rate:float,
                                    hyd_conductivity:float,                                    
                                    bore_lifetime:float,                                    
                                    thickness:float,
                                    is_injection_bore:bool,
                                    drawdown:float=25,
                                    bore_radius:float=.0762,
                                    specific_storage:float=2*10**(-4),) -> float:
    """
    Determines the minimum screen length, SL (m)
    based on Eq 4 at http://quebec.hwr.arizona.edu/classes/hwr431/2006/Lab6.pdf
    If it is an injection bore, screen length is multiplied by 2.0 
    and capped at total aquifer thickness.      
    --------------------------------------------------------
    Input Parameters
        i.	Required flow rate, Q (m3/day)
        ii.	Aquifer hydraulic conductivity, K (m/day)
        iii. Bore/project lifetime, t (days)
        iv. Aquifer thickness, Z (m)
        v.	Production or injection bore? 
        vi.	Allowable drawdown, Sw (m) default: Sw = 25 m
        vii.	Bore radius, r (m) , default: r = 0.0762 m (3”)
        viii.	Aquifer specific storage, Ss (m-1) , default: Ss = 2x10-4 m-1

    --------------------------------------------------------
    Returns
        SL: (float) nominal value of the minimum screen length (metres)
        error: (tuple) lower and upper limits representing the uncertainty bounds
    """
    #
    SL = (2.3*req_flow_rate/ (4*np.pi*hyd_conductivity*drawdown)) \
             * np.log10(2.25*hyd_conductivity*bore_lifetime/(bore_radius**2 * specific_storage))
    if is_injection_bore: SL *= 2
    SL = min(SL, thickness)
    error_lower = SL * .9
    error_upper = min(SL * 1.1, thickness)

    return SL, (error_lower, error_upper)


def calculate_casing_friction(depth_to_top_screen:float,
                              req_flow_rate:float,
                              prod_casing_diameter:float,
                              pipe_roughness_coeff:float=100.):
    """
    Estimates production casing friction loss above aquifer
    for nominal diameters (e.g. 101.6, 127, 152.4, 203.2, 254, 304.8 mm)

    ----------------------------------------------------------------
    Input Parameters:
        depth_to_top_screen: (float) Depth to top of screen in metres (m).
        req_flow_rate: (float) Required flow rate in cubic metres per second (m^3/s).
        prod_casing_diameter: (float) Production casing diameter in metres (m).
        pipe_roughness_coeff: (float) Pipe roughness coefficient, default: 100 for steel

    ----------------------------------------------------------------
    Returns:
        hfpc: (float) production casing friction loss (metres)
    """
    hfpc = (10.67*depth_to_top_screen*req_flow_rate**1.852)/(pipe_roughness_coeff**1.852 * prod_casing_diameter**4.8704)
    return hfpc

#TODO: in the pipeline, should be rounded
def calculate_minimum_screen_diameter(up_hole_friction:float,
                                      screen_length:float,
                                      req_flow_rate:float,
                                      pipe_roughness_coeff:float=100.):
    """
    Determines the minimum screen diameter, SDmin (m), using the Hazen-Williams equation to ensure up-hole friction is less than 20 m.
    Reference: https://en.wikipedia.org/wiki/Hazen%E2%80%93Williams_equation#SI_units

    Parameters:
    - up_hole_friction: (float) Up-hole friction in m. Must be smaller than 20; otherwise, np.nan is returned.
    - screen_length: (float) Length of the screen in metres (m).
    - prod_casing_diameter: (float) Production casing diameter in metres (m).
    - req_flow_rate: (float) Required flow rate in seconds (m^3/s).
    - pipe_roughness_coeff: (float, optional) Pipe roughness coefficient, default: 100.

    Returns:
    - d: (float) Minimum screen diameter (SDmin) in metres (m) to ensure up-hole friction is less than 20. 
    Returns np.nan if up-hole friction is smaller than 20.

    ----------------------------------------------------------------
    Notes:
    - The Hazen-Williams equation is used to calculate friction loss in a pipe.
    - The minimum screen diameter is determined to ensure that the up-hole friction does not exceed 20 m.
    """

    try:
        if up_hole_friction > 20:
            logger.debug(f"{up_hole_friction} Up-hole friction is too high")
            return np.nan
            #raise ValueError("Up-hole friction is too high")
        d = (10.67 * screen_length * req_flow_rate**1.852)\
        / (2*pipe_roughness_coeff**1.852*(20-up_hole_friction))
        d **= 1/4.8704
        return d
    except ValueError as e:
        logger.exception(e)
        return np.nan
    
def calculate_total_casing(prod_casing_diameter:float,
                           screen_diameter,
                           intermediate_casing:float,
                           screen_length:float
                           ) -> float:
    """
    Calculates the total casing length required, including production casing and screen, based on given parameters.

    ----------------------------------------------------------------
    Parameters:
        prod_casing_diameter: (float) Production casing diameter in metres.
        screen_diameter: (float or np.nan) Screen diameter in metres.
        intermediate_casing: (float) Length of intermediate casing, typically (LMTA - 10) in metres.
        screen_length: (float) Length of the production screen in metres.

    ----------------------------------------------------------------
    Returns:
        (float) Total casing length required in metres.
        or np.nan if the screen diameter is an invalid value or greater than the production casing diameter.
    
    """
    nanflag = False
    if prod_casing_diameter <= screen_diameter:
        logger.debug(f"{prod_casing_diameter} <= {screen_diameter}: Production casing diameter must be greater than the screen diameter for a valid result.")
        nanflag = True
    if np.isnan(screen_diameter):
        logger.debug(f"input is nan")
        nanflag = True
    if nanflag: return np.nan
    total_casing = intermediate_casing * np.pi * prod_casing_diameter + \
            screen_length * np.pi * screen_diameter
    return total_casing
    # try:
    #     if prod_casing_diameter <= screen_diameter:
    #         raise ValueError(
    #             "Production casing diameter must be greater than the screen diameter")
    #     total_casing = intermediate_casing * np.pi * prod_casing_diameter + \
    #         screen_length * np.pi * screen_diameter
    #     return total_casing
    # except ValueError as e:
    #     logger.error(e)


def calculate_minimum_open_hole_diameter(req_flow_rate_sec,
                                screen_length,
                               sand_face_velocity,
                               reservoir_porosity,
                               ngr_aquifer=1
                               ):
    """
    Defines variable values to calculate open hole diameter (OHD):
        i. Q = required flow rate (m^3/s)
        ii. 𝜙 = average reservoir porosity (0–1)
        iii. NGR = net-to-gross ratio for the aquifer, default: 1 (K for Gippsland aquifer units is already averaged)
        iv. SL = screen length (m) from Step 3

    Input Parameters:
        req_flow_rate_sec: (float) Required flow rate in cubic metres per second (m^3/s).
        screen_length: (float) Length of the production or injection screen in metres (m).
        sand_face_velocity: (float) Sand face velocity in m/s.
        reservoir_porosity: (float) Average reservoir porosity (0–1).
        ngr_aquifer: (float, optional) Net-to-gross ratio for the aquifer, default: 1 (K for Gippsland aquifer units is already averaged).

    Returns:
        ohd_min: (float) Minimum open hole diameter (OHD) required to meet the specified flow rate, in metres (m).

    Notes:
        - The sand face velocity is the ratio of flow rate to (0.01 * π * screen length * porosity).
        - NGR (Net-to-Gross Ratio) is used to account for the proportion of porous reservoir rock in the aquifer.
    """
    # TODO: prod/injection : sand face velocity differs
    # sand face velocity
    # iii.	NGR = net-to-gross ratio for aquifer = 1 (K for Gippsland aquifer units is already averaged)
    # input porosity / flow rate(sec) / injection or prod screen length
    # flow / (0.01 * pi * sl * porosity)
    ohd_min = req_flow_rate_sec  / \
         (sand_face_velocity * np.pi * reservoir_porosity * ngr_aquifer * screen_length)
    return ohd_min


#================================================================
# Stage 2. Define pump parameters

# TODO: do we need a method for determining the safety margin?


def assign_pump_diameter(req_flow_rate_sec,):
                         #diameter_range=None,
                         #flow_rate_conditions=None):
    """
    Assigns pump diameter based on the required flow rate.

    By default:
    a. 0.10 (4-inch) diameter for flow rates less than 5 L/s.
    b. 0.15 (6-inch) diameter for flow rates between 5 L/s and 10 L/s.
    c. 0.20 (8-inch) diameter for flow rates between 10 L/s and 50 L/s.
    d. 0.25 (10-inch) diameter for flow rates between 50 L/s and 70 L/s.
    e. 0.30 (12-inch) diameter for flow rates greater than 70 L/s.

    Assumes a standard pump type.

    Parameters:
        req_flow_rate_sec: (float) Required flow rate in litres per second (L/s).
        diameter_range: (list, optional) Custom range of diameters to use for assignment.
        flow_rate_conditions: (list, optional) Custom flow rate conditions for diameter assignment.

    Returns:
        (float) Assigned pump diameter, P (m), based on the required flow rate.

    ----------------------------------------------------------------
    Notes:
    - The default diameter assignments are based on typical flow rate ranges.
    - The function assumes a standard pump type.
    """
    inches_to_metre = .0254

    if req_flow_rate_sec < 0:
        raise ValueError('invalid flow rate input for pump diameter')
    if req_flow_rate_sec < 5:
        diameter = 4
    elif req_flow_rate_sec < 10:
        diameter = 6
    elif req_flow_rate_sec < 50:
        diameter = 8
    elif req_flow_rate_sec < 70:
        diameter = 10
    else:
        diameter = 12
    return diameter * inches_to_metre  # TODO: is this in inches?

def calculate_safety_margin(groundwater_depth, allowable_drawdown):
    """
    Calculates the safety margin, M (m), for groundwater drawdown.

    ii. M = the larger of 10 m or [0.2 * (WD + Sw)] m

    Parameters:
    - groundwater_depth: (float) Depth of the groundwater table in meters (WD).
    - allowable_drawdown: (float) Allowable drawdown in meters (Sw).

    Returns:
    - M: (float) The safety margin, M (m), for groundwater drawdown.

    ----------------------------------------------------------------
    Notes:
    - The safety margin is determined by taking the larger value between 10 metres and 0.2 times the sum
      of the groundwater depth (WD) and allowable drawdown (Sw).
    """
    return max(10, 0.2 * (groundwater_depth + allowable_drawdown))

def calculate_pump_inlet_depth(groundwater_depth, allowable_drawdown, safety_margin, long_term_decline_rate, bore_lifetime):
    """
    Calculates the pump inlet depth for a groundwater pumping system.

    i. Present water depth relative to the ground, WD (m)
    ii. Allowable drawdown, Sw (m)
    iii. Safety margin, M (m)
    iv. Long-term decline rate in water level, dS/dt (m/year)
    v. Bore/project lifetime, t (years)

    Parameters:
    - groundwater_depth: (float) Present water depth relative to the ground in metres (WD).
    - allowable_drawdown: (float) Allowable drawdown in metres (Sw).
    - safety_margin: (float) Safety margin in metres (M).
    - long_term_decline_rate: (float) Long-term decline rate in water level in metres per year (dS/dt).
    - bore_lifetime: (float) Bore/project lifetime in years (t).

    Returns:
    - pump_inlet_depth: (float) Pump inlet depth in metres.

    ----------------------------------------------------------------
    Notes:
    - The pump inlet depth is calculated by summing the groundwater depth (WD), allowable drawdown (Sw),
      safety margin (M), and the product of long-term decline rate (dS/dt) and bore/project lifetime (t).
    """
    # Inlet or chamber
    # Water depth WD, drawdown, margin, dS/dt, lifetime years
    # Next step in 2-b
    pump_inlet_depth = groundwater_depth + allowable_drawdown + safety_margin + long_term_decline_rate * bore_lifetime
    return pump_inlet_depth


def calculate_minimum_pump_housing_diameter(req_flow_rate_sec, pump_diameter):
    """
    Calculates the minimum pump housing diameter (MPHD) required based on the specified flow rate and pump diameter.

    Parameters:
    - req_flow_rate_sec: (float) Required flow rate in cubic metres per second (m^3/s).
    - pump_diameter: (float) Diameter of the pump in metres (P).

    Returns:
    - mphd: (float) Minimum pump housing diameter (MPHD) in metres (m).

    ----------------------------------------------------------------
    Notes:
    - The minimum pump housing diameter (MPHD) is calculated using the formula:
      MPHD = √(P² + 4 * Q / (3.7 * π))
      where Q is the required flow rate (m^3/s) and π is the mathematical constant (approximately 3.14159).
    """
    # TODO: req flow rate(sec), pump diameter
    # Formula in the doc
    mphd = np.sqrt(pump_diameter**2 + 4 * req_flow_rate_sec / (3.7 * np.pi))
    return mphd


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



