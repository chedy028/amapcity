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

# =============================================================================
# IEC 60287-1-1:2023 Table 2 - Skin and proximity effects
# Experimental values for the coefficients ks and kp
# =============================================================================
# Structure: [material][conductor_type][insulation_system] -> (ks, kp)
# For Milliken conductors, wire_type is also a factor

IEC_TABLE_2 = {
    "copper": {
        # Round, solid - All insulation systems
        "solid": {
            "all": (1.0, 1.0),
        },
        # Round, stranded
        "stranded": {
            "fluid_paper_ppl": (1.0, 0.8),
            "extruded_mineral": (1.0, 1.0),
        },
        # Round, Milliken
        "milliken": {
            "fluid_paper_ppl": (0.435, 0.37),
            # Extruded insulation - depends on wire construction
            "extruded_insulated": (0.35, 0.20),      # Insulated wires (enamelled, oxidized)
            "extruded_bare_uni": (0.62, 0.37),       # Bare uni-directional wires
            "extruded_bare_bi": (0.80, 0.37),        # Bare bi-directional wires
        },
        # Hollow, helical stranded - ks uses formula (see Note a)
        "hollow_helical": {
            "all": (None, 0.8),  # ks requires formula calculation
        },
        # Sector-shaped
        "sector": {
            "fluid_paper_ppl": (1.0, 0.8),
            "extruded_mineral": (1.0, 1.0),
        },
    },
    "aluminum": {
        # Round, solid - All insulation systems
        "solid": {
            "all": (1.0, 1.0),
        },
        # Round, stranded - All insulation systems
        "stranded": {
            "all": (1.0, 0.8),
        },
        # Round, Milliken - All insulation systems
        "milliken": {
            "all": (0.25, 0.15),
        },
        # Hollow, helical stranded - ks uses formula
        "hollow_helical": {
            "all": (None, 0.8),  # ks requires formula calculation
        },
    },
}

# Simplified lookup for backward compatibility
# Default values assume extruded insulation for copper
SKIN_EFFECT_CONSTANT = {
    "solid": 1.0,
    "stranded_round": 1.0,
    "stranded_compact": 1.0,      # Same as stranded for extruded
    "segmental": 0.435,           # Milliken with fluid/paper/PPL (conservative)
}

PROXIMITY_EFFECT_CONSTANT = {
    "solid": 1.0,
    "stranded_round": 1.0,        # Extruded/mineral insulation
    "stranded_compact": 1.0,      # Extruded/mineral insulation
    "segmental": 0.37,            # Milliken default
}

# =============================================================================
# IEC 60287-1-1:2023 Table 3 - Relative permittivity and loss factors
# Values for insulation of high-voltage and medium-voltage cables
# =============================================================================
# Structure: [insulation_type][voltage_class] -> (permittivity ε, tan_delta)

IEC_TABLE_3 = {
    # Cables insulated with impregnated paper
    "paper_solid": {"all": (4.0, 0.01)},
    "paper_oil_filled": {
        "36kV": (3.6, 0.0035),
        "87kV": (3.6, 0.0033),
        "160kV": (3.5, 0.0030),
        "220kV": (3.5, 0.0028),
    },
    "paper_oil_pressure": {"all": (3.7, 0.0045)},
    "paper_gas_external": {"all": (3.6, 0.0040)},
    "paper_gas_internal": {"all": (3.4, 0.0045)},
    # PPL (Polypropylene Paper Laminate)
    "ppl": {">=63kV": (2.8, 0.0014)},
    # Rubber
    "butyl_rubber": {"all": (4.0, 0.050)},
    # EPR (Ethylene Propylene Rubber)
    "epr": {
        "<=36kV": (3.0, 0.020),
        ">36kV": (3.0, 0.005),
    },
    # PVC
    "pvc": {"all": (8.0, 0.1)},
    # PE (Polyethylene)
    "pe": {"all": (2.3, 0.001)},
    # XLPE (Cross-linked Polyethylene)
    "xlpe": {
        "<=36kV_unfilled": (2.5, 0.004),
        ">36kV_unfilled": (2.5, 0.001),
        ">36kV_filled": (3.0, 0.005),
    },
}

# Simplified lookup for common insulation types
INSULATION_PERMITTIVITY = {
    "xlpe": 2.5,
    "epr": 3.0,
    "pvc": 8.0,
    "pe": 2.3,
    "paper": 4.0,
    "ppl": 2.8,
}

INSULATION_TAN_DELTA = {
    "xlpe": 0.001,      # >36kV unfilled (conservative for HV)
    "epr": 0.005,       # >36kV (conservative for HV)
    "pvc": 0.1,
    "pe": 0.001,
    "paper": 0.01,
    "ppl": 0.0014,
}

# =============================================================================
# IEC 60287-1-1:2023 Table 4 - Absorption coefficient of solar radiation
# =============================================================================

IEC_TABLE_4_SOLAR_ABSORPTION = {
    "bituminized_jute": 0.8,
    "polychloroprene": 0.8,
    "pvc": 0.6,
    "pe": 0.4,
    "lead": 0.6,
}

