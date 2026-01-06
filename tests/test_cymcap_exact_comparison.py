"""
CYMCAP Exact Comparison Test

Uses the exact inputs from "Three Units Deepest Depth 12 31.xlsx" CYMCAP report
to compare calculation results.

CYMCAP Study: HOMER CITY GENERATION
Execution: Three Units Deepest Depth 12 31
Date: 12/31/2025
"""

import math
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cable_ampacity.ac_resistance import ConductorSpec, calculate_ac_resistance
from cable_ampacity.losses import (
    InsulationSpec,
    ShieldSpec,
    calculate_dielectric_loss,
    calculate_shield_loss_factor,
)
from cable_ampacity.thermal_resistance import (
    CableGeometry,
    DuctBankConditions,
    BackfillLayer,
    CablePosition,
    calculate_insulation_thermal_resistance,
    calculate_jacket_thermal_resistance,
    calculate_conduit_air_gap_resistance,
    calculate_conduit_wall_resistance,
    calculate_multilayer_earth_resistance,
    calculate_cable_mutual_heating,
    calculate_per_cable_ampacity,
    ConduitConditions,
)
from cable_ampacity.solver import CableSpec, OperatingConditions, calculate_ampacity


# ============================================================================
# CYMCAP INPUT DATA (from Excel report)
# ============================================================================

# Unit conversions
INCH_TO_MM = 25.4
FT_TO_M = 0.3048

# Cable: HOMER CITY 345KV 5000KCMIL JULY
CYMCAP_CABLE_DATA = {
    # General Cable Information
    "cable_id": "HOMER CITY 345KV 5000KCMIL JULY",
    "num_cores": "Single Core",
    "voltage_kv": 345,  # Line-to-line
    "conductor_area_in2": 3.920243,  # 5000 KCMIL
    "overall_diameter_in": 6.0332,
    "max_steady_state_temp_c": 90,
    "max_emergency_temp_c": 110,

    # Conductor
    "conductor_material": "Copper",
    "conductor_resistivity_uohm_cm": 1.7241,
    "conductor_temp_coeff": 0.00393,
    "conductor_beta_k": 234.452926,
    "conductor_construction": "6 Segments",  # Milliken
    "conductor_insulation_system": "Extruded",
    "milliken_wires": "Bare Unidirectional Wires",
    "ks_skin_effect": 0.62,
    "kp_proximity_effect": 0.37,
    "conductor_diameter_in": 2.48,

    # Conductor Shield
    "conductor_shield_thickness_in": 0.067,
    "conductor_shield_diameter_in": 2.614,

    # Insulation
    "insulation_material": "XLPE Unfilled",
    "insulation_thermal_resistivity": 3.5,  # K.m/W
    "insulation_tan_delta": 0.001,
    "insulation_permittivity": 2.5,
    "insulation_thickness_in": 1.201,
    "insulation_diameter_in": 5.016,

    # Insulation Screen
    "insulation_screen_material": "Semi Conducting Screen",
    "insulation_screen_thickness_in": 0.067,
    "insulation_screen_diameter_in": 5.15,

    # Concentric Neutral/Skid Wires
    "neutral_material": "Copper",
    "neutral_resistivity_uohm_cm": 1.7241,
    "neutral_temp_coeff": 0.00393,
    "neutral_wire_type": "Round Wires",
    "neutral_num_wires": 82,
    "neutral_thickness_in": 0.090598,
    "neutral_diameter_in": 5.3312,

    # Sheath
    "sheath_material": "Copper",
    "sheath_resistivity_uohm_cm": 1.7241,
    "sheath_temp_coeff": 0.00393,
    "sheath_corrugation": "Non Corrugated",
    "sheath_thickness_in": 0.005,
    "sheath_diameter_in": 5.3412,

    # Jacket
    "jacket_material": "Polyethylene",
    "jacket_thermal_resistivity": 3.5,  # K.m/W
    "jacket_thickness_in": 0.346,
    "jacket_diameter_in": 6.0332,

    # Installation
    "frequency_hz": 60,
    "sheath_bonding": "Multicables 1 Point Bonded",
    "loss_factor_alos": 0.3,
    "conduit_construction": "PVC Duct in Concrete",
    "conduit_thermal_resistivity": 6.0,  # K.m/W
    "conduit_filling": "Air",
    "conduit_id_in": 7.981,
    "conduit_od_in": 8.625,
}

