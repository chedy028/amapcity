"""
Cable Ampacity Calculator

Based on Neher-McGrath (1957) method and IEC 60287 standards.
Phase 1: Single cable, direct buried, XLPE insulation.
"""

from .ac_resistance import calculate_ac_resistance
from .losses import calculate_losses
from .thermal_resistance import calculate_thermal_resistances
from .solver import calculate_ampacity

__version__ = "0.1.0"
__all__ = [
    "calculate_ac_resistance",
    "calculate_losses",
    "calculate_thermal_resistances",
    "calculate_ampacity",
]
