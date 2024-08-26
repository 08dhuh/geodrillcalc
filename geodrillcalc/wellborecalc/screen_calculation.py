#!/usr/bin/env python
import numpy as np

from geodrillcalc.utils.calc_utils import find_next_largest_value, query_diameter_table
from ..utils.utils import getlogger 


logger = getlogger()


def is_water_corrosive(temperature_k: float,
                       pH: float,
                       calcium_ion_concentration: float,
                       carbonate_ion_concentration: float,
                       total_dissolved_solids: float) -> float:
    """
    Calculates the Langelier Saturation Index (LSI) of geothermal water.

    The LSI is used to evaluate the corrosive potential of water based on its chemistry.

    Parameters
    ----------
    temperature_k : float
        Temperature of the water in Kelvin, must be in the range of 273 <= T <= 363.
    pH : float
        pH level of the water.
    calcium_ion_concentration : float
        Calcium ion concentration in ppm.
    carbonate_ion_concentration : float
        Carbonate ion concentration in ppm.
    total_dissolved_solids : float
        Total dissolved solids (TDS) in ppm.

    Returns
    -------
    float
        Langelier Saturation Index (LSI), which indicates the water's tendency to precipitate or dissolve calcium carbonate.
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


def calculate_minimum_screen_length(req_flow_rate: float,
                                    hyd_conductivity: float,
                                    bore_lifetime: float,
                                    aquifer_thickness: float,
                                    is_production_well: bool,
                                    allowable_drawdown: float = 25,
                                    bore_radius: float = .0762,
                                    specific_storage: float = 2*10**(-4),) -> float:
    """
    Determines the minimum screen length, SL (m)
    based on Eq 4 at http://quebec.hwr.arizona.edu/classes/hwr431/2006/Lab6.pdf
    If it is an injection bore, screen length is multiplied by 2.0 
    and capped at total aquifer thickness.      
    
    Parameters
    ----------
    req_flow_rate : float
        Required flow rate in cubic metres per day (m3/day).
    hyd_conductivity : float
        Hydraulic conductivity of the aquifer in metres per day (m/day).
    bore_lifetime : float
        Projected lifetime of the bore in days.
    aquifer_thickness : float
        Thickness of the aquifer in metres.
    is_production_well : bool
        Indicates if the well is a production well (True) or an injection well (False).
    allowable_drawdown : float, optional
        Allowable drawdown in metres, default is 25 m.
    bore_radius : float, optional
        Radius of the bore in metres, default is 0.0762 m (3 inches).
    specific_storage : float, optional
        Specific storage of the aquifer in inverse metres (m-1), default is 2x10-4 m-1.

    Returns
    -------
    tuple
        A tuple containing the minimum screen length (float) and a tuple of error bounds (lower, upper).
    """
    screen_length = (2.3*req_flow_rate / (4*np.pi*hyd_conductivity*allowable_drawdown)) \
        * np.log10(2.25*hyd_conductivity*bore_lifetime/(bore_radius**2 * specific_storage))
    if not is_production_well:
        # ii.	If Injection bore, multiply SL x 2.0 (capped at total aquifer thickness)
        screen_length *= 2
    screen_length = min(screen_length, aquifer_thickness)
    error_lower = screen_length * .9
    error_upper = min(screen_length * 1.1, aquifer_thickness)

    return screen_length, (error_lower, error_upper)


def calculate_casing_friction(depth_to_top_screen: float,
                              req_flow_rate: float,
                              casing_diameter: float | np.ndarray,
                              pipe_roughness_coeff: float = 100.):
    """
    Estimates production casing friction loss above aquifer
    for nominal diameters (e.g. 101.6, 127, 152.4, 203.2, 254, 304.8 mm)

    Parameters
    ----------
    depth_to_top_screen : float
        Depth to the top of the screen in metres.
    req_flow_rate : float
        Required flow rate in cubic metres per second (m^3/s).
    casing_diameter : float or np.ndarray
        Diameter of the casing in metres.
    pipe_roughness_coeff : float, optional
        Pipe roughness coefficient, default is 100 for steel.

    Returns
    -------
    float
        The calculated friction loss in metres.
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

    Parameters
    ----------
    up_hole_frictions : np.ndarray
        Array of up-hole friction losses in metres. Values must be less than 20; otherwise, np.nan is returned.
    screen_length : float
        Length of the screen in metres.
    req_flow_rate : float
        Required flow rate in cubic metres per second (m^3/s).
    pipe_roughness_coeff : float, optional
        Pipe roughness coefficient, default is 100.

    Returns
    -------
    np.ndarray
        Array of minimum screen diameters in metres. Returns np.nan for friction values that are too high.
    """
    high_friction_mask = up_hole_frictions > 20

    d = np.empty_like(up_hole_frictions, dtype=float)
    d[~high_friction_mask] = ((10.67 * screen_length * req_flow_rate**1.852)
                              / (2 * pipe_roughness_coeff**1.852 * (20 - up_hole_frictions[~high_friction_mask])))**(1/4.8704)

    d[high_friction_mask] = np.nan

    return d


def calculate_total_casing(prod_casing_diameter: float,
                           screen_diameter,
                           intermediate_casing: float,
                           screen_length: float
                           ) -> float:
    """
    Calculates the total casing length required, including production casing and screen, based on given parameters.

    Parameters
    ----------
    prod_casing_diameter : float
        Diameter of the production casing in metres.
    screen_diameter : float
        Diameter of the screen in metres. If invalid or larger than the production casing diameter, np.nan is returned.
    intermediate_casing : float
        Length of intermediate casing in metres, typically measured from LMTA minus 10 metres.
    screen_length : float
        Length of the screen in metres.

    Returns
    -------
    float
        Total length of casing required in metres. 
        Returns np.nan if screen diameter is invalid or too large.
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


