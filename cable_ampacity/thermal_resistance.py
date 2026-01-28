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
from typing import Literal, Optional


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
class BackfillLayer:
    """Specification for a backfill/soil layer in the installation.

    CYMCAP-style multi-layer backfill support. Each layer is a rectangular
    region with its own thermal resistivity.
    """
    name: str                     # Layer identifier (e.g., "Thermal Backfill", "Native Soil")
    x_center: float               # X coordinate of layer center (m)
    y_top: float                  # Y coordinate of layer top (m, from surface)
    width: float                  # Layer width (m)
    height: float                 # Layer height/thickness (m)
    thermal_resistivity: float    # Thermal resistivity (K.m/W)

    @property
    def y_bottom(self) -> float:
        """Y coordinate of layer bottom (m)."""
        return self.y_top + self.height

    @property
    def x_left(self) -> float:
        """X coordinate of left edge (m)."""
        return self.x_center - self.width / 2

    @property
    def x_right(self) -> float:
        """X coordinate of right edge (m)."""
        return self.x_center + self.width / 2


@dataclass
class CablePosition:
    """Position of a single cable in the installation.

    Used for multi-cable installations where each cable has unique coordinates.
    """
    x: float                      # X coordinate (m, 0 = center of installation)
    y: float                      # Y coordinate (m, depth from surface)
    circuit_id: int = 1           # Circuit number (for grouping phases)
    phase: str = "A"              # Phase identifier (A, B, C)
    cable_id: Optional[str] = None  # Optional cable identifier


@dataclass
class CableGeometry:
    """Cable geometry for thermal calculations.

    Layer structure (from center outward):
    - Conductor (conductor_diameter)
    - Conductor shield/screen (conductor_shield_thickness) - semiconducting
    - Insulation (insulation_thickness)
    - Insulation screen (insulation_screen_thickness) - semiconducting
    - Metallic shield/sheath (shield_thickness)
    - Jacket (jacket_thickness)
    """
    conductor_diameter: float     # mm
    insulation_thickness: float   # mm
    shield_thickness: float       # mm (0 if no metallic shield)
    jacket_thickness: float       # mm
    insulation_material: Literal["xlpe", "epr", "paper_oil"] = "xlpe"
    jacket_material: Literal["pvc", "pe", "hdpe"] = "pe"
    # Optional additional layers (CYMCAP-style detailed geometry)
    conductor_shield_thickness: float = 0.0   # mm (semiconducting layer over conductor)
    insulation_screen_thickness: float = 0.0  # mm (semiconducting layer over insulation)
    # Optional thermal resistivity overrides
    insulation_thermal_resistivity: Optional[float] = None  # K.m/W (override default)
    jacket_thermal_resistivity: Optional[float] = None      # K.m/W (override default)

    @property
    def conductor_shield_outer_diameter(self) -> float:
        """Diameter over conductor shield (mm)."""
        return self.conductor_diameter + 2 * self.conductor_shield_thickness

    @property
    def insulation_outer_diameter(self) -> float:
        """Diameter over insulation (mm)."""
        return self.conductor_shield_outer_diameter + 2 * self.insulation_thickness

    @property
    def insulation_screen_outer_diameter(self) -> float:
        """Diameter over insulation screen (mm)."""
        return self.insulation_outer_diameter + 2 * self.insulation_screen_thickness

    @property
    def shield_outer_diameter(self) -> float:
        """Diameter over metallic shield (mm)."""
        return self.insulation_screen_outer_diameter + 2 * self.shield_thickness

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
    """Concrete duct bank installation conditions.

    Supports CYMCAP-style multi-layer backfill and explicit cable positions.
    """
    depth: float                  # Depth to top of duct bank (m)
    soil_resistivity: float       # Native soil thermal resistivity (K·m/W)
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
    # CYMCAP-style enhancements
    backfill_layers: Optional[list] = None  # List of BackfillLayer objects
    cable_positions: Optional[list] = None  # List of CablePosition objects (overrides occupied_ducts)
    conduit_thermal_resistivity: Optional[float] = None  # Override default for duct material


