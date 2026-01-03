"""
Report Generation API Endpoints

Generates engineering reports in HTML and PDF formats.
"""

from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field

router = APIRouter()


class DesignParameters(BaseModel):
    """Design input parameters for report."""
    project_name: str = "Cable Ampacity Study"
    project_number: Optional[str] = None
    engineer: Optional[str] = None

    # System
    voltage_kv: float
    frequency_hz: float = 60.0
    voltage_class: Literal["MV", "HV"] = "HV"

    # Cable
    conductor_material: Literal["copper", "aluminum"]
    conductor_size_mm2: float
    insulation_type: Literal["xlpe", "epr", "paper_oil"]

    # Installation
    burial_depth_m: float
    soil_resistivity: float
    ambient_temp_c: float
    phase_spacing_m: float = 0.0


class CalculationResults(BaseModel):
    """Calculation results for report."""
    ampacity_a: float
    ampacity_cyclic_a: float
    max_conductor_temp_c: float
    operating_temp_c: float
    temperature_margin_c: float
    ac_resistance_mohm_per_m: float
    conductor_losses_w_per_m: float
    dielectric_losses_w_per_m: float
    total_losses_w_per_m: float
    thermal_resistance_total: float
    design_status: Literal["PASS", "FAIL"]


class ReportRequest(BaseModel):
    """Request to generate an engineering report."""
    parameters: DesignParameters
    results: CalculationResults
    recommendations: Optional[str] = None
    format: Literal["html", "pdf", "both"] = "both"


class ReportResponse(BaseModel):
    """Report generation response."""
    report_id: str
    html_url: Optional[str] = None
    pdf_url: Optional[str] = None
    html_content: Optional[str] = None


def generate_html_report(params: DesignParameters, results: CalculationResults, recommendations: Optional[str] = None) -> str:
    """Generate HTML engineering report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    status_color = "#22c55e" if results.design_status == "PASS" else "#ef4444"
    status_bg = "#dcfce7" if results.design_status == "PASS" else "#fef2f2"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{params.project_name} - Cable Ampacity Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background: #f9fafb;
            padding: 2rem;
        }}
        .report {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            color: white;
            padding: 2rem;
        }}
        .header h1 {{ font-size: 1.75rem; margin-bottom: 0.5rem; }}
        .header .subtitle {{ opacity: 0.9; font-size: 1rem; }}
        .meta {{
            display: flex;
            gap: 2rem;
            margin-top: 1rem;
            font-size: 0.875rem;
            opacity: 0.9;
        }}
        .content {{ padding: 2rem; }}
        .section {{
            margin-bottom: 2rem;
        }}
        .section h2 {{
            font-size: 1.125rem;
            color: #1e40af;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 0.5rem;
            margin-bottom: 1rem;
        }}
        .status-badge {{
            display: inline-block;
            padding: 0.5rem 1.5rem;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 1.25rem;
            background: {status_bg};
            color: {status_color};
            border: 2px solid {status_color};
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin: 1.5rem 0;
        }}
        .summary-card {{
            background: #f8fafc;
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        }}
        .summary-card .value {{
            font-size: 1.5rem;
            font-weight: 700;
            color: #1e40af;
        }}
        .summary-card .label {{
            font-size: 0.75rem;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
        }}
        th, td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }}
        th {{
            background: #f8fafc;
            font-weight: 600;
            color: #374151;
        }}
        td:last-child {{
            text-align: right;
            font-family: 'Courier New', monospace;
        }}
        .recommendations {{
            background: #fffbeb;
            border: 1px solid #fbbf24;
            border-radius: 8px;
            padding: 1rem;
            margin-top: 1rem;
        }}
        .recommendations h3 {{
            color: #92400e;
            margin-bottom: 0.5rem;
        }}
        .footer {{
            background: #f8fafc;
            padding: 1.5rem 2rem;
            font-size: 0.75rem;
            color: #6b7280;
            border-top: 1px solid #e5e7eb;
        }}
        @media print {{
            body {{ background: white; padding: 0; }}
            .report {{ box-shadow: none; }}
        }}
    </style>
</head>
<body>
    <div class="report">
        <div class="header">
            <h1>{params.project_name}</h1>
            <div class="subtitle">Underground Cable Ampacity Analysis Report</div>
            <div class="meta">
                <span>Project: {params.project_number or 'N/A'}</span>
                <span>Engineer: {params.engineer or 'N/A'}</span>
                <span>Date: {timestamp}</span>
            </div>
        </div>

        <div class="content">
            <div class="section">
                <h2>Executive Summary</h2>
                <div style="text-align: center; margin: 1.5rem 0;">
                    <div class="status-badge">{results.design_status}</div>
                </div>
                <div class="summary-grid">
                    <div class="summary-card">
                        <div class="value">{results.ampacity_a:.0f} A</div>
                        <div class="label">Rated Ampacity</div>
                    </div>
                    <div class="summary-card">
                        <div class="value">{results.operating_temp_c:.1f} °C</div>
                        <div class="label">Operating Temperature</div>
                    </div>
                    <div class="summary-card">
                        <div class="value">{results.temperature_margin_c:.1f} °C</div>
                        <div class="label">Temperature Margin</div>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>Design Parameters</h2>
                <table>
                    <tr><th colspan="2">System Parameters</th></tr>
                    <tr><td>System Voltage</td><td>{params.voltage_kv} kV</td></tr>
                    <tr><td>Frequency</td><td>{params.frequency_hz} Hz</td></tr>
                    <tr><td>Voltage Class</td><td>{params.voltage_class}</td></tr>
                </table>
                <table>
                    <tr><th colspan="2">Cable Specification</th></tr>
                    <tr><td>Conductor Material</td><td>{params.conductor_material.title()}</td></tr>
                    <tr><td>Conductor Size</td><td>{params.conductor_size_mm2} mm² ({params.conductor_size_mm2/0.5067:.0f} kcmil)</td></tr>
                    <tr><td>Insulation Type</td><td>{params.insulation_type.upper()}</td></tr>
                </table>
                <table>
                    <tr><th colspan="2">Installation Conditions</th></tr>
                    <tr><td>Burial Depth</td><td>{params.burial_depth_m} m</td></tr>
                    <tr><td>Soil Thermal Resistivity</td><td>{params.soil_resistivity} K·m/W</td></tr>
                    <tr><td>Ambient Soil Temperature</td><td>{params.ambient_temp_c} °C</td></tr>
                    <tr><td>Phase Spacing</td><td>{params.phase_spacing_m} m</td></tr>
                </table>
            </div>

            <div class="section">
                <h2>Thermal Analysis Results</h2>
                <table>
                    <tr><th colspan="2">Ampacity</th></tr>
                    <tr><td>Steady-State Ampacity</td><td>{results.ampacity_a:.1f} A</td></tr>
                    <tr><td>Cyclic Rating (with load factor)</td><td>{results.ampacity_cyclic_a:.1f} A</td></tr>
                </table>
                <table>
                    <tr><th colspan="2">Temperature Analysis</th></tr>
                    <tr><td>Maximum Allowed Temperature</td><td>{results.max_conductor_temp_c} °C</td></tr>
                    <tr><td>Calculated Operating Temperature</td><td>{results.operating_temp_c:.1f} °C</td></tr>
                    <tr><td>Temperature Margin</td><td>{results.temperature_margin_c:.1f} °C</td></tr>
                </table>
                <table>
                    <tr><th colspan="2">Losses</th></tr>
                    <tr><td>Conductor Losses (I²R)</td><td>{results.conductor_losses_w_per_m:.2f} W/m</td></tr>
                    <tr><td>Dielectric Losses</td><td>{results.dielectric_losses_w_per_m:.4f} W/m</td></tr>
                    <tr><td>Total Losses</td><td>{results.total_losses_w_per_m:.2f} W/m</td></tr>
                </table>
                <table>
                    <tr><th colspan="2">Electrical Properties</th></tr>
                    <tr><td>AC Resistance</td><td>{results.ac_resistance_mohm_per_m:.4f} mΩ/m</td></tr>
                    <tr><td>Total Thermal Resistance</td><td>{results.thermal_resistance_total:.4f} K·m/W</td></tr>
                </table>
            </div>

            <div class="section">
                <h2>Design Verification</h2>
                <table>
                    <tr>
                        <td><strong>Temperature Check</strong></td>
                        <td style="color: {status_color}; font-weight: 600;">
                            {results.operating_temp_c:.1f} °C {'≤' if results.design_status == 'PASS' else '>'} {results.max_conductor_temp_c} °C — {results.design_status}
                        </td>
                    </tr>
                </table>
                {"<div class='recommendations'><h3>Recommendations</h3><p>" + recommendations + "</p></div>" if recommendations else ""}
            </div>
        </div>

        <div class="footer">
            <p>This report was generated by the Cable Ampacity Design Assistant.</p>
            <p>Calculations based on IEC 60287 and Neher-McGrath methods.</p>
            <p>Generated: {timestamp}</p>
        </div>
    </div>
</body>
</html>"""

    return html