@dataclass
class ConductorSpec:
    """Specification for cable conductor.

    Skin/Proximity Effect Options (in order of precedence):
    1. ycs_override/ycp_override: Direct values (highest priority)
    2. IEC 60287-1-1:2023 formula with user-provided or default ks/kp
    """
    material: Literal["copper", "aluminum"]
    cross_section: float          # mm²
    diameter: float               # mm
    stranding: Literal["solid", "stranded_round", "stranded_compact", "segmental"] = "stranded_compact"
    dc_resistance_20c: Optional[float] = None  # ohm/m at 20°C (if known from manufacturer)
    ks: Optional[float] = None    # Skin effect coefficient (e.g., 0.35 for Cayuga, 0.62 for Homer City)
    kp: Optional[float] = None    # Proximity effect coefficient (e.g., 0.20 for Cayuga, 0.37 for Homer City)
    # Direct override options (use when you know exact Ycs/Ycp from CYMCAP or measurements)
    ycs_override: Optional[float] = None  # Direct skin effect factor override (e.g., 0.185 from CYMCAP)
    ycp_override: Optional[float] = None  # Direct proximity effect factor override


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
    Calculate skin effect factor (Ycs) per IEC 60287-1-1:2023.

    Priority order:
    1. Direct ycs_override if provided
    2. IEC 60287-1-1:2023 formula with user-provided or default ks

    Args:
        conductor: Conductor specification
        rdc: DC resistance at operating temperature (ohm/m)
        frequency: System frequency in Hz

    Returns:
        Skin effect factor Ycs (dimensionless)
    """
    # Priority 1: Direct override (highest priority)
    if conductor.ycs_override is not None:
        return conductor.ycs_override

    # Priority 2: IEC formula with user or default ks
    ks = conductor.ks if conductor.ks is not None else SKIN_EFFECT_CONSTANT[conductor.stranding]

    # xs² = (8πf / R'dc) × 10^-7 × ks  (IEC 60287-1-1:2023, Clause 5.1.3)
    xs_squared = (8 * math.pi * frequency / rdc) * 1e-7 * ks
    xs = math.sqrt(xs_squared)

    # Ycs calculation per IEC 60287-1-1:2023, Clause 5.1.3
    if xs <= 2.8:
        # For 0 < xs ≤ 2.8: ys = xs⁴ / (192 + 0.8·xs⁴)
        xs_4 = xs ** 4
        ycs = xs_4 / (192 + 0.8 * xs_4)
    elif xs <= 3.8:
        # For 2.8 < xs ≤ 3.8: ys = -0.136 - 0.0177·xs + 0.0563·xs²
        ycs = -0.136 - 0.0177 * xs + 0.0563 * xs_squared
    else:
        # For xs > 3.8: ys = 0.354·xs - 0.733
        ycs = 0.354 * xs - 0.733

    return max(0, ycs)


def calculate_proximity_effect(
    conductor: ConductorSpec,
    rdc: float,
    spacing: float,
    frequency: float = 50.0,
    arrangement: Literal["flat", "trefoil"] = "trefoil",
    num_cables: int = 3,
) -> float:
    """
    Calculate proximity effect factor (Ycp) per IEC 60287-1-1:2023.

    Per IEC 60287-1-1:2023:
    - Section 5.1.4: Two single-core cables (coefficient 1.18)
    - Section 5.1.5: Three single-core cables (coefficient 2.9)

    Priority order:
    1. Direct ycp_override if provided
    2. IEC formula with user or default kp

    Args:
        conductor: Conductor specification
        rdc: DC resistance at operating temperature (ohm/m)
        spacing: Axial spacing between conductors in mm
        frequency: System frequency in Hz
        arrangement: Cable arrangement (flat or trefoil)
        num_cables: Number of cables per circuit (2 or 3, default 3 for 3-phase)

    Returns:
        Proximity effect factor Ycp (dimensionless)
    """
    # Priority 1: Direct override
    if conductor.ycp_override is not None:
        return conductor.ycp_override

    if spacing == 0:
        return 0.0

    # Use user-specified kp if provided, otherwise use default for stranding type
    kp = conductor.kp if conductor.kp is not None else PROXIMITY_EFFECT_CONSTANT[conductor.stranding]
    dc = conductor.diameter  # conductor diameter in mm
    s = spacing  # spacing in mm

    # xp² = (8πf / R'dc) × 10^-7 × kp  (IEC 60287-1-1:2023, Clause 5.1.4/5.1.5)
    xp_squared = (8 * math.pi * frequency / rdc) * 1e-7 * kp
    xp = math.sqrt(xp_squared)

    # F(xp) function per IEC 60287-1-1:2023
    # IMPORTANT: For proximity effect, F(xp) = xp⁴ / (192 + 0.8·xp⁴) for ALL xp values
    # (The piecewise approximation is only for skin effect, NOT proximity effect)
    xp_4 = xp ** 4
    f_xp = xp_4 / (192 + 0.8 * xp_4)

    # Diameter to spacing ratio
    dc_s_ratio = dc / s

    # Select coefficient based on number of cables per circuit
    # IEC 60287-1-1:2023 Section 5.1.4: Two single-core cables -> 1.18
    # IEC 60287-1-1:2023 Section 5.1.5: Three single-core cables -> 2.9
    if num_cables == 2:
        coeff = 1.18
    else:
        # Default to 3 cables (typical 3-phase transmission)
        coeff = 2.9

    if arrangement == "trefoil":
        # Trefoil: Ycp = F(xp) × (dc/s)² × [0.312 × (dc/s)² + coeff / (F(xp) + 0.27)]
        ycp = f_xp * (dc_s_ratio ** 2) * (0.312 * (dc_s_ratio ** 2) + coeff / (f_xp + 0.27))
    else:
        # Flat formation per IEC 60287-1-1:2023 Section 5.1.5.2
        # For outer cables: same formula
        # For center cable: multiply by 2 (two adjacent cables)
        # Average effect: multiply by factor ~1.33 (average of 1, 2, 1 for 3 cables)
        ycp = f_xp * (dc_s_ratio ** 2) * (0.312 * (dc_s_ratio ** 2) + coeff / (f_xp + 0.27))
        ycp *= 4/3  # Average factor for flat formation (outer=1, center=2, outer=1) / 3

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
