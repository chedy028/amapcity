"""
LLM Tool Definitions for OpenRouter Function Calling

Defines tools the AI can use to coordinate cable design.
"""

import sys
from pathlib import Path
from typing import Any

# Add parent directory to path for cable_ampacity imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cable_ampacity.ac_resistance import ConductorSpec, calculate_ac_resistance
from cable_ampacity.losses import InsulationSpec, ShieldSpec, MAX_CONDUCTOR_TEMP
from cable_ampacity.thermal_resistance import BurialConditions
from cable_ampacity.solver import (
    CableSpec,
    OperatingConditions,
    calculate_ampacity,
)

# Standard conductor sizes
STANDARD_SIZES_MM2 = [
    25, 35, 50, 70, 95, 120, 150, 185, 240, 300,
    400, 500, 630, 800, 1000, 1200, 1400, 1600, 2000
]

CONDUCTOR_DIAMETERS = {
    25: 5.64, 35: 6.68, 50: 7.98, 70: 9.44, 95: 11.0,
    120: 12.4, 150: 13.8, 185: 15.3, 240: 17.5, 300: 19.5,
    400: 22.6, 500: 25.2, 630: 28.3, 800: 31.9, 1000: 35.7,
    1200: 39.1, 1400: 42.2, 1600: 45.1, 2000: 50.5
}


def get_insulation_thickness(voltage_kv: float, material: str = "xlpe") -> float:
    """Get typical insulation thickness for voltage level."""
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


# OpenRouter/OpenAI compatible tool definitions
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_cable_ampacity",
            "description": "Calculate the ampacity (current carrying capacity) of a cable given its specifications and installation conditions. Returns detailed thermal analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "conductor_material": {
                        "type": "string",
                        "enum": ["copper", "aluminum"],
                        "description": "Conductor material"
                    },
                    "conductor_size_mm2": {
                        "type": "number",
                        "description": "Conductor cross-sectional area in mm²"
                    },
                    "insulation_type": {
                        "type": "string",
                        "enum": ["xlpe", "epr", "paper_oil"],
                        "description": "Insulation material type"
                    },
                    "voltage_kv": {
                        "type": "number",
                        "description": "System voltage in kV (line-to-line)"
                    },
                    "burial_depth_m": {
                        "type": "number",
                        "description": "Burial depth to cable center in meters"
                    },
                    "soil_resistivity": {
                        "type": "number",
                        "description": "Soil thermal resistivity in K·m/W (typical: 0.5-2.5)"
                    },
                    "ambient_temp_c": {
                        "type": "number",
                        "description": "Ambient soil temperature in °C"
                    },
                    "frequency_hz": {
                        "type": "number",
                        "description": "System frequency in Hz (50 or 60)"
                    },
                    "phase_spacing_m": {
                        "type": "number",
                        "description": "Spacing between phase conductors in meters (0 for single cable)"
                    },
                    "load_factor": {
                        "type": "number",
                        "description": "Load factor for cyclic rating (0-1, typically 0.7-1.0)"
                    }
                },
                "required": [
                    "conductor_material",
                    "conductor_size_mm2",
                    "insulation_type",
                    "voltage_kv",
                    "burial_depth_m",
                    "soil_resistivity",
                    "ambient_temp_c"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_cable_size",
            "description": "Suggest the minimum standard cable size to achieve a target current capacity. Iterates through standard sizes to find the optimal choice.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_current_a": {
                        "type": "number",
                        "description": "Required current capacity in Amperes"
                    },
                    "conductor_material": {
                        "type": "string",
                        "enum": ["copper", "aluminum"],
                        "description": "Conductor material"
                    },
                    "insulation_type": {
                        "type": "string",
                        "enum": ["xlpe", "epr", "paper_oil"],
                        "description": "Insulation material type"
                    },
                    "voltage_kv": {
                        "type": "number",
                        "description": "System voltage in kV (line-to-line)"
                    },
                    "burial_depth_m": {
                        "type": "number",
                        "description": "Burial depth in meters"
                    },
                    "soil_resistivity": {
                        "type": "number",
                        "description": "Soil thermal resistivity in K·m/W"
                    },
                    "ambient_temp_c": {
                        "type": "number",
                        "description": "Ambient soil temperature in °C"
                    }
                },
                "required": [
                    "target_current_a",
                    "conductor_material",
                    "insulation_type",
                    "voltage_kv",
                    "burial_depth_m",
                    "soil_resistivity",
                    "ambient_temp_c"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_design_temperature",
            "description": "Verify if a cable design will operate within safe temperature limits at a given current. Returns PASS/FAIL status with margin analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "conductor_material": {
                        "type": "string",
                        "enum": ["copper", "aluminum"]
                    },
                    "conductor_size_mm2": {
                        "type": "number"
                    },
                    "insulation_type": {
                        "type": "string",
                        "enum": ["xlpe", "epr", "paper_oil"]
                    },
                    "voltage_kv": {
                        "type": "number"
                    },
                    "operating_current_a": {
                        "type": "number",
                        "description": "Expected operating current in Amperes"
                    },
                    "burial_depth_m": {
                        "type": "number"
                    },
                    "soil_resistivity": {
                        "type": "number"
                    },
                    "ambient_temp_c": {
                        "type": "number"
                    },
                    "max_temp_override_c": {
                        "type": "number",
                        "description": "Override maximum conductor temperature (optional)"
                    }
                },
                "required": [
                    "conductor_material",
                    "conductor_size_mm2",
                    "insulation_type",
                    "voltage_kv",
                    "operating_current_a",
                    "burial_depth_m",
                    "soil_resistivity",
                    "ambient_temp_c"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_standard_cable_sizes",
            "description": "Get list of standard cable conductor sizes in mm² and kcmil.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_insulation_properties",
            "description": "Get properties of insulation materials including maximum operating temperatures and typical thermal resistivity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "insulation_type": {
                        "type": "string",
                        "enum": ["xlpe", "epr", "paper_oil"],
                        "description": "Insulation type (optional, returns all if not specified)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_cable_options",
            "description": "Compare multiple cable size options for a given application. Returns ampacity, losses, and cost-effectiveness analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "conductor_material": {
                        "type": "string",
                        "enum": ["copper", "aluminum"]
                    },
                    "sizes_mm2": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "List of conductor sizes to compare in mm²"
                    },
                    "insulation_type": {
                        "type": "string",
                        "enum": ["xlpe", "epr", "paper_oil"]
                    },
                    "voltage_kv": {
                        "type": "number"
                    },
                    "burial_depth_m": {
                        "type": "number"
                    },
                    "soil_resistivity": {
                        "type": "number"
                    },
                    "ambient_temp_c": {
                        "type": "number"
                    }
                },
                "required": [
                    "conductor_material",
                    "sizes_mm2",
                    "insulation_type",
                    "voltage_kv",
                    "burial_depth_m",
                    "soil_resistivity",
                    "ambient_temp_c"
                ]
            }
        }
    }
]


def execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Execute a tool by name with given arguments.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        Tool execution result
    """
    if name == "calculate_cable_ampacity":
        return _calculate_ampacity(arguments)
    elif name == "suggest_cable_size":
        return _suggest_size(arguments)
    elif name == "check_design_temperature":
        return _check_temperature(arguments)
    elif name == "get_standard_cable_sizes":
        return _get_sizes()
    elif name == "get_insulation_properties":
        return _get_insulation_props(arguments)
    elif name == "compare_cable_options":
        return _compare_options(arguments)
    else:
        return {"error": f"Unknown tool: {name}"}


def _calculate_ampacity(args: dict) -> dict:
    """Calculate cable ampacity."""
    size = args["conductor_size_mm2"]
    diameter = CONDUCTOR_DIAMETERS.get(size, size ** 0.5 * 1.13)
    voltage_ll = args["voltage_kv"]
    voltage_lg = voltage_ll / 1.732  # Line-to-ground

    conductor = ConductorSpec(
        material=args["conductor_material"],
        cross_section=size,
        diameter=diameter,
        stranding="stranded_compact",
    )

    insulation_thickness = get_insulation_thickness(voltage_lg, args["insulation_type"])
    insulation = InsulationSpec(
        material=args["insulation_type"],
        thickness=insulation_thickness,
        conductor_diameter=diameter,
    )

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

    burial = BurialConditions(
        depth=args["burial_depth_m"],
        soil_resistivity=args["soil_resistivity"],
        ambient_temp=args["ambient_temp_c"],
        spacing=args.get("phase_spacing_m", 0),
    )

    operating = OperatingConditions(
        voltage=voltage_lg,
        frequency=args.get("frequency_hz", 60),
        load_factor=args.get("load_factor", 1.0),
    )

    results = calculate_ampacity(cable, burial, operating)

    return {
        "ampacity_a": round(results["ampacity"], 1),
        "ampacity_cyclic_a": round(results["ampacity_cyclic"], 1),
        "max_conductor_temp_c": results["max_conductor_temp"],
        "conductor_losses_w_per_m": round(results["losses"]["conductor"], 2),
        "dielectric_losses_w_per_m": round(results["losses"]["dielectric"], 4),
        "total_losses_w_per_m": round(results["losses"]["total"], 2),
        "ac_resistance_mohm_per_m": round(results["ac_resistance"]["rac"] * 1000, 4),
        "thermal_resistance_total": round(results["thermal_resistance"]["total"], 4),
        "temperature_rise_c": round(results["temperature_rise"]["total"], 1),
    }


def _suggest_size(args: dict) -> dict:
    """Suggest cable size for target current."""
    target = args["target_current_a"]

    for size in STANDARD_SIZES_MM2:
        calc_args = {
            "conductor_material": args["conductor_material"],
            "conductor_size_mm2": size,
            "insulation_type": args["insulation_type"],
            "voltage_kv": args["voltage_kv"],
            "burial_depth_m": args["burial_depth_m"],
            "soil_resistivity": args["soil_resistivity"],
            "ambient_temp_c": args["ambient_temp_c"],
        }

        try:
            result = _calculate_ampacity(calc_args)
            if result["ampacity_a"] >= target:
                margin = (result["ampacity_a"] - target) / target * 100
                return {
                    "suggested_size_mm2": size,
                    "suggested_size_kcmil": round(size / 0.5067, 0),
                    "ampacity_a": result["ampacity_a"],
                    "margin_percent": round(margin, 1),
                    "meets_requirement": True,
                }
        except Exception:
            continue

    return {
        "error": f"No standard size achieves {target}A",
        "largest_size_mm2": STANDARD_SIZES_MM2[-1],
        "meets_requirement": False,
    }


def _check_temperature(args: dict) -> dict:
    """Check if design meets temperature requirements."""
    calc_args = {
        "conductor_material": args["conductor_material"],
        "conductor_size_mm2": args["conductor_size_mm2"],
        "insulation_type": args["insulation_type"],
        "voltage_kv": args["voltage_kv"],
        "burial_depth_m": args["burial_depth_m"],
        "soil_resistivity": args["soil_resistivity"],
        "ambient_temp_c": args["ambient_temp_c"],
    }

    result = _calculate_ampacity(calc_args)
    ampacity = result["ampacity_a"]
    operating_current = args["operating_current_a"]

    max_temp = args.get("max_temp_override_c") or result["max_conductor_temp_c"]

    # Calculate actual temperature at operating current
    # Temperature rise is proportional to I²
    current_ratio = operating_current / ampacity
    temp_rise_at_operating = result["temperature_rise_c"] * (current_ratio ** 2)
    actual_temp = args["ambient_temp_c"] + temp_rise_at_operating

    margin = max_temp - actual_temp
    status = "PASS" if actual_temp <= max_temp else "FAIL"

    return {
        "status": status,
        "operating_current_a": operating_current,
        "rated_ampacity_a": ampacity,
        "utilization_percent": round(current_ratio * 100, 1),
        "max_allowed_temp_c": max_temp,
        "estimated_operating_temp_c": round(actual_temp, 1),
        "temperature_margin_c": round(margin, 1),
    }


def _get_sizes() -> dict:
    """Get standard conductor sizes."""
    return {
        "sizes": [
            {"mm2": s, "kcmil": round(s / 0.5067, 0)}
            for s in STANDARD_SIZES_MM2
        ]
    }


def _get_insulation_props(args: dict) -> dict:
    """Get insulation properties."""
    props = {
        "xlpe": {
            "name": "Cross-linked Polyethylene",
            "max_temp_c": 90,
            "emergency_temp_c": 130,
            "thermal_resistivity": 3.5,
            "dielectric_constant": 2.5,
            "tan_delta": 0.004,
        },
        "epr": {
            "name": "Ethylene Propylene Rubber",
            "max_temp_c": 90,
            "emergency_temp_c": 130,
            "thermal_resistivity": 3.5,
            "dielectric_constant": 3.0,
            "tan_delta": 0.020,
        },
        "paper_oil": {
            "name": "Impregnated Paper",
            "max_temp_c": 85,
            "emergency_temp_c": 105,
            "thermal_resistivity": 6.0,
            "dielectric_constant": 3.5,
            "tan_delta": 0.0035,
        },
    }

    insulation_type = args.get("insulation_type")
    if insulation_type:
        return {insulation_type: props.get(insulation_type, {})}
    return props


def _compare_options(args: dict) -> dict:
    """Compare multiple cable size options."""
    sizes = args["sizes_mm2"]
    comparisons = []

    for size in sizes:
        calc_args = {
            "conductor_material": args["conductor_material"],
            "conductor_size_mm2": size,
            "insulation_type": args["insulation_type"],
            "voltage_kv": args["voltage_kv"],
            "burial_depth_m": args["burial_depth_m"],
            "soil_resistivity": args["soil_resistivity"],
            "ambient_temp_c": args["ambient_temp_c"],
        }

        try:
            result = _calculate_ampacity(calc_args)
            comparisons.append({
                "size_mm2": size,
                "size_kcmil": round(size / 0.5067, 0),
                "ampacity_a": result["ampacity_a"],
                "losses_w_per_m": result["total_losses_w_per_m"],
                "ac_resistance_mohm_per_m": result["ac_resistance_mohm_per_m"],
            })
        except Exception as e:
            comparisons.append({
                "size_mm2": size,
                "error": str(e),
            })

    return {"comparisons": comparisons}