@router.post("/report/generate")
async def generate_report(request: ReportRequest):
    """
    Generate an engineering report.

    Returns HTML content and optionally generates PDF.
    """
    import uuid

    report_id = str(uuid.uuid4())[:8]

    html_content = generate_html_report(
        request.parameters,
        request.results,
        request.recommendations,
    )

    response = ReportResponse(
        report_id=report_id,
        html_content=html_content if request.format in ["html", "both"] else None,
        html_url=f"/api/report/{report_id}/html" if request.format in ["html", "both"] else None,
        pdf_url=f"/api/report/{report_id}/pdf" if request.format in ["pdf", "both"] else None,
    )

    # Store report temporarily (in production, use proper storage)
    # For now, we'll regenerate on request
    _report_cache[report_id] = {
        "parameters": request.parameters,
        "results": request.results,
        "recommendations": request.recommendations,
    }

    return response


# Simple in-memory cache for reports (use Redis/DB in production)
_report_cache: dict = {}


@router.get("/report/{report_id}/html")
async def get_report_html(report_id: str):
    """Get HTML report by ID."""
    if report_id not in _report_cache:
        raise HTTPException(status_code=404, detail="Report not found")

    data = _report_cache[report_id]
    html = generate_html_report(
        DesignParameters(**data["parameters"].model_dump()),
        CalculationResults(**data["results"].model_dump()),
        data["recommendations"],
    )

    return HTMLResponse(content=html)


@router.get("/report/{report_id}/pdf")
async def get_report_pdf(report_id: str):
    """
    Get PDF report by ID.

    Note: Requires weasyprint to be installed.
    """
    if report_id not in _report_cache:
        raise HTTPException(status_code=404, detail="Report not found")

    try:
        from weasyprint import HTML
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="PDF generation requires weasyprint. Install with: pip install weasyprint"
        )

    data = _report_cache[report_id]
    html = generate_html_report(
        DesignParameters(**data["parameters"].model_dump()),
        CalculationResults(**data["results"].model_dump()),
        data["recommendations"],
    )

    # Generate PDF
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        HTML(string=html).write_pdf(f.name)
        return FileResponse(
            f.name,
            media_type="application/pdf",
            filename=f"cable_ampacity_report_{report_id}.pdf",
        )