def calculate_insulation_thermal_resistance(
    geometry: CableGeometry,
) -> float:
    """
    Calculate thermal resistance of insulation layer (R1).

    R1 = (ρ_T / 2π) × ln(D_i / d_c)

    Note: Includes conductor shield (semiconducting) as it has similar thermal properties.
    The insulation screen is included in R2 or treated as part of the shield assembly.

    Args:
        geometry: Cable geometry

    Returns:
        Thermal resistance R1 in K·m/W
    """
    # Use user-specified thermal resistivity if provided
    rho_t = (geometry.insulation_thermal_resistivity
             if geometry.insulation_thermal_resistivity is not None
             else THERMAL_RESISTIVITY[geometry.insulation_material])

    # Inner diameter: conductor or conductor shield outer diameter
    d_c = geometry.conductor_diameter  # mm
    # Outer diameter: over insulation (includes conductor shield in the thermal path)
    d_i = geometry.insulation_outer_diameter  # mm

    r1 = (rho_t / (2 * math.pi)) * math.log(d_i / d_c)

    return r1


def calculate_jacket_thermal_resistance(
    geometry: CableGeometry,
) -> float:
    """
    Calculate thermal resistance of jacket/serving layer (R2).

    R2 = (ρ_T / 2π) × ln(D_e / D_s)

    Note: Includes insulation screen thermal resistance if present.

    Args:
        geometry: Cable geometry

    Returns:
        Thermal resistance R2 in K·m/W
    """
    if geometry.jacket_thickness == 0:
        return 0.0

    # Use user-specified thermal resistivity if provided
    rho_t = (geometry.jacket_thermal_resistivity
             if geometry.jacket_thermal_resistivity is not None
             else THERMAL_RESISTIVITY[geometry.jacket_material])

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


def find_layer_at_position(
    x: float,
    y: float,
    layers: list,
) -> Optional[BackfillLayer]:
    """
    Find which backfill layer contains the given position.

    Args:
        x: X coordinate (m)
        y: Y coordinate / depth (m)
        layers: List of BackfillLayer objects

    Returns:
        BackfillLayer containing the position, or None if not found
    """
    for layer in layers:
        if (layer.x_left <= x <= layer.x_right and
            layer.y_top <= y <= layer.y_bottom):
            return layer
    return None


def calculate_effective_soil_resistivity(
    cable_x: float,
    cable_y: float,
    layers: list,
    native_soil_resistivity: float,
    for_mutual_heating: bool = False,
) -> float:
    """
    Calculate effective thermal resistivity at a cable position.

    For mutual heating calculations (for_mutual_heating=True), this considers
    all layers from cable depth to surface, using weighted average based on
    layer thickness. This is important because heat from cables must pass
    through all overlying layers to reach the surface.

    For direct R4 calculation (for_mutual_heating=False), returns the resistivity
    of the layer the cable is in.

    Args:
        cable_x: Cable X position (m)
        cable_y: Cable Y position / depth (m)
        layers: List of BackfillLayer objects
        native_soil_resistivity: Resistivity of native soil (K.m/W)
        for_mutual_heating: If True, calculate weighted average for all layers to surface

    Returns:
        Effective thermal resistivity (K.m/W)
    """
    if not layers:
        return native_soil_resistivity

    if for_mutual_heating:
        # For mutual heating, we need to account for the thermal barrier effect
        # of high-resistivity layers near the surface (like gravel bed, surface aggregate)
        # These layers act as a "thermal blanket" that significantly increases
        # the effective resistance for heat dissipation.

        # Sort layers by depth (y_top)
        sorted_layers = sorted(layers, key=lambda l: l.y_top)

        # Calculate contributions from each layer
        # Use logarithmic weighting to emphasize surface layers (per Neher-McGrath)
        total_weighted_rho = 0.0
        total_weight = 0.0

        for layer in sorted_layers:
            # Check if layer is above cable position
            if layer.y_bottom <= cable_y:
                # Layer is completely above cable
                # Weight layers closer to surface more heavily
                # (heat must pass through them to reach ambient)
                depth_factor = 1.0 + (cable_y - layer.y_top) / cable_y
                layer_contribution = layer.height * layer.thermal_resistivity * depth_factor
                total_weighted_rho += layer_contribution
                total_weight += layer.height * depth_factor
            elif layer.y_top < cable_y:
                # Layer partially overlaps with cable position
                overlap = cable_y - layer.y_top
                depth_factor = 1.0 + (cable_y - layer.y_top) / cable_y
                layer_contribution = overlap * layer.thermal_resistivity * depth_factor
                total_weighted_rho += layer_contribution
                total_weight += overlap * depth_factor

        # Add native soil for remaining depth
        if total_weight < cable_y:
            remaining = cable_y - total_weight
            native_contribution = remaining * native_soil_resistivity
            total_weighted_rho += native_contribution
            total_weight += remaining

        if total_weight > 0:
            eff_rho = total_weighted_rho / total_weight
            # Apply correction for layered soil effect on mutual heating
            # High-resistivity surface layers create a "thermal blanket" that
            # significantly increases mutual heating. The simple image method
            # underestimates this effect.
            # CYMCAP and detailed FEM show ~2-3x increase in effective resistance
            # when high-resistivity surface layers are present.
            max_layer_rho = max(layer.thermal_resistivity for layer in layers)
            if max_layer_rho > 1.5 * native_soil_resistivity:
                # Significant high-resistivity layers present
                # Use more aggressive correction based on ratio of max layer to native
                rho_ratio = max_layer_rho / native_soil_resistivity
                correction = 1.0 + 0.5 * (rho_ratio - 1)  # 50% contribution from excess
                eff_rho *= min(correction, 4.0)  # Cap at 4x correction
            return eff_rho
        return native_soil_resistivity

    # For direct calculation - find the layer at cable position
    cable_layer = find_layer_at_position(cable_x, cable_y, layers)

    if cable_layer:
        return cable_layer.thermal_resistivity

    # Cable not in any defined layer - use native soil
    return native_soil_resistivity


