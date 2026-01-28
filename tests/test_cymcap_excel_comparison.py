"""
CYMCAP Excel File Comparison Tests

This module compares our ampacity calculator results against CYMCAP 8.2 output
from the Excel files provided.

Studies:
1. Case 3 Duct Bank - Cayuga 230kV, 6 cables, duct bank installation
2. Cayuga HDD - Cayuga 230kV, 6 cables, HDD (deep burial)
3. Cayuga Trough - Cayuga 230kV, 6 cables, trough installation
4. Homer HDD - Homer City 345kV, 6 cables, HDD installation
5. Homer 3 Units - Homer City 345kV, 18 cables, duct bank
"""

import math
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cable_ampacity.ac_resistance import (
    ConductorSpec, calculate_dc_resistance, calculate_skin_effect,
    calculate_proximity_effect, calculate_ac_resistance
)
from cable_ampacity.losses import (
    InsulationSpec, ShieldSpec,
    calculate_dielectric_loss
)
from cable_ampacity.thermal_resistance import (
    BurialConditions, ConduitConditions
)
from cable_ampacity.solver import calculate_ampacity, OperatingConditions, CableSpec
from cable_ampacity.report_generator import generate_qaqc_report, ReportConfig
from cable_ampacity.thermal_resistance import DuctBankConditions

# Unit conversions
IN_TO_MM = 25.4
FT_TO_M = 0.3048
IN2_TO_MM2 = 645.16
OHM_PER_MILE_TO_OHM_PER_M = 1 / 1609.34

# =============================================================================
# CYMCAP DATA FROM EXCEL FILES
# =============================================================================

