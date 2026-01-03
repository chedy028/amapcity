'use client';

import { useState, useMemo } from 'react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface CableCrossSectionProps {
  // Cable geometry
  conductorDiameter: number;
  insulationThickness: number;
  shieldThickness: number;
  jacketThickness: number;

  // Installation
  installationType: 'direct_buried' | 'conduit' | 'duct_bank';
  depth: number;
  spacing?: number;

  // Conduit (if applicable)
  conduitId?: number;
  conduitOd?: number;
  conduitMaterial?: string;
  numConduits?: number;

  // Duct bank (if applicable)
  bankWidth?: number;
  bankHeight?: number;
  ductRows?: number;
  ductCols?: number;
  ductSpacingH?: number;
  ductSpacingV?: number;
  ductId?: number;
  ductOd?: number;
  occupiedDucts?: [number, number][];

  // Soil/concrete properties
  soilResistivity?: number;
  concreteResistivity?: number;
  ambientTemp?: number;

  // Display options
  showDimensions?: boolean;
  showTemperatureGradient?: boolean;
  selectedDuct?: [number, number] | null;
  onDuctSelect?: (duct: [number, number] | null) => void;
}

// Color palette for temperature visualization
const TEMP_COLORS = {
  hot: '#ef4444',      // red-500
  warm: '#f97316',     // orange-500
  mild: '#eab308',     // yellow-500
  cool: '#22c55e',     // green-500
  cold: '#3b82f6',     // blue-500
};

// Layer colors
const LAYER_COLORS = {
  conductor: '#d97706',    // amber-600 (copper)
  conductorAl: '#9ca3af',  // gray-400 (aluminum)
  insulation: '#fef08a',   // yellow-200
  shield: '#92400e',       // amber-800
  jacket: '#1f2937',       // gray-800
  conduit: '#6b7280',      // gray-500
  concrete: '#9ca3af',     // gray-400
  soil: '#78350f',         // amber-900
  air: '#e0f2fe',          // sky-100
};