# Environmental conditions
CYMCAP_ENVIRONMENT = {
    "ambient_soil_temp_c": 20,
    "native_soil_resistivity": 1.3,  # K.m/W
    "non_isothermal_surface": False,
    "electrical_interaction": False,
    "daily_load_factor": 1.0,
}

# Backfill layers (from Study Summary)
CYMCAP_BACKFILL_LAYERS = [
    {"name": "Unit 3000", "x_ft": 0.000045, "y_ft": 5.590022, "width_ft": 27.50009, "height_ft": 2.500008, "rho_t": 0.6},
    {"name": "Surface Ag", "x_ft": 0, "y_ft": 0.750002, "width_ft": 29.500097, "height_ft": 1.500005, "rho_t": 5.0},
    {"name": "Gravel Bed", "x_ft": 0, "y_ft": 7.090025, "width_ft": 27.500091, "height_ft": 0.499997, "rho_t": 5.0},
    {"name": "Backfill", "x_ft": 0, "y_ft": 2.920012, "width_ft": 29.500097, "height_ft": 2.840013, "rho_t": 1.0},
]

# Cable positions (from Results Summary - all 36 cables)
# Format: (cable_no, cable_id, circuit, phase, frequency, load_factor, x_ft, y_ft, temp_c, ampacity_a)
CYMCAP_CABLE_POSITIONS = [
    (1, "HOMER CITY  345KV 5000KCMIL JULY", 1, "A", 60, 1, -10.500035, 6.167898, 68.671289, 384),
    (2, "HOMER CITY  345KV 5000KCMIL JULY", 1, "B", 60, 1, -11.500038, 5.167894, 64.159497, 384),
    (3, "HOMER CITY  345KV 5000KCMIL JULY", 1, "C", 60, 1, -12.500041, 6.167898, 62.32698, 384),
    (4, "HOMER CITY  345KV 5000KCMIL JULY", 1, "A", 60, 1, -10.500035, 5.167894, 66.565226, 384),
    (5, "HOMER CITY  345KV 5000KCMIL JULY", 1, "B", 60, 1, -11.500038, 6.167898, 66.460054, 384),
    (6, "HOMER CITY  345KV 5000KCMIL JULY", 1, "C", 60, 1, -12.500041, 5.167894, 60.234925, 384),
    (7, "HOMER CITY  345KV 5000KCMIL JULY", 2, "A", 60, 1, -6.00002, 5.167894, 75.095909, 489),
    (8, "HOMER CITY  345KV 5000KCMIL JULY", 2, "B", 60, 1, -7.000023, 6.167898, 77.399608, 489),
    (9, "HOMER CITY  345KV 5000KCMIL JULY", 2, "C", 60, 1, -8.000026, 6.167898, 74.877654, 489),
    (10, "HOMER CITY  345KV 5000KCMIL JULY", 2, "A", 60, 1, -6.00002, 6.167898, 77.308696, 489),
    (11, "HOMER CITY  345KV 5000KCMIL JULY", 2, "B", 60, 1, -7.000023, 5.167894, 74.895217, 489),
    (12, "HOMER CITY  345KV 5000KCMIL JULY", 2, "C", 60, 1, -8.000026, 5.167894, 72.62793, 489),
    (13, "HOMER CITY  345KV 5000KCMIL JULY", 3, "A", 60, 1, -0.500002, 5.167894, 78.241273, 384),
    (14, "HOMER CITY  345KV 5000KCMIL JULY", 3, "B", 60, 1, -1.500005, 6.167898, 80.19586, 384),
    (15, "HOMER CITY  345KV 5000KCMIL JULY", 3, "C", 60, 1, -2.500008, 6.167898, 78.281848, 384),
    (16, "HOMER CITY  345KV 5000KCMIL JULY", 3, "A", 60, 1, -0.500002, 6.167898, 80.431513, 384),
    (17, "HOMER CITY  345KV 5000KCMIL JULY", 3, "B", 60, 1, -1.500005, 5.167894, 77.840231, 384),
    (18, "HOMER CITY  345KV 5000KCMIL JULY", 3, "C", 60, 1, -2.500008, 5.167894, 76.208421, 384),
    (19, "HOMER CITY  345KV 5000KCMIL JULY", 4, "A", 60, 1, 4.000013, 6.167898, 83.94892, 489),
    (20, "HOMER CITY  345KV 5000KCMIL JULY", 4, "B", 60, 1, 3.00001, 5.167894, 81.997518, 489),
    (21, "HOMER CITY  345KV 5000KCMIL JULY", 4, "C", 60, 1, 2.000007, 6.167898, 83.347926, 489),
    (22, "HOMER CITY  345KV 5000KCMIL JULY", 4, "A", 60, 1, 4.000013, 5.167894, 81.336681, 489),
    (23, "HOMER CITY  345KV 5000KCMIL JULY", 4, "B", 60, 1, 3.00001, 6.167898, 84.722587, 489),  # HOTTEST
    (24, "HOMER CITY  345KV 5000KCMIL JULY", 4, "C", 60, 1, 2.000007, 5.167894, 80.946777, 489),
    (25, "HOMER CITY  345KV 5000KCMIL JULY", 5, "A", 60, 1, 7.500024, 5.167894, 74.977802, 384),
    (26, "HOMER CITY  345KV 5000KCMIL JULY", 5, "B", 60, 1, 6.500021, 5.167894, 77.424956, 384),
    (27, "HOMER CITY  345KV 5000KCMIL JULY", 5, "C", 60, 1, 5.500018, 6.167898, 81.300855, 384),
    (28, "HOMER CITY  345KV 5000KCMIL JULY", 5, "A", 60, 1, 7.500024, 6.167898, 77.15474, 384),
    (29, "HOMER CITY  345KV 5000KCMIL JULY", 5, "B", 60, 1, 6.500021, 6.167898, 79.896535, 384),
    (30, "HOMER CITY  345KV 5000KCMIL JULY", 5, "C", 60, 1, 5.500018, 5.167894, 78.834144, 384),
    (31, "HOMER CITY  345KV 5000KCMIL JULY", 6, "A", 60, 1, 12.00004, 5.167894, 64.989994, 489),
    (32, "HOMER CITY  345KV 5000KCMIL JULY", 6, "B", 60, 1, 11.000036, 5.167894, 69.363761, 489),
    (33, "HOMER CITY  345KV 5000KCMIL JULY", 6, "C", 60, 1, 10.000033, 5.167894, 71.556868, 489),
    (34, "HOMER CITY  345KV 5000KCMIL JULY", 6, "A", 60, 1, 12.00004, 6.167898, 67.222046, 489),
    (35, "HOMER CITY  345KV 5000KCMIL JULY", 6, "B", 60, 1, 11.000036, 6.167898, 71.886353, 489),
    (36, "HOMER CITY  345KV 5000KCMIL JULY", 6, "C", 60, 1, 10.000033, 6.167898, 73.843933, 489),
]


