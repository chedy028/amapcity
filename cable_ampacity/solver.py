"""
Ampacity Solver Module

Main solver that calculates cable ampacity using iterative method.
Based on Neher-McGrath (1957) and IEC 60287 standards.
"""

import math
from dataclasses import dataclass
from typing import Literal, Optional

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
    calculate_thermal_resistances,
)


@dataclass
class CableSpec:
    """Complete cable specification for ampacity calculation."""
    # Conductor
    conductor: ConductorSpec
    # Insulation
    insulation: InsulationSpec
    # Shield (optional)
    shield: Optional[ShieldSpec] = None
    # Jacket
    jacket_thickness: float = 3.0  # mm
    jacket_material: Literal["pvc", "pe", "hdpe"] = "pe"

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
        )


@dataclass
class OperatingConditions:
    """Operating conditions for ampacity calculation."""
    voltage: float                # Phase-to-ground voltage (kV)
    frequency: float = 50.0       # System frequency (Hz)
    max_conductor_temp: Optional[float] = None  # Override max temp (°C)
    load_factor: float = 1.0      # Load factor for cyclic rating (0-1)


def calculate_ampacity(
    cable: CableSpec,
    burial: BurialConditions,
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
        burial: Burial conditions
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
    delta_t_available = tc_max - burial.ambient_temp

    # Calculate thermal resistances
    geometry = cable.geometry
    thermal_r = calculate_thermal_resistances(geometry, burial)

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
            spacing=burial.spacing * 1000,  # m to mm
            frequency=operating.frequency,
        )
        lambda1 = calculate_shield_loss_factor(
            cable.shield,
            r_init["rac"],
            burial.spacing * 1000,
            operating.frequency,
        )
    else:
        lambda1 = 0.0

    # Thermal resistance sums
    r1 = thermal_r["r1"]
    r2 = thermal_r["r2"]
    r4 = thermal_r["r4_effective"]

    # For conductor losses: R_total = (1+λ1)×(R1 + R2 + R4)
    r_conductor = (1 + lambda1) * (r1 + r2 + r4)

    # For dielectric losses: R_dielectric = 0.5×R1 + R2 + R4
    r_dielectric = 0.5 * r1 + r2 + r4

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
        spacing=burial.spacing * 1000,
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
        t_conductor = burial.ambient_temp + delta_t_calc

        # Recalculate AC resistance at actual temperature
        r_ac = calculate_ac_resistance(
            cable.conductor,
            temperature=t_conductor,
            spacing=burial.spacing * 1000,
            frequency=operating.frequency,
        )

        # Recalculate shield loss factor
        if cable.shield is not None:
            lambda1 = calculate_shield_loss_factor(
                cable.shield,
                r_ac["rac"],
                burial.spacing * 1000,
                operating.frequency,
            )
            r_conductor = (1 + lambda1) * (r1 + r2 + r4)

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
        spacing=burial.spacing * 1000,
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

    return {
        "ampacity": current,
        "ampacity_cyclic": current_cyclic,
        "max_conductor_temp": tc_max,
        "ambient_temp": burial.ambient_temp,
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


def format_results(results: dict) -> str:
    """Format ampacity results for display."""
    lines = [
        "=" * 60,
        "CABLE AMPACITY CALCULATION RESULTS",
        "=" * 60,
        "",
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
    ]
    return "\n".join(lines)
