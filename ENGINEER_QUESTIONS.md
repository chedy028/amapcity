# Questions for Human Engineer

These questions arise from comparing our ampacity calculator against two CYMCAP studies:
1. **Homer City** - 345 kV, 36 cables, Ks=0.62
2. **Cayuga** - 230 kV, 6 cables, Ks=0.35

---

## 1. Skin Effect (Ycs) Calculation

### Context
For large Milliken conductors (≥800 mm²), we use a CIGRE lookup table that gives Ycs ≈ 0.05-0.06.
However, CYMCAP shows very different values depending on Ks:

| Study | Ks | Our Ycs | CYMCAP Ycs |
|-------|-----|---------|------------|
| Homer City | 0.62 | 0.059 | 0.04-0.06 |
| Cayuga | 0.35 | 0.059 | 0.185 |

### Questions

**Q1.1**: How does CYMCAP calculate Ycs for Milliken conductors when xs² exceeds 2.8?
- Does it use the IEC 60287-1-1 alternative formula?
- Does it use a proprietary lookup table?
- Does it cap/limit the result?

**Q1.2**: The Cayuga cable specifies "Milliken Wires Construction: Insulated Wires". How does wire insulation type affect skin effect?
- Insulated wires vs enameled wires vs bare wires?
- Does CYMCAP have different Ycs tables for different wire types?

**Q1.3**: Should we:
- (a) Always use CIGRE table for Milliken ≥800 mm² (current approach)?
- (b) Use IEC formula with user Ks, but cap results?
- (c) Allow direct Ycs override input?
- (d) Have different tables for different Milliken constructions?

---

## 2. Thermal Resistance T4 Components

### Context
CYMCAP T4 is significantly higher than our R4_effective:

| Study | Our R4_eff | CYMCAP T4 | Difference |
|-------|------------|-----------|------------|
| Cayuga Cable 4 | 2.62 K.m/W | 3.43 K.m/W | -23% |
| Homer City Cable 23 | ~10 K.m/W | ~30 K.m/W | -67% |

### Questions

**Q2.1**: CYMCAP shows T4 = T4' + T4'' + T4'''. What exactly is included in each component?
- T4' = Inside duct (air gap) - is this the same as our R3?
- T4'' = Duct wall - included in R3?
- T4''' = External medium - our R4?

**Q2.2**: For duct bank installations, does CYMCAP T4 include:
- Thermal resistance through concrete encasement?
- Thermal resistance through backfill layers?
- Full mutual heating from ALL other cables?

**Q2.3**: Our mutual heating uses the Neher-McGrath image method. Does CYMCAP use:
- Same image method?
- Finite element analysis?
- Different coupling factors?

---

## 3. Homer City Circuit Ratings (384 A vs 489 A)

### Context
In the Homer City study, CYMCAP assigns:
- Circuits 1, 3, 5 → 384 A (temps 60-80°C)
- Circuits 2, 4, 6 → 489 A (temps 72-85°C)

The 384 A cables are well below 90°C max, suggesting non-thermal constraints.

### Questions

**Q3.1**: Why do circuits 1, 3, 5 have lower ampacity (384 A) when their temperatures are lower?
- Is this a system design constraint (generator ratings)?
- Is this load balancing between units?
- Is this a derating factor for certain positions?

**Q3.2**: When CYMCAP calculates ampacity for a duct bank:
- Does it find max current per cable position?
- Does it apply same current to all cables in a circuit and find limiting cable?
- Does it apply same current to ALL cables and find limiting position?

**Q3.3**: For validation purposes, which comparison is correct:
- Compare our per-cable ampacity to CYMCAP per-cable ampacity?
- Compare our minimum (limiting) ampacity to CYMCAP circuit rating?

---

## 4. Ks and Kp Values

### Context
Standard IEC values for segmental (Milliken) conductors: Ks=0.435, Kp=0.37

But CYMCAP studies use different values:
- Homer City: Ks=0.62, Kp=0.37
- Cayuga: Ks=0.35, Kp=0.20

### Questions

**Q4.1**: Where do these Ks/Kp values come from?
- Manufacturer test data?
- CYMCAP cable library?
- Calculated from conductor geometry?

**Q4.2**: Is there a reference for Ks/Kp values by:
- Conductor cross-section?
- Number of segments (4, 5, 6)?
- Wire insulation type?

**Q4.3**: For a new cable design, how should we determine Ks/Kp if manufacturer data is not available?

---

## 5. CYMCAP Validation Approach

### Questions

**Q5.1**: What is the expected accuracy tolerance for ampacity calculations?
- ±5%?
- ±10%?
- Different for different installation types?

**Q5.2**: Which CYMCAP output should we validate against:
- Steady-state ampacity (A)?
- Temperature at fixed current (°C)?
- Thermal resistances (K.m/W)?

**Q5.3**: Can you provide a CYMCAP study where:
- Only thermal limit applies (no system constraints)?
- Single circuit (simpler validation)?
- Direct buried (no duct bank complexity)?

---

## 6. Specific Data Requests

**Q6.1**: For Cayuga study, can you run CYMCAP in "Ampacity" mode (not "Temperature" mode) to get the actual calculated ampacity for each cable?

**Q6.2**: Can you export the detailed thermal resistance breakdown from CYMCAP?
- R1 (insulation)
- R2 (bedding)
- R3 (jacket)
- T4', T4'', T4''' separately

**Q6.3**: Can you provide the CYMCAP calculation report showing intermediate values?
- xs², xp² values
- F(xs), F(xp) functions
- Exact formula used for Ycs when xs² > 2.8

---

## Summary Priority

| Priority | Question | Impact |
|----------|----------|--------|
| **HIGH** | Q1.1, Q1.2 | Skin effect is primary cause of Cayuga discrepancy |
| **HIGH** | Q2.2, Q2.3 | R4 difference affects both studies |
| **MEDIUM** | Q3.2 | Understanding CYMCAP methodology |
| **MEDIUM** | Q4.1, Q4.2 | Ks/Kp source for different cables |
| **LOW** | Q5.3, Q6.1 | Additional validation data |
