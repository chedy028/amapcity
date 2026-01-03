"""
Loss Calculation Module

Calculates cable losses:
- Conductor losses (Wc = I²·Rac)
- Dielectric losses (Wd)
- Shield/sheath losses (λ1)

Based on IEC 60287-1-1 and Neher-McGrath method.
"""

import math
from dataclasses import dataclass
from typing import Literal, Optional


# Dielectric properties
INSULATION_PROPERTIES = {
    # (tan_delta, permittivity)
    "xlpe": (0.004, 2.5),          # Cross-linked polyethylene
    "epr": (0.020, 3.0),           # Ethylene propylene rubber
    "paper_oil": (0.0035, 3.5),    # Impregnated paper
}

# Maximum operating temperatures (°C)
MAX_CONDUCTOR_TEMP = {
    "xlpe": 90,
    "epr": 90,
    "paper_oil": 85,
}


@dataclass
class InsulationSpec:
    """Specification for cable insulation."""
    material: Literal["xlpe", "epr", "paper_oil"]
    thickness: float              # mm
    conductor_diameter: float     # mm (over conductor)
    tan_delta: Optional[float] = None  # Loss factor (override default)
    permittivity: Optional[float] = None  # Relative permittivity (override default)


@dataclass
class ShieldSpec:
    """Specification for cable shield/sheath."""
    material: Literal["copper", "aluminum", "lead"]
    type: Literal["tape", "wire", "corrugated", "extruded"]
    thickness: float              # mm
    mean_diameter: float          # mm
    resistance_20c: Optional[float] = None  # ohm/m at 20°C (if known)
    bonding: Literal["single_point", "both_ends", "cross_bonded"] = "single_point"


def calculate_dielectric_loss(
    insulation: InsulationSpec,
    voltage: float,
    frequency: float = 50.0,
) -> float:
    """
    Calculate dielectric loss per unit length.

    Wd = ω × C × U₀² × tan(δ)

    Args:
        insulation: Insulation specification
        voltage: Phase-to-ground voltage U₀ in kV
        frequency: System frequency in Hz

    Returns:
        Dielectric loss in W/m
    """
    # Get material properties
    default_tan_delta, default_permittivity = INSULATION_PROPERTIES[insulation.material]
    tan_delta = insulation.tan_delta or default_tan_delta
    epsilon_r = insulation.permittivity or default_permittivity

    # Capacitance per unit length (F/m)
    # C = 2πε₀εᵣ / ln(D_i / d_c)
    epsilon_0 = 8.854e-12  # F/m
    d_c = insulation.conductor_diameter  # mm
    d_i = insulation.conductor_diameter + 2 * insulation.thickness  # mm

    if d_i <= d_c:
        raise ValueError("Insulation outer diameter must be greater than conductor diameter")

    capacitance = (2 * math.pi * epsilon_0 * epsilon_r) / math.log(d_i / d_c)

    # Angular frequency
    omega = 2 * math.pi * frequency

    # Voltage in V (input is kV)
    u0 = voltage * 1000

    # Dielectric loss (W/m)
    wd = omega * capacitance * (u0 ** 2) * tan_delta

    return wd


def calculate_shield_loss_factor(
    shield: ShieldSpec,
    conductor_rac: float,
    spacing: float,
    frequency: float = 50.0,
    temperature: float = 75.0,
) -> float:
    """
    Calculate shield/sheath loss factor (λ1) per IEC 60287-1-1.

    For single-point bonding: λ1 ≈ 0 (no circulating currents)
    For both-ends bonding: λ1 = λ1' + λ1''
        λ1' = circulating current losses
        λ1'' = eddy current losses

    Args:
        shield: Shield specification
        conductor_rac: Conductor AC resistance (ohm/m)
        spacing: Axial spacing between conductors in mm
        frequency: System frequency in Hz
        temperature: Shield operating temperature in °C

    Returns:
        Shield loss factor λ1 (dimensionless, multiply by Wc to get shield loss)
    """
    # Single-point bonding has negligible circulating current losses
    if shield.bonding == "single_point":
        return calculate_eddy_current_loss_factor(shield, conductor_rac, spacing, frequency)

    # Calculate shield resistance at operating temperature
    rs = calculate_shield_resistance(shield, temperature)

    # Reactance of shield
    # Xs = 2πf × 2 × 10^-7 × ln(2s/d)
    d_s = shield.mean_diameter  # mm
    s = spacing if spacing > 0 else d_s * 2  # use 2×diameter if no spacing given

    xs = 2 * math.pi * frequency * 2e-7 * math.log(2 * s / d_s) * 1000  # ohm/km to ohm/m

    # Circulating current loss factor
    # λ1' = Rs/Rac × 1/(1 + (Rs/Xs)²)
    if xs > 0:
        rs_xs_ratio = rs / xs
        lambda1_cc = (rs / conductor_rac) * (1 / (1 + rs_xs_ratio ** 2))
    else:
        lambda1_cc = 0

    # Eddy current loss factor
    lambda1_ec = calculate_eddy_current_loss_factor(shield, conductor_rac, spacing, frequency)

    # Cross-bonding reduces circulating current losses
    if shield.bonding == "cross_bonded":
        lambda1_cc *= 0.1  # Approximate reduction factor

    return lambda1_cc + lambda1_ec


