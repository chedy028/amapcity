"""
Calculation API Endpoints

Exposes the cable ampacity calculation engine as REST endpoints.
"""

import sys
from pathlib import Path
from typing import Literal, Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Add parent directory to path for cable_ampacity imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cable_ampacity.ac_resistance import ConductorSpec, calculate_ac_resistance
from cable_ampacity.losses import InsulationSpec, ShieldSpec, MAX_CONDUCTOR_TEMP
from cable_ampacity.thermal_resistance import (
    BurialConditions,
    ConduitConditions,
    DuctBankConditions,
    CableGeometry,
    BackfillLayer,
    CablePosition,
)
from cable_ampacity.solver import (
    CableSpec,
    OperatingConditions,
    calculate_ampacity,
    format_results,
)

router = APIRouter()


# Pydantic models for API
class ConductorInput(BaseModel):
    material: Literal["copper", "aluminum"] = "copper"
    cross_section_mm2: float = Field(..., gt=0, description="Cross-sectional area in mm²")
    diameter_mm: float = Field(..., gt=0, description="Conductor diameter in mm")
    stranding: Literal["solid", "stranded_round", "stranded_compact", "segmental"] = "stranded_compact"
    dc_resistance_20c: Optional[float] = Field(None, description="DC resistance at 20°C in ohm/m")
    # CYMCAP-aligned optional parameters
    ks: Optional[float] = Field(None, ge=0, le=1, description="Skin effect coefficient (Ks), e.g., 0.62 for Milliken")
    kp: Optional[float] = Field(None, ge=0, le=1, description="Proximity effect coefficient (Kp), e.g., 0.37 for Milliken")


class InsulationInput(BaseModel):
    material: Literal["xlpe", "epr", "paper_oil"] = "xlpe"
    thickness_mm: float = Field(..., gt=0, description="Insulation thickness in mm")
    # CYMCAP-aligned optional parameters
    tan_delta: Optional[float] = Field(None, ge=0, description="Dielectric loss factor (tan δ), e.g., 0.001 for XLPE")
    permittivity: Optional[float] = Field(None, gt=0, description="Relative permittivity (εr), e.g., 2.5 for XLPE")
    thermal_resistivity: Optional[float] = Field(None, gt=0, description="Thermal resistivity in K.m/W, e.g., 3.5 for XLPE")


class ShieldInput(BaseModel):
    material: Literal["copper", "aluminum", "lead"] = "copper"
    type: Literal["tape", "wire", "corrugated", "extruded"] = "wire"
    thickness_mm: float = Field(..., gt=0, description="Shield thickness in mm")
    mean_diameter_mm: float = Field(..., gt=0, description="Mean diameter of shield in mm")
    bonding: Literal["single_point", "both_ends", "cross_bonded"] = "single_point"


class BackfillLayerInput(BaseModel):
    """CYMCAP-style backfill layer definition."""
    name: str = Field(..., description="Layer identifier (e.g., 'Thermal Backfill')")
    x_center_m: float = Field(0.0, description="X coordinate of layer center (m)")
    y_top_m: float = Field(..., ge=0, description="Depth to top of layer (m)")
    width_m: float = Field(..., gt=0, description="Layer width (m)")
    height_m: float = Field(..., gt=0, description="Layer height/thickness (m)")
    thermal_resistivity: float = Field(..., gt=0, description="Thermal resistivity (K.m/W)")


class CablePositionInput(BaseModel):
    """CYMCAP-style cable position definition."""
    x_m: float = Field(..., description="X coordinate (m, 0 = center)")
    y_m: float = Field(..., gt=0, description="Y coordinate / depth (m)")
    circuit_id: int = Field(1, ge=1, description="Circuit number")
    phase: str = Field("A", description="Phase identifier (A, B, C)")
    cable_id: Optional[str] = Field(None, description="Optional cable identifier")


