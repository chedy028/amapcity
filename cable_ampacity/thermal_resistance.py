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

# Conduit material thermal resistivities (K·m/W)
CONDUIT_THERMAL_RESISTIVITY = {
    "pvc": 6.0,
    "hdpe": 3.5,
    "fiberglass": 4.0,
    "steel": 0.05,  # Negligible but included
}

# Concrete thermal resistivity (K·m/W) - typical range 0.8-1.2
CONCRETE_THERMAL_RESISTIVITY = 1.0


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


@dataclass
class ConduitConditions:
    """Conduit installation conditions (cable in conduit in soil)."""
    depth: float                  # Burial depth to conduit center (m)
    soil_resistivity: float       # Soil thermal resistivity (K·m/W)
    ambient_temp: float           # Ambient soil temperature (°C)
    conduit_id_mm: float          # Conduit inner diameter (mm)
    conduit_od_mm: float          # Conduit outer diameter (mm)
    conduit_material: str = "pvc" # 'pvc', 'hdpe', 'fiberglass', 'steel'
    num_cables_in_conduit: int = 1  # Number of cables in conduit (usually 1 for HV)
    spacing: float = 0.0          # Spacing between conduits (m)
    num_conduits: int = 1         # Number of conduits


@dataclass
class DuctBankConditions:
    """Concrete duct bank installation conditions."""
    depth: float                  # Depth to top of duct bank (m)
    soil_resistivity: float       # Soil thermal resistivity (K·m/W)
    concrete_resistivity: float   # Concrete thermal resistivity (K·m/W)
    ambient_temp: float           # Ambient soil temperature (°C)
    bank_width: float             # Duct bank width (m)
    bank_height: float            # Duct bank height (m)
    duct_rows: int                # Number of duct rows
    duct_cols: int                # Number of duct columns
    duct_spacing_h: float         # Horizontal center-to-center spacing (m)
    duct_spacing_v: float         # Vertical center-to-center spacing (m)
    duct_id_mm: float             # Duct inner diameter (mm)
    duct_od_mm: float             # Duct outer diameter (mm)
    duct_material: str = "pvc"    # Duct material
    occupied_ducts: list = None   # List of (row, col) tuples for occupied ducts
    edge_distance: float = 0.075  # Distance from edge to first duct center (m)


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


# =============================================================================
# Conduit Installation Functions
# =============================================================================

def calculate_conduit_air_gap_resistance(
    cable_diameter_mm: float,
    conduit_id_mm: float,
    mean_temperature: float = 50.0,
) -> float:
    """
    Calculate thermal resistance of air gap between cable and conduit.

    Based on IEC 60287-2-1 method for cables in ducts.
    R_air = 1 / (1 + B1 * (1 + 0.1 * (V + Y*theta_m) * De))

    Simplified approach using empirical coefficients.

    Args:
        cable_diameter_mm: Cable outer diameter (mm)
        conduit_id_mm: Conduit inner diameter (mm)
        mean_temperature: Mean air temperature in gap (°C)

    Returns:
        Air gap thermal resistance (K·m/W)
    """
    D_cable = cable_diameter_mm / 1000  # Convert to m
    D_conduit = conduit_id_mm / 1000    # Convert to m

    # Fill factor (ratio of cable area to conduit area)
    fill_factor = (D_cable / D_conduit) ** 2

    # IEC 60287-2-1 coefficients for air gap
    # These depend on whether cable is in free air or touching conduit
    # Using simplified correlation for single cable in conduit

    # Empirical constants (from IEC 60287-2-1 Table 2)
    U = 1.87  # For black surface (typical cable jacket)
    Y = 0.026  # Temperature coefficient
    V = 0.29  # Velocity coefficient (natural convection)

    # Mean temperature rise above ambient
    theta_m = mean_temperature - 20.0  # Reference 20°C

    # Convection/radiation coefficient
    h = 1 + 0.1 * (V + Y * theta_m) * D_conduit * 1000  # D in mm for formula

    # Air gap thermal resistance
    # For single cable not touching conduit wall
    T4_prime = U / (math.pi * D_cable * 1000 * h)

    return T4_prime


def calculate_conduit_wall_resistance(
    conduit_id_mm: float,
    conduit_od_mm: float,
    conduit_material: str = "pvc",
) -> float:
    """
    Calculate thermal resistance of conduit wall.

    R_conduit = (rho / 2*pi) * ln(D_outer / D_inner)

    Args:
        conduit_id_mm: Inner diameter (mm)
        conduit_od_mm: Outer diameter (mm)
        conduit_material: Material type

    Returns:
        Conduit wall thermal resistance (K·m/W)
    """
    rho = CONDUIT_THERMAL_RESISTIVITY.get(conduit_material, 6.0)

    r_conduit = (rho / (2 * math.pi)) * math.log(conduit_od_mm / conduit_id_mm)

    return r_conduit


