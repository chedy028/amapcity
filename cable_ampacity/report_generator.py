"""
QA/QC Calculation Report Generator

Generates Markdown reports documenting all ampacity calculations with formulas
and actual values for engineering QA/QC review.

Implements report format per IEC 60287-1-1:2023 and IEC 60287-2-1:2023.
"""

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Union, Optional, Dict, Any, List

from .ac_resistance import (
    ConductorSpec,
    TEMPERATURE_COEFFICIENT,
    SKIN_EFFECT_CONSTANT,
    PROXIMITY_EFFECT_CONSTANT,
    calculate_dc_resistance,
    calculate_skin_effect,
    calculate_proximity_effect,
)
from .losses import (
    InsulationSpec,
    ShieldSpec,
    INSULATION_PROPERTIES,
    calculate_dielectric_loss,
    calculate_shield_loss_factor,
)
from .thermal_resistance import (
    CableGeometry,
    BurialConditions,
    ConduitConditions,
    DuctBankConditions,
    THERMAL_RESISTIVITY,
    CONDUIT_THERMAL_RESISTIVITY,
)
from .solver import CableSpec, OperatingConditions


@dataclass
class ReportConfig:
    """Configuration for report generation."""
    study_name: str = "Cable Ampacity Study"
    project_name: str = ""
    software_version: str = "1.0.0"
    include_cymcap_comparison: bool = False
    cymcap_data: Optional[Dict] = None
    decimal_places: int = 4


def _format_number(value: float, decimals: int = 4) -> str:
    """Format a number with specified decimal places."""
    if abs(value) < 1e-6:
        return f"{value:.2e}"
    elif abs(value) > 1e6:
        return f"{value:.2e}"
    else:
        return f"{value:.{decimals}f}"


def _format_scientific(value: float, sig_figs: int = 3) -> str:
    """Format a number in scientific notation."""
    return f"{value:.{sig_figs}e}"


def generate_qaqc_report(
    cable_spec: CableSpec,
    installation: Union[BurialConditions, ConduitConditions, DuctBankConditions],
    operating: OperatingConditions,
    results: dict,
    output_path: str,
    config: Optional[ReportConfig] = None,
) -> str:
    """
    Generate a Markdown QA/QC report with all calculations shown.

    Args:
        cable_spec: Cable specification
        installation: Installation conditions
        operating: Operating conditions
        results: Calculation results from solver
        output_path: Path to write the report
        config: Report configuration options

    Returns:
        Path to the generated report
    """
    if config is None:
        config = ReportConfig()

    # Build report sections
    sections = []

    # Header
    sections.append(_generate_header(config))

    # Input Parameters
    sections.append(_generate_input_section(cable_spec, installation, operating))

    # Calculation Sections
    geometry = cable_spec.geometry
    conductor = cable_spec.conductor
    insulation = cable_spec.insulation

    # Get temperature for calculations
    max_temp = operating.max_conductor_temp or 90.0

    # DC Resistance
    sections.append(_generate_dc_resistance_section(
        conductor, max_temp, results
    ))

    # Skin Effect
    sections.append(_generate_skin_effect_section(
        conductor, results, operating.frequency
    ))

    # Proximity Effect
    sections.append(_generate_proximity_effect_section(
        conductor, results, operating.frequency, installation
    ))

    # AC Resistance
    sections.append(_generate_ac_resistance_section(results))

    # Dielectric Loss
    sections.append(_generate_dielectric_loss_section(
        insulation, operating.voltage, operating.frequency, results
    ))

    # Thermal Resistances
    sections.append(_generate_thermal_resistance_section(
        cable_spec, installation, results
    ))

    # Shield Loss Factor
    if cable_spec.shield:
        sections.append(_generate_shield_loss_section(
            cable_spec.shield, results
        ))

    # Ampacity Calculation
    sections.append(_generate_ampacity_section(
        results, installation.ambient_temp, max_temp
    ))

    # Results Summary Table
    sections.append(_generate_results_summary(results, cable_spec))

    # CYMCAP Comparison (if configured)
    if config.include_cymcap_comparison and config.cymcap_data:
        sections.append(_generate_cymcap_comparison(results, config.cymcap_data))

    # Combine all sections
    report_content = "\n\n".join(sections)

    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    return output_path


def _generate_header(config: ReportConfig) -> str:
    """Generate report header section."""
    now = datetime.now()

    header = f"""# Cable Ampacity QA/QC Calculation Report

## {config.study_name}

| Field | Value |
|-------|-------|
| Date Generated | {now.strftime('%Y-%m-%d %H:%M:%S')} |
| Software Version | {config.software_version} |
| Standards Reference | IEC 60287-1-1:2023, IEC 60287-2-1:2023 |"""

    if config.project_name:
        header += f"\n| Project | {config.project_name} |"

    return header


