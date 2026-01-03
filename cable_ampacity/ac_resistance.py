"""
AC Resistance Calculation Module

Calculates AC resistance considering:
- DC resistance at operating temperature
- Skin effect (Ycs)
- Proximity effect (Ycp)

Based on IEC 60287-1-1 and Neher-McGrath method.
"""

import math
from dataclasses import dataclass
from typing import Literal, Optional


# Material constants
CONDUCTOR_RESISTIVITY = {
    "copper": 1.7241e-8,      # ohm·m at 20°C
    "aluminum": 2.8264e-8,    # ohm·m at 20°C
}

TEMPERATURE_COEFFICIENT = {
    "copper": 0.00393,        # per °C at 20°C
    "aluminum": 0.00403,      # per °C at 20°C
}

# Skin effect constants (ks) - depends on conductor construction
SKIN_EFFECT_CONSTANT = {
    "solid": 1.0,
    "stranded_round": 1.0,
    "stranded_compact": 0.8,
    "segmental": 0.435,
}

# Proximity effect constants (kp)
PROXIMITY_EFFECT_CONSTANT = {
    "solid": 1.0,
    "stranded_round": 0.8,
    "stranded_compact": 0.8,
    "segmental": 0.37,
}


@dataclass
class ConductorSpec:
    """Specification for cable conductor."""
    material: Literal["copper", "aluminum"]
    cross_section: float          # mm²
    diameter: float               # mm
    stranding: Literal["solid", "stranded_round", "stranded_compact", "segmental"] = "stranded_compact"
    dc_resistance_20c: Optional[float] = None  # ohm/m at 20°C (if known from manufacturer)


def calculate_dc_resistance(
    conductor: ConductorSpec,
    temperature: float = 90.0,
) -> float:
    """
    Calculate DC resistance at operating temperature.

    Args:
        conductor: Conductor specification
        temperature: Operating temperature in °C

    Returns:
        DC resistance in ohm/m
    """
    if conductor.dc_resistance_20c is not None:
        r20 = conductor.dc_resistance_20c
    else:
        # Calculate from resistivity
        resistivity = CONDUCTOR_RESISTIVITY[conductor.material]
        area_m2 = conductor.cross_section * 1e-6  # convert mm² to m²
        r20 = resistivity / area_m2  # ohm/m

    # Temperature correction
    alpha = TEMPERATURE_COEFFICIENT[conductor.material]
    r_temp = r20 * (1 + alpha * (temperature - 20))

    return r_temp


def calculate_skin_effect(
    conductor: ConductorSpec,
    rdc: float,
    frequency: float = 50.0,
) -> float:
    """
    Calculate skin effect factor (Ycs) per IEC 60287-1-1.

    Args:
        conductor: Conductor specification
        rdc: DC resistance at operating temperature (ohm/m)
        frequency: System frequency in Hz

    Returns:
        Skin effect factor Ycs (dimensionless)
    """
    ks = SKIN_EFFECT_CONSTANT[conductor.stranding]

    # xs² = (8πf / R'dc) × 10^-7 × ks
    # where R'dc is in ohm/m
    xs_squared = (8 * math.pi * frequency / rdc) * 1e-7 * ks

    # Ycs = xs^4 / (192 + 0.8 × xs^4) for xs² ≤ 2.8
    # Ycs = -0.136 - 0.0177×xs² + 0.0563×xs^4 for xs² > 2.8
    if xs_squared <= 2.8:
        xs_4 = xs_squared ** 2
        ycs = xs_4 / (192 + 0.8 * xs_4)
    else:
        xs_4 = xs_squared ** 2
        ycs = -0.136 - 0.0177 * xs_squared + 0.0563 * xs_4

    return max(0, ycs)


def calculate_proximity_effect(
    conductor: ConductorSpec,
    rdc: float,
    spacing: float,
    frequency: float = 50.0,
    arrangement: Literal["flat", "trefoil"] = "trefoil",
) -> float:
    """
    Calculate proximity effect factor (Ycp) per IEC 60287-1-1.

    Args:
        conductor: Conductor specification
        rdc: DC resistance at operating temperature (ohm/m)
        spacing: Axial spacing between conductors in mm
        frequency: System frequency in Hz
        arrangement: Cable arrangement (flat or trefoil)

    Returns:
        Proximity effect factor Ycp (dimensionless)
    """
    if spacing == 0:
        return 0.0

    kp = PROXIMITY_EFFECT_CONSTANT[conductor.stranding]
    dc = conductor.diameter  # conductor diameter in mm
    s = spacing  # spacing in mm

    # xp² = (8πf / R'dc) × 10^-7 × kp
    xp_squared = (8 * math.pi * frequency / rdc) * 1e-7 * kp

    # F(xp) function
    xp_4 = xp_squared ** 2
    if xp_squared <= 2.8:
        f_xp = xp_4 / (192 + 0.8 * xp_4)
    else:
        f_xp = -0.136 - 0.0177 * xp_squared + 0.0563 * xp_4

    # Diameter to spacing ratio
    dc_s_ratio = dc / s

    if arrangement == "trefoil":
        # Trefoil: Ycp = F(xp) × (dc/s)² × [0.312 × (dc/s)² + 1.18 / (F(xp) + 0.27)]
        ycp = f_xp * (dc_s_ratio ** 2) * (0.312 * (dc_s_ratio ** 2) + 1.18 / (f_xp + 0.27))
    else:
        # Flat formation (simplified - uses average)
        ycp = f_xp * (dc_s_ratio ** 2) * (0.312 * (dc_s_ratio ** 2) + 1.18 / (f_xp + 0.27))
        ycp *= 1.5  # Approximate factor for flat formation

    return max(0, ycp)


def calculate_ac_resistance(
    conductor: ConductorSpec,
    temperature: float = 90.0,
    spacing: float = 0.0,
    frequency: float = 50.0,
    arrangement: Literal["flat", "trefoil"] = "trefoil",
) -> dict:
    """
    Calculate AC resistance including skin and proximity effects.

    Args:
        conductor: Conductor specification
        temperature: Operating temperature in °C
        spacing: Axial spacing between conductors in mm (0 for single cable)
        frequency: System frequency in Hz
        arrangement: Cable arrangement

    Returns:
        Dictionary with:
        - rdc: DC resistance (ohm/m)
        - ycs: Skin effect factor
        - ycp: Proximity effect factor
        - rac: AC resistance (ohm/m)
    """
    rdc = calculate_dc_resistance(conductor, temperature)
    ycs = calculate_skin_effect(conductor, rdc, frequency)
    ycp = calculate_proximity_effect(conductor, rdc, spacing, frequency, arrangement)

    # Rac = Rdc × (1 + Ycs + Ycp)
    rac = rdc * (1 + ycs + ycp)

    return {
        "rdc": rdc,
        "ycs": ycs,
        "ycp": ycp,
        "rac": rac,
    }