def calculate_conduit_thermal_resistances(
    geometry: CableGeometry,
    conduit: ConduitConditions,
) -> dict:
    """
    Calculate all thermal resistances for cable in conduit installation.

    Args:
        geometry: Cable geometry
        conduit: Conduit installation conditions

    Returns:
        Dictionary with all thermal resistance components
    """
    # R1, R2 - same as direct buried
    r1 = calculate_insulation_thermal_resistance(geometry)
    r2 = calculate_jacket_thermal_resistance(geometry)

    # R3 - conduit thermal resistance (air gap + wall)
    r3_air = calculate_conduit_air_gap_resistance(
        geometry.overall_diameter,
        conduit.conduit_id_mm,
    )
    r3_wall = calculate_conduit_wall_resistance(
        conduit.conduit_id_mm,
        conduit.conduit_od_mm,
        conduit.conduit_material,
    )
    r3 = r3_air + r3_wall

    # R4 - earth thermal resistance (from conduit OD)
    # Using Neher-McGrath formula with conduit diameter
    rho_soil = conduit.soil_resistivity
    L = conduit.depth * 1000  # Convert m to mm
    D_e = conduit.conduit_od_mm  # mm

    u = 2 * L / D_e
    if u > 10:
        r4 = (rho_soil / (2 * math.pi)) * math.log(4 * L / D_e)
    else:
        r4 = (rho_soil / (2 * math.pi)) * math.log(u + math.sqrt(u ** 2 - 1))

    # Mutual heating for multiple conduits
    f_mutual = 1.0
    if conduit.num_conduits > 1 and conduit.spacing > 0:
        s = conduit.spacing  # m
        L_m = conduit.depth  # m
        d_pk = s
        d_pk_image = math.sqrt(s ** 2 + (2 * L_m) ** 2)
        delta_f = (rho_soil / (2 * math.pi)) * math.log(d_pk_image / d_pk)
        f_mutual = 1 + (conduit.num_conduits - 1) * delta_f / r4

    r4_effective = r4 * f_mutual
    total = r1 + r2 + r3 + r4_effective

    return {
        "r1": r1,
        "r2": r2,
        "r3": r3,
        "r3_air": r3_air,
        "r3_wall": r3_wall,
        "r4": r4,
        "f_mutual": f_mutual,
        "r4_effective": r4_effective,
        "total": total,
    }


# =============================================================================
# Duct Bank Installation Functions
# =============================================================================

def calculate_duct_position_coordinates(
    duct_bank: DuctBankConditions,
) -> list:
    """
    Calculate x, y coordinates for each duct in the bank.

    Origin is at ground surface, directly above bank center.
    Y is positive downward.

    Args:
        duct_bank: Duct bank conditions

    Returns:
        List of (row, col, x, y) tuples for each duct
    """
    positions = []

    # Bank center depth (from top of bank)
    bank_center_y = duct_bank.depth + duct_bank.bank_height / 2

    # Calculate starting positions
    total_width = (duct_bank.duct_cols - 1) * duct_bank.duct_spacing_h
    total_height = (duct_bank.duct_rows - 1) * duct_bank.duct_spacing_v

    start_x = -total_width / 2
    start_y = bank_center_y - total_height / 2

    for row in range(duct_bank.duct_rows):
        for col in range(duct_bank.duct_cols):
            x = start_x + col * duct_bank.duct_spacing_h
            y = start_y + row * duct_bank.duct_spacing_v
            positions.append((row, col, x, y))

    return positions


def calculate_duct_geometric_factor(
    x: float,
    y: float,
    bank_width: float,
    bank_height: float,
    depth: float,
) -> float:
    """
    Calculate geometric factor G for a duct position in concrete.

    G accounts for the distance from duct to concrete-soil boundary.
    Simplified as logarithmic mean of distances to boundaries.

    Args:
        x: Horizontal position from bank center (m)
        y: Depth to duct center (m)
        bank_width: Bank width (m)
        bank_height: Bank height (m)
        depth: Depth to top of bank (m)

    Returns:
        Geometric factor G
    """
    # Distance to each boundary of concrete
    bank_center_y = depth + bank_height / 2

    # Distances to concrete boundaries
    d_top = y - depth  # Distance to top of bank
    d_bottom = (depth + bank_height) - y  # Distance to bottom
    d_left = bank_width / 2 + x  # Distance to left edge
    d_right = bank_width / 2 - x  # Distance to right edge

    # Ensure positive values
    d_top = max(d_top, 0.01)
    d_bottom = max(d_bottom, 0.01)
    d_left = max(d_left, 0.01)
    d_right = max(d_right, 0.01)

    # Geometric factor - using Kennelly's formula approximation
    # G = ln(geometric mean distance to boundaries)
    d_mean = (d_top * d_bottom * d_left * d_right) ** 0.25

    # For a duct of radius r_duct, G = ln(d_mean / r_duct)
    # We'll apply this in the main calculation

    return d_mean


