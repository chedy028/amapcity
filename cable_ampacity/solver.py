"""
Ampacity Solver Module

Main solver that calculates cable ampacity using iterative method.
Based on Neher-McGrath (1957) and IEC 60287 standards.
"""

import math
from dataclasses import dataclass
from typing import Literal, Optional, Union

from .ac_resistance import ConductorSpec, calculate_ac_resistance
from .losses import (
    InsulationSpec,
    ShieldSpec,
    calculate_dielectric_loss,
    calculate_shield_loss_factor,
    MAX_CONDUCTOR_TEMP,
)
from .thermal_resistance import (
    CableGeometry,
    BurialConditions,
    ConduitConditions,
    DuctBankConditions,
    calculate_thermal_resistances,
    calculate_conduit_thermal_resistances,
    calculate_ductbank_thermal_resistances,
)


@dataclass
class CableSpec:
    """Complete cable specification for ampacity calculation.

    Supports CYMCAP-aligned optional parameters for detailed cable geometry.
    """
    # Conductor
    conductor: ConductorSpec
    # Insulation
    insulation: InsulationSpec
    # Shield (optional)
    shield: Optional[ShieldSpec] = None
    # Jacket
    jacket_thickness: float = 3.0  # mm
    jacket_material: Literal["pvc", "pe", "hdpe"] = "pe"
    # CYMCAP-aligned optional layers
    conductor_shield_thickness: float = 0.0  # mm (semiconducting layer over conductor)
    insulation_screen_thickness: float = 0.0  # mm (semiconducting layer over insulation)
    # CYMCAP-aligned optional thermal resistivity overrides
    insulation_thermal_resistivity: Optional[float] = None  # K.m/W
    jacket_thermal_resistivity: Optional[float] = None  # K.m/W

    @property
    def geometry(self) -> CableGeometry:
        """Create CableGeometry from cable spec."""
        shield_thickness = self.shield.thickness if self.shield else 0.0
        return CableGeometry(
            conductor_diameter=self.conductor.diameter,
            insulation_thickness=self.insulation.thickness,
            shield_thickness=shield_thickness,
            jacket_thickness=self.jacket_thickness,
            insulation_material=self.insulation.material,
            jacket_material=self.jacket_material,
            # CYMCAP-aligned parameters
            conductor_shield_thickness=self.conductor_shield_thickness,
            insulation_screen_thickness=self.insulation_screen_thickness,
            insulation_thermal_resistivity=self.insulation_thermal_resistivity,
            jacket_thermal_resistivity=self.jacket_thermal_resistivity,
        )


@dataclass
class OperatingConditions:
    """Operating conditions for ampacity calculation."""
    voltage: float                # Phase-to-ground voltage (kV)
    frequency: float = 50.0       # System frequency (Hz)
    max_conductor_temp: Optional[float] = None  # Override max temp (°C)
    load_factor: float = 1.0      # Load factor for cyclic rating (0-1)


# Type alias for installation conditions
InstallationConditions = Union[BurialConditions, ConduitConditions, DuctBankConditions]