def calculate_multilayer_earth_resistance(
    cable_x: float,
    cable_y: float,
    cable_diameter: float,
    layers: list,
    native_soil_resistivity: float,
) -> tuple:
    """
    Calculate earth thermal resistance through multiple backfill layers.

    Uses a layered approach based on Neher-McGrath with corrections for
    multiple soil/backfill regions. The heat path is divided into sections
    through different thermal resistivity zones.

    Args:
        cable_x: Cable X position (m)
        cable_y: Cable Y position / depth (m)
        cable_diameter: Cable outer diameter (mm)
        layers: List of BackfillLayer objects
        native_soil_resistivity: Resistivity of native soil (K.m/W)

    Returns:
        Tuple of (R4, details_dict) where R4 is thermal resistance in K.m/W
        and details_dict contains breakdown by layer
    """
    if not layers:
        # Simple case - uniform soil
        D_e = cable_diameter  # mm
        L = cable_y * 1000  # Convert m to mm
        u = 2 * L / D_e
        if u > 10:
            r4 = (native_soil_resistivity / (2 * math.pi)) * math.log(4 * L / D_e)
        else:
            r4 = (native_soil_resistivity / (2 * math.pi)) * math.log(u + math.sqrt(max(u ** 2 - 1, 0.01)))
        return r4, {"native_soil": r4}

    # Sort layers by y_top (depth from surface)
    sorted_layers = sorted(layers, key=lambda l: l.y_top)

    D_e = cable_diameter / 1000  # Convert to m
    total_r4 = 0.0
    details = {}

    # Heat path segments from cable surface to ground surface
    # We trace the thermal path upward from cable position

    current_depth = cable_y  # Starting depth
    previous_boundary = cable_y + D_e / 2  # Start at cable surface

    # For each layer above the cable (in reverse order from cable to surface)
    layers_above = []
    for layer in sorted_layers:
        # Check if layer is between cable and surface
        if layer.y_bottom <= cable_y and layer.y_top < cable_y:
            # Layer is above cable
            layers_above.append(layer)
        elif layer.y_top <= cable_y <= layer.y_bottom:
            # Cable is within this layer
            layers_above.append(layer)

    # Calculate contribution from each layer
    for layer in reversed(layers_above):
        # Determine the portion of heat path through this layer
        layer_top = max(layer.y_top, 0)  # Don't go above surface
        layer_bottom = min(layer.y_bottom, cable_y)

        if layer_bottom <= layer_top:
            continue

        # Thermal resistance contribution from this layer section
        # Using incremental Neher-McGrath approach
        thickness = layer_bottom - layer_top

        # Simplified contribution based on layer thickness and resistivity
        # R_layer ≈ (ρ / 2π) × thickness / (geometric_mean_radius)
        r_contribution = (layer.thermal_resistivity / (2 * math.pi)) * (thickness / cable_y)

        total_r4 += r_contribution
        details[layer.name] = r_contribution

    # Add native soil contribution for remaining path
    # (from uppermost layer to surface, plus image effects)
    uppermost_y = min([l.y_top for l in layers_above]) if layers_above else cable_y

    if uppermost_y > 0:
        # Native soil from surface to uppermost backfill layer
        native_contribution = (native_soil_resistivity / (2 * math.pi)) * (uppermost_y / cable_y)
        total_r4 += native_contribution
        details["native_soil_above"] = native_contribution

    # Base earth thermal resistance using effective approach
    eff_rho = calculate_effective_soil_resistivity(cable_x, cable_y, layers, native_soil_resistivity)
    L = cable_y * 1000  # mm
    u = 2 * L / D_e / 1000  # Dimensionless
    if u > 10:
        r4_base = (eff_rho / (2 * math.pi)) * math.log(4 * L / (D_e * 1000))
    else:
        r4_base = (eff_rho / (2 * math.pi)) * math.log(u + math.sqrt(max(u ** 2 - 1, 0.01)))

    # Use the more accurate of the two approaches
    # (layered calculation or effective resistivity)
    if total_r4 > 0 and len(details) > 1:
        # Multi-layer case - use layered result
        return total_r4, details
    else:
        # Simple case - use effective resistivity
        return r4_base, {"effective": r4_base}


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


