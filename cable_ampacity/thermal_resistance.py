"""
Thermal Resistance Calculation Module

Calculates thermal resistances:
- R1: Insulation thermal resistance
- R2: Jacket/serving thermal resistance
- R4: External thermal resistance (earth for direct buried)

Based on IEC 60287-2-1 and Neher-McGrath method.
"""

import math
from dataclasses import dataclass
from typing import Literal


# Thermal resistivities (K·m/W)
THERMAL_RESISTIVITY = {
    # Insulation materials
    "xlpe": 3.5,
    "epr": 3.5,
    "paper_oil": 6.0,
    # Jacket materials
    "pvc": 5.0,
    "pe": 3.5,
    "hdpe": 3.5,
    "lead": 0.0,  # Metallic - negligible
    # Bedding/serving
    "jute": 6.0,
    "pvc_tape": 5.0,
}

# Soil thermal resistivities (typical values)
SOIL_THERMAL_RESISTIVITY = {
    "dry_sand": 2.5,
    "moist_sand": 1.0,
    "dry_clay": 1.5,
    "moist_clay": 0.9,
    "wet_soil": 0.5,
    "concrete": 1.0,
    "thermal_backfill": 0.5,
}


@dataclass
class CableGeometry:
    """Cable geometry for thermal calculations."""
    conductor_diameter: float     # mm
    insulation_thickness: float   # mm
    shield_thickness: float       # mm (0 if no metallic shield)
    jacket_thickness: float       # mm
    insulation_material: Literal["xlpe", "epr", "paper_oil"] = "xlpe"
    jacket_material: Literal["pvc", "pe", "hdpe"] = "pe"

    @property
    def insulation_outer_diameter(self) -> float:
        """Diameter over insulation (mm)."""
        return self.conductor_diameter + 2 * self.insulation_thickness

    @property
    def shield_outer_diameter(self) -> float:
        """Diameter over shield (mm)."""
        return self.insulation_outer_diameter + 2 * self.shield_thickness

    @property
    def overall_diameter(self) -> float:
        """Overall cable diameter (mm)."""
        return self.shield_outer_diameter + 2 * self.jacket_thickness


@dataclass
class BurialConditions:
    """Direct burial installation conditions."""
    depth: float                  # Burial depth to cable center (m)
    soil_resistivity: float       # Soil thermal resistivity (K·m/W)
    ambient_temp: float           # Ambient soil temperature (°C)
    spacing: float = 0.0          # Axial spacing between phases (m), 0 for single cable
    num_circuits: int = 1         # Number of parallel circuits
    circuit_spacing: float = 0.0  # Spacing between circuits (m)


def calculate_insulation_thermal_resistance(
    geometry: CableGeometry,
) -> float:
    """
    Calculate thermal resistance of insulation layer (R1).

    R1 = (ρ_T / 2π) × ln(D_i / d_c)

    Args:
        geometry: Cable geometry

    Returns:
        Thermal resistance R1 in K·m/W
    """
    rho_t = THERMAL_RESISTIVITY[geometry.insulation_material]
    d_c = geometry.conductor_diameter  # mm
    d_i = geometry.insulation_outer_diameter  # mm

    r1 = (rho_t / (2 * math.pi)) * math.log(d_i / d_c)

    return r1


def calculate_jacket_thermal_resistance(
    geometry: CableGeometry,
) -> float:
    """
    Calculate thermal resistance of jacket/serving layer (R2).

    R2 = (ρ_T / 2π) × ln(D_e / D_s)

    Args:
        geometry: Cable geometry

    Returns:
        Thermal resistance R2 in K·m/W
    """
    if geometry.jacket_thickness == 0:
        return 0.0

    rho_t = THERMAL_RESISTIVITY[geometry.jacket_material]
    d_s = geometry.shield_outer_diameter  # mm
    d_e = geometry.overall_diameter  # mm

    r2 = (rho_t / (2 * math.pi)) * math.log(d_e / d_s)

    return r2


def calculate_earth_thermal_resistance(
    geometry: CableGeometry,
    burial: BurialConditions,
) -> float:
    """
    Calculate external (earth) thermal resistance (R4) for direct burial.

    Uses the Neher-McGrath formula:
    R4 = (ρ_soil / 2π) × ln(2L/D_e + √((2L/D_e)² - 1))

    Simplified for deep burial (L >> D_e):
    R4 ≈ (ρ_soil / 2π) × ln(4L / D_e)

    Args:
        geometry: Cable geometry
        burial: Burial conditions

    Returns:
        Thermal resistance R4 in K·m/W
    """
    rho_soil = burial.soil_resistivity
    L = burial.depth * 1000  # Convert m to mm
    D_e = geometry.overall_diameter  # mm

    # Neher-McGrath formula
    u = 2 * L / D_e
    if u > 10:
        # Simplified formula for deep burial
        r4 = (rho_soil / (2 * math.pi)) * math.log(4 * L / D_e)
    else:
        # Full formula
        r4 = (rho_soil / (2 * math.pi)) * math.log(u + math.sqrt(u ** 2 - 1))

    return r4


