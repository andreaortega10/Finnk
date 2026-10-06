import React, { useState } from 'react';
import { formatCurrency } from '../../utils/helpers';

export function CategoryDonutChart({ data = [], totalAmount = 0 }) {
  const [hoveredIdx, setHoveredIdx] = useState(null);

  if (!data || data.length === 0 || totalAmount === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-10 text-center">
        <div className="w-24 h-24 rounded-full border-4 border-dashed border-slate-200 flex items-center justify-center mb-3">
          <span className="text-xs text-slate-400 font-medium">Sem dados</span>
        </div>
        <p className="text-xs text-slate-500">Nenhum gasto registrado neste período.</p>
      </div>
    );
  }

  const pastelPalette = [
    '#D83A6F', // Pink primary
    '#F9A88F', // Salmon / Peach
    '#817DD8', // Indigo / Periwinkle
    '#A890E2', // Soft Purple
    '#9CA3AF', // Slate Gray
    '#34D399', // Emerald
    '#FBBF24', // Amber
    '#60A5FA', // Blue
  ];

  const size = 180;
  const strokeWidth = 26;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  let cumulativePercent = 0;

  return (
    <div className="flex flex-col items-center">
      <div className="relative flex items-center justify-center">
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="transform -rotate-90">
          {data.map((item, index) => {
            const percentage = item.percentage || 0;
            const strokeDasharray = `${(percentage / 100) * circumference} ${circumference}`;
            const strokeDashoffset = -((cumulativePercent / 100) * circumference);
            cumulativePercent += percentage;

            const color = item.color || pastelPalette[index % pastelPalette.length];
            const isHovered = hoveredIdx === index;

            return (
              <circle
                key={item.category_id || index}
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="transparent"
                stroke={color}
                strokeWidth={isHovered ? strokeWidth + 4 : strokeWidth}
                strokeDasharray={strokeDasharray}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                className="transition-all duration-300 cursor-pointer"
                onMouseEnter={() => setHoveredIdx(index)}
                onMouseLeave={() => setHoveredIdx(null)}
              />
            );
          })}
        </svg>

        {/* Center Text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none text-center px-4">
          <span className="text-base font-bold text-slate-800 leading-tight">
            {hoveredIdx !== null ? formatCurrency(data[hoveredIdx].amount) : formatCurrency(totalAmount)}
          </span>
          <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
            {hoveredIdx !== null ? data[hoveredIdx].name : 'Total'}
          </span>
        </div>
      </div>
    </div>
  );
}