def _generate_input_section(
    cable_spec: CableSpec,
    installation: Union[BurialConditions, ConduitConditions, DuctBankConditions],
    operating: OperatingConditions,
) -> str:
    """Generate input parameters section."""
    conductor = cable_spec.conductor
    insulation = cable_spec.insulation
    geometry = cable_spec.geometry

    # Determine installation type
    if isinstance(installation, DuctBankConditions):
        install_type = "Duct Bank"
    elif isinstance(installation, ConduitConditions):
        install_type = "Conduit"
    else:
        install_type = "Direct Buried"

    section = """## Input Parameters

### Cable Construction

| Parameter | Symbol | Value | Unit |
|-----------|--------|-------|------|"""

    section += f"""
| Conductor Material | - | {conductor.material.capitalize()} | - |
| Conductor Cross-Section | $A_c$ | {conductor.cross_section:.2f} | mm² |
| Conductor Diameter | $d_c$ | {conductor.diameter:.2f} | mm |
| Conductor Stranding | - | {conductor.stranding.replace('_', ' ').title()} | - |
| Insulation Material | - | {insulation.material.upper()} | - |
| Insulation Thickness | $t_{{ins}}$ | {insulation.thickness:.2f} | mm |
| Conductor Shield Thickness | $t_{{cs}}$ | {cable_spec.conductor_shield_thickness:.2f} | mm |
| Insulation Screen Thickness | $t_{{is}}$ | {cable_spec.insulation_screen_thickness:.2f} | mm |
| Jacket Thickness | $t_j$ | {cable_spec.jacket_thickness:.2f} | mm |
| Overall Cable Diameter | $D_e$ | {geometry.overall_diameter:.2f} | mm |"""

    if conductor.dc_resistance_20c:
        section += f"""
| DC Resistance at 20°C | $R_{{DC,20}}$ | {conductor.dc_resistance_20c*1e6:.4f} | μΩ/m |"""

    if conductor.ks:
        section += f"""
| Skin Effect Coefficient | $k_s$ | {conductor.ks} | - |"""

    if conductor.kp:
        section += f"""
| Proximity Effect Coefficient | $k_p$ | {conductor.kp} | - |"""

    section += """

### Operating Conditions

| Parameter | Symbol | Value | Unit |
|-----------|--------|-------|------|"""

    section += f"""
| System Voltage (L-G) | $U_0$ | {operating.voltage:.2f} | kV |
| Frequency | $f$ | {operating.frequency:.0f} | Hz |
| Maximum Conductor Temperature | $T_{{max}}$ | {operating.max_conductor_temp or 90.0:.0f} | °C |
| Load Factor | $LF$ | {operating.load_factor:.2f} | - |"""

    section += """

### Installation Conditions

| Parameter | Symbol | Value | Unit |
|-----------|--------|-------|------|"""

    section += f"""
| Installation Type | - | {install_type} | - |
| Ambient Temperature | $T_{{amb}}$ | {installation.ambient_temp:.1f} | °C |
| Soil Thermal Resistivity | $\\rho_{{soil}}$ | {installation.soil_resistivity:.2f} | K·m/W |"""

    if isinstance(installation, (ConduitConditions, DuctBankConditions)):
        if isinstance(installation, ConduitConditions):
            section += f"""
| Conduit Inner Diameter | $D_{{ci}}$ | {installation.conduit_id_mm:.2f} | mm |
| Conduit Outer Diameter | $D_{{co}}$ | {installation.conduit_od_mm:.2f} | mm |
| Conduit Material | - | {installation.conduit_material.upper()} | - |
| Burial Depth | $L$ | {installation.depth:.3f} | m |"""
        else:
            section += f"""
| Duct Inner Diameter | $D_{{di}}$ | {installation.duct_id_mm:.2f} | mm |
| Duct Outer Diameter | $D_{{do}}$ | {installation.duct_od_mm:.2f} | mm |
| Duct Material | - | {installation.duct_material.upper()} | - |
| Depth to Top of Duct Bank | $L$ | {installation.depth:.3f} | m |
| Duct Bank Width | $W$ | {installation.bank_width:.3f} | m |
| Duct Bank Height | $H$ | {installation.bank_height:.3f} | m |
| Concrete Thermal Resistivity | $\\rho_{{conc}}$ | {installation.concrete_resistivity:.2f} | K·m/W |
| Duct Array | - | {installation.duct_rows} × {installation.duct_cols} | rows × cols |"""
    else:
        section += f"""
| Burial Depth | $L$ | {installation.depth:.3f} | m |
| Cable Spacing | $s$ | {installation.spacing*1000:.0f} | mm |"""

    return section