def calculate_mutual_heating_factor(
    geometry: CableGeometry,
    burial: BurialConditions,
) -> float:
    """
    Calculate mutual heating factor for multiple cables.

    The factor accounts for heat from adjacent cables.
    F = 1 + Σ(ρ_soil / 2π) × ln(d'_pk / d_pk)

    where d_pk is distance to cable k
    and d'_pk is distance to image of cable k

    Args:
        geometry: Cable geometry
        burial: Burial conditions

    Returns:
        Mutual heating factor (≥1.0)
    """
    if burial.spacing == 0 or burial.num_circuits <= 1:
        return 1.0

    rho_soil = burial.soil_resistivity
    L = burial.depth  # m
    s = burial.spacing  # m

    # For trefoil arrangement, simplified mutual heating
    # Distance to adjacent cable
    d_pk = s

    # Distance to image of adjacent cable (reflection about ground surface)
    d_pk_image = math.sqrt(s ** 2 + (2 * L) ** 2)

    # Mutual heating contribution per adjacent cable
    delta_r4 = (rho_soil / (2 * math.pi)) * math.log(d_pk_image / d_pk)

    # For trefoil, 2 adjacent cables
    # The mutual heating increases the effective thermal resistance
    factor = 1 + 2 * delta_r4 / calculate_earth_thermal_resistance(geometry, burial)

    return max(1.0, factor)


def calculate_thermal_resistances(
    geometry: CableGeometry,
    burial: BurialConditions,
) -> dict:
    """
    Calculate all thermal resistances for direct buried cable.

    Args:
        geometry: Cable geometry
        burial: Burial conditions

    Returns:
        Dictionary with:
        - r1: Insulation thermal resistance (K·m/W)
        - r2: Jacket thermal resistance (K·m/W)
        - r4: Earth thermal resistance (K·m/W)
        - f_mutual: Mutual heating factor
        - r4_effective: Effective earth resistance with mutual heating (K·m/W)
        - total: Total thermal resistance (K·m/W)
    """
    r1 = calculate_insulation_thermal_resistance(geometry)
    r2 = calculate_jacket_thermal_resistance(geometry)
    r4 = calculate_earth_thermal_resistance(geometry, burial)
    f_mutual = calculate_mutual_heating_factor(geometry, burial)

    r4_effective = r4 * f_mutual
    total = r1 + r2 + r4_effective

    return {
        "r1": r1,
        "r2": r2,
        "r4": r4,
        "f_mutual": f_mutual,
        "r4_effective": r4_effective,
        "total": total,
    }


def calculate_temperature_rise(
    losses: dict,
    thermal_resistances: dict,
    lambda1: float = 0.0,
) -> dict:
    """
    Calculate temperature rise from conductor to ambient.

    Based on the thermal equation:
    ΔT = Wc×(R1 + R2 + R4) + Wd×(0.5×R1 + R2 + R4) + Ws×(R2 + R4)

    For single cable with shield losses represented by λ1:
    ΔT = Wc×[(1+λ1)×R1 + (1+λ1)×R2 + (1+λ1)×R4] + Wd×[0.5×R1 + R2 + R4]

    Args:
        losses: Dictionary with wc, wd, ws values (W/m)
        thermal_resistances: Dictionary with r1, r2, r4_effective values (K·m/W)
        lambda1: Shield loss factor

    Returns:
        Dictionary with temperature rise breakdown (°C)
    """
    wc = losses["wc"]
    wd = losses["wd"]
    r1 = thermal_resistances["r1"]
    r2 = thermal_resistances["r2"]
    r4 = thermal_resistances["r4_effective"]

    # Temperature rise from conductor losses
    # (includes shield losses via (1+λ1) factor)
    delta_t_conductor = wc * (1 + lambda1) * (r1 + r2 + r4)

    # Temperature rise from dielectric losses
    # (generated uniformly in insulation, so use 0.5×R1)
    delta_t_dielectric = wd * (0.5 * r1 + r2 + r4)

    total = delta_t_conductor + delta_t_dielectric

    return {
        "delta_t_conductor": delta_t_conductor,
        "delta_t_dielectric": delta_t_dielectric,
        "total": total,
    }
