# Cayuga Duct Bank CYMCAP Analysis

## Study Details
- **CYMCAP Version**: 8.2 Revision 3
- **Study**: CAYUGA 230 KV
- **Execution**: CAYUGA Duct Bank
- **Date**: 5/2/2025
- **Type**: Temperature calculation at fixed current (1000 A)

---

## Environment Parameters

| Parameter | Value | Unit |
|-----------|-------|------|
| Ambient Temperature | 25 | °C |
| Native Soil Resistivity | 0.9 | K.m/W |
| Installation Type | Multiple Ductbanks | - |

---

## Cable Specification: CAYUGA 230 KV 5000 KCMIL 2

### Conductor
| Parameter | Value (Imperial) | Value (Metric) | Source |
|-----------|------------------|----------------|--------|
| Material | Copper | - | CYMCAP |
| Construction | 4 Segments (Milliken) | - | CYMCAP |
| Milliken Type | Insulated Wires | - | CYMCAP |
| Area | 3.930 in² | 2535.6 mm² | CYMCAP |
| Diameter | 2.238 in | 56.85 mm | CYMCAP |
| **Ks (Skin Effect)** | **0.35** | - | CYMCAP |
| **Kp (Proximity)** | **0.20** | - | CYMCAP |
| DC Resistance at 20°C | 0.01116 Ω/mile | 6.94 µΩ/m | CYMCAP |

### Insulation
| Parameter | Value (Imperial) | Value (Metric) | Source |
|-----------|------------------|----------------|--------|
| Material | XLPE Unfilled | - | CYMCAP |
| Thermal Resistivity | 3.5 | K.m/W | CYMCAP |
| tan δ | 0.001 | - | CYMCAP |
| Permittivity (ε) | 2.5 | - | CYMCAP |
| Thickness | 0.906 in | 23.01 mm | CYMCAP |
| Outer Diameter | 4.15 in | 105.4 mm | CYMCAP |