def calculate_eddy_current_loss_factor(
    shield: ShieldSpec,
    conductor_rac: float,
    spacing: float,
    frequency: float = 50.0,
) -> float:
    """
    Calculate eddy current loss factor in shield.

    Args:
        shield: Shield specification
        conductor_rac: Conductor AC resistance (ohm/m)
        spacing: Axial spacing between conductors in mm
        frequency: System frequency in Hz

    Returns:
        Eddy current loss factor λ1'' (dimensionless)
    """
    # Simplified eddy current calculation
    # For thin sheaths, eddy current losses are typically small
    d_s = shield.mean_diameter  # mm
    t_s = shield.thickness  # mm
    s = spacing if spacing > 0 else d_s * 2

    # Approximate formula for eddy current losses
    # λ1'' ≈ gs × (Rs/Rac) × (ts/Ds)² × (Ds/s)²
    gs = 1.0  # geometric factor, approximately 1 for round cables

    # This is a simplified approximation
    lambda1_ec = gs * 0.01 * (t_s / d_s) ** 2 * (d_s / s) ** 2

    return lambda1_ec


def calculate_shield_resistance(
    shield: ShieldSpec,
    temperature: float = 75.0,
) -> float:
    """
    Calculate shield resistance at operating temperature.

    Args:
        shield: Shield specification
        temperature: Operating temperature in °C

    Returns:
        Shield resistance in ohm/m
    """
    if shield.resistance_20c is not None:
        r20 = shield.resistance_20c
    else:
        # Calculate from geometry
        resistivity_20c = {
            "copper": 1.7241e-8,
            "aluminum": 2.8264e-8,
            "lead": 21.4e-8,
        }
        rho = resistivity_20c[shield.material]

        # Approximate cross-sectional area of shield
        d_s = shield.mean_diameter * 1e-3  # m
        t_s = shield.thickness * 1e-3  # m
        area = math.pi * d_s * t_s  # m² (approximation for thin annular section)

        r20 = rho / area  # ohm/m

    # Temperature coefficient
    alpha = {
        "copper": 0.00393,
        "aluminum": 0.00403,
        "lead": 0.00400,
    }

    r_temp = r20 * (1 + alpha[shield.material] * (temperature - 20))

    return r_temp


def calculate_losses(
    current: float,
    rac: float,
    insulation: InsulationSpec,
    voltage: float,
    shield: Optional[ShieldSpec] = None,
    spacing: float = 0.0,
    frequency: float = 50.0,
) -> dict:
    """
    Calculate all cable losses.

    Args:
        current: Load current in A
        rac: AC resistance of conductor in ohm/m
        insulation: Insulation specification
        voltage: Phase-to-ground voltage in kV
        shield: Shield specification (optional)
        spacing: Axial spacing between conductors in mm
        frequency: System frequency in Hz

    Returns:
        Dictionary with:
        - wc: Conductor losses (W/m)
        - wd: Dielectric losses (W/m)
        - ws: Shield losses (W/m)
        - lambda1: Shield loss factor
        - total: Total losses (W/m)
    """
    # Conductor losses
    wc = current ** 2 * rac

    # Dielectric losses
    wd = calculate_dielectric_loss(insulation, voltage, frequency)

    # Shield losses
    if shield is not None:
        lambda1 = calculate_shield_loss_factor(shield, rac, spacing, frequency)
        ws = lambda1 * wc
    else:
        lambda1 = 0.0
        ws = 0.0

    total = wc + wd + ws

    return {
        "wc": wc,
        "wd": wd,
        "ws": ws,
        "lambda1": lambda1,
        "total": total,
    }