CYMCAP_STUDIES = {
    "Case 3 Duct Bank": {
        "description": "Cayuga 230kV, 6 cables in duct bank",
        "cable": {
            "voltage_kv": 230,
            "conductor_area_in2": 3.9302436604716,
            "conductor_diameter_in": 2.48,
            "conductor_shield_thickness_in": 0.094,
            "insulation_thickness_in": 0.906,
            "insulation_screen_thickness_in": 0.094,
            "sheath_thickness_in": 0.005,
            "concentric_wire_thickness_in": 0.0508,  # calculated from diameter diff
            "jacket_thickness_in": 0.34,
            "overall_diameter_in": 5.46,
            "insulation_thermal_resistivity": 3.5,
            "jacket_thermal_resistivity": 3.5,
            "ks": 0.62,
            "kp": 0.37,
            "milliken_type": "Bare Unidirectional Wires",
        },
        "environment": {
            "ambient_temp_c": 29,
            "soil_resistivity": 0.9,
            "frequency_hz": 60,
            "max_conductor_temp_c": 90,
        },
        "conduit": {
            "inner_diameter_in": 7.981,
            "outer_diameter_in": 8.625,
            "material": "pvc",
            "thermal_resistivity": 6.0,
        },
        "installation": {
            "type": "duct_bank",
            "depth_ft": 3.91,  # Y coordinate from Excel
            "num_cables": 6,
        },
        "cymcap_results": {
            "ampacity_A": 1288,
            "conductor_temps_c": [80.62, 86.71, 88.40, 88.40, 86.71, 80.62],
            "ys": [0.419, 0.407, 0.404, 0.404, 0.407, 0.419],
            "yp": [0.005, 0.007, 0.007, 0.007, 0.007, 0.005],
            "R_dc_20c_ohm_per_mile": 0.01116,
            "T1_Km_per_W": 0.341,
        },
    },

    "Cayuga HDD": {
        "description": "Cayuga 230kV, 6 cables in HDD at ~29ft depth",
        "cable": {
            "voltage_kv": 230,
            "conductor_area_in2": 3.9302436604716,
            "conductor_diameter_in": 2.48,
            "conductor_shield_thickness_in": 0.094,
            "insulation_thickness_in": 0.906,
            "insulation_screen_thickness_in": 0.094,
            "sheath_thickness_in": 0.005,
            "concentric_wire_thickness_in": 0.0508,
            "jacket_thickness_in": 0.34,
            "overall_diameter_in": 5.46,
            "insulation_thermal_resistivity": 3.5,
            "jacket_thermal_resistivity": 3.5,
            "ks": 0.80,  # Bare Bidirectional
            "kp": 0.37,
            "milliken_type": "Bare Bidirectional Wires",
        },
        "environment": {
            "ambient_temp_c": 14.2,
            "soil_resistivity": 0.9,
            "frequency_hz": 60,
            "max_conductor_temp_c": 90,
        },
        "conduit": {
            "inner_diameter_in": 6.963,
            "outer_diameter_in": 8.47,
            "material": "pvc",
            "thermal_resistivity": 6.0,
        },
        "installation": {
            "type": "hdd",
            "depth_ft": 29.08,
            "num_cables": 6,
        },
        "cymcap_results": {
            "ampacity_A": 1143,
            "conductor_temps_c": [88.32, 88.58, 87.28, 88.56, 88.30, 87.27],
            "ys": [0.570, 0.570, 0.573, 0.570, 0.571, 0.573],
            "yp": [0.040, 0.040, 0.040, 0.040, 0.040, 0.040],
            "R_dc_20c_ohm_per_mile": 0.01116,
            "T1_Km_per_W": 0.341,
        },
    },

    "Cayuga Trough": {
        "description": "Cayuga 230kV, 6 cables in air-filled trough",
        "cable": {
            "voltage_kv": 230,
            "conductor_area_in2": 3.9302436604716,
            "conductor_diameter_in": 2.48,
            "conductor_shield_thickness_in": 0.094,
            "insulation_thickness_in": 0.906,
            "insulation_screen_thickness_in": 0.094,
            "sheath_thickness_in": 0.005,
            "concentric_wire_thickness_in": 0.0508,
            "jacket_thickness_in": 0.34,
            "overall_diameter_in": 5.46,
            "insulation_thermal_resistivity": 3.5,
            "jacket_thermal_resistivity": 3.5,
            "ks": 0.62,
            "kp": 0.37,
            "milliken_type": "Bare Unidirectional Wires",
        },
        "environment": {
            "ambient_temp_c": 36,
            "soil_resistivity": None,  # Trough, not buried
            "frequency_hz": 60,
            "max_conductor_temp_c": 90,
        },
        "installation": {
            "type": "trough",
            "trough_width_ft": 7.0,
            "trough_height_ft": 3.0,
            "cover_thickness_ft": 0.625,
            "num_cables": 6,
        },
        "cymcap_results": {
            "ampacity_A": 1288,
            "conductor_temps_c": [72.78] * 6,
            "ys": [0.433] * 6,
            "yp": [0.105] * 6,
            "R_dc_20c_ohm_per_mile": 0.01116,
            "T1_Km_per_W": 0.341,
            "T4_Km_per_W": 0.532,
        },
    },

    "Homer HDD": {
        "description": "Homer City 345kV, 6 cables in HDD at ~25ft depth",
        "cable": {
            "voltage_kv": 345,
            "conductor_area_in2": 3.9202430404704,
            "conductor_diameter_in": 2.48,
            "conductor_shield_thickness_in": 0.067,
            "insulation_thickness_in": 1.201,
            "insulation_screen_thickness_in": 0.067,
            "sheath_thickness_in": 0.005,
            "concentric_wire_thickness_in": 0.0906,
            "jacket_thickness_in": 0.346,
            "overall_diameter_in": 6.033,
            "insulation_thermal_resistivity": 3.5,
            "jacket_thermal_resistivity": 3.5,
            "ks": 0.62,
            "kp": 0.37,
            "milliken_type": "Bare Unidirectional Wires",
        },
        "environment": {
            "ambient_temp_c": 12.2,
            "soil_resistivity": 0.7,
            "frequency_hz": 60,
            "max_conductor_temp_c": 90,
        },
        "conduit": {
            "inner_diameter_in": 7.981,
            "outer_diameter_in": 8.625,
            "material": "pvc",
            "thermal_resistivity": 6.0,
        },
        "installation": {
            "type": "hdd",
            "depth_ft": 25.08,
            "num_cables": 6,
        },
        "cymcap_results": {
            "ampacity_A": 529,
            "conductor_temps_c": [38.85, 39.27, 39.96, 40.21, 39.96, 39.27],
            "ys": [0.506, 0.505, 0.503, 0.503, 0.503, 0.505],
            "yp": [0.045, 0.045, 0.045, 0.045, 0.045, 0.045],
            "R_dc_20c_ohm_per_mile": 0.01119,
            "T1_Km_per_W": 0.399,
        },
    },

    "Homer 3 Units": {
        "description": "Homer City 345kV, 18 cables in duct bank",
        "cable": {
            "voltage_kv": 345,
            "conductor_area_in2": 3.9202430404704,
            "conductor_diameter_in": 2.48,
            "conductor_shield_thickness_in": 0.067,
            "insulation_thickness_in": 1.201,
            "insulation_screen_thickness_in": 0.067,
            "sheath_thickness_in": 0.005,
            "concentric_wire_thickness_in": 0.0906,
            "jacket_thickness_in": 0.346,
            "overall_diameter_in": 6.033,
            "insulation_thermal_resistivity": 3.5,
            "jacket_thermal_resistivity": 3.5,
            "ks": 0.62,
            "kp": 0.37,
            "milliken_type": "Bare Unidirectional Wires",
        },
        "environment": {
            "ambient_temp_c": 19.4,
            "soil_resistivity": 1.3,
            "frequency_hz": 60,
            "max_conductor_temp_c": 90,
        },
        "conduit": {
            "inner_diameter_in": 7.981,
            "outer_diameter_in": 8.625,
            "material": "pvc",
            "thermal_resistivity": 6.0,
        },
        "installation": {
            "type": "duct_bank",
            "depth_ft": 6.5,  # Average depth
            "num_cables": 18,
        },
        "cymcap_results": {
            # Circuit 1 (cables 1-6): 384 A, Circuit 2 (cables 7-12): 489 A
            "ampacity_A": [384, 384, 384, 384, 384, 384, 489, 489, 489, 489, 489],
            "conductor_temps_c": [69.75, 65.28, 63.47, 67.65, 67.56, 61.40,
                                  76.21, 78.47, 75.94, 78.39, 76.00],
            "ys": [0.438, 0.447, 0.451, 0.442, 0.442, 0.455,
                   0.425, 0.421, 0.426, 0.421, 0.426],
            "yp": [0.012, 0.016, 0.012, 0.012, 0.016, 0.012,
                   0.012, 0.015, 0.012, 0.012, 0.015],
            "R_dc_20c_ohm_per_mile": 0.01119,
            "T1_Km_per_W": 0.399,
        },
    },
}