def _generate_dc_resistance_section(
    conductor: ConductorSpec,
    max_temp: float,
    results: dict,
) -> str:
    """Generate DC resistance calculation section."""
    # Get values
    alpha = TEMPERATURE_COEFFICIENT[conductor.material]
    rdc_90 = results["ac_resistance"]["rdc"]

    # Calculate R_DC at 20°C from the result (reverse calculation)
    rdc_20 = rdc_90 / (1 + alpha * (max_temp - 20))

    section = f"""## 3.1 DC Resistance Calculation

**Standard Reference:** IEC 60287-1-1:2023, Clause 5.1.2

The DC resistance at operating temperature is calculated from:

$$R_{{DC}}(T) = R_{{DC}}(20°C) \\times [1 + \\alpha_{{20}} \\times (T - 20)]$$

**Where:**
- $R_{{DC}}(20°C)$ = DC resistance at 20°C
- $\\alpha_{{20}}$ = Temperature coefficient at 20°C = {alpha} /°C ({conductor.material})
- $T$ = Operating temperature = {max_temp:.0f}°C

**Calculation:**
```
R_DC(20°C) = {_format_scientific(rdc_20)} Ω/m
           = {rdc_20 * 1609.34:.6f} Ω/mile

R_DC({max_temp:.0f}°C) = {_format_scientific(rdc_20)} × [1 + {alpha} × ({max_temp:.0f} - 20)]
           = {_format_scientific(rdc_20)} × [1 + {alpha} × {max_temp - 20:.0f}]
           = {_format_scientific(rdc_20)} × {1 + alpha * (max_temp - 20):.4f}
           = {_format_scientific(rdc_90)} Ω/m
           = {rdc_90 * 1609.34:.6f} Ω/mile
```

**Result:**
- $R_{{DC}}({max_temp:.0f}°C)$ = **{_format_scientific(rdc_90)} Ω/m** ({rdc_90 * 1e6:.4f} μΩ/m)"""

    return section


def _generate_skin_effect_section(
    conductor: ConductorSpec,
    results: dict,
    frequency: float,
) -> str:
    """Generate skin effect calculation section."""
    rdc = results["ac_resistance"]["rdc"]
    ycs = results["ac_resistance"]["ycs"]

    # Get ks value
    ks = conductor.ks if conductor.ks is not None else SKIN_EFFECT_CONSTANT.get(conductor.stranding, 1.0)

    # Calculate xs
    xs_squared = (8 * math.pi * frequency / rdc) * 1e-7 * ks
    xs = math.sqrt(xs_squared)

    # Determine formula used
    if xs <= 2.8:
        formula_range = "0 < $x_s$ ≤ 2.8"
        formula_tex = r"y_s = \frac{x_s^4}{192 + 0.8 \cdot x_s^4}"
        xs_4 = xs ** 4
        formula_calc = f"""y_s = {xs_4:.4f} / (192 + 0.8 × {xs_4:.4f})
    = {xs_4:.4f} / {192 + 0.8 * xs_4:.4f}
    = {ycs:.4f}"""
    elif xs <= 3.8:
        formula_range = "2.8 < $x_s$ ≤ 3.8"
        formula_tex = r"y_s = -0.136 - 0.0177 \cdot x_s + 0.0563 \cdot x_s^2"
        formula_calc = f"""y_s = -0.136 - 0.0177 × {xs:.4f} + 0.0563 × {xs_squared:.4f}
    = -0.136 - {0.0177 * xs:.4f} + {0.0563 * xs_squared:.4f}
    = {ycs:.4f}"""
    else:
        formula_range = "$x_s$ > 3.8"
        formula_tex = r"y_s = 0.354 \cdot x_s - 0.733"
        formula_calc = f"""y_s = 0.354 × {xs:.4f} - 0.733
    = {0.354 * xs:.4f} - 0.733
    = {ycs:.4f}"""

    section = f"""## 3.2 Skin Effect (IEC 60287-1-1:2023, Clause 5.1.3)

**Formula for $x_s^2$:**

$$x_s^2 = \\frac{{8\\pi f}}{{R'_{{DC}}}} \\times 10^{{-7}} \\times k_s$$

**Where:**
- $f$ = System frequency = {frequency:.0f} Hz
- $R'_{{DC}}$ = DC resistance at max temperature = {_format_scientific(rdc)} Ω/m
- $k_s$ = Skin effect coefficient = {ks} (Table 2, {conductor.stranding.replace('_', ' ').title()})

**Calculation of $x_s$:**
```
x_s² = (8 × π × {frequency:.0f} / {_format_scientific(rdc)}) × 10⁻⁷ × {ks}
     = {8 * math.pi * frequency / rdc:.4f} × 10⁻⁷ × {ks}
     = {xs_squared:.4f}

x_s  = √({xs_squared:.4f})
     = {xs:.4f}
```

**Formula Selection ({formula_range}):**

$${formula_tex}$$

**Calculation of $y_s$:**
```
{formula_calc}
```

**Result:**
- $y_s$ = **{ycs:.4f}**"""

    return section