class InstallationInput(BaseModel):
    installation_type: Literal["direct_buried", "conduit", "duct_bank"] = "direct_buried"
    depth_m: float = Field(1.0, gt=0, description="Burial depth to cable center in m")
    soil_resistivity: float = Field(1.0, gt=0, description="Soil thermal resistivity in K·m/W")
    ambient_temp_c: float = Field(25.0, description="Ambient soil temperature in °C")
    spacing_m: float = Field(0.0, ge=0, description="Phase spacing in m (0 for single cable)")

    # Conduit-specific parameters
    conduit_id_mm: Optional[float] = Field(None, description="Conduit inner diameter in mm")
    conduit_od_mm: Optional[float] = Field(None, description="Conduit outer diameter in mm")
    conduit_material: Literal["pvc", "hdpe", "fiberglass", "steel"] = "pvc"
    conduit_thermal_resistivity: Optional[float] = Field(None, gt=0, description="Conduit thermal resistivity in K.m/W")
    num_conduits: int = Field(1, ge=1, description="Number of conduits")

    # Duct bank-specific parameters
    concrete_resistivity: float = Field(1.0, gt=0, description="Concrete thermal resistivity in K·m/W")
    bank_width_m: Optional[float] = Field(None, description="Duct bank width in m")
    bank_height_m: Optional[float] = Field(None, description="Duct bank height in m")
    duct_rows: int = Field(2, ge=1, description="Number of duct rows")
    duct_cols: int = Field(3, ge=1, description="Number of duct columns")
    duct_spacing_h_m: float = Field(0.2, gt=0, description="Horizontal duct spacing in m")
    duct_spacing_v_m: float = Field(0.2, gt=0, description="Vertical duct spacing in m")
    duct_id_mm: Optional[float] = Field(None, description="Duct inner diameter in mm")
    duct_od_mm: Optional[float] = Field(None, description="Duct outer diameter in mm")
    occupied_ducts: Optional[list] = Field(None, description="List of [row, col] positions for occupied ducts")

    # CYMCAP-style multi-layer and multi-cable support
    backfill_layers: Optional[List[BackfillLayerInput]] = Field(None, description="List of backfill layers")
    cable_positions: Optional[List[CablePositionInput]] = Field(None, description="Explicit cable positions")


class OperatingInput(BaseModel):
    voltage_kv: float = Field(..., gt=0, description="Phase-to-ground voltage in kV")
    frequency_hz: float = Field(60.0, gt=0, description="System frequency in Hz")
    max_conductor_temp_c: Optional[float] = Field(None, description="Max conductor temperature (°C)")
    load_factor: float = Field(1.0, gt=0, le=1, description="Load factor (0-1)")


class AmpacityRequest(BaseModel):
    """Complete request for ampacity calculation."""
    conductor: ConductorInput
    insulation: InsulationInput
    shield: Optional[ShieldInput] = None
    jacket_thickness_mm: float = Field(3.0, gt=0)
    jacket_material: Literal["pvc", "pe", "hdpe"] = "pe"
    jacket_thermal_resistivity: Optional[float] = Field(None, gt=0, description="Jacket thermal resistivity in K.m/W")
    installation: InstallationInput
    operating: OperatingInput
    # CYMCAP-style additional cable layers
    conductor_shield_thickness_mm: float = Field(0.0, ge=0, description="Conductor shield thickness in mm")
    insulation_screen_thickness_mm: float = Field(0.0, ge=0, description="Insulation screen thickness in mm")


class AmpacityResponse(BaseModel):
    """Ampacity calculation response."""
    ampacity_a: float
    ampacity_cyclic_a: float
    installation_type: str
    max_conductor_temp_c: float
    ambient_temp_c: float
    delta_t_available_c: float
    ac_resistance: dict
    losses: dict
    thermal_resistance: dict
    temperature_rise: dict
    shield_loss_factor: float
    design_status: str
    formatted_report: str
    duct_info: Optional[dict] = None


