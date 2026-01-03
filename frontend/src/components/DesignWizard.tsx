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
import { CableCrossSection } from './CableCrossSection';

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
  installationType: 'direct_buried' | 'conduit' | 'duct_bank';
  burialDepth: number;
  soilResistivity: number;
  ambientTemp: number;
  phaseSpacing: number;
  arrangement: 'trefoil' | 'flat';

  // Conduit specific
  conduitIdMm: number;
  conduitOdMm: number;
  conduitMaterial: 'pvc' | 'hdpe' | 'fiberglass' | 'steel';
  numConduits: number;

  // Duct bank specific
  concreteResistivity: number;
  ductRows: number;
  ductCols: number;
  ductSpacingH: number;
  ductSpacingV: number;
  ductIdMm: number;
  ductOdMm: number;
  occupiedDucts: [number, number][];

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
  installationType: 'direct_buried',
  burialDepth: 1.0,
  soilResistivity: 1.0,
  ambientTemp: 25,
  phaseSpacing: 0.3,
  arrangement: 'trefoil',
  // Conduit defaults
  conduitIdMm: 150,
  conduitOdMm: 160,
  conduitMaterial: 'pvc',
  numConduits: 3,
  // Duct bank defaults
  concreteResistivity: 1.0,
  ductRows: 2,
  ductCols: 3,
  ductSpacingH: 0.2,
  ductSpacingV: 0.2,
  ductIdMm: 150,
  ductOdMm: 160,
  occupiedDucts: [[0, 0], [0, 1], [0, 2]], // Top row occupied by default
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
            {/* Installation Type Selector */}
            <div className="space-y-2">
              <Label>Installation Type</Label>
              <Select
                value={formData.installationType}
                onValueChange={(v) => updateField('installationType', v as 'direct_buried' | 'conduit' | 'duct_bank')}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="direct_buried">Direct Buried</SelectItem>
                  <SelectItem value="conduit">PVC/HDPE Conduit</SelectItem>
                  <SelectItem value="duct_bank">Concrete Duct Bank</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Separator className="my-2" />

            {/* Common Parameters */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="burialDepth">
                  {formData.installationType === 'duct_bank' ? 'Depth to Top of Bank (m)' : 'Burial Depth (m)'}
                </Label>
                <Input
                  id="burialDepth"
                  type="number"
                  step="0.1"
                  value={formData.burialDepth}
                  onChange={(e) => updateField('burialDepth', parseFloat(e.target.value) || 1)}
                />
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
              {formData.installationType !== 'duct_bank' && (
                <div className="space-y-2">
                  <Label htmlFor="phaseSpacing">
                    {formData.installationType === 'conduit' ? 'Conduit Spacing (m)' : 'Phase Spacing (m)'}
                  </Label>
                  <Input
                    id="phaseSpacing"
                    type="number"
                    step="0.05"
                    value={formData.phaseSpacing}
                    onChange={(e) => updateField('phaseSpacing', parseFloat(e.target.value) || 0)}
                  />
                </div>
              )}
            </div>

            {/* Conduit-Specific Parameters */}
            {formData.installationType === 'conduit' && (
              <>
                <Separator className="my-2" />
                <h4 className="text-sm font-medium">Conduit Parameters</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Conduit Material</Label>
                    <Select
                      value={formData.conduitMaterial}
                      onValueChange={(v) => updateField('conduitMaterial', v as 'pvc' | 'hdpe' | 'fiberglass' | 'steel')}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pvc">PVC</SelectItem>
                        <SelectItem value="hdpe">HDPE</SelectItem>
                        <SelectItem value="fiberglass">Fiberglass</SelectItem>
                        <SelectItem value="steel">Steel</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="numConduits">Number of Conduits</Label>
                    <Input
                      id="numConduits"
                      type="number"
                      min={1}
                      max={6}
                      value={formData.numConduits}
                      onChange={(e) => updateField('numConduits', parseInt(e.target.value) || 1)}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="conduitIdMm">Conduit ID (mm)</Label>
                    <Input
                      id="conduitIdMm"
                      type="number"
                      value={formData.conduitIdMm}
                      onChange={(e) => updateField('conduitIdMm', parseFloat(e.target.value) || 150)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="conduitOdMm">Conduit OD (mm)</Label>
                    <Input
                      id="conduitOdMm"
                      type="number"
                      value={formData.conduitOdMm}
                      onChange={(e) => updateField('conduitOdMm', parseFloat(e.target.value) || 160)}
                    />
                  </div>
                </div>
              </>
            )}

            {/* Duct Bank-Specific Parameters */}
            {formData.installationType === 'duct_bank' && (
              <>
                <Separator className="my-2" />
                <h4 className="text-sm font-medium">Duct Bank Parameters</h4>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="concreteResistivity">Concrete ρ (K·m/W)</Label>
                    <Input
                      id="concreteResistivity"
                      type="number"
                      step="0.1"
                      value={formData.concreteResistivity}
                      onChange={(e) => updateField('concreteResistivity', parseFloat(e.target.value) || 1)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="ductRows">Rows</Label>
                    <Input
                      id="ductRows"
                      type="number"
                      min={1}
                      max={6}
                      value={formData.ductRows}
                      onChange={(e) => updateField('ductRows', parseInt(e.target.value) || 2)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="ductCols">Columns</Label>
                    <Input
                      id="ductCols"
                      type="number"
                      min={1}
                      max={6}
                      value={formData.ductCols}
                      onChange={(e) => updateField('ductCols', parseInt(e.target.value) || 3)}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="ductSpacingH">Horizontal Spacing (m)</Label>
                    <Input
                      id="ductSpacingH"
                      type="number"
                      step="0.05"
                      value={formData.ductSpacingH}
                      onChange={(e) => updateField('ductSpacingH', parseFloat(e.target.value) || 0.2)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="ductSpacingV">Vertical Spacing (m)</Label>
                    <Input
                      id="ductSpacingV"
                      type="number"
                      step="0.05"
                      value={formData.ductSpacingV}
                      onChange={(e) => updateField('ductSpacingV', parseFloat(e.target.value) || 0.2)}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="ductIdMm">Duct ID (mm)</Label>
                    <Input
                      id="ductIdMm"
                      type="number"
                      value={formData.ductIdMm}
                      onChange={(e) => updateField('ductIdMm', parseFloat(e.target.value) || 150)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="ductOdMm">Duct OD (mm)</Label>
                    <Input
                      id="ductOdMm"
                      type="number"
                      value={formData.ductOdMm}
                      onChange={(e) => updateField('ductOdMm', parseFloat(e.target.value) || 160)}
                    />
                  </div>
                </div>
                <p className="text-xs text-muted-foreground">
                  Click on ducts in the visualization below to mark them as occupied.
                </p>
              </>
            )}

            {/* Visualization */}
            <Separator className="my-2" />
            <div className="p-3 bg-muted rounded-lg">
              <h4 className="text-sm font-medium mb-2">Cross-Section Preview</h4>
              <CableCrossSection
                conductorDiameter={getConductorDiameter(formData.conductorSize)}
                insulationThickness={getInsulationThicknessValue()}
                shieldThickness={2.0}
                jacketThickness={3.0}
                installationType={formData.installationType}
                depth={formData.burialDepth}
                spacing={formData.phaseSpacing}
                conduitId={formData.conduitIdMm}
                conduitOd={formData.conduitOdMm}
                conduitMaterial={formData.conduitMaterial}
                numConduits={formData.numConduits}
                ductRows={formData.ductRows}
                ductCols={formData.ductCols}
                ductSpacingH={formData.ductSpacingH * 1000}
                ductSpacingV={formData.ductSpacingV * 1000}
                ductId={formData.ductIdMm}
                ductOd={formData.ductOdMm}
                occupiedDucts={formData.occupiedDucts}
                soilResistivity={formData.soilResistivity}
                concreteResistivity={formData.concreteResistivity}
                ambientTemp={formData.ambientTemp}
                onDuctSelect={(duct) => {
                  if (duct && formData.installationType === 'duct_bank') {
                    const exists = formData.occupiedDucts.some(
                      d => d[0] === duct[0] && d[1] === duct[1]
                    );
                    if (exists) {
                      updateField(
                        'occupiedDucts',
                        formData.occupiedDucts.filter(d => !(d[0] === duct[0] && d[1] === duct[1]))
                      );
                    } else {
                      updateField('occupiedDucts', [...formData.occupiedDucts, duct]);
                    }
                  }
                }}
              />
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
                <div>Installation: <Badge variant="outline">
                  {formData.installationType === 'direct_buried' ? 'Direct Buried' :
                   formData.installationType === 'conduit' ? 'Conduit' : 'Duct Bank'}
                </Badge></div>
                <div>Depth: <Badge variant="outline">{formData.burialDepth} m</Badge></div>
                <div>Soil ρ: <Badge variant="outline">{formData.soilResistivity} K·m/W</Badge></div>
                {formData.installationType === 'duct_bank' && (
                  <div>Concrete ρ: <Badge variant="outline">{formData.concreteResistivity} K·m/W</Badge></div>
                )}
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