def _generate_proximity_effect_section(
    conductor: ConductorSpec,
    results: dict,
    frequency: float,
    installation: Union[BurialConditions, ConduitConditions, DuctBankConditions],
) -> str:
    """Generate proximity effect calculation section."""
    rdc = results["ac_resistance"]["rdc"]
    ycp = results["ac_resistance"]["ycp"]

    # Get kp value
    kp = conductor.kp if conductor.kp is not None else PROXIMITY_EFFECT_CONSTANT.get(conductor.stranding, 1.0)

    # Get spacing
    if isinstance(installation, DuctBankConditions):
        spacing = installation.duct_spacing_h * 1000  # m to mm
    elif isinstance(installation, ConduitConditions):
        spacing = installation.spacing * 1000
    else:
        spacing = installation.spacing * 1000

    dc = conductor.diameter

    if spacing == 0 or ycp == 0:
        section = f"""## 3.3 Proximity Effect (IEC 60287-1-1:2023, Clause 5.1.4)

**Note:** Proximity effect is negligible for single isolated cable or widely spaced cables.

**Result:**
- $y_p$ = **{ycp:.4f}**"""
        return section

    # Calculate xp
    xp_squared = (8 * math.pi * frequency / rdc) * 1e-7 * kp
    xp = math.sqrt(xp_squared)

    # Calculate F(xp)
    if xp <= 2.8:
        xp_4 = xp ** 4
        f_xp = xp_4 / (192 + 0.8 * xp_4)
        f_formula = r"F(x_p) = \frac{x_p^4}{192 + 0.8 \cdot x_p^4}"
    elif xp <= 3.8:
        f_xp = -0.136 - 0.0177 * xp + 0.0563 * xp_squared
        f_formula = r"F(x_p) = -0.136 - 0.0177 \cdot x_p + 0.0563 \cdot x_p^2"
    else:
        f_xp = 0.354 * xp - 0.733
        f_formula = r"F(x_p) = 0.354 \cdot x_p - 0.733"

    dc_s_ratio = dc / spacing

    section = f"""## 3.3 Proximity Effect (IEC 60287-1-1:2023, Clause 5.1.4)

**Formula for $x_p^2$:**

$$x_p^2 = \\frac{{8\\pi f}}{{R'_{{DC}}}} \\times 10^{{-7}} \\times k_p$$

**Where:**
- $f$ = System frequency = {frequency:.0f} Hz
- $R'_{{DC}}$ = DC resistance at max temperature = {_format_scientific(rdc)} Ω/m
- $k_p$ = Proximity effect coefficient = {kp}

**Calculation of $x_p$:**
```
x_p² = (8 × π × {frequency:.0f} / {_format_scientific(rdc)}) × 10⁻⁷ × {kp}
     = {xp_squared:.4f}

x_p  = √({xp_squared:.4f})
     = {xp:.4f}
```

**Function $F(x_p)$:**

$${f_formula}$$

```
F(x_p) = {f_xp:.4f}
```

**Proximity Effect Formula (Trefoil):**

$$y_p = F(x_p) \\times \\left(\\frac{{d_c}}{{s}}\\right)^2 \\times \\left[0.312 \\times \\left(\\frac{{d_c}}{{s}}\\right)^2 + \\frac{{1.18}}{{F(x_p) + 0.27}}\\right]$$

**Where:**
- $d_c$ = Conductor diameter = {dc:.2f} mm
- $s$ = Axial spacing = {spacing:.2f} mm
- $d_c/s$ = {dc_s_ratio:.4f}

**Result:**
- $y_p$ = **{ycp:.4f}**"""

    return section


def _generate_ac_resistance_section(results: dict) -> str:
    """Generate AC resistance calculation section."""
    rdc = results["ac_resistance"]["rdc"]
    ycs = results["ac_resistance"]["ycs"]
    ycp = results["ac_resistance"]["ycp"]
    rac = results["ac_resistance"]["rac"]

    section = f"""## 3.4 AC Resistance Calculation

**Standard Reference:** IEC 60287-1-1:2023, Clause 5.1

**Formula:**

$$R_{{AC}} = R_{{DC}} \\times (1 + y_s + y_p)$$

**Calculation:**
```
R_AC = {_format_scientific(rdc)} × (1 + {ycs:.4f} + {ycp:.4f})
     = {_format_scientific(rdc)} × {1 + ycs + ycp:.4f}
     = {_format_scientific(rac)} Ω/m
     = {rac * 1e6:.4f} μΩ/m
     = {rac * 1609.34:.6f} Ω/mile
```

**Result:**
- $R_{{AC}}$ = **{_format_scientific(rac)} Ω/m** ({rac * 1e6:.4f} μΩ/m)
- AC/DC Ratio = **{1 + ycs + ycp:.4f}**"""

    return section