export function CableCrossSection({
  conductorDiameter,
  insulationThickness,
  shieldThickness,
  jacketThickness,
  installationType,
  depth,
  spacing = 0,
  conduitId,
  conduitOd,
  conduitMaterial = 'pvc',
  numConduits = 1,
  bankWidth,
  bankHeight,
  ductRows = 2,
  ductCols = 3,
  ductSpacingH = 200,
  ductSpacingV = 200,
  ductId,
  ductOd,
  occupiedDucts = [],
  soilResistivity = 1.0,
  concreteResistivity = 1.0,
  ambientTemp = 25,
  showDimensions = true,
  showTemperatureGradient = false,
  selectedDuct = null,
  onDuctSelect,
}: CableCrossSectionProps) {
  const [hoveredLayer, setHoveredLayer] = useState<string | null>(null);
  const [hoveredDuct, setHoveredDuct] = useState<[number, number] | null>(null);

  // Calculate cable dimensions
  const cableDimensions = useMemo(() => {
    const insulationOuter = conductorDiameter + 2 * insulationThickness;
    const shieldOuter = insulationOuter + 2 * shieldThickness;
    const jacketOuter = shieldOuter + 2 * jacketThickness;
    return {
      conductorRadius: conductorDiameter / 2,
      insulationRadius: insulationOuter / 2,
      shieldRadius: shieldOuter / 2,
      jacketRadius: jacketOuter / 2,
      overallDiameter: jacketOuter,
    };
  }, [conductorDiameter, insulationThickness, shieldThickness, jacketThickness]);

  // Render cable cross-section
  const renderCable = (cx: number, cy: number, scale: number = 1, label?: string) => {
    const { conductorRadius, insulationRadius, shieldRadius, jacketRadius } = cableDimensions;

    return (
      <g transform={`translate(${cx}, ${cy})`}>
        {/* Jacket (outermost) */}
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <circle
                r={jacketRadius * scale}
                fill={LAYER_COLORS.jacket}
                stroke={hoveredLayer === 'jacket' ? '#fff' : 'none'}
                strokeWidth={hoveredLayer === 'jacket' ? 2 : 0}
                onMouseEnter={() => setHoveredLayer('jacket')}
                onMouseLeave={() => setHoveredLayer(null)}
                className="cursor-pointer transition-all"
              />
            </TooltipTrigger>
            <TooltipContent>
              <p className="font-semibold">Jacket</p>
              <p>Thickness: {jacketThickness.toFixed(1)} mm</p>
              <p>Outer: {(jacketRadius * 2).toFixed(1)} mm</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        {/* Shield */}
        {shieldThickness > 0 && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <circle
                  r={shieldRadius * scale}
                  fill={LAYER_COLORS.shield}
                  stroke={hoveredLayer === 'shield' ? '#fff' : 'none'}
                  strokeWidth={hoveredLayer === 'shield' ? 2 : 0}
                  onMouseEnter={() => setHoveredLayer('shield')}
                  onMouseLeave={() => setHoveredLayer(null)}
                  className="cursor-pointer transition-all"
                />
              </TooltipTrigger>
              <TooltipContent>
                <p className="font-semibold">Shield</p>
                <p>Thickness: {shieldThickness.toFixed(1)} mm</p>
                <p>Outer: {(shieldRadius * 2).toFixed(1)} mm</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}

        {/* Insulation */}
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <circle
                r={insulationRadius * scale}
                fill={LAYER_COLORS.insulation}
                stroke={hoveredLayer === 'insulation' ? '#000' : 'none'}
                strokeWidth={hoveredLayer === 'insulation' ? 2 : 0}
                onMouseEnter={() => setHoveredLayer('insulation')}
                onMouseLeave={() => setHoveredLayer(null)}
                className="cursor-pointer transition-all"
              />
            </TooltipTrigger>
            <TooltipContent>
              <p className="font-semibold">Insulation (XLPE)</p>
              <p>Thickness: {insulationThickness.toFixed(1)} mm</p>
              <p>Outer: {(insulationRadius * 2).toFixed(1)} mm</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        {/* Conductor */}
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <circle
                r={conductorRadius * scale}
                fill={LAYER_COLORS.conductor}
                stroke={hoveredLayer === 'conductor' ? '#fff' : 'none'}
                strokeWidth={hoveredLayer === 'conductor' ? 2 : 0}
                onMouseEnter={() => setHoveredLayer('conductor')}
                onMouseLeave={() => setHoveredLayer(null)}
                className="cursor-pointer transition-all"
              />
            </TooltipTrigger>
            <TooltipContent>
              <p className="font-semibold">Conductor (Copper)</p>
              <p>Diameter: {conductorDiameter.toFixed(1)} mm</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        {/* Label */}
        {label && (
          <text
            y={jacketRadius * scale + 15}
            textAnchor="middle"
            className="text-xs fill-gray-600"
          >
            {label}
          </text>
        )}
      </g>
    );
  };

  // Render conduit
  const renderConduit = (cx: number, cy: number, scale: number = 1, hasLabel: boolean = true) => {
    const cId = conduitId || cableDimensions.overallDiameter + 20;
    const cOd = conduitOd || cId + 10;

    return (
      <g transform={`translate(${cx}, ${cy})`}>
        {/* Conduit outer */}
        <circle
          r={(cOd / 2) * scale}
          fill={LAYER_COLORS.conduit}
          className="opacity-80"
        />
        {/* Air gap inside conduit */}
        <circle
          r={(cId / 2) * scale}
          fill={LAYER_COLORS.air}
        />
        {/* Cable inside */}
        {renderCable(0, 0, scale)}

        {/* Conduit label */}
        {hasLabel && showDimensions && (
          <text
            y={(cOd / 2) * scale + 20}
            textAnchor="middle"
            className="text-xs fill-gray-600"
          >
            Conduit {cOd.toFixed(0)}mm OD
          </text>
        )}
      </g>
    );
  };

  // Render duct in duct bank
  const renderDuct = (
    row: number,
    col: number,
    cx: number,
    cy: number,
    scale: number,
    isOccupied: boolean,
    isSelected: boolean
  ) => {
    const dId = ductId || cableDimensions.overallDiameter + 20;
    const dOd = ductOd || dId + 10;
    const isHovered = hoveredDuct && hoveredDuct[0] === row && hoveredDuct[1] === col;

    return (
      <g
        key={`duct-${row}-${col}`}
        transform={`translate(${cx}, ${cy})`}
        onMouseEnter={() => setHoveredDuct([row, col])}
        onMouseLeave={() => setHoveredDuct(null)}
        onClick={() => onDuctSelect?.([row, col])}
        className="cursor-pointer"
      >
        {/* Duct outer */}
        <circle
          r={(dOd / 2) * scale}
          fill={LAYER_COLORS.conduit}
          stroke={isSelected ? '#3b82f6' : isHovered ? '#60a5fa' : 'none'}
          strokeWidth={isSelected || isHovered ? 3 : 0}
          className="transition-all"
        />
        {/* Air gap / cable inside */}
        <circle
          r={(dId / 2) * scale}
          fill={isOccupied ? LAYER_COLORS.air : '#f3f4f6'}
        />

        {/* Cable if occupied */}
        {isOccupied && renderCable(0, 0, scale * 0.9)}

        {/* Empty duct indicator */}
        {!isOccupied && (
          <text
            textAnchor="middle"
            dominantBaseline="middle"
            className="text-xs fill-gray-400"
          >
            Empty
          </text>
        )}
      </g>
    );
  };

  // Calculate SVG viewBox based on installation type
  const getViewBox = () => {
    switch (installationType) {
      case 'duct_bank': {
        const bw = bankWidth || (ductCols * ductSpacingH);
        const bh = bankHeight || (ductRows * ductSpacingV);
        const padding = 80;
        return {
          width: bw + padding * 2,
          height: bh + depth * 1000 / 10 + padding * 2, // Scale depth
          centerX: (bw + padding * 2) / 2,
          surfaceY: padding,
        };
      }
      case 'conduit': {
        const cOd = conduitOd || (cableDimensions.overallDiameter + 30);
        const totalWidth = numConduits > 1 ? (numConduits - 1) * (spacing * 1000) + cOd + 100 : cOd + 100;
        return {
          width: Math.max(totalWidth, 300),
          height: 400,
          centerX: Math.max(totalWidth, 300) / 2,
          surfaceY: 50,
        };
      }
      default: {
        // Direct buried
        const cableD = cableDimensions.overallDiameter;
        const totalWidth = spacing > 0 ? spacing * 1000 * 2 + cableD + 100 : cableD + 150;
        return {
          width: Math.max(totalWidth, 300),
          height: 400,
          centerX: Math.max(totalWidth, 300) / 2,
          surfaceY: 50,
        };
      }
    }
  };

  const viewBox = getViewBox();

  // Render based on installation type
  const renderInstallation = () => {
    switch (installationType) {
      case 'duct_bank':
        return renderDuctBank();
      case 'conduit':
        return renderConduitInstallation();
      default:
        return renderDirectBuried();
    }
  };

  // Direct buried installation
  const renderDirectBuried = () => {
    const depthPx = Math.min(depth * 150, 250); // Scale depth
    const cableY = viewBox.surfaceY + depthPx;

    return (
      <>
        {/* Soil background */}
        <rect
          x={0}
          y={viewBox.surfaceY}
          width={viewBox.width}
          height={viewBox.height - viewBox.surfaceY}
          fill={LAYER_COLORS.soil}
          className="opacity-30"
        />

        {/* Ground surface */}
        <line
          x1={0}
          y1={viewBox.surfaceY}
          x2={viewBox.width}
          y2={viewBox.surfaceY}
          stroke="#78350f"
          strokeWidth={3}
        />
        <text
          x={10}
          y={viewBox.surfaceY - 10}
          className="text-xs fill-gray-600"
        >
          Ground Surface
        </text>

        {/* Depth indicator */}
        {showDimensions && (
          <>
            <line
              x1={30}
              y1={viewBox.surfaceY + 5}
              x2={30}
              y2={cableY}
              stroke="#666"
              strokeWidth={1}
              markerEnd="url(#arrowhead)"
            />
            <text
              x={35}
              y={(viewBox.surfaceY + cableY) / 2}
              className="text-xs fill-gray-600"
            >
              {depth.toFixed(2)}m
            </text>
          </>
        )}

        {/* Cable(s) */}
        {spacing > 0 ? (
          // Multiple cables with spacing
          <>
            {renderCable(viewBox.centerX - spacing * 500, cableY, 1, 'A')}
            {renderCable(viewBox.centerX, cableY, 1, 'B')}
            {renderCable(viewBox.centerX + spacing * 500, cableY, 1, 'C')}
          </>
        ) : (
          // Single cable
          renderCable(viewBox.centerX, cableY, 1)
        )}

        {/* Soil properties */}
        <text
          x={viewBox.width - 10}
          y={viewBox.height - 20}
          textAnchor="end"
          className="text-xs fill-gray-600"
        >
          Soil: {soilResistivity.toFixed(1)} K·m/W
        </text>
      </>
    );
  };

  // Conduit installation
  const renderConduitInstallation = () => {
    const depthPx = Math.min(depth * 150, 250);
    const conduitY = viewBox.surfaceY + depthPx;

    return (
      <>
        {/* Soil background */}
        <rect
          x={0}
          y={viewBox.surfaceY}
          width={viewBox.width}
          height={viewBox.height - viewBox.surfaceY}
          fill={LAYER_COLORS.soil}
          className="opacity-30"
        />

        {/* Ground surface */}
        <line
          x1={0}
          y1={viewBox.surfaceY}
          x2={viewBox.width}
          y2={viewBox.surfaceY}
          stroke="#78350f"
          strokeWidth={3}
        />
        <text
          x={10}
          y={viewBox.surfaceY - 10}
          className="text-xs fill-gray-600"
        >
          Ground Surface
        </text>

        {/* Depth indicator */}
        {showDimensions && (
          <>
            <line
              x1={30}
              y1={viewBox.surfaceY + 5}
              x2={30}
              y2={conduitY}
              stroke="#666"
              strokeWidth={1}
            />
            <text
              x={35}
              y={(viewBox.surfaceY + conduitY) / 2}
              className="text-xs fill-gray-600"
            >
              {depth.toFixed(2)}m
            </text>
          </>
        )}

        {/* Conduit(s) */}
        {numConduits > 1 ? (
          // Multiple conduits with spacing
          Array.from({ length: numConduits }).map((_, i) => {
            const offset = (i - (numConduits - 1) / 2) * spacing * 500;
            return (
              <g key={`conduit-${i}`}>
                {renderConduit(viewBox.centerX + offset, conduitY, 1, i === Math.floor(numConduits / 2))}
              </g>
            );
          })
        ) : (
          // Single conduit
          renderConduit(viewBox.centerX, conduitY, 1)
        )}

        {/* Soil properties */}
        <text
          x={viewBox.width - 10}
          y={viewBox.height - 20}
          textAnchor="end"
          className="text-xs fill-gray-600"
        >
          Soil: {soilResistivity.toFixed(1)} K·m/W | {conduitMaterial.toUpperCase()} Conduit
        </text>
      </>
    );
  };

  // Duct bank installation
  const renderDuctBank = () => {
    const bw = bankWidth || (ductCols * ductSpacingH);
    const bh = bankHeight || (ductRows * ductSpacingV);
    const depthPx = Math.min(depth * 100, 150);
    const scale = 0.6;

    const bankX = viewBox.centerX - bw / 2;
    const bankY = viewBox.surfaceY + depthPx;

    // Generate duct positions
    const ducts = [];
    for (let row = 0; row < ductRows; row++) {
      for (let col = 0; col < ductCols; col++) {
        const cx = bankX + (col + 0.5) * (bw / ductCols);
        const cy = bankY + (row + 0.5) * (bh / ductRows);
        const isOccupied = occupiedDucts.some(d => d[0] === row && d[1] === col);
        const isSelected = selectedDuct && selectedDuct[0] === row && selectedDuct[1] === col;
        ducts.push({ row, col, cx, cy, isOccupied, isSelected: isSelected || false });
      }
    }

    return (
      <>
        {/* Soil background */}
        <rect
          x={0}
          y={viewBox.surfaceY}
          width={viewBox.width}
          height={viewBox.height - viewBox.surfaceY}
          fill={LAYER_COLORS.soil}
          className="opacity-30"
        />

        {/* Concrete duct bank */}
        <rect
          x={bankX - 20}
          y={bankY - 20}
          width={bw + 40}
          height={bh + 40}
          fill={LAYER_COLORS.concrete}
          rx={5}
          className="opacity-60"
        />

        {/* Ground surface */}
        <line
          x1={0}
          y1={viewBox.surfaceY}
          x2={viewBox.width}
          y2={viewBox.surfaceY}
          stroke="#78350f"
          strokeWidth={3}
        />
        <text
          x={10}
          y={viewBox.surfaceY - 10}
          className="text-xs fill-gray-600"
        >
          Ground Surface
        </text>

        {/* Depth indicator */}
        {showDimensions && (
          <>
            <line
              x1={20}
              y1={viewBox.surfaceY + 5}
              x2={20}
              y2={bankY - 20}
              stroke="#666"
              strokeWidth={1}
            />
            <text
              x={25}
              y={(viewBox.surfaceY + bankY - 20) / 2}
              className="text-xs fill-gray-600"
            >
              {depth.toFixed(2)}m
            </text>
          </>
        )}

        {/* Bank dimensions */}
        {showDimensions && (
          <>
            <text
              x={bankX + bw / 2}
              y={bankY + bh + 45}
              textAnchor="middle"
              className="text-xs fill-gray-600"
            >
              {(bw / 1000).toFixed(2)}m × {(bh / 1000).toFixed(2)}m
            </text>
          </>
        )}

        {/* Ducts */}
        {ducts.map(duct => renderDuct(
          duct.row,
          duct.col,
          duct.cx,
          duct.cy,
          scale,
          duct.isOccupied,
          duct.isSelected
        ))}

        {/* Properties */}
        <text
          x={viewBox.width - 10}
          y={viewBox.height - 35}
          textAnchor="end"
          className="text-xs fill-gray-600"
        >
          Soil: {soilResistivity.toFixed(1)} K·m/W
        </text>
        <text
          x={viewBox.width - 10}
          y={viewBox.height - 20}
          textAnchor="end"
          className="text-xs fill-gray-600"
        >
          Concrete: {concreteResistivity.toFixed(1)} K·m/W
        </text>
      </>
    );
  };

  return (
    <div className="w-full">
      <svg
        viewBox={`0 0 ${viewBox.width} ${viewBox.height}`}
        className="w-full h-auto border rounded-lg bg-sky-50"
        style={{ maxHeight: '400px' }}
      >
        {/* Defs for markers */}
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="#666" />
          </marker>
        </defs>

        {/* Sky background */}
        <rect
          x={0}
          y={0}
          width={viewBox.width}
          height={viewBox.surfaceY}
          fill="#bae6fd"
          className="opacity-50"
        />

        {renderInstallation()}
      </svg>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 mt-3 text-xs text-gray-600">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: LAYER_COLORS.conductor }} />
          <span>Conductor</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: LAYER_COLORS.insulation }} />
          <span>Insulation</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: LAYER_COLORS.shield }} />
          <span>Shield</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: LAYER_COLORS.jacket }} />
          <span>Jacket</span>
        </div>
        {(installationType === 'conduit' || installationType === 'duct_bank') && (
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: LAYER_COLORS.conduit }} />
            <span>Conduit/Duct</span>
          </div>
        )}
        {installationType === 'duct_bank' && (
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: LAYER_COLORS.concrete }} />
            <span>Concrete</span>
          </div>
        )}
      </div>
    </div>
  );
}
