/**
 * API Client for Cable Ampacity Design Assistant
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types
export interface ConductorInput {
  material: 'copper' | 'aluminum';
  cross_section_mm2: number;
  diameter_mm: number;
  stranding: 'solid' | 'stranded_round' | 'stranded_compact' | 'segmental';
  dc_resistance_20c?: number;
}

export interface InsulationInput {
  material: 'xlpe' | 'epr' | 'paper_oil';
  thickness_mm: number;
}

export interface ShieldInput {
  material: 'copper' | 'aluminum' | 'lead';
  type: 'tape' | 'wire' | 'corrugated' | 'extruded';
  thickness_mm: number;
  mean_diameter_mm: number;
  bonding: 'single_point' | 'both_ends' | 'cross_bonded';
}

export interface InstallationInput {
  installation_type: 'direct_buried' | 'conduit' | 'duct_bank';
  depth_m: number;
  soil_resistivity: number;
  ambient_temp_c: number;
  spacing_m: number;

  // Conduit-specific
  conduit_id_mm?: number;
  conduit_od_mm?: number;
  conduit_material?: 'pvc' | 'hdpe' | 'fiberglass' | 'steel';
  num_conduits?: number;

  // Duct bank-specific
  concrete_resistivity?: number;
  bank_width_m?: number;
  bank_height_m?: number;
  duct_rows?: number;
  duct_cols?: number;
  duct_spacing_h_m?: number;
  duct_spacing_v_m?: number;
  duct_id_mm?: number;
  duct_od_mm?: number;
  occupied_ducts?: [number, number][];
}

export interface OperatingInput {
  voltage_kv: number;
  frequency_hz: number;
  max_conductor_temp_c?: number;
  load_factor: number;
}

export interface CalculationRequest {
  conductor: ConductorInput;
  insulation: InsulationInput;
  shield?: ShieldInput;
  jacket_thickness_mm: number;
  jacket_material: 'pvc' | 'pe' | 'hdpe';
  installation: InstallationInput;
  operating: OperatingInput;
}

export interface CalculationResponse {
  ampacity_a: number;
  ampacity_cyclic_a: number;
  installation_type: string;
  max_conductor_temp_c: number;
  ambient_temp_c: number;
  delta_t_available_c: number;
  ac_resistance: {
    rdc: number;
    rac: number;
    ycs: number;
    ycp: number;
  };
  losses: {
    conductor: number;
    dielectric: number;
    shield: number;
    total: number;
  };
  thermal_resistance: {
    r1_insulation: number;
    r2_jacket: number;
    r3_conduit?: number;
    r_concrete?: number;
    r4_earth: number;
    r4_effective: number;
    mutual_heating_factor: number;
    total: number;
  };
  temperature_rise: {
    conductor_losses: number;
    dielectric_losses: number;
    total: number;
  };
  shield_loss_factor: number;
  design_status: 'PASS' | 'FAIL';
  formatted_report: string;
  duct_info?: {
    target_duct: [number, number];
    duct_positions: Array<[number, number, number, number]>;
  };
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  tool_call_id?: string;
  tool_calls?: unknown[];
}

export interface ChatRequest {
  messages: ChatMessage[];
  model: string;
  api_key: string;
  stream?: boolean;
  design_context?: Record<string, unknown>;
}

export interface ChatResponse {
  message: ChatMessage;
  tool_results?: Array<{
    tool: string;
    arguments: Record<string, unknown>;
    result: Record<string, unknown>;
  }>;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface Model {
  id: string;
  name: string;
  description: string;
  recommended: boolean;
}

export interface ReportRequest {
  parameters: {
    project_name: string;
    project_number?: string;
    engineer?: string;
    voltage_kv: number;
    frequency_hz: number;
    voltage_class: 'MV' | 'HV';
    conductor_material: 'copper' | 'aluminum';
    conductor_size_mm2: number;
    insulation_type: 'xlpe' | 'epr' | 'paper_oil';
    installation_type: 'direct_buried' | 'conduit' | 'duct_bank';
    burial_depth_m: number;
    soil_resistivity: number;
    ambient_temp_c: number;
    phase_spacing_m: number;
    // Conduit parameters
    conduit_material?: string;
    conduit_od_mm?: number;
    // Duct bank parameters
    concrete_resistivity?: number;
    duct_rows?: number;
    duct_cols?: number;
  };
  results: {
    ampacity_a: number;
    ampacity_cyclic_a: number;
    max_conductor_temp_c: number;
    operating_temp_c: number;
    temperature_margin_c: number;
    ac_resistance_mohm_per_m: number;
    conductor_losses_w_per_m: number;
    dielectric_losses_w_per_m: number;
    total_losses_w_per_m: number;
    thermal_resistance_total: number;
    design_status: 'PASS' | 'FAIL';
  };
  recommendations?: string;
  format: 'html' | 'pdf' | 'both';
}

// API Functions
export async function calculateAmpacity(request: CalculationRequest): Promise<CalculationResponse> {
  const response = await fetch(`${API_BASE}/api/calculate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Calculation failed');
  }

  return response.json();
}

export async function getModels(): Promise<Model[]> {
  const response = await fetch(`${API_BASE}/api/models`);
  if (!response.ok) throw new Error('Failed to fetch models');
  const data = await response.json();
  return data.models;
}

export async function chat(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Chat failed');
  }

  return response.json();
}

export async function generateReport(request: ReportRequest): Promise<{ report_id: string; html_content?: string }> {
  const response = await fetch(`${API_BASE}/api/report/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Report generation failed');
  }

  return response.json();
}

export function getReportPdfUrl(reportId: string): string {
  return `${API_BASE}/api/report/${reportId}/pdf`;
}

export async function suggestCableSize(
  targetCurrent: number,
  material: 'copper' | 'aluminum',
  insulation: 'xlpe' | 'epr' | 'paper_oil',
  voltageKv: number,
  installation: InstallationInput
): Promise<{ suggested_size_mm2: number; ampacity_a: number; margin_percent: number }> {
  const response = await fetch(`${API_BASE}/api/suggest-size`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      target_current_a: targetCurrent,
      conductor_material: material,
      insulation_material: insulation,
      voltage_kv: voltageKv,
      installation,
      frequency_hz: 60,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Size suggestion failed');
  }

  return response.json();
}

// Standard conductor sizes with approximate diameters
export const CONDUCTOR_SIZES: Array<{ mm2: number; kcmil: number; diameter_mm: number }> = [
  { mm2: 25, kcmil: 49, diameter_mm: 5.64 },
  { mm2: 35, kcmil: 69, diameter_mm: 6.68 },
  { mm2: 50, kcmil: 99, diameter_mm: 7.98 },
  { mm2: 70, kcmil: 138, diameter_mm: 9.44 },
  { mm2: 95, kcmil: 188, diameter_mm: 11.0 },
  { mm2: 120, kcmil: 237, diameter_mm: 12.4 },
  { mm2: 150, kcmil: 296, diameter_mm: 13.8 },
  { mm2: 185, kcmil: 365, diameter_mm: 15.3 },
  { mm2: 240, kcmil: 474, diameter_mm: 17.5 },
  { mm2: 300, kcmil: 592, diameter_mm: 19.5 },
  { mm2: 400, kcmil: 789, diameter_mm: 22.6 },
  { mm2: 500, kcmil: 987, diameter_mm: 25.2 },
  { mm2: 630, kcmil: 1243, diameter_mm: 28.3 },
  { mm2: 800, kcmil: 1579, diameter_mm: 31.9 },
  { mm2: 1000, kcmil: 1974, diameter_mm: 35.7 },
  { mm2: 1200, kcmil: 2368, diameter_mm: 39.1 },
  { mm2: 1400, kcmil: 2763, diameter_mm: 42.2 },
  { mm2: 1600, kcmil: 3158, diameter_mm: 45.1 },
  { mm2: 2000, kcmil: 3947, diameter_mm: 50.5 },
];

// Insulation thickness by voltage (approximate)
export function getInsulationThickness(voltageKv: number, material: 'xlpe' | 'epr' | 'paper_oil'): number {
  const baseThickness: { [key: number]: number } = {
    15: 4.5,
    25: 5.5,
    35: 8.0,
    69: 12.0,
    115: 16.0,
    138: 18.0,
    230: 24.0,
  };

  const voltages = Object.keys(baseThickness).map(Number).sort((a, b) => a - b);
  let thickness = 4.5;

  for (const v of voltages) {
    if (voltageKv <= v) {
      thickness = baseThickness[v];
      break;
    }
    thickness = baseThickness[v];
  }

  // EPR and paper are thicker
  if (material !== 'xlpe') {
    thickness *= 1.1;
  }

  return thickness;
}