def _generate_dielectric_loss_section(
    insulation: InsulationSpec,
    voltage: float,
    frequency: float,
    results: dict,
) -> str:
    """Generate dielectric loss calculation section."""
    wd = results["losses"]["dielectric"]

    # Get insulation properties
    default_tan_delta, default_permittivity = INSULATION_PROPERTIES.get(insulation.material, (0.001, 2.5))
    tan_delta = insulation.tan_delta or default_tan_delta
    epsilon_r = insulation.permittivity or default_permittivity

    # Calculate capacitance
    epsilon_0 = 8.854e-12
    d_c = insulation.conductor_diameter
    d_i = insulation.conductor_diameter + 2 * insulation.thickness

    capacitance = (2 * math.pi * epsilon_0 * epsilon_r) / math.log(d_i / d_c)
    omega = 2 * math.pi * frequency
    u0 = voltage * 1000  # kV to V

    section = f"""## 3.5 Dielectric Loss (IEC 60287-1-1:2023, Clause 5.3)

**Formula:**

$$W_d = \\omega \\cdot C \\cdot U_0^2 \\cdot \\tan(\\delta)$$

**Where:**
- $\\omega$ = Angular frequency = $2\\pi f$ = 2 × π × {frequency:.0f} = {omega:.2f} rad/s
- $C$ = Capacitance per unit length (F/m)
- $U_0$ = Phase-to-ground voltage = {voltage:.2f} kV = {u0:.0f} V
- $\\tan(\\delta)$ = Insulation loss factor = {tan_delta} ({insulation.material.upper()})

**Capacitance Calculation:**

$$C = \\frac{{2\\pi\\varepsilon_0\\varepsilon_r}}{{\\ln(D_i/d_c)}}$$

**Where:**
- $\\varepsilon_0$ = Permittivity of free space = {_format_scientific(epsilon_0)} F/m
- $\\varepsilon_r$ = Relative permittivity = {epsilon_r} ({insulation.material.upper()})
- $d_c$ = Conductor diameter = {d_c:.2f} mm
- $D_i$ = Diameter over insulation = {d_i:.2f} mm

```
C = (2 × π × {_format_scientific(epsilon_0)} × {epsilon_r}) / ln({d_i:.2f} / {d_c:.2f})
  = {_format_scientific(2 * math.pi * epsilon_0 * epsilon_r)} / ln({d_i/d_c:.4f})
  = {_format_scientific(2 * math.pi * epsilon_0 * epsilon_r)} / {math.log(d_i/d_c):.4f}
  = {_format_scientific(capacitance)} F/m
```

**Dielectric Loss Calculation:**
```
W_d = {omega:.2f} × {_format_scientific(capacitance)} × {u0:.0f}² × {tan_delta}
    = {omega:.2f} × {_format_scientific(capacitance)} × {u0**2:.2e} × {tan_delta}
    = {wd:.6f} W/m
```

**Result:**
- $W_d$ = **{wd:.6f} W/m** ({wd * 1000:.4f} mW/m)"""

    return section