def create_cable_spec(study_data):
    """Create CableSpec from CYMCAP study data."""
    cable = study_data["cable"]
    env = study_data["environment"]

    # Convert units
    conductor_area_mm2 = cable["conductor_area_in2"] * IN2_TO_MM2
    conductor_diameter_mm = cable["conductor_diameter_in"] * IN_TO_MM
    insulation_thickness_mm = cable["insulation_thickness_in"] * IN_TO_MM
    conductor_shield_thickness_mm = cable["conductor_shield_thickness_in"] * IN_TO_MM
    insulation_screen_thickness_mm = cable["insulation_screen_thickness_in"] * IN_TO_MM
    sheath_thickness_mm = cable["sheath_thickness_in"] * IN_TO_MM
    jacket_thickness_mm = cable["jacket_thickness_in"] * IN_TO_MM
    overall_diameter_mm = cable["overall_diameter_in"] * IN_TO_MM

    conductor = ConductorSpec(
        material="copper",
        cross_section=conductor_area_mm2,
        diameter=conductor_diameter_mm,
        stranding="segmental",
        ks=cable["ks"],
        kp=cable["kp"],
    )

    insulation = InsulationSpec(
        material="xlpe",
        thickness=insulation_thickness_mm,
        conductor_diameter=conductor_diameter_mm,
        thermal_resistivity=cable["insulation_thermal_resistivity"],
        tan_delta=0.001,  # XLPE default
        permittivity=2.5,
    )

    # Shield mean diameter is between insulation screen OD and sheath OD
    insulation_od = conductor_diameter_mm + 2 * conductor_shield_thickness_mm + 2 * insulation_thickness_mm
    shield_mean_diameter = insulation_od + insulation_screen_thickness_mm

    shield = ShieldSpec(
        material="copper",
        type="tape",
        thickness=sheath_thickness_mm,
        mean_diameter=shield_mean_diameter,
        bonding="single_point",
    )

    cable_spec = CableSpec(
        conductor=conductor,
        insulation=insulation,
        shield=shield,
        jacket_thickness=jacket_thickness_mm,
        jacket_material="pe",
        conductor_shield_thickness=conductor_shield_thickness_mm,
        insulation_screen_thickness=insulation_screen_thickness_mm,
        insulation_thermal_resistivity=cable["insulation_thermal_resistivity"],
        jacket_thermal_resistivity=cable["jacket_thermal_resistivity"],
    )

    return cable_spec