def calculate_cable_mutual_heating(
    target_cable: CablePosition,
    all_cables: list,
    soil_resistivity: float,
    target_current: float,
    other_currents: Optional[dict] = None,
) -> float:
    """
    Calculate mutual heating contribution at a specific cable from all other cables.

    Uses image method: ΔT_mutual = Σ (I_k² × R_ac_k × (1+λ_k)) × (ρ / 2π) × ln(d'_pk / d_pk)

    For simplified case where all cables have same current and losses, this becomes
    a multiplier on the external thermal resistance.

    Args:
        target_cable: The cable position to calculate heating for
        all_cables: List of all CablePosition objects (including target)
        soil_resistivity: Soil thermal resistivity (K.m/W)
        target_current: Current in target cable (A)
        other_currents: Optional dict of {cable_id: current} for different currents

    Returns:
        Additional thermal resistance due to mutual heating (K.m/W)
    """
    if len(all_cables) <= 1:
        return 0.0

    x_t = target_cable.x
    y_t = target_cable.y
    rho = soil_resistivity

    total_mutual = 0.0

    for cable in all_cables:
        # Skip self
        if (cable.x == x_t and cable.y == y_t and
            cable.circuit_id == target_cable.circuit_id and
            cable.phase == target_cable.phase):
            continue

        x_k = cable.x
        y_k = cable.y

        # Distance to other cable
        d_pk = math.sqrt((x_t - x_k) ** 2 + (y_t - y_k) ** 2)

        if d_pk < 0.001:  # Essentially same position
            continue

        # Distance to image of other cable (reflected about ground surface)
        d_pk_image = math.sqrt((x_t - x_k) ** 2 + (y_t + y_k) ** 2)

        # Mutual heating contribution
        # Using image method: ΔR = (ρ / 2π) × ln(d'_pk / d_pk)
        if d_pk_image > d_pk:
            delta_r = (rho / (2 * math.pi)) * math.log(d_pk_image / d_pk)
            total_mutual += delta_r

    return total_mutual