def _generate_thermal_resistance_section(
    cable_spec: CableSpec,
    installation: Union[BurialConditions, ConduitConditions, DuctBankConditions],
    results: dict,
) -> str:
    """Generate thermal resistance calculation section."""
    geometry = cable_spec.geometry
    thermal_r = results["thermal_resistance"]

    r1 = thermal_r["r1_insulation"]
    r2 = thermal_r["r2_jacket"]
    r3 = thermal_r.get("r3_conduit", 0.0)
    r_concrete = thermal_r.get("r_concrete", 0.0)
    r4 = thermal_r["r4_earth"]
    r4_eff = thermal_r["r4_effective"]
    f_mutual = thermal_r["mutual_heating_factor"]

    # Get thermal resistivities
    rho_ins = (cable_spec.insulation_thermal_resistivity
               or THERMAL_RESISTIVITY.get(cable_spec.insulation.material, 3.5))
    rho_jacket = (cable_spec.jacket_thermal_resistivity
                  or THERMAL_RESISTIVITY.get(cable_spec.jacket_material, 3.5))

    # Cable diameters
    dc = geometry.conductor_diameter
    t1_total = (cable_spec.conductor_shield_thickness +
                cable_spec.insulation.thickness +
                cable_spec.insulation_screen_thickness)
    d_ins = geometry.insulation_outer_diameter
    d_shield = geometry.shield_outer_diameter
    d_e = geometry.overall_diameter

    section = f"""## 3.6 Thermal Resistances (IEC 60287-2-1:2023)

### T₁ - Insulation Thermal Resistance

**Formula (including semi-conducting layers):**

$$T_1 = \\frac{{\\rho_T}}{{2\\pi}} \\times \\ln\\left(1 + \\frac{{2t_1}}{{d_c}}\\right)$$

**Where:**
- $\\rho_T$ = Thermal resistivity of insulation = {rho_ins} K·m/W
- $d_c$ = Conductor diameter = {dc:.2f} mm
- $t_1$ = Total insulation thickness (including semi-con) = {t1_total:.2f} mm
  - Conductor shield: {cable_spec.conductor_shield_thickness:.2f} mm
  - Insulation: {cable_spec.insulation.thickness:.2f} mm
  - Insulation screen: {cable_spec.insulation_screen_thickness:.2f} mm

**Calculation:**
```
T₁ = ({rho_ins} / 2π) × ln(1 + 2 × {t1_total:.2f} / {dc:.2f})
   = {rho_ins / (2 * math.pi):.4f} × ln(1 + {2 * t1_total / dc:.4f})
   = {rho_ins / (2 * math.pi):.4f} × ln({1 + 2 * t1_total / dc:.4f})
   = {rho_ins / (2 * math.pi):.4f} × {math.log(1 + 2 * t1_total / dc):.4f}
   = {r1:.4f} K·m/W
```

### T₂ - Jacket Thermal Resistance

**Formula:**

$$T_2 = \\frac{{\\rho_T}}{{2\\pi}} \\times \\ln\\left(\\frac{{D_e}}{{D_s}}\\right)$$

**Where:**
- $\\rho_T$ = Thermal resistivity of jacket = {rho_jacket} K·m/W
- $D_s$ = Diameter over shield = {d_shield:.2f} mm
- $D_e$ = Overall cable diameter = {d_e:.2f} mm

**Calculation:**
```
T₂ = ({rho_jacket} / 2π) × ln({d_e:.2f} / {d_shield:.2f})
   = {rho_jacket / (2 * math.pi):.4f} × ln({d_e / d_shield:.4f})
   = {rho_jacket / (2 * math.pi):.4f} × {math.log(d_e / d_shield):.4f}
   = {r2:.4f} K·m/W
```"""

    # Add T3 if applicable (conduit/duct)
    if r3 > 0:
        if isinstance(installation, ConduitConditions):
            duct_id = installation.conduit_id_mm
            duct_od = installation.conduit_od_mm
        else:
            duct_id = installation.duct_id_mm
            duct_od = installation.duct_od_mm

        rho_duct = CONDUIT_THERMAL_RESISTIVITY.get(
            getattr(installation, 'conduit_material', getattr(installation, 'duct_material', 'pvc')), 6.0)

        section += f"""

### T₃ - Conduit/Duct Thermal Resistance

T₃ consists of two components:
1. **Air gap** between cable and conduit inner surface
2. **Conduit wall** thermal resistance

**Conduit Parameters:**
- Inner diameter: {duct_id:.2f} mm
- Outer diameter: {duct_od:.2f} mm
- Cable diameter: {d_e:.2f} mm
- Duct thermal resistivity: {rho_duct} K·m/W

**Result:**
- $T_3$ = **{r3:.4f} K·m/W**"""

    # Add concrete resistance if applicable
    if r_concrete > 0:
        section += f"""

### R_concrete - Concrete Encasement

For duct bank installations, the thermal resistance through the concrete encasement
is calculated using the IEC geometric factor method.

**Result:**
- $R_{{concrete}}$ = **{r_concrete:.4f} K·m/W**"""

    # Add T4 - External thermal resistance
    if isinstance(installation, (BurialConditions, ConduitConditions)):
        L = installation.depth
    else:
        L = installation.depth + installation.bank_height / 2

    section += f"""

### T₄ - External (Earth) Thermal Resistance

**Formula (Neher-McGrath):**

$$T_4 = \\frac{{\\rho_{{soil}}}}{{2\\pi}} \\times \\ln\\left(\\frac{{4L}}{{D_e}}\\right)$$

**Where:**
- $\\rho_{{soil}}$ = Soil thermal resistivity = {installation.soil_resistivity} K·m/W
- $L$ = Burial depth = {L:.3f} m = {L * 1000:.1f} mm
- $D_e$ = External diameter = {d_e:.2f} mm

**Calculation:**
```
T₄ = ({installation.soil_resistivity} / 2π) × ln(4 × {L * 1000:.1f} / {d_e:.2f})
   = {installation.soil_resistivity / (2 * math.pi):.4f} × ln({4 * L * 1000 / d_e:.4f})
   = {r4:.4f} K·m/W
```

### Mutual Heating Factor

**Factor:** F_mutual = {f_mutual:.4f}

**Effective T₄ with mutual heating:**
```
T₄_effective = T₄ × F_mutual
             = {r4:.4f} × {f_mutual:.4f}
             = {r4_eff:.4f} K·m/W
```

### Summary of Thermal Resistances

| Component | Symbol | Value (K·m/W) |
|-----------|--------|---------------|
| Insulation | T₁ | {r1:.4f} |
| Jacket | T₂ | {r2:.4f} |"""

    if r3 > 0:
        section += f"""
| Conduit/Duct | T₃ | {r3:.4f} |"""

    if r_concrete > 0:
        section += f"""
| Concrete | R_conc | {r_concrete:.4f} |"""

    section += f"""
| Earth | T₄ | {r4:.4f} |
| Earth (effective) | T₄_eff | {r4_eff:.4f} |
| **Total** | **ΣT** | **{thermal_r['total']:.4f}** |"""

    return section


def _generate_shield_loss_section(
    shield: ShieldSpec,
    results: dict,
) -> str:
    """Generate shield loss factor calculation section."""
    lambda1 = results["shield_loss_factor"]

    section = f"""## 3.7 Shield Loss Factor (λ₁)

**Shield Specifications:**
- Material: {shield.material.capitalize()}
- Type: {shield.type.capitalize()}
- Thickness: {shield.thickness:.2f} mm
- Mean diameter: {shield.mean_diameter:.2f} mm
- Bonding: {shield.bonding.replace('_', ' ').title()}

**For single-point bonding:**
- No circulating currents flow in the shield
- Only eddy current losses apply

**Result:**
- $\\lambda_1$ = **{lambda1:.6f}**

**Shield losses at rated current:**
- $W_s = \\lambda_1 \\times W_c$ = {results['losses']['shield']:.4f} W/m"""

    return section


