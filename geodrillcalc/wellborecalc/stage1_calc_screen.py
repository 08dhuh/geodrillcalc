#!/usr/bin/env python

import numpy as np
# import logging
from ..utils.utils import getlogger

logger = getlogger()


def is_water_corrosive(temperature_k: float,
                       pH: float,
                       calcium_ion_concentration: float,
                       carbonate_ion_concentration: float,
                       total_dissolved_solids: float) -> float:
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
    # TODO: Check if the temperature input is in the valid range

    def K_potenz(coeff, t): return np.dot(
        coeff, [1, t, -1/t, -np.log10(t), 1/t**2])
    pK2_coeff = [107.8871, .03252849, 5151.79, 38.92561, 563713.9]
    pKsc_coeff = [171.9065, 0.077993, 2839.319, 71.595, 0]

    pK2 = K_potenz(pK2_coeff, temperature_k)
    logger.info(f'pk2: {pK2}')
    pKsc = K_potenz(pKsc_coeff, temperature_k)
    logger.info(f'pKsc: {pKsc}')
    pCa2 = -np.log10(calcium_ion_concentration/(1000*40.08))
    pHCO3 = -np.log10(carbonate_ion_concentration/(1000*61.0168))
    ionic_strength = total_dissolved_solids/40000
    dielectric_stength = 60954/(temperature_k+116) - 68.937
    alkalinity = 1.82*10**6*(dielectric_stength*temperature_k)**(-1.5)
    # activity coefficient for monovalent species at the specified temperature
    pfm = alkalinity*(np.sqrt(ionic_strength)/(1+np.sqrt(ionic_strength))-.31)
    # pH of saturation, or the pH at which water is saturated with CaCO3
    pH_saturation = pK2 - pKsc + pCa2 + pHCO3 + 5*pfm
    langelier_saturation_index = pH - pH_saturation

    return langelier_saturation_index

# ================================================================
# Stage 1. Define parameters for screened interval
# TODO: test with the whole casing diameter list


def calculate_minimum_screen_length(req_flow_rate: float,
                                    hyd_conductivity: float,
                                    bore_lifetime: float,
                                    thickness: float,
                                    is_injection_bore: bool,
                                    drawdown: float = 25,
                                    bore_radius: float = .0762,
                                    specific_storage: float = 2*10**(-4),) -> float:
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
        v.	Allowable drawdown, Sw (m) default: Sw = 25 m
        vi.	Bore radius, r (m) , default: r = 0.0762 m (3”)
        vii.	Aquifer specific storage, Ss (m-1) , default: Ss = 2x10-4 m-1
        viii.	Production or injection bore? True for production
    --------------------------------------------------------
    Returns
        SL: (float) nominal value of the minimum screen length (metres)
        error: (tuple) lower and upper limits representing the uncertainty bounds
    """
    #
    screen_length = (2.3*req_flow_rate / (4*np.pi*hyd_conductivity*drawdown)) \
        * np.log10(2.25*hyd_conductivity*bore_lifetime/(bore_radius**2 * specific_storage))
    if is_injection_bore:
        screen_length *= 2
    screen_length = min(screen_length, thickness)
    error_lower = screen_length * .9
    error_upper = min(screen_length * 1.1, thickness)

    return screen_length, (error_lower, error_upper)


def calculate_casing_friction(depth_to_top_screen: float,
                              req_flow_rate: float,
                              casing_diameter: float | np.ndarray,
                              pipe_roughness_coeff: float = 100.):
    """
    Estimates production casing friction loss above aquifer
    for nominal diameters (e.g. 101.6, 127, 152.4, 203.2, 254, 304.8 mm)

    ----------------------------------------------------------------
    Input Parameters:
        depth_to_top_screen: (float) Depth to top of screen in metres (m).
        req_flow_rate: (float) Required flow rate in cubic metres per second (m^3/s).
        casing_diameter: (float or np.ndarray) Casing diameter in metres (m).
        pipe_roughness_coeff: (float) Pipe roughness coefficient, default: 100 for steel

    ----------------------------------------------------------------
    Returns:
        hfpc: (float) production casing friction loss (metres)
    """
    hfpc = (10.67*depth_to_top_screen*req_flow_rate**1.852) / \
        (pipe_roughness_coeff**1.852 * casing_diameter**4.8704)
    return hfpc


def calculate_minimum_screen_diameter(up_hole_frictions: np.ndarray,
                                      screen_length,
                                      req_flow_rate,
                                      pipe_roughness_coeff=100):
    """
    Determines the minimum screen diameter, SDmin (m), using the Hazen-Williams equation to ensure up-hole friction is less than 20 m.
    Reference: https://en.wikipedia.org/wiki/Hazen%E2%80%93Williams_equation#SI_units

    Parameters:
    - up_hole_friction: (np.ndarray) Up-hole friction in m. Must be smaller than 20; otherwise, np.nan is returned.
    - screen_length: (float) Length of the screen in metres (m).
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
    high_friction_mask = up_hole_frictions > 20

    d = np.empty_like(up_hole_frictions, dtype=float)
    d[~high_friction_mask] = ((10.67 * screen_length * req_flow_rate**1.852)
                              / (2 * pipe_roughness_coeff**1.852 * (20 - up_hole_frictions[~high_friction_mask])))**(1/4.8704)

    d[high_friction_mask] = np.nan

    return d


@DeprecationWarning
def _calculate_minimum_screen_diameter(up_hole_friction: float,
                                       screen_length: float,
                                       req_flow_rate: float,
                                       pipe_roughness_coeff: float = 100.):
    """
    Determines the minimum screen diameter, SDmin (m), using the Hazen-Williams equation to ensure up-hole friction is less than 20 m.
    Reference: https://en.wikipedia.org/wiki/Hazen%E2%80%93Williams_equation#SI_units

    Parameters:
    - up_hole_friction: (float or np.ndarray) Up-hole friction in m. Must be smaller than 20; otherwise, np.nan is returned.
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
            # logger.debug(f"{up_hole_friction} Up-hole friction is too high")
            return np.nan
            # raise ValueError("Up-hole friction is too high")
        d = (10.67 * screen_length * req_flow_rate**1.852)\
            / (2*pipe_roughness_coeff**1.852*(20-up_hole_friction))
        d **= 1/4.8704
        return d
    except ValueError as e:
        logger.exception(e)
        return np.nan


def calculate_total_casing(prod_casing_diameter: float,
                           screen_diameter,
                           intermediate_casing: float,
                           screen_length: float
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
        logger.debug(
            f"{prod_casing_diameter} <= {screen_diameter}: Production casing diameter must be greater than the screen diameter for a valid result.")
        nanflag = True
    if np.isnan(screen_diameter):
        logger.debug("input is nan")
        nanflag = True
    if nanflag:
        return np.nan
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

    """
    # TODO: prod/injection : sand face velocity differs
    # sand face velocity
    # iii.	NGR = net-to-gross ratio for aquifer = 1 (K for Gippsland aquifer units is already averaged)
    # input porosity / flow rate(sec) / injection or prod screen length
    # flow / (0.01 * pi * sl * porosity)
    ohd_min = req_flow_rate_sec / \
        (sand_face_velocity * np.pi * reservoir_porosity * ngr_aquifer * screen_length)
    return ohd_min