def run_comparison(study_name):
    """Run comparison for a single CYMCAP study."""
    study = CYMCAP_STUDIES[study_name]
    cable = study["cable"]
    env = study["environment"]
    cymcap = study["cymcap_results"]

    print(f"\n{'='*70}")
    print(f"STUDY: {study_name}")
    print(f"Description: {study['description']}")
    print(f"{'='*70}")

    # Convert units
    conductor_area_mm2 = cable["conductor_area_in2"] * IN2_TO_MM2
    conductor_diameter_mm = cable["conductor_diameter_in"] * IN_TO_MM

    # Create conductor spec
    conductor = ConductorSpec(
        material="copper",
        cross_section=conductor_area_mm2,
        diameter=conductor_diameter_mm,
        stranding="segmental",
        ks=cable["ks"],
        kp=cable["kp"],
    )

    # Calculate DC resistance at 20°C
    rdc_20c = calculate_dc_resistance(conductor, 20.0)
    rdc_20c_ohm_per_mile = rdc_20c * 1609.34
    cymcap_rdc = cymcap["R_dc_20c_ohm_per_mile"]
    rdc_diff = (rdc_20c_ohm_per_mile - cymcap_rdc) / cymcap_rdc * 100

    print(f"\n--- DC Resistance at 20°C ---")
    print(f"  Our R_dc:    {rdc_20c_ohm_per_mile:.6f} Ω/mile")
    print(f"  CYMCAP R_dc: {cymcap_rdc:.6f} Ω/mile")
    print(f"  Difference:  {rdc_diff:+.2f}%")

    # Calculate DC resistance at operating temperature (use CYMCAP conductor temp)
    avg_temp = sum(cymcap["conductor_temps_c"]) / len(cymcap["conductor_temps_c"])
    rdc_op = calculate_dc_resistance(conductor, avg_temp)

    # Calculate skin effect
    ys = calculate_skin_effect(conductor, rdc_op, env["frequency_hz"])
    cymcap_ys_avg = sum(cymcap["ys"]) / len(cymcap["ys"])
    ys_diff = (ys - cymcap_ys_avg) / cymcap_ys_avg * 100

    print(f"\n--- Skin Effect Factor (ys) at {avg_temp:.1f}°C ---")
    print(f"  Our ys:      {ys:.4f}")
    print(f"  CYMCAP ys:   {cymcap_ys_avg:.4f} (avg)")
    print(f"  Difference:  {ys_diff:+.2f}%")

    # Calculate xs to show formula range
    xs_squared = (8 * math.pi * env["frequency_hz"] / rdc_op) * 1e-7 * cable["ks"]
    xs = math.sqrt(xs_squared)
    if xs <= 2.8:
        formula_range = "0 < xs ≤ 2.8"
    elif xs <= 3.8:
        formula_range = "2.8 < xs ≤ 3.8"
    else:
        formula_range = "xs > 3.8"
    print(f"  xs = {xs:.4f} (using formula: {formula_range})")

    # Calculate proximity effect (estimate spacing from installation)
    spacing_mm = 300  # Approximate spacing
    yp = calculate_proximity_effect(conductor, rdc_op, spacing_mm, env["frequency_hz"])
    cymcap_yp_avg = sum(cymcap["yp"]) / len(cymcap["yp"])

    print(f"\n--- Proximity Effect Factor (yp) ---")
    print(f"  Our yp:      {yp:.4f}")
    print(f"  CYMCAP yp:   {cymcap_yp_avg:.4f} (avg)")

    # Calculate T1 (thermal resistance through insulation)
    # Per IEC 60287-2-1:2023: Semi-conducting layers are considered part of insulation
    # t1 = conductor_shield + insulation + insulation_screen
    insulation_thickness_mm = cable["insulation_thickness_in"] * IN_TO_MM
    conductor_shield_thickness_mm = cable["conductor_shield_thickness_in"] * IN_TO_MM
    insulation_screen_thickness_mm = cable["insulation_screen_thickness_in"] * IN_TO_MM

    # T1 = (ρT / 2π) × ln(1 + 2×t1 / dc)
    # dc = conductor diameter (bare conductor)
    # t1 = total insulation thickness INCLUDING semi-con layers
    dc = conductor_diameter_mm
    t1_total = conductor_shield_thickness_mm + insulation_thickness_mm + insulation_screen_thickness_mm
    rho_ins = cable["insulation_thermal_resistivity"]
    t1_calc = (rho_ins / (2 * math.pi)) * math.log(1 + 2 * t1_total / dc)
    cymcap_t1 = cymcap["T1_Km_per_W"]
    t1_diff = (t1_calc - cymcap_t1) / cymcap_t1 * 100

    print(f"\n--- Thermal Resistance T1 (IEC 60287-2-1:2023) ---")
    print(f"  dc (conductor diameter):     {dc:.2f} mm")
    print(f"  t1 (total incl. semi-con):   {t1_total:.2f} mm")
    print(f"    - Conductor shield:        {conductor_shield_thickness_mm:.2f} mm")
    print(f"    - Insulation:              {insulation_thickness_mm:.2f} mm")
    print(f"    - Insulation screen:       {insulation_screen_thickness_mm:.2f} mm")
    print(f"  Our T1:      {t1_calc:.4f} K.m/W")
    print(f"  CYMCAP T1:   {cymcap_t1:.4f} K.m/W")
    print(f"  Difference:  {t1_diff:+.2f}%")

    # Summary
    print(f"\n--- CYMCAP Ampacity Result ---")
    if isinstance(cymcap["ampacity_A"], list):
        print(f"  Ampacity:    {min(cymcap['ampacity_A'])}-{max(cymcap['ampacity_A'])} A")
    else:
        print(f"  Ampacity:    {cymcap['ampacity_A']} A")

    return {
        "study": study_name,
        "rdc_diff_pct": rdc_diff,
        "ys_diff_pct": ys_diff,
        "t1_diff_pct": t1_diff,
        "our_ys": ys,
        "cymcap_ys": cymcap_ys_avg,
        "xs": xs,
    }


