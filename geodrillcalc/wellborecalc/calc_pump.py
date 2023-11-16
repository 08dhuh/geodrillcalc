#!/usr/bin/env python

import numpy as np
#import logging
from geodrillcalc.utils.utils import getlogger

logger = getlogger()

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


    Returns:
        (float) Assigned pump diameter based on the required flow rate.

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
        groundwater_depth: (float) Depth of the groundwater table in metres (WD).
        allowable_drawdown: (float) Allowable drawdown in metres (Sw).

    Returns:
        M: (float) The safety margin, M (m), for groundwater drawdown.

    ----------------------------------------------------------------
    Notes:
        The safety margin is determined by taking the larger value between 10 metres and 0.2 times the sum
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
        groundwater_depth: (float) Present water depth relative to the ground in metres (WD).
        allowable_drawdown: (float) Allowable drawdown in metres (Sw).
        safety_margin: (float) Safety margin in metres (M).
        long_term_decline_rate: (float) Long-term decline rate in water level in metres per year (dS/dt).
        bore_lifetime: (float) Bore/project lifetime in years (t).

    Returns:
        pump_inlet_depth: (float) Pump inlet depth in metres.

    ----------------------------------------------------------------
    Notes:
        The pump inlet depth is calculated by summing the groundwater depth (WD), allowable drawdown (Sw),
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