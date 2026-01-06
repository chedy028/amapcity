"""
AC Resistance Calculation Module

Calculates AC resistance considering:
- DC resistance at operating temperature
- Skin effect (Ycs)
- Proximity effect (Ycp)

Based on IEC 60287-1-1 and Neher-McGrath method.

Standards alignment:
- IEC-228: Conductor DC resistance standards
- IEC 60287-1-1: AC resistance calculation with skin/proximity effects

Temperature coefficient notes:
- Copper: α = 0.00393 /K at 20°C (equivalent to BETA = 234.5 K per IEC-228)
- Aluminum: α = 0.00403 /K at 20°C (equivalent to BETA = 228.0 K per IEC-228)

The relationship is: α₂₀ = 1 / (BETA + 20) where BETA is at 0°C reference.
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

# CIGRE-based skin effect lookup table for Milliken (segmental) conductors
# Reference: CIGRE Technical Brochure 272 and 531
# Keys: frequency (Hz), then cross-section (mm²) -> Ycs value
# For large Milliken conductors, the IEC 60287 formula becomes invalid when xs² > 2.8
# These empirical values are used instead
MILLIKEN_SKIN_EFFECT_TABLE = {
    50: {
        800: 0.015,
        1000: 0.019,
        1200: 0.023,
        1400: 0.027,
        1600: 0.031,
        1800: 0.035,
        2000: 0.039,
        2500: 0.048,
        3000: 0.057,
    },
    60: {
        800: 0.018,
        1000: 0.023,
        1200: 0.028,
        1400: 0.032,
        1600: 0.037,
        1800: 0.042,
        2000: 0.047,
        2500: 0.058,
        3000: 0.069,
    },
}


@dataclass
class ConductorSpec:
    """Specification for cable conductor."""
    material: Literal["copper", "aluminum"]
    cross_section: float          # mm²
    diameter: float               # mm
    stranding: Literal["solid", "stranded_round", "stranded_compact", "segmental"] = "stranded_compact"
    dc_resistance_20c: Optional[float] = None  # ohm/m at 20°C (if known from manufacturer)
    ks: Optional[float] = None    # Skin effect coefficient (user override, e.g., 0.62 for Milliken)
    kp: Optional[float] = None    # Proximity effect coefficient (user override, e.g., 0.37 for Milliken)


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


def lookup_milliken_skin_effect(
    cross_section: float,
    frequency: float,
) -> Optional[float]:
    """
    Lookup skin effect factor (Ycs) from CIGRE tables for Milliken conductors.

    For large Milliken (segmental) conductors, the IEC 60287-1-1 formula
    produces unrealistic results when xs² > 2.8. This function provides
    empirical values from CIGRE Technical Brochures 272 and 531.

    Args:
        cross_section: Conductor cross-section in mm²
        frequency: System frequency in Hz (50 or 60)

    Returns:
        Ycs if found/interpolatable, None otherwise
    """
    # Select frequency table (use nearest 50 or 60 Hz)
    if frequency <= 55:
        freq_key = 50
    else:
        freq_key = 60

    if freq_key not in MILLIKEN_SKIN_EFFECT_TABLE:
        return None

    table = MILLIKEN_SKIN_EFFECT_TABLE[freq_key]
    sizes = sorted(table.keys())

    # Check bounds
    if cross_section < sizes[0]:
        return None  # Below table range, use IEC formula
    if cross_section > sizes[-1]:
        # Extrapolate for sizes above 3000 mm² (rare but possible)
        # Use linear extrapolation from last two points
        x0, x1 = sizes[-2], sizes[-1]
        y0, y1 = table[x0], table[x1]
        slope = (y1 - y0) / (x1 - x0)
        return y1 + slope * (cross_section - x1)

    # Linear interpolation between bracketing sizes
    for i in range(len(sizes) - 1):
        if sizes[i] <= cross_section <= sizes[i + 1]:
            x0, x1 = sizes[i], sizes[i + 1]
            y0, y1 = table[x0], table[x1]
            return y0 + (y1 - y0) * (cross_section - x0) / (x1 - x0)

    return None


def calculate_skin_effect(
    conductor: ConductorSpec,
    rdc: float,
    frequency: float = 50.0,
) -> float:
    """
    Calculate skin effect factor (Ycs) per IEC 60287-1-1.

    For large Milliken (segmental) conductors >= 800 mm², uses CIGRE
    lookup tables instead of the IEC formula which becomes invalid
    when xs² exceeds 2.8.

    Args:
        conductor: Conductor specification
        rdc: DC resistance at operating temperature (ohm/m)
        frequency: System frequency in Hz

    Returns:
        Skin effect factor Ycs (dimensionless)
    """
    # For segmental (Milliken) conductors with large cross-sections,
    # prefer CIGRE lookup table over IEC formula
    if conductor.stranding == "segmental" and conductor.cross_section >= 800:
        ycs_lookup = lookup_milliken_skin_effect(conductor.cross_section, frequency)
        if ycs_lookup is not None:
            return ycs_lookup

    # Use user-specified ks if provided, otherwise use default for stranding type
    ks = conductor.ks if conductor.ks is not None else SKIN_EFFECT_CONSTANT[conductor.stranding]

    # xs² = (8πf / R'dc) × 10^-7 × ks
    # where R'dc is in ohm/m
    xs_squared = (8 * math.pi * frequency / rdc) * 1e-7 * ks

    # Ycs = xs^4 / (192 + 0.8 × xs^4) for xs² ≤ 2.8
    # Ycs = -0.136 - 0.0177×xs² + 0.0563×xs^4 for xs² > 2.8
    if xs_squared <= 2.8:
        xs_4 = xs_squared ** 2
        ycs = xs_4 / (192 + 0.8 * xs_4)
    else:
        # For non-Milliken conductors or when lookup fails,
        # cap xs_squared to prevent unrealistic values
        xs_squared_capped = min(xs_squared, 2.8)
        xs_4 = xs_squared_capped ** 2
        ycs = xs_4 / (192 + 0.8 * xs_4)

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

    # Use user-specified kp if provided, otherwise use default for stranding type
    kp = conductor.kp if conductor.kp is not None else PROXIMITY_EFFECT_CONSTANT[conductor.stranding]
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