def _generate_ampacity_section(
    results: dict,
    ambient_temp: float,
    max_temp: float,
) -> str:
    """Generate ampacity calculation section."""
    delta_t_available = results["delta_t_available"]
    delta_t_conductor = results["temperature_rise"]["conductor_losses"]
    delta_t_dielectric = results["temperature_rise"]["dielectric_losses"]

    rac = results["ac_resistance"]["rac"]
    lambda1 = results["shield_loss_factor"]

    thermal_r = results["thermal_resistance"]
    r1 = thermal_r["r1_insulation"]
    r2 = thermal_r["r2_jacket"]
    r3 = thermal_r.get("r3_conduit", 0.0)
    r_concrete = thermal_r.get("r_concrete", 0.0)
    r4_eff = thermal_r["r4_effective"]

    r_total = r1 + r2 + r3 + r_concrete + r4_eff
    r_conductor = (1 + lambda1) * r_total
    r_dielectric = 0.5 * r1 + r2 + r3 + r_concrete + r4_eff

    ampacity = results["ampacity"]
    wd = results["losses"]["dielectric"]

    section = f"""## 3.8 Ampacity Calculation

**Standard Reference:** IEC 60287-1-1:2023, Clause 1.4

### Temperature Budget

| Parameter | Value |
|-----------|-------|
| Maximum conductor temperature | $T_{{max}}$ = {max_temp:.0f}°C |
| Ambient temperature | $T_{{amb}}$ = {ambient_temp:.1f}°C |
| Available temperature rise | $\\Delta T_{{available}}$ = {delta_t_available:.1f}°C |

### Temperature Rise from Dielectric Losses

$$\\Delta T_{{dielectric}} = W_d \\times (0.5 \\cdot T_1 + T_2 + T_3 + R_{{conc}} + T_4)$$

```
ΔT_dielectric = {wd:.6f} × (0.5 × {r1:.4f} + {r2:.4f} + {r3:.4f} + {r_concrete:.4f} + {r4_eff:.4f})
              = {wd:.6f} × {r_dielectric:.4f}
              = {delta_t_dielectric:.4f}°C
```

### Temperature Rise Available for Conductor Losses

```
ΔT_conductor = ΔT_available - ΔT_dielectric
             = {delta_t_available:.1f} - {delta_t_dielectric:.4f}
             = {delta_t_available - delta_t_dielectric:.4f}°C
```

### Ampacity Formula

$$I = \\sqrt{{\\frac{{\\Delta T_{{conductor}}}}{{R_{{AC}} \\times (1 + \\lambda_1) \\times (T_1 + T_2 + T_3 + R_{{conc}} + T_4)}}}}$$

**Where:**
- $\\Delta T_{{conductor}}$ = {delta_t_available - delta_t_dielectric:.4f}°C
- $R_{{AC}}$ = {_format_scientific(rac)} Ω/m
- $(1 + \\lambda_1)$ = {1 + lambda1:.6f}
- $\\Sigma T$ = {r_total:.4f} K·m/W

**Calculation:**
```
I = √({delta_t_available - delta_t_dielectric:.4f} / ({_format_scientific(rac)} × {1 + lambda1:.6f} × {r_total:.4f}))
  = √({delta_t_available - delta_t_dielectric:.4f} / {rac * (1 + lambda1) * r_total:.6e})
  = √({(delta_t_available - delta_t_dielectric) / (rac * (1 + lambda1) * r_total):.2f})
  = {ampacity:.1f} A
```

### Result

| Parameter | Value |
|-----------|-------|
| **Ampacity (steady-state)** | **{ampacity:.1f} A** |
| **Ampacity (cyclic)** | **{results['ampacity_cyclic']:.1f} A** |"""

    return section


