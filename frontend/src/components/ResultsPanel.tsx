'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import type { CalculationResponse } from '@/lib/api';

interface ResultsPanelProps {
  results: CalculationResponse | null;
  onGenerateReport: () => void;
  isGeneratingReport?: boolean;
}

export function ResultsPanel({ results, onGenerateReport, isGeneratingReport }: ResultsPanelProps) {
  if (!results) {
    return (
      <Card className="w-full h-full flex items-center justify-center">
        <CardContent className="text-center py-12">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="mx-auto mb-4 text-muted-foreground"
          >
            <circle cx="12" cy="12" r="10" />
            <path d="M12 6v6l4 2" />
          </svg>
          <h3 className="text-lg font-medium mb-2">No Results Yet</h3>
          <p className="text-muted-foreground text-sm">
            Configure your cable parameters and click Calculate to see results.
          </p>
        </CardContent>
      </Card>
    );
  }

  const statusColor = results.design_status === 'PASS' ? 'bg-green-500' : 'bg-red-500';
  const statusBg = results.design_status === 'PASS' ? 'bg-green-50' : 'bg-red-50';
  const tempMargin = results.max_conductor_temp_c - (results.ambient_temp_c + results.temperature_rise.total);

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Calculation Results</CardTitle>
            <CardDescription>Ampacity analysis based on IEC 60287</CardDescription>
          </div>
          <Badge className={`${statusColor} text-white text-lg px-4 py-1`}>
            {results.design_status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {/* Summary Cards */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className={`p-4 rounded-lg ${statusBg}`}>
            <div className="text-3xl font-bold text-center">
              {results.ampacity_a.toFixed(0)} A
            </div>
            <div className="text-sm text-center text-muted-foreground">
              Rated Ampacity
            </div>
          </div>
          <div className="p-4 rounded-lg bg-blue-50">
            <div className="text-3xl font-bold text-center">
              {(results.ambient_temp_c + results.temperature_rise.total).toFixed(1)}°C
            </div>
            <div className="text-sm text-center text-muted-foreground">
              Operating Temp
            </div>
          </div>
          <div className={`p-4 rounded-lg ${tempMargin > 0 ? 'bg-green-50' : 'bg-red-50'}`}>
            <div className="text-3xl font-bold text-center">
              {tempMargin.toFixed(1)}°C
            </div>
            <div className="text-sm text-center text-muted-foreground">
              Temp Margin
            </div>
          </div>
        </div>

        <Tabs defaultValue="summary">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="summary">Summary</TabsTrigger>
            <TabsTrigger value="losses">Losses</TabsTrigger>
            <TabsTrigger value="thermal">Thermal</TabsTrigger>
            <TabsTrigger value="electrical">Electrical</TabsTrigger>
          </TabsList>

          <TabsContent value="summary" className="space-y-4 mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <h4 className="font-medium">Ampacity</h4>
                <table className="w-full text-sm">
                  <tbody>
                    <tr>
                      <td className="text-muted-foreground">Steady-State</td>
                      <td className="text-right font-mono">{results.ampacity_a.toFixed(1)} A</td>
                    </tr>
                    <tr>
                      <td className="text-muted-foreground">Cyclic Rating</td>
                      <td className="text-right font-mono">{results.ampacity_cyclic_a.toFixed(1)} A</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium">Temperature</h4>
                <table className="w-full text-sm">
                  <tbody>
                    <tr>
                      <td className="text-muted-foreground">Max Allowed</td>
                      <td className="text-right font-mono">{results.max_conductor_temp_c}°C</td>
                    </tr>
                    <tr>
                      <td className="text-muted-foreground">Ambient</td>
                      <td className="text-right font-mono">{results.ambient_temp_c}°C</td>
                    </tr>
                    <tr>
                      <td className="text-muted-foreground">Rise</td>
                      <td className="text-right font-mono">{results.temperature_rise.total.toFixed(1)}°C</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="losses" className="mt-4">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Loss Component</th>
                  <th className="text-right py-2">Value (W/m)</th>
                  <th className="text-right py-2">Percentage</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b">
                  <td className="py-2">Conductor (I²R)</td>
                  <td className="text-right font-mono">{results.losses.conductor.toFixed(2)}</td>
                  <td className="text-right font-mono">
                    {((results.losses.conductor / results.losses.total) * 100).toFixed(1)}%
                  </td>
                </tr>
                <tr className="border-b">
                  <td className="py-2">Dielectric</td>
                  <td className="text-right font-mono">{results.losses.dielectric.toFixed(4)}</td>
                  <td className="text-right font-mono">
                    {((results.losses.dielectric / results.losses.total) * 100).toFixed(1)}%
                  </td>
                </tr>
                <tr className="border-b">
                  <td className="py-2">Shield</td>
                  <td className="text-right font-mono">{results.losses.shield.toFixed(2)}</td>
                  <td className="text-right font-mono">
                    {((results.losses.shield / results.losses.total) * 100).toFixed(1)}%
                  </td>
                </tr>
                <tr className="font-medium">
                  <td className="py-2">Total</td>
                  <td className="text-right font-mono">{results.losses.total.toFixed(2)}</td>
                  <td className="text-right font-mono">100%</td>
                </tr>
              </tbody>
            </table>
            <p className="text-xs text-muted-foreground mt-2">
              Shield loss factor (λ1): {results.shield_loss_factor.toFixed(4)}
            </p>
          </TabsContent>

          <TabsContent value="thermal" className="mt-4">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Thermal Resistance</th>
                  <th className="text-right py-2">Value (K·m/W)</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b">
                  <td className="py-2">R1 (Insulation)</td>
                  <td className="text-right font-mono">{results.thermal_resistance.r1_insulation.toFixed(4)}</td>
                </tr>
                <tr className="border-b">
                  <td className="py-2">R2 (Jacket)</td>
                  <td className="text-right font-mono">{results.thermal_resistance.r2_jacket.toFixed(4)}</td>
                </tr>
                <tr className="border-b">
                  <td className="py-2">R4 (Earth)</td>
                  <td className="text-right font-mono">{results.thermal_resistance.r4_earth.toFixed(4)}</td>
                </tr>
                <tr className="border-b">
                  <td className="py-2">Mutual Heating Factor</td>
                  <td className="text-right font-mono">{results.thermal_resistance.mutual_heating_factor.toFixed(3)}</td>
                </tr>
                <tr className="border-b">
                  <td className="py-2">R4 (Effective)</td>
                  <td className="text-right font-mono">{results.thermal_resistance.r4_effective.toFixed(4)}</td>
                </tr>
                <tr className="font-medium">
                  <td className="py-2">Total</td>
                  <td className="text-right font-mono">{results.thermal_resistance.total.toFixed(4)}</td>
                </tr>
              </tbody>
            </table>

            <Separator className="my-4" />

            <h4 className="font-medium mb-2">Temperature Rise Breakdown</h4>
            <table className="w-full text-sm">
              <tbody>
                <tr className="border-b">
                  <td className="py-2">From Conductor Losses</td>
                  <td className="text-right font-mono">{results.temperature_rise.conductor_losses.toFixed(1)}°C</td>
                </tr>
                <tr className="border-b">
                  <td className="py-2">From Dielectric Losses</td>
                  <td className="text-right font-mono">{results.temperature_rise.dielectric_losses.toFixed(2)}°C</td>
                </tr>
                <tr className="font-medium">
                  <td className="py-2">Total Rise</td>
                  <td className="text-right font-mono">{results.temperature_rise.total.toFixed(1)}°C</td>
                </tr>
              </tbody>
            </table>
          </TabsContent>

          <TabsContent value="electrical" className="mt-4">
            <h4 className="font-medium mb-2">AC Resistance</h4>
            <table className="w-full text-sm">
              <tbody>
                <tr className="border-b">
                  <td className="py-2">DC Resistance</td>
                  <td className="text-right font-mono">{(results.ac_resistance.rdc * 1000).toFixed(4)} mΩ/m</td>
                </tr>
                <tr className="border-b">
                  <td className="py-2">Skin Effect (Ycs)</td>
                  <td className="text-right font-mono">{results.ac_resistance.ycs.toFixed(4)}</td>
                </tr>
                <tr className="border-b">
                  <td className="py-2">Proximity Effect (Ycp)</td>
                  <td className="text-right font-mono">{results.ac_resistance.ycp.toFixed(4)}</td>
                </tr>
                <tr className="font-medium">
                  <td className="py-2">AC Resistance</td>
                  <td className="text-right font-mono">{(results.ac_resistance.rac * 1000).toFixed(4)} mΩ/m</td>
                </tr>
              </tbody>
            </table>
            <p className="text-xs text-muted-foreground mt-2">
              AC/DC ratio: {(results.ac_resistance.rac / results.ac_resistance.rdc).toFixed(4)}
            </p>
          </TabsContent>
        </Tabs>

        <Separator className="my-4" />

        <div className="flex gap-2">
          <Button
            className="flex-1"
            onClick={onGenerateReport}
            disabled={isGeneratingReport}
          >
            {isGeneratingReport ? 'Generating...' : 'Generate Engineering Report'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
