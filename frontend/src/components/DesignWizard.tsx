'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { CONDUCTOR_SIZES, getInsulationThickness } from '@/lib/api';

export interface DesignFormData {
  // Project
  projectName: string;
  projectNumber: string;
  engineer: string;

  // System
  voltageClass: 'MV' | 'HV';
  systemVoltage: number;
  frequency: number;
  targetCurrent: number;
  loadFactor: number;

  // Cable
  conductorMaterial: 'copper' | 'aluminum';
  conductorSize: number;
  insulationType: 'xlpe' | 'epr' | 'paper_oil';
  shieldBonding: 'single_point' | 'both_ends' | 'cross_bonded';
  jacketMaterial: 'pvc' | 'pe' | 'hdpe';

  // Installation
  burialDepth: number;
  soilResistivity: number;
  ambientTemp: number;
  phaseSpacing: number;
  arrangement: 'trefoil' | 'flat';

  // Constraints
  maxConductorTemp: number;
  designMargin: number;
}

const defaultFormData: DesignFormData = {
  projectName: '',
  projectNumber: '',
  engineer: '',
  voltageClass: 'HV',
  systemVoltage: 138,
  frequency: 60,
  targetCurrent: 1000,
  loadFactor: 0.85,
  conductorMaterial: 'copper',
  conductorSize: 500,
  insulationType: 'xlpe',
  shieldBonding: 'single_point',
  jacketMaterial: 'pe',
  burialDepth: 1.0,
  soilResistivity: 1.0,
  ambientTemp: 25,
  phaseSpacing: 0.3,
  arrangement: 'trefoil',
  maxConductorTemp: 90,
  designMargin: 10,
};

interface DesignWizardProps {
  onCalculate: (data: DesignFormData) => void;
  onFormChange?: (data: DesignFormData) => void;
  isCalculating?: boolean;
}