def calculate_iterative_mutual_heating(
    cable_positions: list,
    geometry_od_mm: float,
    duct_bank,
    conductor_rac: float,
    dielectric_loss: float,
    lambda1: float,
    max_temp: float,
    ambient_temp: float,
    r1: float,
    r2: float,
    r3: float,
    max_iterations: int = 20,
    tolerance: float = 0.5,
) -> list:
    """
    Calculate per-cable ampacity using iterative current-weighted mutual heating.

    This method accounts for the fact that hotter cables contribute more heat
    to their neighbors than cooler cables. It iterates until temperatures converge.

    Algorithm (per IEC 60287-3-2):
    1. Initialize all cables at equal currents
    2. Calculate heat output from each cable based on current
    3. Weight mutual heating by relative heat output
    4. Calculate position-specific ampacity
    5. Iterate until ampacities converge

    Args:
        cable_positions: List of CablePosition objects
        geometry_od_mm: Cable overall diameter (mm)
        duct_bank: DuctBankConditions object
        conductor_rac: Conductor AC resistance at max_temp (ohm/m)
        dielectric_loss: Dielectric loss (W/m)
        lambda1: Shield loss factor
        max_temp: Maximum conductor temperature (°C)
        ambient_temp: Ambient soil temperature (°C)
        r1, r2, r3: Internal thermal resistances (K.m/W)
        max_iterations: Maximum iterations for convergence
        tolerance: Ampacity convergence tolerance (A)

    Returns:
        List of dicts with per-cable results including ampacity and mutual heating
    """
    n_cables = len(cable_positions)
    if n_cables == 0:
        return []

    # Use effective soil resistivity if backfill layers are defined
    # This accounts for high-resistivity layers like gravel beds and surface aggregate
    # For mutual heating, we need to consider all layers from cable to surface
    if duct_bank.backfill_layers:
        # Calculate average effective resistivity based on cable positions
        # Using for_mutual_heating=True to consider all layers to surface
        avg_x = sum(cp.x for cp in cable_positions) / n_cables
        avg_y = sum(cp.y for cp in cable_positions) / n_cables
        rho = calculate_effective_soil_resistivity(
            avg_x, avg_y, duct_bank.backfill_layers, duct_bank.soil_resistivity,
            for_mutual_heating=True
        )
    else:
        rho = duct_bank.soil_resistivity

    delta_t_available = max_temp - ambient_temp
    delta_t_dielectric = dielectric_loss * (0.5 * r1 + r2 + r3)
    delta_t_conductor = delta_t_available - delta_t_dielectric

    if delta_t_conductor <= 0:
        return [{"cable_position": cp, "ampacity": 0.0} for cp in cable_positions]

    # Pre-calculate coupling factors F_ij = (ρ/2π) × ln(d'_ij / d_ij)
    # This represents the thermal resistance coupling between cables
    # Uses effective soil resistivity to account for layered backfill
    coupling_factors = [[0.0] * n_cables for _ in range(n_cables)]

    for i in range(n_cables):
        for j in range(n_cables):
            if i == j:
                continue
            xi, yi = cable_positions[i].x, cable_positions[i].y
            xj, yj = cable_positions[j].x, cable_positions[j].y

            # Distance to cable j
            d_ij = math.sqrt((xi - xj) ** 2 + (yi - yj) ** 2)

            # Distance to image of cable j (reflected about ground surface)
            d_ij_image = math.sqrt((xi - xj) ** 2 + (yi + yj) ** 2)

            if d_ij > 0.001 and d_ij_image > d_ij:
                coupling_factors[i][j] = (rho / (2 * math.pi)) * math.log(d_ij_image / d_ij)

    # Calculate R4 for each cable position
    r4_values = []
    for cable in cable_positions:
        if duct_bank.backfill_layers:
            r4, _ = calculate_multilayer_earth_resistance(
                cable.x, cable.y,
                geometry_od_mm,
                duct_bank.backfill_layers,
                duct_bank.soil_resistivity,
            )
        else:
            L = cable.y * 1000  # mm
            D_e = duct_bank.duct_od_mm
            u = 2 * L / D_e
            if u > 10:
                r4 = (rho / (2 * math.pi)) * math.log(4 * L / D_e)
            else:
                r4 = (rho / (2 * math.pi)) * math.log(u + math.sqrt(max(u ** 2 - 1, 0.01)))
        r4_values.append(r4)

    # Initialize with equal currents (no weighting)
    # First pass: calculate base ampacity without current weighting
    ampacities = []
    for i in range(n_cables):
        r_mutual_unweighted = sum(coupling_factors[i])
        r4_total = r4_values[i] + r_mutual_unweighted
        r_conductor = (1 + lambda1) * (r1 + r2 + r3 + r4_total)
        if r_conductor > 0 and delta_t_conductor > 0:
            amp = math.sqrt(delta_t_conductor / (conductor_rac * r_conductor))
        else:
            amp = 0.0
        ampacities.append(amp)

    # Iterative refinement with current-weighted mutual heating
    for iteration in range(max_iterations):
        # Calculate heat output for each cable based on current ampacity
        # Q_i = I_i² × Rac × (1 + λ1)
        heat_outputs = [(amp ** 2 * conductor_rac * (1 + lambda1)) for amp in ampacities]
        total_heat = sum(heat_outputs)
        if total_heat <= 0:
            break

        # Normalize heat outputs to weights
        heat_weights = [q / (total_heat / n_cables) if total_heat > 0 else 1.0 for q in heat_outputs]

        new_ampacities = []
        for i in range(n_cables):
            # Calculate weighted mutual heating
            # Cables with higher heat output contribute more to mutual heating
            r_mutual_weighted = 0.0
            for j in range(n_cables):
                if i != j:
                    # Weight by relative heat output of cable j
                    r_mutual_weighted += coupling_factors[i][j] * heat_weights[j]

            r4_total = r4_values[i] + r_mutual_weighted
            r_conductor = (1 + lambda1) * (r1 + r2 + r3 + r4_total)

            if r_conductor > 0 and delta_t_conductor > 0:
                amp = math.sqrt(delta_t_conductor / (conductor_rac * r_conductor))
            else:
                amp = 0.0
            new_ampacities.append(amp)

        # Check convergence
        max_diff = max(abs(new_ampacities[i] - ampacities[i]) for i in range(n_cables))
        ampacities = new_ampacities

        if max_diff < tolerance:
            break

    # Build results
    results = []
    for i in range(n_cables):
        # Final mutual heating calculation
        r_mutual = sum(coupling_factors[i][j] * heat_weights[j] for j in range(n_cables) if i != j)

        results.append({
            "cable_position": cable_positions[i],
            "ampacity": ampacities[i],
            "r1": r1,
            "r2": r2,
            "r3": r3,
            "r4": r4_values[i],
            "r_mutual": r_mutual,
            "r4_total": r4_values[i] + r_mutual,
            "delta_t_conductor": delta_t_conductor,
            "delta_t_dielectric": delta_t_dielectric,
            "iterations": iteration + 1,
        })

    return results