def main():
    """Run all CYMCAP comparisons."""
    print("="*70)
    print("CYMCAP Excel File Comparison - IEC 60287-1-1:2023")
    print("="*70)

    results = []
    for study_name in CYMCAP_STUDIES:
        result = run_comparison(study_name)
        results.append(result)

    # Summary table
    print("\n" + "="*70)
    print("SUMMARY TABLE")
    print("="*70)
    print(f"{'Study':<20} {'R_dc %':<10} {'ys %':<10} {'T1 %':<10} {'Our ys':<10} {'CYMCAP ys':<10} {'xs':<8}")
    print("-"*70)
    for r in results:
        print(f"{r['study']:<20} {r['rdc_diff_pct']:>+8.2f}% {r['ys_diff_pct']:>+8.2f}% {r['t1_diff_pct']:>+8.2f}% {r['our_ys']:<10.4f} {r['cymcap_ys']:<10.4f} {r['xs']:<8.4f}")


def generate_case3_ductbank_report(output_path: str = "Case3_DuctBank_QAQC_Report.md"):
    """
    Generate a QA/QC report for the Case 3 Duct Bank study.

    This demonstrates the report generator using actual CYMCAP study data.
    """
    study = CYMCAP_STUDIES["Case 3 Duct Bank"]
    cable_data = study["cable"]
    env = study["environment"]
    conduit = study["conduit"]
    install = study["installation"]
    cymcap = study["cymcap_results"]

    # Create cable specification
    cable_spec = create_cable_spec(study)

    # Create duct bank conditions
    # Using simplified single conduit model (approximation of duct bank)
    depth_m = install["depth_ft"] * FT_TO_M
    conduit_id_mm = conduit["inner_diameter_in"] * IN_TO_MM
    conduit_od_mm = conduit["outer_diameter_in"] * IN_TO_MM

    # Create a duct bank configuration
    duct_bank = DuctBankConditions(
        depth=depth_m - 0.3,  # Approximate depth to top of bank
        soil_resistivity=env["soil_resistivity"],
        concrete_resistivity=1.0,  # Standard concrete
        ambient_temp=env["ambient_temp_c"],
        bank_width=1.0,  # Approximate bank dimensions
        bank_height=0.6,
        duct_rows=2,
        duct_cols=3,
        duct_spacing_h=0.3,  # 300mm spacing
        duct_spacing_v=0.3,
        duct_id_mm=conduit_id_mm,
        duct_od_mm=conduit_od_mm,
        duct_material=conduit["material"],
        occupied_ducts=[(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)],
    )

    # Create operating conditions
    operating = OperatingConditions(
        voltage=cable_data["voltage_kv"] / math.sqrt(3),  # Phase-to-ground
        frequency=env["frequency_hz"],
        max_conductor_temp=env["max_conductor_temp_c"],
    )

    # Run calculation
    results = calculate_ampacity(cable_spec, duct_bank, operating)

    # Generate report with CYMCAP comparison
    config = ReportConfig(
        study_name="Case 3 Duct Bank - Cayuga 230kV",
        project_name="Cayuga 230kV Transmission Line",
        software_version="1.0.0",
        include_cymcap_comparison=True,
        cymcap_data=cymcap,
    )

    report_path = generate_qaqc_report(
        cable_spec=cable_spec,
        installation=duct_bank,
        operating=operating,
        results=results,
        output_path=output_path,
        config=config,
    )

    print(f"\n{'='*70}")
    print("QA/QC REPORT GENERATED")
    print(f"{'='*70}")
    print(f"Report saved to: {report_path}")
    print(f"Calculated Ampacity: {results['ampacity']:.1f} A")
    print(f"CYMCAP Ampacity: {cymcap['ampacity_A']} A")
    print(f"Difference: {(results['ampacity'] - cymcap['ampacity_A']) / cymcap['ampacity_A'] * 100:+.2f}%")

    return report_path, results


if __name__ == "__main__":
    main()
    print("\n" + "="*70)
    print("GENERATING QA/QC REPORT")
    print("="*70)
    generate_case3_ductbank_report()