def run_cymcap_comparison():
    """Run comparison between our calculation and CYMCAP results."""

    print("=" * 80)
    print("CYMCAP COMPARISON TEST")
    print("Study: HOMER CITY GENERATION - Three Units Deepest Depth 12 31")
    print("=" * 80)

    # ========================================================================
    # Build cable specification from CYMCAP data
    # ========================================================================

    print("\n1. CABLE PARAMETERS (from CYMCAP)")
    print("-" * 40)

    # Convert inches to mm
    conductor_diameter_mm = CYMCAP_CABLE_DATA["conductor_diameter_in"] * INCH_TO_MM
    insulation_thickness_mm = CYMCAP_CABLE_DATA["insulation_thickness_in"] * INCH_TO_MM
    conductor_shield_mm = CYMCAP_CABLE_DATA["conductor_shield_thickness_in"] * INCH_TO_MM
    insulation_screen_mm = CYMCAP_CABLE_DATA["insulation_screen_thickness_in"] * INCH_TO_MM
    sheath_thickness_mm = CYMCAP_CABLE_DATA["sheath_thickness_in"] * INCH_TO_MM
    jacket_thickness_mm = CYMCAP_CABLE_DATA["jacket_thickness_in"] * INCH_TO_MM
    overall_diameter_mm = CYMCAP_CABLE_DATA["overall_diameter_in"] * INCH_TO_MM
    conduit_id_mm = CYMCAP_CABLE_DATA["conduit_id_in"] * INCH_TO_MM
    conduit_od_mm = CYMCAP_CABLE_DATA["conduit_od_in"] * INCH_TO_MM

    # Cross-section in mm²
    conductor_area_mm2 = CYMCAP_CABLE_DATA["conductor_area_in2"] * (INCH_TO_MM ** 2)

    print(f"Conductor: {conductor_area_mm2:.1f} mm² ({CYMCAP_CABLE_DATA['conductor_area_in2']:.3f} in²)")
    print(f"Conductor diameter: {conductor_diameter_mm:.2f} mm")
    print(f"Insulation thickness: {insulation_thickness_mm:.2f} mm")
    print(f"Overall diameter: {overall_diameter_mm:.2f} mm")
    print(f"Ks (skin effect): {CYMCAP_CABLE_DATA['ks_skin_effect']}")
    print(f"Kp (proximity effect): {CYMCAP_CABLE_DATA['kp_proximity_effect']}")
    print(f"tan δ: {CYMCAP_CABLE_DATA['insulation_tan_delta']}")
    print(f"Conduit ID/OD: {conduit_id_mm:.1f} / {conduit_od_mm:.1f} mm")

    # Create conductor spec
    conductor = ConductorSpec(
        material="copper",
        cross_section=conductor_area_mm2,
        diameter=conductor_diameter_mm,
        stranding="segmental",
        ks=CYMCAP_CABLE_DATA["ks_skin_effect"],
        kp=CYMCAP_CABLE_DATA["kp_proximity_effect"],
    )

    # Create insulation spec
    insulation = InsulationSpec(
        material="xlpe",
        thickness=insulation_thickness_mm,
        conductor_diameter=conductor_diameter_mm,
        tan_delta=CYMCAP_CABLE_DATA["insulation_tan_delta"],
        permittivity=CYMCAP_CABLE_DATA["insulation_permittivity"],
        thermal_resistivity=CYMCAP_CABLE_DATA["insulation_thermal_resistivity"],
    )

    # Create shield spec (using sheath)
    sheath_mean_diameter = (CYMCAP_CABLE_DATA["insulation_screen_diameter_in"] +
                           CYMCAP_CABLE_DATA["sheath_diameter_in"]) / 2 * INCH_TO_MM
    shield = ShieldSpec(
        material="copper",
        type="extruded",
        thickness=sheath_thickness_mm,
        mean_diameter=sheath_mean_diameter,
        bonding="single_point",
    )

    # Create cable geometry
    geometry = CableGeometry(
        conductor_diameter=conductor_diameter_mm,
        insulation_thickness=insulation_thickness_mm,
        shield_thickness=sheath_thickness_mm,
        jacket_thickness=jacket_thickness_mm,
        insulation_material="xlpe",
        jacket_material="pe",
        conductor_shield_thickness=conductor_shield_mm,
        insulation_screen_thickness=insulation_screen_mm,
        insulation_thermal_resistivity=CYMCAP_CABLE_DATA["insulation_thermal_resistivity"],
        jacket_thermal_resistivity=CYMCAP_CABLE_DATA["jacket_thermal_resistivity"],
    )

    print(f"\nCalculated overall diameter: {geometry.overall_diameter:.2f} mm")
    print(f"CYMCAP overall diameter: {overall_diameter_mm:.2f} mm")
    print(f"Difference: {abs(geometry.overall_diameter - overall_diameter_mm):.2f} mm ({abs(geometry.overall_diameter - overall_diameter_mm)/overall_diameter_mm*100:.1f}%)")

    # ========================================================================
    # Calculate AC Resistance
    # ========================================================================

    print("\n2. AC RESISTANCE CALCULATION")
    print("-" * 40)

    # Calculate at 90°C (max operating temp)
    ac_res = calculate_ac_resistance(
        conductor=conductor,
        temperature=CYMCAP_CABLE_DATA["max_steady_state_temp_c"],
        spacing=0,  # Will add mutual heating separately
        frequency=CYMCAP_CABLE_DATA["frequency_hz"],
    )

    print(f"DC resistance at 90°C: {ac_res['rdc']*1e6:.4f} µΩ/m")
    print(f"Skin effect factor (Ycs): {ac_res['ycs']:.6f}")
    print(f"Proximity effect factor (Ycp): {ac_res['ycp']:.6f}")
    print(f"AC resistance at 90°C: {ac_res['rac']*1e6:.4f} µΩ/m")

    # ========================================================================
    # Calculate Dielectric Loss
    # ========================================================================

    print("\n3. DIELECTRIC LOSS CALCULATION")
    print("-" * 40)

    # Phase voltage (line-to-line / sqrt(3))
    voltage_phase = CYMCAP_CABLE_DATA["voltage_kv"] / math.sqrt(3)

    wd = calculate_dielectric_loss(
        insulation=insulation,
        voltage=voltage_phase,
        frequency=CYMCAP_CABLE_DATA["frequency_hz"],
    )

    print(f"Phase voltage: {voltage_phase:.2f} kV")
    print(f"Dielectric loss (Wd): {wd:.4f} W/m")

    # ========================================================================
    # Calculate Thermal Resistances
    # ========================================================================

    print("\n4. THERMAL RESISTANCE CALCULATION")
    print("-" * 40)

    r1 = calculate_insulation_thermal_resistance(geometry)
    r2 = calculate_jacket_thermal_resistance(geometry)
    r3_air = calculate_conduit_air_gap_resistance(geometry.overall_diameter, conduit_id_mm)
    r3_wall = calculate_conduit_wall_resistance(
        conduit_id_mm, conduit_od_mm, "pvc"
    )
    r3 = r3_air + r3_wall

    print(f"R1 (insulation): {r1:.4f} K.m/W")
    print(f"R2 (jacket): {r2:.4f} K.m/W")
    print(f"R3 (air gap): {r3_air:.4f} K.m/W")
    print(f"R3 (conduit wall): {r3_wall:.4f} K.m/W")
    print(f"R3 (total): {r3:.4f} K.m/W")

    # ========================================================================
    # Build cable positions from CYMCAP data
    # ========================================================================

    print("\n5. CABLE POSITIONS (36 cables)")
    print("-" * 40)

    cable_positions = []
    for pos_data in CYMCAP_CABLE_POSITIONS:
        (cable_no, cable_id, circuit, phase, freq, lf, x_ft, y_ft, temp_c, amp_a) = pos_data
        cable_positions.append(CablePosition(
            x=x_ft * FT_TO_M,
            y=y_ft * FT_TO_M,
            circuit_id=circuit,
            phase=phase,
            cable_id=str(cable_no),
        ))

    print(f"Total cables: {len(cable_positions)}")
    print(f"X range: {min(p.x for p in cable_positions):.2f} to {max(p.x for p in cable_positions):.2f} m")
    print(f"Y range: {min(p.y for p in cable_positions):.2f} to {max(p.y for p in cable_positions):.2f} m")

    # ========================================================================
    # Build backfill layers
    # ========================================================================

    print("\n6. BACKFILL LAYERS")
    print("-" * 40)

    backfill_layers = []
    for layer_data in CYMCAP_BACKFILL_LAYERS:
        layer = BackfillLayer(
            name=layer_data["name"],
            x_center=layer_data["x_ft"] * FT_TO_M,
            y_top=layer_data["y_ft"] * FT_TO_M,
            width=layer_data["width_ft"] * FT_TO_M,
            height=layer_data["height_ft"] * FT_TO_M,
            thermal_resistivity=layer_data["rho_t"],
        )
        backfill_layers.append(layer)
        print(f"{layer.name}: ρT={layer.thermal_resistivity} K.m/W, depth={layer.y_top:.2f}-{layer.y_bottom:.2f} m")

    # ========================================================================
    # Calculate per-cable ampacity
    # ========================================================================

    print("\n7. PER-CABLE AMPACITY CALCULATION")
    print("-" * 40)

    # Create a simplified duct bank for the per-cable calculation
    avg_depth = sum(p.y for p in cable_positions) / len(cable_positions)

    duct_bank = DuctBankConditions(
        depth=avg_depth - 0.5,  # Approximate depth to top
        soil_resistivity=CYMCAP_ENVIRONMENT["native_soil_resistivity"],
        concrete_resistivity=1.0,
        ambient_temp=CYMCAP_ENVIRONMENT["ambient_soil_temp_c"],
        bank_width=8.0,  # meters
        bank_height=1.0,  # meters
        duct_rows=2,
        duct_cols=18,
        duct_spacing_h=0.3,
        duct_spacing_v=0.3,
        duct_id_mm=conduit_id_mm,
        duct_od_mm=conduit_od_mm,
        duct_material="pvc",
        backfill_layers=backfill_layers,
        cable_positions=cable_positions,
        conduit_thermal_resistivity=CYMCAP_CABLE_DATA["conduit_thermal_resistivity"],
    )

    # Calculate shield loss factor
    lambda1 = 0.0  # Single-point bonding -> negligible circulating currents

    # Calculate per-cable ampacity
    results = calculate_per_cable_ampacity(
        geometry=geometry,
        cable_positions=cable_positions,
        duct_bank=duct_bank,
        conductor_rac=ac_res["rac"],
        dielectric_loss=wd,
        lambda1=lambda1,
        max_temp=CYMCAP_CABLE_DATA["max_steady_state_temp_c"],
        ambient_temp=CYMCAP_ENVIRONMENT["ambient_soil_temp_c"],
    )

    # ========================================================================
    # Compare results
    # ========================================================================

    print("\n8. RESULTS COMPARISON")
    print("=" * 80)
    print(f"{'Cable':<6} {'Circuit':<8} {'Phase':<6} {'CYMCAP Amp':<12} {'Calc Amp':<12} {'Diff %':<10} {'CYMCAP Temp':<12} {'Status'}")
    print("-" * 80)

    total_diff = 0
    max_diff = 0

    for i, (cymcap_data, calc_result) in enumerate(zip(CYMCAP_CABLE_POSITIONS, results)):
        (cable_no, cable_id, circuit, phase, freq, lf, x_ft, y_ft, cymcap_temp, cymcap_amp) = cymcap_data
        calc_amp = calc_result["ampacity"]

        diff_pct = (calc_amp - cymcap_amp) / cymcap_amp * 100
        total_diff += abs(diff_pct)
        max_diff = max(max_diff, abs(diff_pct))

        status = "OK" if abs(diff_pct) < 20 else "HIGH" if diff_pct > 0 else "LOW"

        print(f"{cable_no:<6} {circuit:<8} {phase:<6} {cymcap_amp:<12} {calc_amp:<12.1f} {diff_pct:<+10.1f} {cymcap_temp:<12.2f} {status}")

    avg_diff = total_diff / len(CYMCAP_CABLE_POSITIONS)

    print("-" * 80)
    print(f"\nSUMMARY:")
    print(f"  Average absolute difference: {avg_diff:.1f}%")
    print(f"  Maximum difference: {max_diff:.1f}%")
    print(f"  CYMCAP ampacity range: 384-489 A")
    print(f"  Calculated ampacity range: {min(r['ampacity'] for r in results):.1f}-{max(r['ampacity'] for r in results):.1f} A")

    # ========================================================================
    # Also run single-cable calculation for comparison
    # ========================================================================

    print("\n9. SINGLE-CABLE CALCULATION (for reference)")
    print("-" * 40)

    cable_spec = CableSpec(
        conductor=conductor,
        insulation=insulation,
        shield=shield,
        jacket_thickness=jacket_thickness_mm,
        jacket_material="pe",
        conductor_shield_thickness=conductor_shield_mm,
        insulation_screen_thickness=insulation_screen_mm,
        insulation_thermal_resistivity=CYMCAP_CABLE_DATA["insulation_thermal_resistivity"],
        jacket_thermal_resistivity=CYMCAP_CABLE_DATA["jacket_thermal_resistivity"],
    )

    # Use conduit installation
    conduit_install = ConduitConditions(
        depth=avg_depth,
        soil_resistivity=CYMCAP_ENVIRONMENT["native_soil_resistivity"],
        ambient_temp=CYMCAP_ENVIRONMENT["ambient_soil_temp_c"],
        conduit_id_mm=conduit_id_mm,
        conduit_od_mm=conduit_od_mm,
        conduit_material="pvc",
        spacing=0.3,
        num_conduits=36,  # All 36 conduits
    )

    operating = OperatingConditions(
        voltage=voltage_phase,
        frequency=CYMCAP_CABLE_DATA["frequency_hz"],
        max_conductor_temp=CYMCAP_CABLE_DATA["max_steady_state_temp_c"],
    )

    single_result = calculate_ampacity(cable_spec, conduit_install, operating)

    print(f"Single-cable ampacity (with 36-conduit mutual heating): {single_result['ampacity']:.1f} A")
    print(f"Thermal resistance breakdown:")
    print(f"  R1: {single_result['thermal_resistance'].get('r1', 'N/A')}")
    print(f"  R2: {single_result['thermal_resistance'].get('r2', 'N/A')}")
    print(f"  R3: {single_result['thermal_resistance'].get('r3', 'N/A')}")
    print(f"  R4: {single_result['thermal_resistance'].get('r4', 'N/A')}")

    print("\n" + "=" * 80)
    print("NOTE: Differences from CYMCAP may be due to:")
    print("  1. Different mutual heating calculation methods")
    print("  2. Multi-layer backfill calculation approach")
    print("  3. Concrete encasement thermal model")
    print("  4. CIGRE vs IEC calculation method differences")
    print("=" * 80)

    return results, single_result


if __name__ == "__main__":
    run_cymcap_comparison()