def calculate_ampacity(
    cable: CableSpec,
    installation: InstallationConditions,
    operating: OperatingConditions,
    tolerance: float = 0.01,
    max_iterations: int = 100,
) -> dict:
    """
    Calculate cable ampacity using iterative method.

    The ampacity is found by solving the thermal equation:
    ΔT = I²·Rac·(1+λ1)·ΣR + Wd·ΣR'

    where:
    - ΔT = Tc_max - T_ambient
    - Rac = AC resistance at conductor temperature
    - λ1 = shield loss factor
    - ΣR = sum of thermal resistances
    - Wd = dielectric losses
    - ΣR' = modified thermal resistance sum for dielectric losses

    Args:
        cable: Cable specification
        installation: Installation conditions (burial, conduit, or duct bank)
        operating: Operating conditions
        tolerance: Convergence tolerance for ampacity (A)
        max_iterations: Maximum iterations

    Returns:
        Dictionary with ampacity and detailed breakdown
    """
    # Maximum conductor temperature
    if operating.max_conductor_temp is not None:
        tc_max = operating.max_conductor_temp
    else:
        tc_max = MAX_CONDUCTOR_TEMP[cable.insulation.material]

    # Temperature difference available
    delta_t_available = tc_max - installation.ambient_temp

    # Determine installation type and calculate thermal resistances
    geometry = cable.geometry

    if isinstance(installation, DuctBankConditions):
        installation_type = "duct_bank"
        thermal_r = calculate_ductbank_thermal_resistances(geometry, installation)
        spacing = installation.duct_spacing_h * 1000  # m to mm for resistance calc
    elif isinstance(installation, ConduitConditions):
        installation_type = "conduit"
        thermal_r = calculate_conduit_thermal_resistances(geometry, installation)
        spacing = installation.spacing * 1000  # m to mm
    else:
        installation_type = "direct_buried"
        thermal_r = calculate_thermal_resistances(geometry, installation)
        spacing = installation.spacing * 1000  # m to mm

    # Calculate dielectric losses (constant, independent of current)
    wd = calculate_dielectric_loss(
        cable.insulation,
        operating.voltage,
        operating.frequency,
    )

    # Calculate shield loss factor (approximate, will be refined)
    if cable.shield is not None:
        # Initial estimate using approximate conductor resistance
        r_init = calculate_ac_resistance(
            cable.conductor,
            temperature=tc_max,
            spacing=spacing,
            frequency=operating.frequency,
        )
        lambda1 = calculate_shield_loss_factor(
            cable.shield,
            r_init["rac"],
            spacing,
            operating.frequency,
        )
    else:
        lambda1 = 0.0

    # Thermal resistance sums
    r1 = thermal_r["r1"]
    r2 = thermal_r["r2"]
    r4 = thermal_r["r4_effective"]

    # R3 (conduit) and R_concrete only apply for certain installation types
    r3 = thermal_r.get("r3", 0.0)
    r_concrete = thermal_r.get("r_concrete", 0.0)

    # For conductor losses: R_total = (1+λ1)×(R1 + R2 + R3 + R_concrete + R4)
    r_conductor = (1 + lambda1) * (r1 + r2 + r3 + r_concrete + r4)

    # For dielectric losses: R_dielectric = 0.5×R1 + R2 + R3 + R_concrete + R4
    r_dielectric = 0.5 * r1 + r2 + r3 + r_concrete + r4

    # Temperature rise from dielectric losses (constant)
    delta_t_dielectric = wd * r_dielectric

    # Temperature available for conductor losses
    delta_t_conductor = delta_t_available - delta_t_dielectric

    if delta_t_conductor <= 0:
        raise ValueError(
            f"Dielectric losses exceed available temperature rise. "
            f"ΔT_available={delta_t_available:.1f}°C, ΔT_dielectric={delta_t_dielectric:.1f}°C"
        )

    # Initial ampacity estimate
    # I² = ΔT_conductor / (Rac × R_conductor)
    r_ac_init = calculate_ac_resistance(
        cable.conductor,
        temperature=tc_max,
        spacing=spacing,
        frequency=operating.frequency,
    )
    i_estimate = math.sqrt(delta_t_conductor / (r_ac_init["rac"] * r_conductor))

    # Iterative refinement
    current = i_estimate
    for iteration in range(max_iterations):
        # Calculate losses at current estimate
        wc = current ** 2 * r_ac_init["rac"]

        # Calculate actual temperature rise
        delta_t_calc = wc * r_conductor + delta_t_dielectric
        t_conductor = installation.ambient_temp + delta_t_calc

        # Recalculate AC resistance at actual temperature
        r_ac = calculate_ac_resistance(
            cable.conductor,
            temperature=t_conductor,
            spacing=spacing,
            frequency=operating.frequency,
        )

        # Recalculate shield loss factor
        if cable.shield is not None:
            lambda1 = calculate_shield_loss_factor(
                cable.shield,
                r_ac["rac"],
                spacing,
                operating.frequency,
            )
            r_conductor = (1 + lambda1) * (r1 + r2 + r3 + r_concrete + r4)

        # New current estimate
        new_current = math.sqrt(delta_t_conductor / (r_ac["rac"] * r_conductor))

        # Check convergence
        if abs(new_current - current) < tolerance:
            current = new_current
            break

        current = new_current
        r_ac_init = r_ac
    else:
        # Did not converge
        pass

    # Final calculations at converged current
    r_ac_final = calculate_ac_resistance(
        cable.conductor,
        temperature=tc_max,
        spacing=spacing,
        frequency=operating.frequency,
    )

    wc = current ** 2 * r_ac_final["rac"]
    ws = lambda1 * wc

    # Apply load factor if specified
    if operating.load_factor < 1.0:
        # For cyclic loading, effective current is higher
        # Simplified: I_cyclic = I_steady / sqrt(load_factor)
        # This is an approximation; full calculation requires loss factor μ
        current_cyclic = current / math.sqrt(operating.load_factor)
    else:
        current_cyclic = current

    result = {
        "ampacity": current,
        "ampacity_cyclic": current_cyclic,
        "installation_type": installation_type,
        "max_conductor_temp": tc_max,
        "ambient_temp": installation.ambient_temp,
        "delta_t_available": delta_t_available,
        "ac_resistance": {
            "rdc": r_ac_final["rdc"],
            "rac": r_ac_final["rac"],
            "ycs": r_ac_final["ycs"],
            "ycp": r_ac_final["ycp"],
        },
        "losses": {
            "conductor": wc,
            "dielectric": wd,
            "shield": ws,
            "total": wc + wd + ws,
        },
        "thermal_resistance": {
            "r1_insulation": r1,
            "r2_jacket": r2,
            "r3_conduit": r3,
            "r_concrete": r_concrete,
            "r4_earth": thermal_r["r4"],
            "r4_effective": r4,
            "mutual_heating_factor": thermal_r["f_mutual"],
            "total": thermal_r["total"],
        },
        "temperature_rise": {
            "conductor_losses": wc * r_conductor,
            "dielectric_losses": delta_t_dielectric,
            "total": wc * r_conductor + delta_t_dielectric,
        },
        "shield_loss_factor": lambda1,
        "iterations": iteration + 1 if 'iteration' in dir() else 1,
    }

    # Add duct bank specific info
    if installation_type == "duct_bank":
        result["duct_info"] = {
            "target_duct": thermal_r.get("target_duct"),
            "duct_positions": thermal_r.get("duct_positions"),
        }

    return result


