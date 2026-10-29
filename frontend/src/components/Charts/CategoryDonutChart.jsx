import React, { useState } from 'react';
import { formatCurrency } from '../../utils/helpers';

export const PASTEL_PALETTE = [
  '#D83A6F', // Pink primary
  '#F97316', // Orange
  '#3B82F6', // Blue
  '#8B5CF6', // Purple
  '#10B981', // Emerald
  '#EC4899', // Pink secondary
  '#F59E0B', // Amber
  '#06B6D4', // Cyan
  '#6366F1', // Indigo
  '#64748B', // Slate
];

export function getDistinctCategoryColor(item, index, allItems = []) {
  // Se o item tem cor explícita e ela não está duplicada anteriormente
  if (item.color && item.color !== '#D83A6F') {
    return item.color;
  }
  // Se for a cor padrão ou duplicada, pega da paleta distinta
  return PASTEL_PALETTE[index % PASTEL_PALETTE.length];
}

export function CategoryDonutChart({ data = [], totalAmount = 0 }) {
  const [hoveredIdx, setHoveredIdx] = useState(null);
  const [selectedIdx, setSelectedIdx] = useState(null);

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

  const activeIdx = hoveredIdx !== null ? hoveredIdx : selectedIdx;

  const size = 180;
  const strokeWidth = 24;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  // Garante que a soma total seja calculada para precisão angular
  const total = data.reduce((acc, curr) => acc + (curr.amount || 0), 0) || totalAmount || 1;

  let cumulativeOffset = 0;

  return (
    <div className="flex flex-col items-center select-none">
      <div className="relative flex items-center justify-center">
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="transform -rotate-90">
          {data.map((item, index) => {
            const fraction = (item.amount || 0) / total;
            const percentage = item.percentage || Math.round(fraction * 100);
            const strokeDasharray = `${fraction * circumference} ${circumference}`;
            const strokeDashoffset = -cumulativeOffset;
            cumulativeOffset += fraction * circumference;

            const color = getDistinctCategoryColor(item, index, data);
            const isActive = activeIdx === index;

            return (
              <circle
                key={item.category_id || index}
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="transparent"
                stroke={color}
                strokeWidth={isActive ? strokeWidth + 4 : strokeWidth}
                strokeDasharray={strokeDasharray}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="butt"
                className="transition-all duration-200 cursor-pointer origin-center"
                style={{
                  opacity: activeIdx !== null && !isActive ? 0.45 : 1.0,
                  transform: isActive ? 'scale(1.02)' : 'scale(1)',
                }}
                onMouseEnter={() => setHoveredIdx(index)}
                onMouseLeave={() => setHoveredIdx(null)}
                onClick={() => setSelectedIdx(selectedIdx === index ? null : index)}
                onTouchStart={() => setSelectedIdx(selectedIdx === index ? null : index)}
              />
            );
          })}
        </svg>

        {/* Center Text with Selection / Hover State */}
        <div 
          className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none text-center px-4"
          aria-live="polite"
        >
          <span className="text-base font-extrabold text-slate-800 leading-tight">
            {activeIdx !== null ? formatCurrency(data[activeIdx].amount) : formatCurrency(totalAmount)}
          </span>
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mt-0.5 max-w-[120px] truncate">
            {activeIdx !== null 
              ? `${data[activeIdx].name} (${data[activeIdx].percentage || Math.round(((data[activeIdx].amount || 0) / total) * 100)}%)`
              : 'Total de Gastos'}
          </span>
        </div>
      </div>
      {activeIdx !== null && (
        <span className="text-[10px] text-slate-400 mt-2">
          Toque para desmarcar
        </span>
      )}
    </div>
  );
}
