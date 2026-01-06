# Formulas and Standards Reference

This document provides a comprehensive reference for all formulas, input parameters, and their sources used in the cable ampacity calculation engine.

---

## Table of Contents

1. [Standards Overview](#standards-overview)
2. [Material Properties](#material-properties)
3. [DC Resistance](#dc-resistance)
4. [AC Resistance](#ac-resistance)
5. [Skin Effect](#skin-effect)
6. [Proximity Effect](#proximity-effect)
7. [Dielectric Losses](#dielectric-losses)
8. [Shield Losses](#shield-losses)
9. [Thermal Resistances](#thermal-resistances)
10. [Mutual Heating](#mutual-heating)
11. [Ampacity Equation](#ampacity-equation)
12. [Maximum Operating Temperatures](#maximum-operating-temperatures)

---

## Standards Overview

| Standard | Description | Application |
|----------|-------------|-------------|
| **IEC 60287-1-1** | Electric cables - Calculation of current rating - Part 1-1: Current rating equations and calculation of losses | AC resistance, skin/proximity effects, loss calculations |
| **IEC 60287-2-1** | Electric cables - Calculation of current rating - Part 2-1: Thermal resistance | Thermal resistance calculations (R1, R2, R3, R4) |
| **IEC 60287-3-2** | Electric cables - Calculation of current rating - Part 3-2: Sections on operating conditions - Economic optimization | Cyclic rating, load factor |
| **IEC 60228** | Conductors of insulated cables | DC resistance standards, temperature coefficients |
| **CIGRE TB 272** | Large Cross-sections and Composite Screens Design (2005) | Milliken conductor skin effect values |
| **CIGRE TB 531** | Cable Systems Electrical Characteristics (2013) | Additional Milliken conductor data |
| **Neher-McGrath (1957)** | "The Calculation of the Temperature Rise and Load Capability of Cable Systems" AIEE Trans. | Earth thermal resistance, mutual heating |

---

## Material Properties

### Conductor Resistivity at 20°C

| Material | Resistivity (Ω·m) | Source |
|----------|-------------------|--------|
| Copper | 1.7241 × 10⁻⁸ | IEC 60228 |
| Aluminum | 2.8264 × 10⁻⁸ | IEC 60228 |

**Code location**: `ac_resistance.py:28-31`

### Temperature Coefficient (α₂₀)

| Material | α₂₀ (per °C) | Equivalent β (K) | Source |
|----------|--------------|------------------|--------|
| Copper | 0.00393 | 234.5 | IEC 60228 |
| Aluminum | 0.00403 | 228.0 | IEC 60228 |

The relationship: **α₂₀ = 1 / (β + 20)**

**Code location**: `ac_resistance.py:33-36`

### Insulation Properties

| Material | tan δ | Permittivity (εᵣ) | Thermal Resistivity (K·m/W) | Max Temp (°C) | Source |
|----------|-------|-------------------|---------------------------|--------------|--------|
| XLPE | 0.001 | 2.5 | 3.5 | 90 | IEC 60287-1-1, manufacturer data |
| EPR | 0.005 | 3.0 | 3.5 | 90 | IEC 60287-1-1 |
| Paper-Oil | 0.0035 | 3.5 | 6.0 | 85 | IEC 60287-1-1 |

**Code location**: `losses.py:17-31`, `thermal_resistance.py:17-31`

### Jacket/Conduit Thermal Resistivity

| Material | Thermal Resistivity (K·m/W) | Source |
|----------|---------------------------|--------|
| PVC | 5.0 (jacket), 6.0 (conduit) | IEC 60287-2-1 |
| PE | 3.5 | IEC 60287-2-1 |
| HDPE | 3.5 | IEC 60287-2-1 |
| Fiberglass | 4.0 | IEC 60287-2-1 |

**Code location**: `thermal_resistance.py:17-50`

---

## DC Resistance

### Formula

$$R_{dc}(\theta) = R_{20} \times [1 + \alpha_{20} \times (\theta - 20)]$$

Where:
- R₂₀ = DC resistance at 20°C (Ω/m)
- α₂₀ = temperature coefficient at 20°C (per °C)
- θ = operating temperature (°C)

### From First Principles

If R₂₀ is not provided by manufacturer:

$$R_{20} = \frac{\rho_{20}}{A}$$

Where:
- ρ₂₀ = resistivity at 20°C (Ω·m)
- A = cross-sectional area (m²)

**Source**: IEC 60228, IEC 60287-1-1 Section 2.1
**Code location**: `ac_resistance.py:97-123`

---

## AC Resistance

### Master Formula

$$R_{ac} = R_{dc} \times (1 + Y_{cs} + Y_{cp})$$

Where:
- Rdc = DC resistance at operating temperature
- Ycs = skin effect factor
- Ycp = proximity effect factor

**Source**: IEC 60287-1-1 Section 2.1
**Code location**: `ac_resistance.py:278-314`

---

## Skin Effect

### IEC 60287-1-1 Formula

**Step 1**: Calculate x²s

$$x_s^2 = \frac{8 \pi f}{R'_{dc}} \times 10^{-7} \times k_s$$

Where:
- f = frequency (Hz)
- R'dc = DC resistance at operating temperature (Ω/m)
- ks = skin effect constant

**Step 2**: Calculate Ycs

For **xs² ≤ 2.8**:
$$Y_{cs} = \frac{x_s^4}{192 + 0.8 \times x_s^4}$$

For **xs² > 2.8** (IEC alternative formula):
$$Y_{cs} = -0.136 - 0.0177 \times x_s^2 + 0.0563 \times x_s^4$$

**Source**: IEC 60287-1-1 Section 2.1.2
**Code location**: `ac_resistance.py:177-223`

### Skin Effect Constant (ks)

| Conductor Type | ks | Source |
|----------------|-----|--------|
| Solid | 1.0 | IEC 60287-1-1 Table 2 |
| Stranded round | 1.0 | IEC 60287-1-1 Table 2 |
| Stranded compact | 0.8 | IEC 60287-1-1 Table 2 |
| Segmental (Milliken) | 0.435 | IEC 60287-1-1 Table 2 |

**Note**: User can override with measured ks values (e.g., 0.62 from CYMCAP).

**Code location**: `ac_resistance.py:38-44`

### CIGRE Lookup Table for Large Milliken Conductors

For segmental (Milliken) conductors ≥ 800 mm², the IEC formula becomes invalid when xs² > 2.8. Empirical values from CIGRE are used instead:

| Cross-section (mm²) | 50 Hz Ycs | 60 Hz Ycs |
|---------------------|-----------|-----------|
| 800 | 0.015 | 0.018 |
| 1000 | 0.019 | 0.023 |
| 1200 | 0.023 | 0.028 |
| 1400 | 0.027 | 0.032 |
| 1600 | 0.031 | 0.037 |
| 1800 | 0.035 | 0.042 |
| 2000 | 0.039 | 0.047 |
| 2500 | 0.048 | 0.058 |
| 3000 | 0.057 | 0.069 |

**Source**: CIGRE Technical Brochure 272 (2005), CIGRE TB 531 (2013)
**Code location**: `ac_resistance.py:54-82`, `ac_resistance.py:126-174`

---

## Proximity Effect

### IEC 60287-1-1 Formula

**Step 1**: Calculate xp²

$$x_p^2 = \frac{8 \pi f}{R'_{dc}} \times 10^{-7} \times k_p$$

**Step 2**: Calculate F(xp)

For **xp² ≤ 2.8**:
$$F(x_p) = \frac{x_p^4}{192 + 0.8 \times x_p^4}$$

For **xp² > 2.8**:
$$F(x_p) = -0.136 - 0.0177 \times x_p^2 + 0.0563 \times x_p^4$$

**Step 3**: Calculate Ycp (trefoil arrangement)

$$Y_{cp} = F(x_p) \times \left(\frac{d_c}{s}\right)^2 \times \left[0.312 \times \left(\frac{d_c}{s}\right)^2 + \frac{1.18}{F(x_p) + 0.27}\right]$$

Where:
- dc = conductor diameter (mm)
- s = axial spacing between conductors (mm)

**Source**: IEC 60287-1-1 Section 2.1.4
**Code location**: `ac_resistance.py:226-275`

### Proximity Effect Constant (kp)

| Conductor Type | kp | Source |
|----------------|-----|--------|
| Solid | 1.0 | IEC 60287-1-1 Table 2 |
| Stranded round | 0.8 | IEC 60287-1-1 Table 2 |
| Stranded compact | 0.8 | IEC 60287-1-1 Table 2 |
| Segmental (Milliken) | 0.37 | IEC 60287-1-1 Table 2 |

**Code location**: `ac_resistance.py:46-52`

---

## Dielectric Losses

### Formula

$$W_d = \omega \times C \times U_0^2 \times \tan\delta$$

Where:
- ω = 2πf (angular frequency)
- C = capacitance per unit length (F/m)
- U₀ = phase-to-ground voltage (V)
- tan δ = loss factor

### Capacitance Calculation

$$C = \frac{2\pi\varepsilon_0\varepsilon_r}{\ln(D_i/d_c)}$$

Where:
- ε₀ = 8.854 × 10⁻¹² F/m (permittivity of free space)
- εᵣ = relative permittivity of insulation
- Di = diameter over insulation (mm)
- dc = conductor diameter (mm)

**Source**: IEC 60287-1-1 Section 2.2
**Code location**: `losses.py:60-103`

---

## Shield Losses

### Shield Loss Factor (λ₁)

For single-point bonding:
$$\lambda_1 \approx \lambda_1'' \text{ (eddy current only)}$$

For both-ends or cross-bonding:
$$\lambda_1 = \lambda_1' + \lambda_1''$$

### Circulating Current Loss Factor (λ₁')

$$\lambda_1' = \frac{R_s}{R_{ac}} \times \frac{1}{1 + (R_s/X_s)^2}$$

Where:
- Rs = shield resistance at operating temperature (Ω/m)
- Rac = conductor AC resistance (Ω/m)
- Xs = shield reactance (Ω/m)

### Shield Reactance

$$X_s = 2\pi f \times 2 \times 10^{-7} \times \ln\left(\frac{2s}{d_s}\right)$$

Where:
- s = axial spacing (mm)
- ds = shield mean diameter (mm)

**Source**: IEC 60287-1-1 Section 2.3
**Code location**: `losses.py:106-194`

---

## Thermal Resistances

### R1 - Insulation Thermal Resistance

$$R_1 = \frac{\rho_T}{2\pi} \times \ln\left(\frac{D_i}{d_c}\right)$$

Where:
- ρT = thermal resistivity of insulation (K·m/W)
- Di = diameter over insulation (mm)
- dc = conductor diameter (mm)

**Source**: IEC 60287-2-1 Section 2.1.1
**Code location**: `thermal_resistance.py:202-231`

### R2 - Jacket Thermal Resistance

$$R_2 = \frac{\rho_T}{2\pi} \times \ln\left(\frac{D_e}{D_s}\right)$$

Where:
- De = overall cable diameter (mm)
- Ds = diameter over shield (mm)

**Source**: IEC 60287-2-1 Section 2.1.2
**Code location**: `thermal_resistance.py:234-263`

### R3 - Conduit Thermal Resistance

#### Air Gap Component

Based on IEC 60287-2-1 empirical coefficients:

$$T'_4 = \frac{U}{\pi \times D_{cable} \times h}$$

Where:
- U = 1.87 (black surface emissivity factor)
- h = 1 + 0.1 × (V + Y × θm) × Dconduit
- V = 0.29 (velocity coefficient)
- Y = 0.026 (temperature coefficient)

**Source**: IEC 60287-2-1 Table 2
**Code location**: `thermal_resistance.py:1043-1089`

#### Conduit Wall Component

$$R_{conduit} = \frac{\rho_T}{2\pi} \times \ln\left(\frac{D_{outer}}{D_{inner}}\right)$$

**Source**: IEC 60287-2-1 Section 2.2.2
**Code location**: `thermal_resistance.py:1092-1114`

### R4 - External (Earth) Thermal Resistance

#### Neher-McGrath Formula

$$R_4 = \frac{\rho_{soil}}{2\pi} \times \ln\left(u + \sqrt{u^2 - 1}\right)$$

Where:
- u = 2L / De
- L = burial depth to cable center (mm)
- De = cable/conduit outer diameter (mm)

For deep burial (u > 10):
$$R_4 \approx \frac{\rho_{soil}}{2\pi} \times \ln\left(\frac{4L}{D_e}\right)$$

**Source**: Neher-McGrath (1957) AIEE Trans., IEC 60287-2-1 Section 2.2.3
**Code location**: `thermal_resistance.py:266-299`

### Concrete Encasement (Duct Bank)

#### IEC 60287-2-1 Geometric Factor (Kennelly Formula)

$$G = \ln\left(\frac{(2d_{top} \times 2d_{bottom} \times 2d_{left} \times 2d_{right})^{0.25}}{r_{duct}}\right)$$

Where dtop, dbottom, dleft, dright are distances from cable to concrete boundaries.

$$R_{concrete} = \frac{\rho_{concrete}}{2\pi} \times G$$

**Source**: IEC 60287-2-1 Section 2.2.7 (Kennelly's method)
**Code location**: `thermal_resistance.py:1225-1286`

---

## Mutual Heating

### Image Method (Neher-McGrath)

The mutual heating from cable k to target cable p:

$$\Delta R_{4,k} = \frac{\rho_{soil}}{2\pi} \times \ln\left(\frac{d'_{pk}}{d_{pk}}\right)$$

Where:
- dpk = distance to cable k (m)
- d'pk = distance to image of cable k (m)

Image distance formula:
$$d'_{pk} = \sqrt{(x_p - x_k)^2 + (y_p + y_k)^2}$$

**Source**: Neher-McGrath (1957), IEC 60287-2-1 Section 2.2.3.2
**Code location**: `thermal_resistance.py:576-635`

### Iterative Current-Weighted Mutual Heating

For multi-cable installations per IEC 60287-3-2:

1. Initialize all cables at equal currents
2. Calculate heat output: Qi = Ii² × Rac × (1 + λ₁)
3. Weight mutual heating by relative heat output
4. Iterate until convergence

$$R_{mutual,i} = \sum_{j \neq i} F_{ij} \times w_j$$

Where:
- Fij = coupling factor between cables i and j
- wj = Qj / (Qtotal / n) (normalized heat weight)

**Source**: IEC 60287-3-2 Section 3
**Code location**: `thermal_resistance.py:638-820`

---

## Ampacity Equation

### Master Thermal Equation

$$\Delta T = I^2 \times R_{ac} \times (1 + \lambda_1) \times \sum R + W_d \times \sum R'$$

Where:
- ΔT = Tc,max - Tambient
- I = current (A)
- Rac = AC resistance (Ω/m)
- λ₁ = shield loss factor
- ΣR = R1 + R2 + R3 + Rconcrete + R4,effective
- Wd = dielectric loss (W/m)
- ΣR' = 0.5×R1 + R2 + R3 + Rconcrete + R4,effective

### Solving for Ampacity

$$I = \sqrt{\frac{\Delta T - W_d \times \sum R'}{R_{ac} \times (1 + \lambda_1) \times \sum R}}$$

**Source**: IEC 60287-1-1 Section 1.4
**Code location**: `solver.py:85-310`

### Cyclic Rating Approximation

For load factor < 1.0:
$$I_{cyclic} = \frac{I_{steady}}{\sqrt{LF}}$$

Where LF = load factor (0-1)

**Note**: Full cyclic rating calculation requires loss factor μ per IEC 60287-3-2.

**Source**: IEC 60287-3-2 Section 4
**Code location**: `solver.py:256-263`

---

## Maximum Operating Temperatures

| Insulation | Normal (°C) | Emergency (°C) | Short Circuit (°C) | Source |
|------------|-------------|----------------|-------------------|--------|
| XLPE | 90 | 105 | 250 | IEC 60287-1-1 |
| EPR | 90 | 130 | 250 | IEC 60287-1-1 |
| Paper-Oil | 85 | 100 | 160 | IEC 60287-1-1 |

**Code location**: `losses.py:26-31`

---

## Input Parameters Summary

### User-Configurable Parameters

| Parameter | Symbol | Unit | Default | Source |
|-----------|--------|------|---------|--------|
| Skin effect coefficient | ks | - | Per conductor type | IEC 60287-1-1 or manufacturer |
| Proximity effect coefficient | kp | - | Per conductor type | IEC 60287-1-1 or manufacturer |
| Loss factor | tan δ | - | Per insulation type | IEC 60287-1-1 or manufacturer |
| DC resistance at 20°C | R20 | Ω/m | Calculated | IEC 60228 or manufacturer |
| Insulation thermal resistivity | ρT | K·m/W | Per material | IEC 60287-2-1 or manufacturer |
| Soil thermal resistivity | ρsoil | K·m/W | Required input | Site measurement |
| Ambient temperature | Tamb | °C | Required input | Site conditions |

### CYMCAP-Aligned Optional Parameters

| Parameter | Description | Source |
|-----------|-------------|--------|
| conductor_shield_thickness | Semiconducting layer over conductor | Manufacturer data |
| insulation_screen_thickness | Semiconducting layer over insulation | Manufacturer data |
| backfill_layers | Multi-layer backfill definitions | CYMCAP methodology |
| cable_positions | Explicit (x, y) coordinates | CYMCAP methodology |

---

## Validation

This implementation has been validated against:
- **CYMCAP 8.2** - Homer City 345kV 5000 KCMIL study
- Hottest cable: **-1.7%** difference
- Thermally-limited circuits: **±3-8%** difference

See `CYMCAP_COMPARISON_REPORT.md` for detailed validation results.

---

## References

1. IEC 60287-1-1:2023 - Electric cables - Calculation of current rating - Part 1-1
2. IEC 60287-2-1:2023 - Electric cables - Calculation of current rating - Part 2-1
3. IEC 60287-3-2:2012 - Electric cables - Calculation of current rating - Part 3-2
4. IEC 60228:2004 - Conductors of insulated cables
5. CIGRE Technical Brochure 272 (2005) - Large Cross-sections and Composite Screens Design
6. CIGRE Technical Brochure 531 (2013) - Cable Systems Electrical Characteristics
7. Neher, J.H. and McGrath, M.H. (1957) - "The Calculation of the Temperature Rise and Load Capability of Cable Systems", AIEE Transactions Part III, Vol. 76, pp. 752-772