export function DesignWizard({ onCalculate, onFormChange, isCalculating }: DesignWizardProps) {
  const [formData, setFormData] = useState<DesignFormData>(defaultFormData);
  const [activeTab, setActiveTab] = useState('project');

  const updateField = <K extends keyof DesignFormData>(field: K, value: DesignFormData[K]) => {
    const newData = { ...formData, [field]: value };

    // Auto-update related fields
    if (field === 'voltageClass') {
      newData.systemVoltage = value === 'MV' ? 35 : 138;
      newData.maxConductorTemp = newData.insulationType === 'paper_oil' ? 85 : 90;
    }
    if (field === 'insulationType') {
      newData.maxConductorTemp = value === 'paper_oil' ? 85 : 90;
    }

    setFormData(newData);
    onFormChange?.(newData);
  };

  const getConductorDiameter = (size: number): number => {
    const found = CONDUCTOR_SIZES.find(s => s.mm2 === size);
    return found?.diameter_mm || Math.sqrt(size) * 1.13;
  };

  const getInsulationThicknessValue = (): number => {
    const voltageLG = formData.systemVoltage / 1.732;
    return getInsulationThickness(voltageLG, formData.insulationType);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Cable Design Parameters</CardTitle>
        <CardDescription>
          Configure your underground cable design parameters
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="project">Project</TabsTrigger>
            <TabsTrigger value="cable">Cable</TabsTrigger>
            <TabsTrigger value="installation">Installation</TabsTrigger>
            <TabsTrigger value="constraints">Constraints</TabsTrigger>
          </TabsList>

          <TabsContent value="project" className="space-y-4 mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="projectName">Project Name</Label>
                <Input
                  id="projectName"
                  value={formData.projectName}
                  onChange={(e) => updateField('projectName', e.target.value)}
                  placeholder="Enter project name"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="projectNumber">Project Number</Label>
                <Input
                  id="projectNumber"
                  value={formData.projectNumber}
                  onChange={(e) => updateField('projectNumber', e.target.value)}
                  placeholder="e.g., PRJ-2024-001"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="engineer">Engineer</Label>
              <Input
                id="engineer"
                value={formData.engineer}
                onChange={(e) => updateField('engineer', e.target.value)}
                placeholder="Your name"
              />
            </div>

            <Separator className="my-4" />

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Voltage Class</Label>
                <Select
                  value={formData.voltageClass}
                  onValueChange={(v) => updateField('voltageClass', v as 'MV' | 'HV')}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="MV">Medium Voltage (5-46 kV)</SelectItem>
                    <SelectItem value="HV">High Voltage (69-230 kV)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="systemVoltage">System Voltage (kV)</Label>
                <Input
                  id="systemVoltage"
                  type="number"
                  value={formData.systemVoltage}
                  onChange={(e) => updateField('systemVoltage', parseFloat(e.target.value) || 0)}
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="frequency">Frequency (Hz)</Label>
                <Select
                  value={formData.frequency.toString()}
                  onValueChange={(v) => updateField('frequency', parseInt(v))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="50">50 Hz</SelectItem>
                    <SelectItem value="60">60 Hz</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="targetCurrent">Target Current (A)</Label>
                <Input
                  id="targetCurrent"
                  type="number"
                  value={formData.targetCurrent}
                  onChange={(e) => updateField('targetCurrent', parseFloat(e.target.value) || 0)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="loadFactor">Load Factor</Label>
                <Input
                  id="loadFactor"
                  type="number"
                  step="0.05"
                  min="0.1"
                  max="1.0"
                  value={formData.loadFactor}
                  onChange={(e) => updateField('loadFactor', parseFloat(e.target.value) || 1)}
                />
              </div>
            </div>

            <div className="flex justify-end mt-4">
              <Button onClick={() => setActiveTab('cable')}>
                Next: Cable Selection
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="cable" className="space-y-4 mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Conductor Material</Label>
                <Select
                  value={formData.conductorMaterial}
                  onValueChange={(v) => updateField('conductorMaterial', v as 'copper' | 'aluminum')}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="copper">Copper</SelectItem>
                    <SelectItem value="aluminum">Aluminum</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Conductor Size</Label>
                <Select
                  value={formData.conductorSize.toString()}
                  onValueChange={(v) => updateField('conductorSize', parseInt(v))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CONDUCTOR_SIZES.map((size) => (
                      <SelectItem key={size.mm2} value={size.mm2.toString()}>
                        {size.mm2} mm² ({size.kcmil} kcmil)
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="p-3 bg-muted rounded-lg">
              <div className="text-sm text-muted-foreground">
                Conductor Diameter: <strong>{getConductorDiameter(formData.conductorSize).toFixed(1)} mm</strong>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Insulation Type</Label>
                <Select
                  value={formData.insulationType}
                  onValueChange={(v) => updateField('insulationType', v as 'xlpe' | 'epr' | 'paper_oil')}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="xlpe">XLPE (90°C)</SelectItem>
                    <SelectItem value="epr">EPR (90°C)</SelectItem>
                    <SelectItem value="paper_oil">Paper/Oil (85°C)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Shield Bonding</Label>
                <Select
                  value={formData.shieldBonding}
                  onValueChange={(v) => updateField('shieldBonding', v as 'single_point' | 'both_ends' | 'cross_bonded')}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="single_point">Single-Point Bonding</SelectItem>
                    <SelectItem value="both_ends">Both-Ends Bonding</SelectItem>
                    <SelectItem value="cross_bonded">Cross-Bonded</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="p-3 bg-muted rounded-lg">
              <div className="text-sm text-muted-foreground">
                Estimated Insulation Thickness: <strong>{getInsulationThicknessValue().toFixed(1)} mm</strong>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Jacket Material</Label>
              <Select
                value={formData.jacketMaterial}
                onValueChange={(v) => updateField('jacketMaterial', v as 'pvc' | 'pe' | 'hdpe')}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pe">PE (Polyethylene)</SelectItem>
                  <SelectItem value="hdpe">HDPE</SelectItem>
                  <SelectItem value="pvc">PVC</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex justify-between mt-4">
              <Button variant="outline" onClick={() => setActiveTab('project')}>
                Back
              </Button>
              <Button onClick={() => setActiveTab('installation')}>
                Next: Installation
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="installation" className="space-y-4 mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="burialDepth">Burial Depth (m)</Label>
                <Input
                  id="burialDepth"
                  type="number"
                  step="0.1"
                  value={formData.burialDepth}
                  onChange={(e) => updateField('burialDepth', parseFloat(e.target.value) || 1)}
                />
                <p className="text-xs text-muted-foreground">Depth to cable center</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="soilResistivity">Soil Thermal Resistivity (K·m/W)</Label>
                <Input
                  id="soilResistivity"
                  type="number"
                  step="0.1"
                  value={formData.soilResistivity}
                  onChange={(e) => updateField('soilResistivity', parseFloat(e.target.value) || 1)}
                />
                <p className="text-xs text-muted-foreground">Typical: 0.5 (wet) - 2.5 (dry)</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="ambientTemp">Ambient Soil Temperature (°C)</Label>
                <Input
                  id="ambientTemp"
                  type="number"
                  value={formData.ambientTemp}
                  onChange={(e) => updateField('ambientTemp', parseFloat(e.target.value) || 25)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phaseSpacing">Phase Spacing (m)</Label>
                <Input
                  id="phaseSpacing"
                  type="number"
                  step="0.05"
                  value={formData.phaseSpacing}
                  onChange={(e) => updateField('phaseSpacing', parseFloat(e.target.value) || 0)}
                />
                <p className="text-xs text-muted-foreground">0 for single cable</p>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Cable Arrangement</Label>
              <Select
                value={formData.arrangement}
                onValueChange={(v) => updateField('arrangement', v as 'trefoil' | 'flat')}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="trefoil">Trefoil (Touching)</SelectItem>
                  <SelectItem value="flat">Flat Formation</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex justify-between mt-4">
              <Button variant="outline" onClick={() => setActiveTab('cable')}>
                Back
              </Button>
              <Button onClick={() => setActiveTab('constraints')}>
                Next: Constraints
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="constraints" className="space-y-4 mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="maxConductorTemp">Max Conductor Temperature (°C)</Label>
                <Input
                  id="maxConductorTemp"
                  type="number"
                  value={formData.maxConductorTemp}
                  onChange={(e) => updateField('maxConductorTemp', parseFloat(e.target.value) || 90)}
                />
                <p className="text-xs text-muted-foreground">
                  {formData.insulationType === 'xlpe' && 'XLPE rated: 90°C'}
                  {formData.insulationType === 'epr' && 'EPR rated: 90°C'}
                  {formData.insulationType === 'paper_oil' && 'Paper/Oil rated: 85°C'}
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="designMargin">Design Margin (%)</Label>
                <Input
                  id="designMargin"
                  type="number"
                  value={formData.designMargin}
                  onChange={(e) => updateField('designMargin', parseFloat(e.target.value) || 10)}
                />
                <p className="text-xs text-muted-foreground">Recommended: 10-15%</p>
              </div>
            </div>

            <Separator className="my-4" />

            <div className="p-4 bg-muted rounded-lg">
              <h4 className="font-medium mb-2">Design Summary</h4>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>Voltage: <Badge variant="outline">{formData.systemVoltage} kV</Badge></div>
                <div>Target Current: <Badge variant="outline">{formData.targetCurrent} A</Badge></div>
                <div>Conductor: <Badge variant="outline">{formData.conductorSize} mm² {formData.conductorMaterial}</Badge></div>
                <div>Insulation: <Badge variant="outline">{formData.insulationType.toUpperCase()}</Badge></div>
                <div>Depth: <Badge variant="outline">{formData.burialDepth} m</Badge></div>
                <div>Soil ρ: <Badge variant="outline">{formData.soilResistivity} K·m/W</Badge></div>
              </div>
            </div>

            <div className="flex justify-between mt-4">
              <Button variant="outline" onClick={() => setActiveTab('installation')}>
                Back
              </Button>
              <Button
                onClick={() => onCalculate(formData)}
                disabled={isCalculating}
              >
                {isCalculating ? 'Calculating...' : 'Calculate Ampacity'}
              </Button>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
