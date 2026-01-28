# Cable Ampacity Calculator - Development Plan & Summary

## Project Overview

**Goal**: Build an LLM-powered cable ampacity calculator validated against CYMCAP 8.2

**Status**: Core calculation engine complete, validated against two CYMCAP studies with identified gaps

---

## Completed Work

### 1. Core Calculation Engine Implementation

| Module | File | Description | Status |
|--------|------|-------------|--------|
| AC Resistance | `ac_resistance.py` | DC→AC resistance with skin/proximity effects | ✅ Complete |
| Losses | `losses.py` | Conductor, dielectric, shield losses | ✅ Complete |
| Thermal Resistance | `thermal_resistance.py` | R1-R4 per IEC 60287-2-1 | ✅ Complete |
| Solver | `solver.py` | Iterative ampacity calculation | ✅ Complete |

### 2. CYMCAP-Aligned Enhancements

| Feature | Description | Status |
|---------|-------------|--------|
| CIGRE Skin Effect Table | Lookup table for Milliken ≥800 mm² | ✅ Implemented |
| User Ks/Kp Override | Allow custom skin/proximity coefficients | ✅ Implemented |
| tan δ Configuration | Configurable dielectric loss factor | ✅ Implemented |
| Multi-layer Backfill | Support for layered soil/backfill | ✅ Implemented |
| Per-cable Positions | Individual (x, y) coordinates | ✅ Implemented |
| Iterative Mutual Heating | Current-weighted mutual heating solver | ✅ Implemented |
| IEC Geometric Factor | Kennelly formula for concrete encasement | ✅ Implemented |

### 3. Documentation

| Document | Description | Status |
|----------|-------------|--------|
| `CLAUDE.md` | Claude Code guidance for this repo | ✅ Created |
| `FORMULAS_AND_STANDARDS.md` | All formulas with IEC/CIGRE sources | ✅ Created |
| `CYMCAP_COMPARISON_REPORT.md` | Homer City validation results | ✅ Created |
| `CAYUGA_ANALYSIS.md` | Cayuga 230 KV analysis | ✅ Created |
| `ENGINEER_QUESTIONS.md` | Questions for human engineer | ✅ Created |

---

## Validation Results

### Study 1: Homer City 345 KV (36 cables)

| Metric | Result | Status |
|--------|--------|--------|
| Hottest cable (Cable 23) | -1.7% error | ✅ Excellent |
| Thermally-limited circuits (2, 4, 6) | ±3-8% error | ✅ Good |
| Design-limited circuits (1, 3, 5) | +26-38% error | ⚠️ Expected* |

*Circuits 1, 3, 5 have system design constraints (384 A rating) below thermal limit

### Study 2: Cayuga 230 KV (6 cables)

| Metric | Result | Status |
|--------|--------|--------|
| Average ampacity difference | +19.7% | ⚠️ Gap identified |
| Skin effect (Ycs) | Our 0.059 vs CYMCAP 0.185 | ❌ 3.1x difference |
| R4 thermal resistance | Our 2.6 vs CYMCAP 3.4 K.m/W | ⚠️ 23% lower |

---

## Identified Gaps

### Gap 1: Skin Effect for Non-Standard Milliken (HIGH PRIORITY)

**Problem**: CIGRE lookup table overrides user Ks for all Milliken ≥800 mm²

| Study | Ks | Our Ycs | CYMCAP Ycs | Match |
|-------|-----|---------|------------|-------|
| Homer City | 0.62 | 0.059 | 0.04-0.06 | ✅ Good |
| Cayuga | 0.35 | 0.059 | 0.185 | ❌ 3.1x off |

**Root Cause**:
- Homer City Ks=0.62 is close to IEC default (0.435), so CIGRE table works
- Cayuga Ks=0.35 ("Insulated Wires" Milliken) needs different treatment

**Solution Options**:
1. Add flag to bypass CIGRE table when user provides Ks
2. Add direct Ycs/Ycp override parameters
3. Create different tables for different Milliken constructions

### Gap 2: R4 Thermal Resistance (MEDIUM PRIORITY)

**Problem**: Our R4 is ~23% lower than CYMCAP T4

**Possible Causes**:
- Missing thermal path components in concrete encasement
- Different mutual heating methodology
- CYMCAP proprietary corrections

### Gap 3: Circuit Rating Logic (LOW PRIORITY)

**Problem**: Don't understand why Homer City has 384 A vs 489 A circuit ratings

**Need**: Clarification from engineer on CYMCAP's circuit rating methodology

---

## Next Steps

### Immediate (Before Engineer Meeting)

- [x] Document all questions in `ENGINEER_QUESTIONS.md`
- [x] Push code to GitHub
- [x] Create this summary document

### After Engineer Feedback

| Priority | Task | Depends On |
|----------|------|------------|
| HIGH | Implement CIGRE bypass / Ycs override | Q1.1, Q1.2 answers |
| HIGH | Review R4 calculation methodology | Q2.1, Q2.2 answers |
| MEDIUM | Add different Milliken construction types | Q1.2, Q4.2 answers |
| LOW | Implement circuit-based rating option | Q3.2 answer |

### Future Enhancements

| Feature | Description | Priority |
|---------|-------------|----------|
| Emergency rating | Short-term overload calculation | Medium |
| Cyclic rating | Full IEC 60287-3-2 implementation | Medium |
| Soil dryout | Temperature-dependent soil resistivity | Low |
| FEM validation | Compare with finite element analysis | Low |

---

## Key Files Reference

```
ampacity/
├── cable_ampacity/           # Core calculation engine
│   ├── ac_resistance.py      # 314 lines - AC resistance
│   ├── losses.py             # 292 lines - Loss calculations
│   ├── thermal_resistance.py # 1,527 lines - Thermal model
│   └── solver.py             # 382 lines - Ampacity solver
├── backend/                  # FastAPI server
├── frontend/                 # Next.js UI
├── tests/                    # CYMCAP validation tests
│   ├── test_cymcap_validation.py
│   └── test_cymcap_exact_comparison.py
├── CLAUDE.md                 # Claude Code guidance
├── FORMULAS_AND_STANDARDS.md # Formula reference
├── CYMCAP_COMPARISON_REPORT.md # Homer City results
├── CAYUGA_ANALYSIS.md        # Cayuga analysis
├── ENGINEER_QUESTIONS.md     # Questions for engineer
└── PLAN.md                   # This file
```

---

## Git History

| Commit | Description |
|--------|-------------|
| `b4c69bf` | Add Cayuga 230 KV CYMCAP analysis and engineer questions |
| `c331d89` | Improve CYMCAP accuracy with CIGRE skin effect and IEC thermal models |
| `1914f6e` | Add conduit and duct bank installation types with 2D visualization |
| `dddc574` | Initial commit: Cable Ampacity Design Assistant |

**Repository**: https://github.com/chedy028/amapcity.git

---

## Summary

The calculator achieves **excellent accuracy (<5%)** for thermally-limited cables with standard Milliken construction (Homer City). However, there's a **~20% gap** for non-standard Milliken with lower Ks values (Cayuga).

**Key insight**: The CIGRE lookup table is too aggressive in overriding user-provided Ks values. The fix requires either:
1. A bypass option for the CIGRE table, or
2. Direct Ycs/Ycp override capability

Awaiting engineer feedback on questions before implementing fixes.
