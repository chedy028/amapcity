# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cable Ampacity Design Assistant - an LLM-powered engineering tool for calculating the current-carrying capacity of underground power cables. Implements IEC 60287 and Neher-McGrath standards.

## Commands

### Quick Start
```bash
./start.sh              # Starts backend (port 8000) + frontend (port 3000)
```

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
# API docs: http://localhost:8000/docs
```

### Frontend
```bash
cd frontend
npm install
npm run dev             # Development server
npm run build           # Production build
```

### Testing
```bash
pytest tests/                               # Run all tests
pytest tests/test_cymcap_validation.py -v   # Run specific test
pytest tests/ --cov=cable_ampacity          # With coverage
```

## Architecture

### Three-Layer Structure

```
frontend/               → Next.js 16 + React 19 + Tailwind 4
    └── src/lib/api.ts  → Type-safe API client
backend/                → FastAPI
    └── routes/         → API endpoints (calculations, chat, reports)
cable_ampacity/         → Pure Python calculation engine (2,500 lines)
```

### Core Calculation Engine (`cable_ampacity/`)

Four modules implementing IEC 60287 and CIGRE standards:

1. **ac_resistance.py** - AC resistance with skin/proximity effects
   - CIGRE lookup table for Milliken conductors ≥800 mm²
   - Configurable Ks/Kp coefficients

2. **losses.py** - Conductor, dielectric, and shield losses
   - Temperature-dependent resistivity correction

3. **thermal_resistance.py** (most complex, 1,500+ lines)
   - R1-R4 thermal resistances per IEC 60287-2-1
   - Multi-layer backfill support (CYMCAP-aligned)
   - Duct bank with geometric factors
   - Current-weighted mutual heating between cables

4. **solver.py** - Iterative ampacity solver
   - Finds current where conductor reaches max temperature (typically 90°C)

### Key Data Structures

All specs use dataclasses for clean APIs:
```python
CableSpec(conductor, insulation, shield, jacket_thickness, ...)
OperatingConditions(voltage, frequency, max_conductor_temp)
BurialConditions(depth, soil_resistivity, ambient_temp, spacing)
ConduitConditions(...)
DuctBankConditions(...)
```

### API Endpoints

```
POST /api/calculate     → Main ampacity calculation
POST /api/chat          → LLM chat with function calling (OpenRouter)
POST /api/reports       → Generate HTML/PDF reports
GET  /api/health        → Health check
```

### Frontend Component Hierarchy

```
page.tsx
├── DesignWizard        → Multi-step form with tabs
├── ResultsPanel        → Results display
├── CableCrossSection   → 2D cable visualization
├── ChatSidebar         → AI assistant interface
└── ReportViewer        → HTML report modal
```

## Installation Types Supported

- **Direct Buried**: Single or multi-cable with spacing
- **Conduit**: Single/multiple conduits in soil or concrete
- **Duct Banks**: 2D arrays (e.g., 3×3) with configurable occupied positions

## Validation

The calculation engine is validated against CYMCAP 8.2:
- Hottest cable match: **-1.7%** (excellent)
- Thermally-limited circuits: **±3-8%**
- See `CYMCAP_COMPARISON_REPORT.md` for details

## Key Dependencies

**Backend**: FastAPI, Pydantic, httpx, WeasyPrint (PDF)
**Frontend**: React 19, Next.js 16, Tailwind 4, shadcn/ui, Zod, react-hook-form
