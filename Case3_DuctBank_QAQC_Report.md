# Cable Ampacity QA/QC Calculation Report

## Case 3 Duct Bank - Cayuga 230kV

| Field | Value |
|-------|-------|
| Date Generated | 2026-01-17 12:17:33 |
| Software Version | 1.0.0 |
| Standards Reference | IEC 60287-1-1:2023, IEC 60287-2-1:2023 |
| Project | Cayuga 230kV Transmission Line |

## Input Parameters

### Cable Construction

| Parameter | Symbol | Value | Unit |
|-----------|--------|-------|------|
| Conductor Material | - | Copper | - |
| Conductor Cross-Section | $A_c$ | 2535.64 | mm² |
| Conductor Diameter | $d_c$ | 62.99 | mm |
| Conductor Stranding | - | Segmental | - |
| Insulation Material | - | XLPE | - |
| Insulation Thickness | $t_{ins}$ | 23.01 | mm |
| Conductor Shield Thickness | $t_{cs}$ | 2.39 | mm |
| Insulation Screen Thickness | $t_{is}$ | 2.39 | mm |
| Jacket Thickness | $t_j$ | 8.64 | mm |
| Overall Cable Diameter | $D_e$ | 136.09 | mm |
| Skin Effect Coefficient | $k_s$ | 0.62 | - |
| Proximity Effect Coefficient | $k_p$ | 0.37 | - |

### Operating Conditions

| Parameter | Symbol | Value | Unit |
|-----------|--------|-------|------|
| System Voltage (L-G) | $U_0$ | 132.79 | kV |
| Frequency | $f$ | 60 | Hz |
| Maximum Conductor Temperature | $T_{max}$ | 90 | °C |
| Load Factor | $LF$ | 1.00 | - |

### Installation Conditions

| Parameter | Symbol | Value | Unit |
|-----------|--------|-------|------|
| Installation Type | - | Duct Bank | - |
| Ambient Temperature | $T_{amb}$ | 29.0 | °C |
| Soil Thermal Resistivity | $\rho_{soil}$ | 0.90 | K·m/W |
| Duct Inner Diameter | $D_{di}$ | 202.72 | mm |
| Duct Outer Diameter | $D_{do}$ | 219.07 | mm |
| Duct Material | - | PVC | - |
| Depth to Top of Duct Bank | $L$ | 0.892 | m |
| Duct Bank Width | $W$ | 1.000 | m |
| Duct Bank Height | $H$ | 0.600 | m |
| Concrete Thermal Resistivity | $\rho_{conc}$ | 1.00 | K·m/W |
| Duct Array | - | 2 × 3 | rows × cols |

## 3.1 DC Resistance Calculation

**Standard Reference:** IEC 60287-1-1:2023, Clause 5.1.2

The DC resistance at operating temperature is calculated from:

$$R_{DC}(T) = R_{DC}(20°C) \times [1 + \alpha_{20} \times (T - 20)]$$

**Where:**
- $R_{DC}(20°C)$ = DC resistance at 20°C
- $\alpha_{20}$ = Temperature coefficient at 20°C = 0.00393 /°C (copper)
- $T$ = Operating temperature = 90°C

**Calculation:**
```
R_DC(20°C) = 6.799e-06 Ω/m
           = 0.010943 Ω/mile

R_DC(90°C) = 6.799e-06 × [1 + 0.00393 × (90 - 20)]
           = 6.799e-06 × [1 + 0.00393 × 70]
           = 6.799e-06 × 1.2751
           = 8.670e-06 Ω/m
           = 0.013953 Ω/mile
```

**Result:**
- $R_{DC}(90°C)$ = **8.670e-06 Ω/m** (8.6700 μΩ/m)

## 3.2 Skin Effect (IEC 60287-1-1:2023, Clause 5.1.3)

**Formula for $x_s^2$:**

