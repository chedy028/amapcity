'use client';

import { useState } from 'react';
import { DesignWizard, type DesignFormData } from '@/components/DesignWizard';
import { ChatSidebar } from '@/components/ChatSidebar';
import { ResultsPanel } from '@/components/ResultsPanel';
import { ReportViewer } from '@/components/ReportViewer';
import {
  calculateAmpacity,
  generateReport,
  getReportPdfUrl,
  CONDUCTOR_SIZES,
  getInsulationThickness,
  type CalculationResponse,
} from '@/lib/api';

export default function Home() {
  const [formData, setFormData] = useState<DesignFormData | null>(null);
  const [results, setResults] = useState<CalculationResponse | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [reportHtml, setReportHtml] = useState<string | null>(null);
  const [reportPdfUrl, setReportPdfUrl] = useState<string | null>(null);
  const [isReportOpen, setIsReportOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCalculate = async (data: DesignFormData) => {
    setIsCalculating(true);
    setError(null);

    try {
      // Find conductor diameter
      const sizeInfo = CONDUCTOR_SIZES.find((s) => s.mm2 === data.conductorSize);
      const diameter = sizeInfo?.diameter_mm || Math.sqrt(data.conductorSize) * 1.13;

      // Get insulation thickness
      const voltageLG = data.systemVoltage / 1.732;
      const insulationThickness = getInsulationThickness(voltageLG, data.insulationType);

      // Calculate shield diameter
      const shieldDiameter = diameter + 2 * insulationThickness + 2;

      const request = {
        conductor: {
          material: data.conductorMaterial,
          cross_section_mm2: data.conductorSize,
          diameter_mm: diameter,
          stranding: 'stranded_compact' as const,
        },
        insulation: {
          material: data.insulationType,
          thickness_mm: insulationThickness,
        },
        shield: {
          material: 'copper' as const,
          type: 'wire' as const,
          thickness_mm: 1.5,
          mean_diameter_mm: shieldDiameter,
          bonding: data.shieldBonding,
        },
        jacket_thickness_mm: 3.0,
        jacket_material: data.jacketMaterial,
        installation: {
          depth_m: data.burialDepth,
          soil_resistivity: data.soilResistivity,
          ambient_temp_c: data.ambientTemp,
          spacing_m: data.phaseSpacing,
        },
        operating: {
          voltage_kv: voltageLG,
          frequency_hz: data.frequency,
          max_conductor_temp_c: data.maxConductorTemp,
          load_factor: data.loadFactor,
        },
      };

      const response = await calculateAmpacity(request);
      setResults(response);
      setFormData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Calculation failed');
    } finally {
      setIsCalculating(false);
    }
  };

  const handleGenerateReport = async () => {
    if (!results || !formData) return;

    setIsGeneratingReport(true);
    setError(null);

    try {
      const operatingTemp = results.ambient_temp_c + results.temperature_rise.total;
      const tempMargin = results.max_conductor_temp_c - operatingTemp;

      const response = await generateReport({
        parameters: {
          project_name: formData.projectName || 'Cable Ampacity Study',
          project_number: formData.projectNumber || undefined,
          engineer: formData.engineer || undefined,
          voltage_kv: formData.systemVoltage,
          frequency_hz: formData.frequency,
          voltage_class: formData.voltageClass,
          conductor_material: formData.conductorMaterial,
          conductor_size_mm2: formData.conductorSize,
          insulation_type: formData.insulationType,
          burial_depth_m: formData.burialDepth,
          soil_resistivity: formData.soilResistivity,
          ambient_temp_c: formData.ambientTemp,
          phase_spacing_m: formData.phaseSpacing,
        },
        results: {
          ampacity_a: results.ampacity_a,
          ampacity_cyclic_a: results.ampacity_cyclic_a,
          max_conductor_temp_c: results.max_conductor_temp_c,
          operating_temp_c: operatingTemp,
          temperature_margin_c: tempMargin,
          ac_resistance_mohm_per_m: results.ac_resistance.rac * 1000,
          conductor_losses_w_per_m: results.losses.conductor,
          dielectric_losses_w_per_m: results.losses.dielectric,
          total_losses_w_per_m: results.losses.total,
          thermal_resistance_total: results.thermal_resistance.total,
          design_status: results.design_status,
        },
        format: 'both',
      });

      setReportHtml(response.html_content || null);
      setReportPdfUrl(response.report_id ? getReportPdfUrl(response.report_id) : null);
      setIsReportOpen(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Report generation failed');
    } finally {
      setIsGeneratingReport(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Cable Ampacity Calculator</h1>
              <p className="text-sm text-muted-foreground">
                Underground cable design assistant powered by AI
              </p>
            </div>
            <div className="text-sm text-muted-foreground">
              Based on IEC 60287 &amp; Neher-McGrath
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        {error && (
          <div className="mb-4 p-4 bg-destructive/10 border border-destructive rounded-lg text-destructive">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left: Design Wizard */}
          <div>
            <DesignWizard
              onCalculate={handleCalculate}
              onFormChange={setFormData}
              isCalculating={isCalculating}
            />
          </div>

          {/* Right: Results Panel */}
          <div>
            <ResultsPanel
              results={results}
              onGenerateReport={handleGenerateReport}
              isGeneratingReport={isGeneratingReport}
            />
          </div>
        </div>
      </main>

      {/* Chat Sidebar */}
      <ChatSidebar designContext={formData || undefined} />

      {/* Report Viewer Modal */}
      <ReportViewer
        isOpen={isReportOpen}
        onClose={() => setIsReportOpen(false)}
        htmlContent={reportHtml}
        pdfUrl={reportPdfUrl}
      />
    </div>
  );
}