def calculate_ductbank_thermal_resistances(
    geometry: CableGeometry,
    duct_bank: DuctBankConditions,
    target_duct: tuple = None,  # (row, col) of duct to calculate for
) -> dict:
    """
    Calculate thermal resistances for cable in concrete duct bank.

    Args:
        geometry: Cable geometry
        duct_bank: Duct bank installation conditions
        target_duct: Specific duct position (row, col), defaults to worst case

    Returns:
        Dictionary with all thermal resistance components
    """
    # R1, R2 - cable internal resistances
    r1 = calculate_insulation_thermal_resistance(geometry)
    r2 = calculate_jacket_thermal_resistance(geometry)

    # R3 - duct thermal resistance (air gap + duct wall)
    r3_air = calculate_conduit_air_gap_resistance(
        geometry.overall_diameter,
        duct_bank.duct_id_mm,
    )
    r3_wall = calculate_conduit_wall_resistance(
        duct_bank.duct_id_mm,
        duct_bank.duct_od_mm,
        duct_bank.duct_material,
    )
    r3 = r3_air + r3_wall

    # Get duct positions
    positions = calculate_duct_position_coordinates(duct_bank)

    # Determine which duct to calculate (worst case = center-bottom typically)
    if target_duct is None:
        # Find center duct in bottom row (typically hottest)
        center_col = duct_bank.duct_cols // 2
        bottom_row = duct_bank.duct_rows - 1
        target_duct = (bottom_row, center_col)

    # Find target duct position
    target_pos = None
    for pos in positions:
        if pos[0] == target_duct[0] and pos[1] == target_duct[1]:
            target_pos = pos
            break

    if target_pos is None:
        target_pos = positions[0]  # Fallback

    _, _, x, y = target_pos

    # R_concrete - thermal resistance through concrete
    # R_concrete = (rho_concrete / 2*pi) * G
    rho_concrete = duct_bank.concrete_resistivity

    G_factor = calculate_duct_geometric_factor(
        x, y,
        duct_bank.bank_width,
        duct_bank.bank_height,
        duct_bank.depth,
    )

    # Duct radius in meters
    r_duct = duct_bank.duct_od_mm / 2000

    # Geometric factor for concrete resistance
    G = math.log(G_factor / r_duct) if G_factor > r_duct else 0.5
    r_concrete = (rho_concrete / (2 * math.pi)) * G

    # R4 - earth thermal resistance from duct bank surface
    # Use equivalent diameter approach
    rho_soil = duct_bank.soil_resistivity

    # Equivalent diameter of duct bank
    D_eq = math.sqrt(duct_bank.bank_width * duct_bank.bank_height) * 1000  # mm

    # Equivalent depth to center of duct bank
    L_eq = (duct_bank.depth + duct_bank.bank_height / 2) * 1000  # mm

    u = 2 * L_eq / D_eq
    if u > 10:
        r4 = (rho_soil / (2 * math.pi)) * math.log(4 * L_eq / D_eq)
    else:
        r4 = (rho_soil / (2 * math.pi)) * math.log(u + math.sqrt(max(u ** 2 - 1, 0.01)))

    # Mutual heating factor for multiple occupied ducts
    f_mutual = 1.0
    occupied = duct_bank.occupied_ducts or [target_duct]

    if len(occupied) > 1:
        # Calculate mutual heating from other occupied ducts
        total_mutual = 0.0
        for occ in occupied:
            if occ == target_duct:
                continue
            # Find position of this occupied duct
            occ_pos = None
            for pos in positions:
                if pos[0] == occ[0] and pos[1] == occ[1]:
                    occ_pos = pos
                    break
            if occ_pos is None:
                continue

            _, _, ox, oy = occ_pos

            # Distance between ducts
            d_pk = math.sqrt((x - ox) ** 2 + (y - oy) ** 2)
            d_pk = max(d_pk, 0.01)  # Avoid division by zero

            # Distance to image of other duct
            d_pk_image = math.sqrt((x - ox) ** 2 + (y + oy) ** 2)

            # Mutual heating contribution
            if d_pk_image > d_pk:
                mutual_contrib = (rho_soil / (2 * math.pi)) * math.log(d_pk_image / d_pk)
                total_mutual += mutual_contrib

        if r4 > 0:
            f_mutual = 1 + total_mutual / r4

    r4_effective = r4 * f_mutual
    total = r1 + r2 + r3 + r_concrete + r4_effective

    return {
        "r1": r1,
        "r2": r2,
        "r3": r3,
        "r3_air": r3_air,
        "r3_wall": r3_wall,
        "r_concrete": r_concrete,
        "r4": r4,
        "f_mutual": f_mutual,
        "r4_effective": r4_effective,
        "total": total,
        "target_duct": target_duct,
        "duct_positions": positions,
    }