$$x_s^2 = \frac{8\pi f}{R'_{DC}} \times 10^{-7} \times k_s$$

**Where:**
- $f$ = System frequency = 60 Hz
- $R'_{DC}$ = DC resistance at max temperature = 8.670e-06 Ω/m
- $k_s$ = Skin effect coefficient = 0.62 (Table 2, Segmental)

**Calculation of $x_s$:**
```
x_s² = (8 × π × 60 / 8.670e-06) × 10⁻⁷ × 0.62
     = 173928728.2939 × 10⁻⁷ × 0.62
     = 10.7836

x_s  = √(10.7836)
     = 3.2838
```

**Formula Selection (2.8 < $x_s$ ≤ 3.8):**

$$y_s = -0.136 - 0.0177 \cdot x_s + 0.0563 \cdot x_s^2$$

**Calculation of $y_s$:**
```
y_s = -0.136 - 0.0177 × 3.2838 + 0.0563 × 10.7836
    = -0.136 - 0.0581 + 0.6071
    = 0.4130
```

**Result:**
- $y_s$ = **0.4130**

## 3.3 Proximity Effect (IEC 60287-1-1:2023, Clause 5.1.4)

**Formula for $x_p^2$:**

$$x_p^2 = \frac{8\pi f}{R'_{DC}} \times 10^{-7} \times k_p$$

**Where:**
- $f$ = System frequency = 60 Hz
- $R'_{DC}$ = DC resistance at max temperature = 8.670e-06 Ω/m
- $k_p$ = Proximity effect coefficient = 0.37

**Calculation of $x_p$:**
```
x_p² = (8 × π × 60 / 8.670e-06) × 10⁻⁷ × 0.37
     = 6.4354

x_p  = √(6.4354)
     = 2.5368
```

**Function $F(x_p)$:**

$$F(x_p) = \frac{x_p^4}{192 + 0.8 \cdot x_p^4}$$

```
F(x_p) = 0.1840
```

**Proximity Effect Formula (Trefoil):**

$$y_p = F(x_p) \times \left(\frac{d_c}{s}\right)^2 \times \left[0.312 \times \left(\frac{d_c}{s}\right)^2 + \frac{1.18}{F(x_p) + 0.27}\right]$$

**Where:**
- $d_c$ = Conductor diameter = 62.99 mm
- $s$ = Axial spacing = 300.00 mm
- $d_c/s$ = 0.2100

**Result:**
- $y_p$ = **0.0519**

## 3.4 AC Resistance Calculation

**Standard Reference:** IEC 60287-1-1:2023, Clause 5.1

**Formula:**

$$R_{AC} = R_{DC} \times (1 + y_s + y_p)$$

**Calculation:**
```
R_AC = 8.670e-06 × (1 + 0.4130 + 0.0519)
     = 8.670e-06 × 1.4649
     = 1.270e-05 Ω/m
     = 12.7008 μΩ/m
     = 0.020440 Ω/mile
```

**Result:**
- $R_{AC}$ = **1.270e-05 Ω/m** (12.7008 μΩ/m)
- AC/DC Ratio = **1.4649**

## 3.5 Dielectric Loss (IEC 60287-1-1:2023, Clause 5.3)

**Formula:**

$$W_d = \omega \cdot C \cdot U_0^2 \cdot \tan(\delta)$$

**Where:**
- $\omega$ = Angular frequency = $2\pi f$ = 2 × π × 60 = 376.99 rad/s
- $C$ = Capacitance per unit length (F/m)
- $U_0$ = Phase-to-ground voltage = 132.79 kV = 132791 V
- $\tan(\delta)$ = Insulation loss factor = 0.001 (XLPE)

**Capacitance Calculation:**

$$C = \frac{2\pi\varepsilon_0\varepsilon_r}{\ln(D_i/d_c)}$$

**Where:**
- $\varepsilon_0$ = Permittivity of free space = 8.854e-12 F/m
- $\varepsilon_r$ = Relative permittivity = 2.5 (XLPE)
- $d_c$ = Conductor diameter = 62.99 mm
- $D_i$ = Diameter over insulation = 109.02 mm

```
C = (2 × π × 8.854e-12 × 2.5) / ln(109.02 / 62.99)
  = 1.391e-10 / ln(1.7306)
  = 1.391e-10 / 0.5485
  = 2.536e-10 F/m
```

**Dielectric Loss Calculation:**
```
W_d = 376.99 × 2.536e-10 × 132791² × 0.001
    = 376.99 × 2.536e-10 × 1.76e+10 × 0.001
    = 1.685593 W/m
```

**Result:**
- $W_d$ = **1.685593 W/m** (1685.5935 mW/m)

## 3.6 Thermal Resistances (IEC 60287-2-1:2023)

### T₁ - Insulation Thermal Resistance

**Formula (including semi-conducting layers):**

$$T_1 = \frac{\rho_T}{2\pi} \times \ln\left(1 + \frac{2t_1}{d_c}\right)$$

**Where:**
- $\rho_T$ = Thermal resistivity of insulation = 3.5 K·m/W
- $d_c$ = Conductor diameter = 62.99 mm
- $t_1$ = Total insulation thickness (including semi-con) = 27.79 mm
  - Conductor shield: 2.39 mm
  - Insulation: 23.01 mm
  - Insulation screen: 2.39 mm

**Calculation:**
```
T₁ = (3.5 / 2π) × ln(1 + 2 × 27.79 / 62.99)
   = 0.5570 × ln(1 + 0.8823)
   = 0.5570 × ln(1.8823)
   = 0.5570 × 0.6325
   = 0.3294 K·m/W
```

### T₂ - Jacket Thermal Resistance

**Formula:**

$$T_2 = \frac{\rho_T}{2\pi} \times \ln\left(\frac{D_e}{D_s}\right)$$

**Where:**
- $\rho_T$ = Thermal resistivity of jacket = 3.5 K·m/W
- $D_s$ = Diameter over shield = 118.82 mm
- $D_e$ = Overall cable diameter = 136.09 mm

**Calculation:**
```
T₂ = (3.5 / 2π) × ln(136.09 / 118.82)
   = 0.5570 × ln(1.1454)
   = 0.5570 × 0.1357
   = 0.0756 K·m/W
```

### T₃ - Conduit/Duct Thermal Resistance

T₃ consists of two components:
1. **Air gap** between cable and conduit inner surface
2. **Conduit wall** thermal resistance

**Conduit Parameters:**
- Inner diameter: 202.72 mm
- Outer diameter: 219.07 mm
- Cable diameter: 136.09 mm
- Duct thermal resistivity: 6.0 K·m/W

**Result:**
- $T_3$ = **0.0743 K·m/W**

### R_concrete - Concrete Encasement

For duct bank installations, the thermal resistance through the concrete encasement
is calculated using the IEC geometric factor method.

**Result:**
- $R_{concrete}$ = **0.2999 K·m/W**

### T₄ - External (Earth) Thermal Resistance

**Formula (Neher-McGrath):**

$$T_4 = \frac{\rho_{soil}}{2\pi} \times \ln\left(\frac{4L}{D_e}\right)$$

**Where:**
- $\rho_{soil}$ = Soil thermal resistivity = 0.9 K·m/W
- $L$ = Burial depth = 1.192 m = 1191.8 mm
- $D_e$ = External diameter = 136.09 mm

**Calculation:**
```
T₄ = (0.9 / 2π) × ln(4 × 1191.8 / 136.09)
   = 0.1432 × ln(35.0280)
   = 0.2563 K·m/W
```

### Mutual Heating Factor

**Factor:** F_mutual = 6.5514

**Effective T₄ with mutual heating:**
```
T₄_effective = T₄ × F_mutual
             = 0.2563 × 6.5514
             = 1.6794 K·m/W
```

### Summary of Thermal Resistances

| Component | Symbol | Value (K·m/W) |
|-----------|--------|---------------|
| Insulation | T₁ | 0.3294 |
| Jacket | T₂ | 0.0756 |
| Conduit/Duct | T₃ | 0.0743 |
| Concrete | R_conc | 0.2999 |
| Earth | T₄ | 0.2563 |
| Earth (effective) | T₄_eff | 1.6794 |
| **Total** | **ΣT** | **2.4586** |

## 3.7 Shield Loss Factor (λ₁)

**Shield Specifications:**
- Material: Copper
- Type: Tape
- Thickness: 0.13 mm
- Mean diameter: 116.18 mm
- Bonding: Single Point

**For single-point bonding:**
- No circulating currents flow in the shield
- Only eddy current losses apply

**Result:**
- $\lambda_1$ = **0.000000**

**Shield losses at rated current:**
- $W_s = \lambda_1 \times W_c$ = 0.0000 W/m

## 3.8 Ampacity Calculation

**Standard Reference:** IEC 60287-1-1:2023, Clause 1.4

### Temperature Budget

| Parameter | Value |
|-----------|-------|
| Maximum conductor temperature | $T_{max}$ = 90°C |
| Ambient temperature | $T_{amb}$ = 29.0°C |
| Available temperature rise | $\Delta T_{available}$ = 61.0°C |

### Temperature Rise from Dielectric Losses

$$\Delta T_{dielectric} = W_d \times (0.5 \cdot T_1 + T_2 + T_3 + R_{conc} + T_4)$$

```
ΔT_dielectric = 1.685593 × (0.5 × 0.3294 + 0.0756 + 0.0743 + 0.2999 + 1.6794)
              = 1.685593 × 2.2939
              = 3.8666°C
```

### Temperature Rise Available for Conductor Losses

```
ΔT_conductor = ΔT_available - ΔT_dielectric
             = 61.0 - 3.8666
             = 57.1334°C
```

### Ampacity Formula

$$I = \sqrt{\frac{\Delta T_{conductor}}{R_{AC} \times (1 + \lambda_1) \times (T_1 + T_2 + T_3 + R_{conc} + T_4)}}$$

**Where:**
- $\Delta T_{conductor}$ = 57.1334°C
- $R_{AC}$ = 1.270e-05 Ω/m
- $(1 + \lambda_1)$ = 1.000000
- $\Sigma T$ = 2.4586 K·m/W

**Calculation:**
```
I = √(57.1334 / (1.270e-05 × 1.000000 × 2.4586))
  = √(57.1334 / 3.122624e-05)
  = √(1829660.95)
  = 1352.6 A
```

### Result

| Parameter | Value |
|-----------|-------|
| **Ampacity (steady-state)** | **1352.6 A** |
| **Ampacity (cyclic)** | **1352.6 A** |

## 4. Results Summary

### Ampacity

| Parameter | Symbol | Value | Unit |
|-----------|--------|-------|------|
| Ampacity (steady-state) | $I$ | **1352.6** | A |
| Ampacity (cyclic) | $I_{cyclic}$ | 1352.6 | A |

### Resistance Values

| Parameter | Symbol | Value | Unit |
|-----------|--------|-------|------|
| DC Resistance at max temp | $R_{DC}$ | 8.6700 | μΩ/m |
| AC Resistance | $R_{AC}$ | 12.7008 | μΩ/m |
| AC/DC Ratio | $R_{AC}/R_{DC}$ | 1.4649 | - |
| Skin Effect Factor | $y_s$ | 0.4130 | - |
| Proximity Effect Factor | $y_p$ | 0.0519 | - |

### Losses at Rated Current

| Parameter | Symbol | Value | Unit |
|-----------|--------|-------|------|
| Conductor Losses | $W_c$ | 23.24 | W/m |
| Dielectric Losses | $W_d$ | 1.685593 | W/m |
| Shield Losses | $W_s$ | 0.0000 | W/m |
| Total Losses | $W_{total}$ | 24.92 | W/m |
| Shield Loss Factor | $\lambda_1$ | 0.000000 | - |

### Thermal Resistances

| Parameter | Symbol | Value | Unit |
|-----------|--------|-------|------|
| Insulation | $T_1$ | 0.3294 | K·m/W |
| Jacket | $T_2$ | 0.0756 | K·m/W |
| Conduit/Duct | $T_3$ | 0.0743 | K·m/W |
| Concrete | $R_{conc}$ | 0.2999 | K·m/W |
| Earth | $T_4$ | 0.2563 | K·m/W |
| Earth (effective) | $T_{4,eff}$ | 1.6794 | K·m/W |
| Mutual Heating Factor | $F$ | 6.5514 | - |
| **Total** | $\Sigma T$ | **2.4586** | K·m/W |

### Temperature Rise

| Parameter | Symbol | Value | Unit |
|-----------|--------|-------|------|
| From Conductor Losses | $\Delta T_c$ | 57.13 | °C |
| From Dielectric Losses | $\Delta T_d$ | 3.8666 | °C |
| Total | $\Delta T$ | 61.00 | °C |
| Ambient Temperature | $T_{amb}$ | 29.0 | °C |
| Max Conductor Temperature | $T_{max}$ | 90 | °C |

## 5. Comparison with CYMCAP

| Parameter | Our Value | CYMCAP | Difference |
|-----------|-----------|--------|------------|
| Ampacity (A) | 1352.6 | 1288 | +5.02% |
| Skin Effect (ys) | 0.4130 | 0.4100 | +0.73% |
| Proximity Effect (yp) | 0.0519 | 0.0063 | - |
| T1 (K·m/W) | 0.3294 | 0.3410 | -3.40% |