def calculate_minimum_open_hole_diameter(req_flow_rate_sec,
                                         screen_length,
                                         sand_face_velocity,
                                         reservoir_porosity,
                                         ngr_aquifer=1
                                         ):
    """
    Calculates the minimum open hole diameter (OHD) required to meet the specified flow rate.

    Parameters
    ----------
    req_flow_rate_sec : float
        Required flow rate in cubic metres per second (m^3/s).
    screen_length : float
        Length of the screen in metres.
    sand_face_velocity : float
        Sand face velocity in metres per second (m/s).
    reservoir_porosity : float
        Average reservoir porosity (0 to 1).
    ngr_aquifer : float, optional
        Net-to-gross ratio for the aquifer, default is 1.

    Returns
    -------
    float
        Minimum open hole diameter in metres.
    """

    ohd_min = req_flow_rate_sec / \
        (sand_face_velocity * np.pi * reservoir_porosity * ngr_aquifer * screen_length)
    return ohd_min


def calculate_open_hole_diameter(ohd_min: float,
                                 drilling_diameters_in_metres: list | np.ndarray,
                                 ) -> float:
    """
    Determines the open hole diameter based on the minimum required diameter and available standard bit sizes.

    Parameters
    ----------
    ohd_min : float
        Minimum open hole diameter in metres.
    drilling_diameters_in_metres : list or np.ndarray
        List or array of standard drilling diameters in metres.

    Returns
    -------
    float
        The open hole diameter in metres, which is the next largest standard bit size greater than the minimum required diameter.
    """

    ohd = find_next_largest_value(
        ohd_min, drilling_diameters_in_metres)
    return ohd


def calibrate_open_hole_diameter(ohd: float,
                                 screen_diameter: float,
                                 casing_diameter_table
                                 ):
    """
    Calibrates the open hole diameter to ensure it is suitable for the given screen diameter.

    Parameters
    ----------
    ohd : float
        Current open hole diameter in metres.
    screen_diameter : float
        Diameter of the screen in metres.
    casing_diameter_table : DataFrame
        DataFrame containing standard casing diameters and related data.

    Returns
    -------
    float
        Calibrated open hole diameter in metres.
    """
    if ohd < screen_diameter:
        ohd = query_diameter_table(screen_diameter,
                                   casing_diameter_table
                                   )
    return ohd