def _generate_results_summary(results: dict, cable_spec: CableSpec) -> str:
    """Generate results summary table."""
    thermal_r = results["thermal_resistance"]

    section = f"""## 4. Results Summary

### Ampacity

| Parameter | Symbol | Value | Unit |
|-----------|--------|-------|------|
| Ampacity (steady-state) | $I$ | **{results['ampacity']:.1f}** | A |
| Ampacity (cyclic) | $I_{{cyclic}}$ | {results['ampacity_cyclic']:.1f} | A |

### Resistance Values

| Parameter | Symbol | Value | Unit |
|-----------|--------|-------|------|
| DC Resistance at max temp | $R_{{DC}}$ | {results['ac_resistance']['rdc'] * 1e6:.4f} | μΩ/m |
| AC Resistance | $R_{{AC}}$ | {results['ac_resistance']['rac'] * 1e6:.4f} | μΩ/m |
| AC/DC Ratio | $R_{{AC}}/R_{{DC}}$ | {results['ac_resistance']['rac'] / results['ac_resistance']['rdc']:.4f} | - |
| Skin Effect Factor | $y_s$ | {results['ac_resistance']['ycs']:.4f} | - |
| Proximity Effect Factor | $y_p$ | {results['ac_resistance']['ycp']:.4f} | - |

### Losses at Rated Current

| Parameter | Symbol | Value | Unit |
|-----------|--------|-------|------|
| Conductor Losses | $W_c$ | {results['losses']['conductor']:.2f} | W/m |
| Dielectric Losses | $W_d$ | {results['losses']['dielectric']:.6f} | W/m |
| Shield Losses | $W_s$ | {results['losses']['shield']:.4f} | W/m |
| Total Losses | $W_{{total}}$ | {results['losses']['total']:.2f} | W/m |
| Shield Loss Factor | $\\lambda_1$ | {results['shield_loss_factor']:.6f} | - |

### Thermal Resistances

| Parameter | Symbol | Value | Unit |
|-----------|--------|-------|------|
| Insulation | $T_1$ | {thermal_r['r1_insulation']:.4f} | K·m/W |
| Jacket | $T_2$ | {thermal_r['r2_jacket']:.4f} | K·m/W |"""

    if thermal_r.get('r3_conduit', 0) > 0:
        section += f"""
| Conduit/Duct | $T_3$ | {thermal_r['r3_conduit']:.4f} | K·m/W |"""

    if thermal_r.get('r_concrete', 0) > 0:
        section += f"""
| Concrete | $R_{{conc}}$ | {thermal_r['r_concrete']:.4f} | K·m/W |"""

    section += f"""
| Earth | $T_4$ | {thermal_r['r4_earth']:.4f} | K·m/W |
| Earth (effective) | $T_{{4,eff}}$ | {thermal_r['r4_effective']:.4f} | K·m/W |
| Mutual Heating Factor | $F$ | {thermal_r['mutual_heating_factor']:.4f} | - |
| **Total** | $\\Sigma T$ | **{thermal_r['total']:.4f}** | K·m/W |

### Temperature Rise

| Parameter | Symbol | Value | Unit |
|-----------|--------|-------|------|
| From Conductor Losses | $\\Delta T_c$ | {results['temperature_rise']['conductor_losses']:.2f} | °C |
| From Dielectric Losses | $\\Delta T_d$ | {results['temperature_rise']['dielectric_losses']:.4f} | °C |
| Total | $\\Delta T$ | {results['temperature_rise']['total']:.2f} | °C |
| Ambient Temperature | $T_{{amb}}$ | {results['ambient_temp']:.1f} | °C |
| Max Conductor Temperature | $T_{{max}}$ | {results['max_conductor_temp']:.0f} | °C |"""

    return section


def _generate_cymcap_comparison(results: dict, cymcap_data: dict) -> str:
    """Generate CYMCAP comparison section."""
    section = """## 5. Comparison with CYMCAP

| Parameter | Our Value | CYMCAP | Difference |
|-----------|-----------|--------|------------|"""

    our_amp = results["ampacity"]
    cymcap_amp = cymcap_data.get("ampacity_A", 0)
    if isinstance(cymcap_amp, list):
        cymcap_amp = max(cymcap_amp)
    amp_diff = ((our_amp - cymcap_amp) / cymcap_amp * 100) if cymcap_amp else 0

    section += f"""
| Ampacity (A) | {our_amp:.1f} | {cymcap_amp} | {amp_diff:+.2f}% |"""

    our_ys = results["ac_resistance"]["ycs"]
    cymcap_ys = cymcap_data.get("ys", [])
    if cymcap_ys:
        cymcap_ys_avg = sum(cymcap_ys) / len(cymcap_ys)
        ys_diff = ((our_ys - cymcap_ys_avg) / cymcap_ys_avg * 100) if cymcap_ys_avg else 0
        section += f"""
| Skin Effect (ys) | {our_ys:.4f} | {cymcap_ys_avg:.4f} | {ys_diff:+.2f}% |"""

    our_yp = results["ac_resistance"]["ycp"]
    cymcap_yp = cymcap_data.get("yp", [])
    if cymcap_yp:
        cymcap_yp_avg = sum(cymcap_yp) / len(cymcap_yp)
        section += f"""
| Proximity Effect (yp) | {our_yp:.4f} | {cymcap_yp_avg:.4f} | - |"""

    cymcap_t1 = cymcap_data.get("T1_Km_per_W")
    if cymcap_t1:
        our_t1 = results["thermal_resistance"]["r1_insulation"]
        t1_diff = ((our_t1 - cymcap_t1) / cymcap_t1 * 100) if cymcap_t1 else 0
        section += f"""
| T1 (K·m/W) | {our_t1:.4f} | {cymcap_t1:.4f} | {t1_diff:+.2f}% |"""

    return section