@router.post("/calculate", response_model=AmpacityResponse)
async def calculate(request: AmpacityRequest):
    """
    Calculate cable ampacity.

    Takes cable specifications, installation conditions, and operating parameters.
    Returns ampacity rating with detailed breakdown.
    """
    try:
        # Build internal objects from request
        conductor = ConductorSpec(
            material=request.conductor.material,
            cross_section=request.conductor.cross_section_mm2,
            diameter=request.conductor.diameter_mm,
            stranding=request.conductor.stranding,
            dc_resistance_20c=request.conductor.dc_resistance_20c,
            ks=request.conductor.ks,  # CYMCAP-aligned
            kp=request.conductor.kp,  # CYMCAP-aligned
        )

        insulation = InsulationSpec(
            material=request.insulation.material,
            thickness=request.insulation.thickness_mm,
            conductor_diameter=request.conductor.diameter_mm,
            tan_delta=request.insulation.tan_delta,  # CYMCAP-aligned
            permittivity=request.insulation.permittivity,  # CYMCAP-aligned
            thermal_resistivity=request.insulation.thermal_resistivity,  # CYMCAP-aligned
        )

        shield = None
        if request.shield:
            shield = ShieldSpec(
                material=request.shield.material,
                type=request.shield.type,
                thickness=request.shield.thickness_mm,
                mean_diameter=request.shield.mean_diameter_mm,
                bonding=request.shield.bonding,
            )

        cable = CableSpec(
            conductor=conductor,
            insulation=insulation,
            shield=shield,
            jacket_thickness=request.jacket_thickness_mm,
            jacket_material=request.jacket_material,
            conductor_shield_thickness=request.conductor_shield_thickness_mm,  # CYMCAP-aligned
            insulation_screen_thickness=request.insulation_screen_thickness_mm,  # CYMCAP-aligned
            insulation_thermal_resistivity=request.insulation.thermal_resistivity,  # CYMCAP-aligned
            jacket_thermal_resistivity=request.jacket_thermal_resistivity,  # CYMCAP-aligned
        )

        # Create installation conditions based on type
        inst = request.installation
        if inst.installation_type == "conduit":
            # Conduit installation
            conduit_id = inst.conduit_id_mm or (cable.geometry.overall_diameter + 20)
            conduit_od = inst.conduit_od_mm or (conduit_id + 10)
            installation = ConduitConditions(
                depth=inst.depth_m,
                soil_resistivity=inst.soil_resistivity,
                ambient_temp=inst.ambient_temp_c,
                conduit_id_mm=conduit_id,
                conduit_od_mm=conduit_od,
                conduit_material=inst.conduit_material,
                spacing=inst.spacing_m,
                num_conduits=inst.num_conduits,
            )
        elif inst.installation_type == "duct_bank":
            # Duct bank installation
            duct_id = inst.duct_id_mm or (cable.geometry.overall_diameter + 20)
            duct_od = inst.duct_od_mm or (duct_id + 10)
            bank_width = inst.bank_width_m or ((inst.duct_cols - 1) * inst.duct_spacing_h_m + 0.3)
            bank_height = inst.bank_height_m or ((inst.duct_rows - 1) * inst.duct_spacing_v_m + 0.3)

            # Convert occupied_ducts from list of lists to list of tuples
            occupied = None
            if inst.occupied_ducts:
                occupied = [tuple(d) for d in inst.occupied_ducts]

            # Convert backfill layers from input to internal format
            backfill_layers = None
            if inst.backfill_layers:
                backfill_layers = [
                    BackfillLayer(
                        name=layer.name,
                        x_center=layer.x_center_m,
                        y_top=layer.y_top_m,
                        width=layer.width_m,
                        height=layer.height_m,
                        thermal_resistivity=layer.thermal_resistivity,
                    )
                    for layer in inst.backfill_layers
                ]

            # Convert cable positions from input to internal format
            cable_positions = None
            if inst.cable_positions:
                cable_positions = [
                    CablePosition(
                        x=pos.x_m,
                        y=pos.y_m,
                        circuit_id=pos.circuit_id,
                        phase=pos.phase,
                        cable_id=pos.cable_id,
                    )
                    for pos in inst.cable_positions
                ]

            installation = DuctBankConditions(
                depth=inst.depth_m,
                soil_resistivity=inst.soil_resistivity,
                concrete_resistivity=inst.concrete_resistivity,
                ambient_temp=inst.ambient_temp_c,
                bank_width=bank_width,
                bank_height=bank_height,
                duct_rows=inst.duct_rows,
                duct_cols=inst.duct_cols,
                duct_spacing_h=inst.duct_spacing_h_m,
                duct_spacing_v=inst.duct_spacing_v_m,
                duct_id_mm=duct_id,
                duct_od_mm=duct_od,
                duct_material=inst.conduit_material,
                occupied_ducts=occupied,
                backfill_layers=backfill_layers,  # CYMCAP-aligned
                cable_positions=cable_positions,  # CYMCAP-aligned
                conduit_thermal_resistivity=inst.conduit_thermal_resistivity,  # CYMCAP-aligned
            )
        else:
            # Direct buried (default)
            installation = BurialConditions(
                depth=inst.depth_m,
                soil_resistivity=inst.soil_resistivity,
                ambient_temp=inst.ambient_temp_c,
                spacing=inst.spacing_m,
            )

        operating = OperatingConditions(
            voltage=request.operating.voltage_kv,
            frequency=request.operating.frequency_hz,
            max_conductor_temp=request.operating.max_conductor_temp_c,
            load_factor=request.operating.load_factor,
        )

        # Calculate ampacity
        results = calculate_ampacity(cable, installation, operating)

        # Determine design status
        temp_rise = results["temperature_rise"]["total"]
        max_temp = results["max_conductor_temp"]
        actual_temp = results["ambient_temp"] + temp_rise
        if actual_temp <= max_temp:
            design_status = "PASS"
        else:
            design_status = "FAIL"

        return AmpacityResponse(
            ampacity_a=results["ampacity"],
            ampacity_cyclic_a=results["ampacity_cyclic"],
            installation_type=results.get("installation_type", "direct_buried"),
            max_conductor_temp_c=results["max_conductor_temp"],
            ambient_temp_c=results["ambient_temp"],
            delta_t_available_c=results["delta_t_available"],
            ac_resistance=results["ac_resistance"],
            losses=results["losses"],
            thermal_resistance=results["thermal_resistance"],
            temperature_rise=results["temperature_rise"],
            shield_loss_factor=results["shield_loss_factor"],
            design_status=design_status,
            formatted_report=format_results(results),
            duct_info=results.get("duct_info"),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


class SuggestSizeRequest(BaseModel):
    """Request to suggest cable size for target current."""
    target_current_a: float = Field(..., gt=0, description="Required current capacity in A")
    conductor_material: Literal["copper", "aluminum"] = "copper"
    insulation_material: Literal["xlpe", "epr", "paper_oil"] = "xlpe"
    voltage_kv: float = Field(..., gt=0, description="Phase-to-ground voltage in kV")
    installation: InstallationInput
    frequency_hz: float = Field(60.0, gt=0)


class SuggestSizeResponse(BaseModel):
    """Suggested cable size response."""
    suggested_size_mm2: float
    suggested_size_kcmil: float
    expected_ampacity_a: float
    margin_percent: float


# Standard conductor sizes (mm²)
STANDARD_SIZES_MM2 = [
    25, 35, 50, 70, 95, 120, 150, 185, 240, 300,
    400, 500, 630, 800, 1000, 1200, 1400, 1600, 2000
]

# Approximate conductor diameters (mm) for standard sizes
CONDUCTOR_DIAMETERS = {
    25: 5.64, 35: 6.68, 50: 7.98, 70: 9.44, 95: 11.0,
    120: 12.4, 150: 13.8, 185: 15.3, 240: 17.5, 300: 19.5,
    400: 22.6, 500: 25.2, 630: 28.3, 800: 31.9, 1000: 35.7,
    1200: 39.1, 1400: 42.2, 1600: 45.1, 2000: 50.5
}

# Insulation thickness by voltage class (approximate, mm)
def get_insulation_thickness(voltage_kv: float, material: str) -> float:
    """Get typical insulation thickness for voltage level."""
    # Simplified - actual values depend on BIL, etc.
    if voltage_kv <= 15:
        return 4.5 if material == "xlpe" else 5.5
    elif voltage_kv <= 25:
        return 5.5 if material == "xlpe" else 6.5
    elif voltage_kv <= 35:
        return 8.0 if material == "xlpe" else 9.0
    elif voltage_kv <= 69:
        return 12.0 if material == "xlpe" else 14.0
    elif voltage_kv <= 115:
        return 16.0 if material == "xlpe" else 18.0
    elif voltage_kv <= 138:
        return 18.0 if material == "xlpe" else 20.0
    else:
        return 24.0 if material == "xlpe" else 26.0


@router.post("/suggest-size", response_model=SuggestSizeResponse)
async def suggest_size(request: SuggestSizeRequest):
    """
    Suggest minimum cable size for target current.

    Iterates through standard sizes to find smallest that meets requirement.
    """
    target = request.target_current_a
    insulation_thickness = get_insulation_thickness(
        request.voltage_kv, request.insulation_material
    )

    for size_mm2 in STANDARD_SIZES_MM2:
        diameter = CONDUCTOR_DIAMETERS.get(size_mm2, size_mm2 ** 0.5 * 1.13)

        conductor = ConductorSpec(
            material=request.conductor_material,
            cross_section=size_mm2,
            diameter=diameter,
            stranding="stranded_compact",
        )

        insulation = InsulationSpec(
            material=request.insulation_material,
            thickness=insulation_thickness,
            conductor_diameter=diameter,
        )

        # Estimate shield diameter
        shield_diameter = diameter + 2 * insulation_thickness + 2

        shield = ShieldSpec(
            material="copper",
            type="wire",
            thickness=1.5,
            mean_diameter=shield_diameter,
            bonding="single_point",
        )

        cable = CableSpec(
            conductor=conductor,
            insulation=insulation,
            shield=shield,
            jacket_thickness=3.0,
            jacket_material="pe",
        )

        # For suggest-size, use direct buried installation (default)
        installation = BurialConditions(
            depth=request.installation.depth_m,
            soil_resistivity=request.installation.soil_resistivity,
            ambient_temp=request.installation.ambient_temp_c,
            spacing=request.installation.spacing_m,
        )

        operating = OperatingConditions(
            voltage=request.voltage_kv,
            frequency=request.frequency_hz,
            load_factor=1.0,
        )

        try:
            results = calculate_ampacity(cable, installation, operating)
            ampacity = results["ampacity"]

            if ampacity >= target:
                margin = (ampacity - target) / target * 100
                return SuggestSizeResponse(
                    suggested_size_mm2=size_mm2,
                    suggested_size_kcmil=size_mm2 / 0.5067,
                    expected_ampacity_a=ampacity,
                    margin_percent=margin,
                )
        except Exception:
            continue

    # If no standard size works, return largest
    raise HTTPException(
        status_code=400,
        detail=f"No standard cable size can achieve {target}A. Maximum size may be insufficient."
    )


@router.get("/conductor-sizes")
async def get_conductor_sizes():
    """Get list of standard conductor sizes."""
    return {
        "sizes_mm2": STANDARD_SIZES_MM2,
        "sizes_kcmil": [s / 0.5067 for s in STANDARD_SIZES_MM2],
    }


@router.get("/max-temperatures")
async def get_max_temperatures():
    """Get maximum conductor temperatures by insulation type."""
    return MAX_CONDUCTOR_TEMP