def calculate_per_cable_ampacity(
    geometry: CableGeometry,
    cable_positions: list,
    duct_bank: DuctBankConditions,
    conductor_rac: float,
    dielectric_loss: float,
    lambda1: float,
    max_temp: float,
    ambient_temp: float,
    use_iterative: bool = True,
) -> list:
    """
    Calculate ampacity for each cable position considering mutual heating.

    This is the CYMCAP-style per-cable calculation that gives different
    ampacity values for cables at different positions.

    Uses iterative current-weighted mutual heating by default for improved
    accuracy matching CYMCAP results.

    Args:
        geometry: Cable geometry
        cable_positions: List of CablePosition objects
        duct_bank: Duct bank conditions
        conductor_rac: Conductor AC resistance (ohm/m) at max temp
        dielectric_loss: Dielectric loss (W/m)
        lambda1: Shield loss factor
        max_temp: Maximum conductor temperature (°C)
        ambient_temp: Ambient soil temperature (°C)
        use_iterative: Use iterative mutual heating solver (default True)

    Returns:
        List of dicts with {position, ampacity, temperature_rise, mutual_heating}
    """
    # Calculate internal thermal resistances (same for all cables)
    r1 = calculate_insulation_thermal_resistance(geometry)
    r2 = calculate_jacket_thermal_resistance(geometry)

    # Duct thermal resistance
    r3_air = calculate_conduit_air_gap_resistance(
        geometry.overall_diameter,
        duct_bank.duct_id_mm,
    )
    duct_rho = (duct_bank.conduit_thermal_resistivity
                if duct_bank.conduit_thermal_resistivity
                else CONDUIT_THERMAL_RESISTIVITY.get(duct_bank.duct_material, 6.0))
    r3_wall = (duct_rho / (2 * math.pi)) * math.log(
        duct_bank.duct_od_mm / duct_bank.duct_id_mm
    )
    r3 = r3_air + r3_wall

    # Use iterative method for improved accuracy
    if use_iterative and len(cable_positions) > 1:
        return calculate_iterative_mutual_heating(
            cable_positions=cable_positions,
            geometry_od_mm=geometry.overall_diameter,
            duct_bank=duct_bank,
            conductor_rac=conductor_rac,
            dielectric_loss=dielectric_loss,
            lambda1=lambda1,
            max_temp=max_temp,
            ambient_temp=ambient_temp,
            r1=r1,
            r2=r2,
            r3=r3,
        )

    # Fallback to simple method (for single cable or when iterative disabled)
    results = []
    delta_t_available = max_temp - ambient_temp
    delta_t_dielectric = dielectric_loss * (0.5 * r1 + r2 + r3)

    for cable in cable_positions:
        # Calculate earth thermal resistance for this position
        if duct_bank.backfill_layers:
            r4, layer_details = calculate_multilayer_earth_resistance(
                cable.x, cable.y,
                geometry.overall_diameter,
                duct_bank.backfill_layers,
                duct_bank.soil_resistivity,
            )
        else:
            # Simple earth resistance
            L = cable.y * 1000  # mm
            D_e = duct_bank.duct_od_mm
            u = 2 * L / D_e
            if u > 10:
                r4 = (duct_bank.soil_resistivity / (2 * math.pi)) * math.log(4 * L / D_e)
            else:
                r4 = (duct_bank.soil_resistivity / (2 * math.pi)) * math.log(
                    u + math.sqrt(max(u ** 2 - 1, 0.01))
                )
            layer_details = {"soil": r4}

        # Calculate mutual heating from other cables (simple method)
        r_mutual = calculate_cable_mutual_heating(
            cable, cable_positions,
            duct_bank.soil_resistivity,
            0,  # Current not needed for resistance calculation
        )

        # Total external resistance with mutual heating
        r4_total = r4 + r_mutual

        # Temperature rise for conductor (excluding dielectric)
        delta_t_conductor = delta_t_available - delta_t_dielectric

        # Thermal resistance for conductor heat
        r_conductor = (1 + lambda1) * (r1 + r2 + r3 + r4_total)

        # Calculate ampacity
        if r_conductor > 0 and delta_t_conductor > 0:
            ampacity = math.sqrt(delta_t_conductor / (conductor_rac * r_conductor))
        else:
            ampacity = 0.0

        results.append({
            "cable_position": cable,
            "ampacity": ampacity,
            "r1": r1,
            "r2": r2,
            "r3": r3,
            "r4": r4,
            "r_mutual": r_mutual,
            "r4_total": r4_total,
            "delta_t_conductor": delta_t_conductor,
            "delta_t_dielectric": delta_t_dielectric,
            "layer_details": layer_details,
        })

    return results


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