def format_results(results: dict) -> str:
    """Format ampacity results for display."""
    installation_type = results.get("installation_type", "direct_buried")
    installation_labels = {
        "direct_buried": "Direct Buried",
        "conduit": "Conduit",
        "duct_bank": "Duct Bank",
    }

    lines = [
        "=" * 60,
        "CABLE AMPACITY CALCULATION RESULTS",
        "=" * 60,
        "",
        f"Installation Type:       {installation_labels.get(installation_type, installation_type)}",
        f"Ampacity (steady-state): {results['ampacity']:.1f} A",
        f"Ampacity (cyclic):       {results['ampacity_cyclic']:.1f} A",
        "",
        "TEMPERATURES",
        "-" * 40,
        f"  Max conductor temp:    {results['max_conductor_temp']:.1f} °C",
        f"  Ambient temp:          {results['ambient_temp']:.1f} °C",
        f"  Available ΔT:          {results['delta_t_available']:.1f} °C",
        "",
        "AC RESISTANCE",
        "-" * 40,
        f"  DC resistance:         {results['ac_resistance']['rdc']*1000:.4f} mΩ/m",
        f"  AC resistance:         {results['ac_resistance']['rac']*1000:.4f} mΩ/m",
        f"  Skin effect (Ycs):     {results['ac_resistance']['ycs']:.4f}",
        f"  Proximity effect (Ycp):{results['ac_resistance']['ycp']:.4f}",
        "",
        "LOSSES (at rated current)",
        "-" * 40,
        f"  Conductor losses:      {results['losses']['conductor']:.2f} W/m",
        f"  Dielectric losses:     {results['losses']['dielectric']:.4f} W/m",
        f"  Shield losses:         {results['losses']['shield']:.2f} W/m",
        f"  Total losses:          {results['losses']['total']:.2f} W/m",
        f"  Shield loss factor:    {results['shield_loss_factor']:.4f}",
        "",
        "THERMAL RESISTANCES",
        "-" * 40,
        f"  R1 (insulation):       {results['thermal_resistance']['r1_insulation']:.4f} K·m/W",
        f"  R2 (jacket):           {results['thermal_resistance']['r2_jacket']:.4f} K·m/W",
    ]

    # Add R3 (conduit) if applicable
    r3 = results['thermal_resistance'].get('r3_conduit', 0)
    if r3 > 0:
        lines.append(f"  R3 (conduit):          {r3:.4f} K·m/W")

    # Add R_concrete if applicable
    r_concrete = results['thermal_resistance'].get('r_concrete', 0)
    if r_concrete > 0:
        lines.append(f"  R (concrete):          {r_concrete:.4f} K·m/W")

    lines.extend([
        f"  R4 (earth):            {results['thermal_resistance']['r4_earth']:.4f} K·m/W",
        f"  Mutual heating factor: {results['thermal_resistance']['mutual_heating_factor']:.3f}",
        f"  R4 (effective):        {results['thermal_resistance']['r4_effective']:.4f} K·m/W",
        f"  Total:                 {results['thermal_resistance']['total']:.4f} K·m/W",
        "",
        "TEMPERATURE RISE",
        "-" * 40,
        f"  From conductor losses: {results['temperature_rise']['conductor_losses']:.2f} °C",
        f"  From dielectric losses:{results['temperature_rise']['dielectric_losses']:.2f} °C",
        f"  Total:                 {results['temperature_rise']['total']:.2f} °C",
        "",
        "=" * 60,
    ])
    return "\n".join(lines)