### Additional Layers
| Layer | Thickness (in) | Diameter (in) |
|-------|----------------|---------------|
| Conductor Shield | 0.05 | 2.338 |
| Insulation Screen | 0.08 | 4.31 |
| Concentric Wires (40 × #16 Cu) | 0.0508 | 4.412 |
| Jacket (PE) | 0.16 | 4.732 |

### Conduit
| Parameter | Value (Imperial) | Value (Metric) |
|-----------|------------------|----------------|
| Type | PVC in Concrete | - |
| Thermal Resistivity | 6.0 K.m/W | - |
| Inner Diameter | 7.981 in | 202.7 mm |
| Outer Diameter | 8.625 in | 219.1 mm |

---

## Backfill Layers

| Layer | Y (ft) | Height (ft) | Width (ft) | ρ (K.m/W) | Description |
|-------|--------|-------------|------------|-----------|-------------|
| Surface | 0.75 | 1.505 | 3.25 | 1.2 | Upper backfill |
| Middle | 5.75 | 8.495 | 3.25 | 1.0 | Main backfill |
| Duct Bank | 11.125 | 2.25 | 3.25 | 0.7 | Thermal concrete |
| Bottom | 12.5 | 0.5 | 3.25 | 2.5 | Below duct bank |

---

## Cable Positions

```
                X (ft)
        -1.0      0.0      1.0
         ┌────────┬────────┐
Y=10.76  │  (1)A  │  (2)B  │  (3)C   ← Top Row
         ├────────┼────────┤
Y=11.76  │  (6)C  │  (4)A  │  (5)B   ← Bottom Row (deeper)
         └────────┴────────┘
```

| Cable | Circuit | Phase | X (ft) | Y (ft) | X (m) | Y (m) |
|-------|---------|-------|--------|--------|-------|-------|
| 1 | 1 | A | -1.000 | 10.757 | -0.305 | 3.279 |
| 2 | 1 | B | 0.000 | 10.757 | 0.000 | 3.279 |
| 3 | 1 | C | 1.000 | 10.757 | 0.305 | 3.279 |
| 4 | 1 | A | 0.000 | 11.757 | 0.000 | 3.584 |
| 5 | 1 | B | 1.000 | 11.757 | 0.305 | 3.584 |
| 6 | 1 | C | -1.000 | 11.757 | -0.305 | 3.584 |

---

## CYMCAP Results at 1000 A

### Temperatures
| Cable | Conductor (°C) | Sheath (°C) | Cable Surface (°C) | Duct Surface (°C) | ΔT from Mutual (°C) |
|-------|----------------|-------------|-------------------|-------------------|---------------------|
| 1 | 63.41 | 59.66 | 59.21 | 55.49 | 23.55 |
| 2 | 65.64 | 61.86 | 61.42 | 57.72 | 25.61 |
| 3 | 63.41 | 59.65 | 59.21 | 55.49 | 23.55 |
| **4** | **68.33** | 64.53 | 64.09 | 60.41 | **27.86** |
| 5 | 65.61 | 61.84 | 61.40 | 57.70 | 25.36 |
| 6 | 65.61 | 61.84 | 61.39 | 57.70 | 25.36 |

**Hottest Cable**: #4 (center of bottom row) at 68.33°C

### AC Resistance Components
| Cable | Ys (Skin) | Yp (Proximity) | Rac (Ω/mile) | Rac (µΩ/m) |
|-------|-----------|----------------|--------------|------------|
| 1 | 0.1872 | 0.0047 | 0.01557 | 9.68 |
| 2 | 0.1848 | 0.0060 | 0.01568 | 9.74 |
| 3 | 0.1872 | 0.0047 | 0.01557 | 9.68 |
| 4 | 0.1820 | 0.0059 | 0.01578 | 9.80 |
| 5 | 0.1848 | 0.0046 | 0.01566 | 9.73 |
| 6 | 0.1848 | 0.0046 | 0.01566 | 9.73 |

### Thermal Resistances
| Cable | T1 (K.m/W) | T3 (K.m/W) | T4 (K.m/W) | Total (K.m/W) |
|-------|------------|------------|------------|---------------|
| 1 | 0.358 | 0.039 | 3.032 | 3.429 |
| 2 | 0.358 | 0.039 | 3.209 | 3.606 |
| 3 | 0.358 | 0.039 | 3.032 | 3.429 |
| 4 | 0.358 | 0.039 | **3.425** | **3.822** |
| 5 | 0.358 | 0.039 | 3.211 | 3.608 |
| 6 | 0.358 | 0.039 | 3.210 | 3.607 |

### Losses at 1000 A
| Cable | Wc (W/ft) | Wd (W/ft) | Wc (W/m) | Wd (W/m) |
|-------|-----------|-----------|----------|----------|
| 1 | 2.949 | 0.490 | 9.68 | 1.61 |
| 2 | 2.969 | 0.490 | 9.74 | 1.61 |
| 3 | 2.949 | 0.490 | 9.68 | 1.61 |
| 4 | 2.988 | 0.490 | 9.80 | 1.61 |
| 5 | 2.965 | 0.490 | 9.73 | 1.61 |
| 6 | 2.965 | 0.490 | 9.73 | 1.61 |

---

## Key Observations

### 1. Skin Effect (Ys = 0.18-0.19)
- CYMCAP uses Ks = 0.35, Kp = 0.20 for this Milliken conductor
- Resulting Ys ≈ 0.185 is **reasonable** for Milliken
- **Much lower** than Homer City study (Ks=0.62 → Ys=0.04-0.06 with CIGRE table)

### 2. Thermal Resistance Pattern
- T4 ranges from 3.03 to 3.43 K.m/W
- Cable 4 (center-bottom) has highest T4 due to mutual heating
- Corner cables (1, 3) have lowest T4

### 3. Temperature Pattern
- Cable 4 is hottest: 68.33°C (center of bottom row)
- Cables 1, 3 are coolest: 63.41°C (top row corners)
- ΔT range: ~5°C across all cables

### 4. Ampacity Estimation
With max temp 90°C, available ΔT = 90 - 25 = 65°C
At 1000 A, hottest cable reaches 68.33°C (43.33°C rise)
Estimated ampacity ≈ 1000 × √(65/43.33) ≈ **1225 A**

---

## Comparison with Homer City Study

| Parameter | Cayuga | Homer City |
|-----------|--------|------------|
| Voltage | 230 kV | 345 kV |
| Conductor Area | 2536 mm² | 2529 mm² |
| Ks | **0.35** | **0.62** |
| Kp | **0.20** | **0.37** |
| Ys (result) | 0.18-0.19 | 0.04-0.06 |
| Number of Cables | 6 | 36 |
| Depth | ~11 ft (~3.4 m) | ~5-6 ft (~1.7 m) |
| Soil Resistivity | 0.9 K.m/W | 1.3 K.m/W |
| Ambient Temp | 25°C | 20°C |
| Study Type | Temperature | Ampacity |

---

## Test Data for Validation

To validate our calculator against this study:

```python
# Cayuga study parameters
CAYUGA_PARAMS = {
    "conductor": {
        "material": "copper",
        "cross_section": 2535.636,  # mm²
        "diameter": 56.85,  # mm
        "stranding": "segmental",
        "ks": 0.35,
        "kp": 0.20,
        "dc_resistance_20c": 6.94e-6,  # ohm/m
    },
    "insulation": {
        "material": "xlpe",
        "thickness": 23.01,  # mm
        "tan_delta": 0.001,
        "permittivity": 2.5,
        "thermal_resistivity": 3.5,
    },
    "geometry": {
        "conductor_shield_thickness": 1.27,  # mm
        "insulation_screen_thickness": 2.03,  # mm
        "concentric_wire_thickness": 1.29,  # mm
        "jacket_thickness": 4.06,  # mm
        "overall_diameter": 120.18,  # mm
    },
    "conduit": {
        "id_mm": 202.72,
        "od_mm": 219.08,
        "material": "pvc",
        "thermal_resistivity": 6.0,
    },
    "environment": {
        "ambient_temp": 25,  # °C
        "soil_resistivity": 0.9,  # K.m/W
    },
    "cable_positions": [
        {"id": 1, "x_m": -0.305, "y_m": 3.279, "phase": "A"},
        {"id": 2, "x_m": 0.000, "y_m": 3.279, "phase": "B"},
        {"id": 3, "x_m": 0.305, "y_m": 3.279, "phase": "C"},
        {"id": 4, "x_m": 0.000, "y_m": 3.584, "phase": "A"},
        {"id": 5, "x_m": 0.305, "y_m": 3.584, "phase": "B"},
        {"id": 6, "x_m": -0.305, "y_m": 3.584, "phase": "C"},
    ],
    "cymcap_results_at_1000A": {
        1: {"temp": 63.41, "ys": 0.1872, "yp": 0.0047, "t4": 3.032},
        2: {"temp": 65.64, "ys": 0.1848, "yp": 0.0060, "t4": 3.209},
        3: {"temp": 63.41, "ys": 0.1872, "yp": 0.0047, "t4": 3.032},
        4: {"temp": 68.33, "ys": 0.1820, "yp": 0.0059, "t4": 3.425},
        5: {"temp": 65.61, "ys": 0.1848, "yp": 0.0046, "t4": 3.211},
        6: {"temp": 65.61, "ys": 0.1848, "yp": 0.0046, "t4": 3.210},
    },
}
```

---

---

## Our Calculator Comparison Results

### Ampacity Comparison

| Cable | Position | Our Ampacity | CYMCAP Est. | Difference |
|-------|----------|--------------|-------------|------------|
| 1 | (-0.305, 3.279) | 1543 A | 1301 A | +18.6% |
| 2 | (0.000, 3.279) | 1485 A | 1265 A | +17.4% |
| 3 | (0.305, 3.279) | 1543 A | 1301 A | +18.6% |
| **4** | (0.000, 3.584) | **1478 A** | **1225 A** | **+20.7%** |
| 5 | (0.305, 3.584) | 1536 A | 1265 A | +21.4% |
| 6 | (-0.305, 3.584) | 1536 A | 1265 A | +21.4% |

**Average difference: +19.7%**

### R4 Thermal Resistance Comparison

| Cable | Our R4_eff | CYMCAP T4 | Difference |
|-------|------------|-----------|------------|
| 1 | 2.36 K.m/W | 3.03 K.m/W | -22.1% |
| 2 | 2.59 K.m/W | 3.21 K.m/W | -19.3% |
| 3 | 2.36 K.m/W | 3.03 K.m/W | -22.1% |
| 4 | 2.62 K.m/W | 3.43 K.m/W | -23.6% |
| 5 | 2.39 K.m/W | 3.21 K.m/W | -25.5% |
| 6 | 2.39 K.m/W | 3.21 K.m/W | -25.5% |

### Skin Effect Comparison

| Parameter | Our Calculator | CYMCAP |
|-----------|---------------|--------|
| Ks (input) | 0.35 | 0.35 |
| **Ycs (result)** | **0.059** | **0.185** |
| Ratio | - | 3.1x higher |

---

## Root Cause Analysis

Our ampacity is **~20% higher** than CYMCAP estimates due to two factors:

### 1. Skin Effect (Ycs) - Primary Factor (~15%)

| Issue | Description |
|-------|-------------|
| Problem | CIGRE lookup table overrides user Ks for Milliken ≥800 mm² |
| Our Ycs | 0.059 (from CIGRE table) |
| CYMCAP Ycs | 0.185 (from Ks=0.35 with proprietary formula) |
| Impact | Lower Rac → Higher ampacity |

### 2. Thermal Resistance (R4) - Secondary Factor (~5%)

| Issue | Description |
|-------|-------------|
| Our R4_eff | 2.4-2.6 K.m/W |
| CYMCAP T4 | 3.0-3.4 K.m/W |
| Difference | ~23% lower |
| Impact | Lower thermal resistance → Higher ampacity |

---

## Recommendations

1. **Add CIGRE bypass option**: Allow user to force IEC formula with custom Ks/Kp
2. **Add direct Ycs/Ycp override**: For cases where measured or CYMCAP values are known
3. **Review R4 calculation**: CYMCAP may include additional thermal path components

---

## Notes

1. This is a **temperature study** (fixed current = 1000 A), not an ampacity study
2. The Ks=0.35 suggests this is using manufacturer-specific values, not standard IEC
3. CYMCAP Ys ≈ 0.185 is **3x higher** than our CIGRE table value (~0.059)
4. The CIGRE table may be too conservative for some Milliken constructions
5. Different Milliken types (insulated vs enameled wires) have different Ycs characteristics