def calculate_iec_geometric_factor(
    x_cable: float,
    y_cable: float,
    duct_od_m: float,
    bank_left: float,
    bank_right: float,
    bank_top: float,
    bank_bottom: float,
) -> float:
    """
    Calculate geometric factor G per IEC 60287-2-1 Section 2.2.7.

    Uses Kennelly's formula for a cylindrical heat source in a rectangular
    region with isothermal boundaries. This properly accounts for heat flow
    to all four boundaries of the concrete encasement.

    Args:
        x_cable: Cable X position (m)
        y_cable: Cable Y position (depth, m)
        duct_od_m: Duct outer diameter (m)
        bank_left: Left boundary X coordinate (m)
        bank_right: Right boundary X coordinate (m)
        bank_top: Top boundary Y coordinate (m, depth)
        bank_bottom: Bottom boundary Y coordinate (m, depth)

    Returns:
        Geometric factor G (dimensionless)
    """
    r_duct = duct_od_m / 2

    # Distance to each boundary
    d_left = abs(x_cable - bank_left)
    d_right = abs(bank_right - x_cable)
    d_top = abs(y_cable - bank_top)
    d_bottom = abs(bank_bottom - y_cable)

    # Ensure minimum distances (at least 1.1 times duct radius)
    min_dist = r_duct * 1.1
    d_left = max(d_left, min_dist)
    d_right = max(d_right, min_dist)
    d_top = max(d_top, min_dist)
    d_bottom = max(d_bottom, min_dist)

    # IEC 60287-2-1 Kennelly formula for geometric factor
    # G = (1/π) × Σ ln(2×d_i / r) where sum is over all boundaries
    # For a rectangular enclosure with 4 boundaries:
    # G = (1/π) × [ln(2d_top/r) + ln(2d_bottom/r) + ln(2d_left/r) + ln(2d_right/r)] / 4
    #
    # Simplified: G = ln(geometric_mean_of_2d_i/r)
    # where geometric_mean = (2d_top × 2d_bottom × 2d_left × 2d_right)^0.25

    geometric_mean = (2 * d_top * 2 * d_bottom * 2 * d_left * 2 * d_right) ** 0.25
    G = math.log(geometric_mean / r_duct)

    # Apply correction for aspect ratio of the bank
    # Wide shallow banks vs narrow deep banks have different thermal behavior
    aspect_ratio = (bank_right - bank_left) / max(bank_bottom - bank_top, 0.1)
    if aspect_ratio > 2 or aspect_ratio < 0.5:
        # Correction factor for non-square banks (CIGRE guidance)
        G *= 1.0 + 0.05 * abs(math.log(aspect_ratio))

    return max(G, 0.5)  # Minimum practical value


def calculate_multiregion_thermal_resistance(
    cable_x: float,
    cable_y: float,
    duct_od_mm: float,
    duct_bank,
) -> tuple:
    """
    Calculate external thermal resistance through multiple regions per IEC 60287-2-1.

    Implements the multi-region thermal model for cables in ducts in concrete:
    R_external = R_concrete + R_soil

    The thermal path is:
    1. Duct surface to concrete boundary (R_concrete)
    2. Concrete surface to remote soil (R_soil)

    Args:
        cable_x: Cable X position (m)
        cable_y: Cable Y position (depth, m)
        duct_od_mm: Duct outer diameter (mm)
        duct_bank: DuctBankConditions object

    Returns:
        Tuple of (r_concrete, r_soil, details_dict)
    """
    duct_od_m = duct_od_mm / 1000
    r_duct = duct_od_m / 2

    # Bank boundaries
    bank_left = -duct_bank.bank_width / 2
    bank_right = duct_bank.bank_width / 2
    bank_top = duct_bank.depth
    bank_bottom = duct_bank.depth + duct_bank.bank_height

    # R_concrete using IEC geometric factor
    G = calculate_iec_geometric_factor(
        cable_x, cable_y, duct_od_m,
        bank_left, bank_right, bank_top, bank_bottom
    )

    rho_concrete = duct_bank.concrete_resistivity
    r_concrete = (rho_concrete / (2 * math.pi)) * G

    # R_soil from bank surface to remote ground
    # Use equivalent diameter approach per IEC 60287-2-1
    # D_eq = sqrt(bank_width × bank_height)
    D_eq = math.sqrt(duct_bank.bank_width * duct_bank.bank_height)

    # Equivalent burial depth to center of bank
    L_eq = duct_bank.depth + duct_bank.bank_height / 2

    # External thermal resistance using Neher-McGrath formula
    u = 2 * L_eq / D_eq
    if u > 10:
        r_soil = (duct_bank.soil_resistivity / (2 * math.pi)) * math.log(4 * L_eq / D_eq)
    else:
        r_soil = (duct_bank.soil_resistivity / (2 * math.pi)) * math.log(
            u + math.sqrt(max(u ** 2 - 1, 0.01))
        )

    details = {
        "G_factor": G,
        "r_concrete": r_concrete,
        "r_soil": r_soil,
        "bank_boundaries": {
            "left": bank_left,
            "right": bank_right,
            "top": bank_top,
            "bottom": bank_bottom,
        },
        "equivalent_diameter": D_eq,
        "equivalent_depth": L_eq,
    }

    return r_concrete, r_soil, details


def calculate_duct_geometric_factor(
    x: float,
    y: float,
    bank_width: float,
    bank_height: float,
    depth: float,
) -> float:
    """
    Calculate geometric factor G for a duct position in concrete.

    DEPRECATED: Use calculate_iec_geometric_factor for IEC 60287-2-1 compliance.
    This function is kept for backward compatibility.

    Args:
        x: Horizontal position from bank center (m)
        y: Depth to duct center (m)
        bank_width: Bank width (m)
        bank_height: Bank height (m)
        depth: Depth to top of bank (m)

    Returns:
        Geometric factor G (as distance, not logarithmic)
    """
    # Convert to IEC function format and return distance (for backward compat)
    bank_left = -bank_width / 2
    bank_right = bank_width / 2
    bank_top = depth
    bank_bottom = depth + bank_height

    # Distances to concrete boundaries
    d_top = y - depth
    d_bottom = (depth + bank_height) - y
    d_left = bank_width / 2 + x
    d_right = bank_width / 2 - x

    # Ensure positive values
    d_top = max(d_top, 0.01)
    d_bottom = max(d_bottom, 0.01)
    d_left = max(d_left, 0.01)
    d_right = max(d_right, 0.01)

    # Geometric mean of distances (old method for backward compat)
    d_mean = (d_top * d_bottom * d_left * d_right) ** 0.25

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

    # Use IEC 60287-2-1 multi-region thermal resistance calculation
    r_concrete, r4, thermal_details = calculate_multiregion_thermal_resistance(
        cable_x=x,
        cable_y=y,
        duct_od_mm=duct_bank.duct_od_mm,
        duct_bank=duct_bank,
    )

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
                mutual_contrib = (duct_bank.soil_resistivity / (2 * math.pi)) * math.log(d_pk_image / d_pk)
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
