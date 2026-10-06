import React, { useState } from 'react';
import { formatCurrency } from '../../utils/helpers';

export function MonthlyEvolutionChart({ data = [] }) {
  const [hoveredIdx, setHoveredIdx] = useState(null);

  if (!data || data.length === 0) {
    return (
      <div className="py-12 text-center text-slate-400 text-xs">
        Sem dados de evolução financeira disponíveis.
      </div>
    );
  }

  // Encontra o valor máximo para a escala
  const maxVal = Math.max(
    ...data.flatMap(d => [d.receitas || 0, d.despesas || 0]),
    100
  );

  return (
    <div className="w-full">
      <div className="flex items-center justify-end space-x-4 mb-4 text-xs">
        <div className="flex items-center space-x-1.5">
          <div className="w-3 h-3 rounded-full bg-emerald-400" />
          <span className="text-slate-600 font-medium">Receitas</span>
        </div>
        <div className="flex items-center space-x-1.5">
          <div className="w-3 h-3 rounded-full bg-[#D83A6F]" />
          <span className="text-slate-600 font-medium">Despesas</span>
        </div>
      </div>

      <div className="grid grid-cols-6 gap-2 sm:gap-4 items-end h-48 pt-6 pb-2 border-b border-slate-100">
        {data.map((item, idx) => {
          const recHeight = maxVal > 0 ? (item.receitas / maxVal) * 100 : 0;
          const expHeight = maxVal > 0 ? (item.despesas / maxVal) * 100 : 0;
          const isHovered = hoveredIdx === idx;

          return (
            <div
              key={idx}
              className="flex flex-col items-center justify-end h-full relative group cursor-pointer"
              onMouseEnter={() => setHoveredIdx(idx)}
              onMouseLeave={() => setHoveredIdx(null)}
            >
              {/* Tooltip */}
              {isHovered && (
                <div className="absolute -top-14 z-20 bg-slate-900 text-white text-[11px] rounded-lg px-2.5 py-1.5 shadow-xl whitespace-nowrap pointer-events-none">
                  <div className="font-semibold text-slate-200">{item.label}</div>
                  <div className="text-emerald-400 font-medium">Rec: {formatCurrency(item.receitas)}</div>
                  <div className="text-rose-400 font-medium">Desp: {formatCurrency(item.despesas)}</div>
                </div>
              )}

              {/* Bars Pair */}
              <div className="flex items-end space-x-1 sm:space-x-1.5 w-full justify-center h-full">
                {/* Receitas */}
                <div
                  style={{ height: `${Math.max(recHeight, 4)}%` }}
                  className={`w-3 sm:w-5 bg-gradient-to-t from-emerald-500 to-emerald-300 rounded-t-md transition-all duration-300 ${
                    isHovered ? 'brightness-110 shadow-md' : 'opacity-90'
                  }`}
                />
                {/* Despesas */}
                <div
                  style={{ height: `${Math.max(expHeight, 4)}%` }}
                  className={`w-3 sm:w-5 bg-gradient-to-t from-[#D83A6F] to-[#FB7185] rounded-t-md transition-all duration-300 ${
                    isHovered ? 'brightness-110 shadow-md' : 'opacity-90'
                  }`}
                />
              </div>

              {/* Month Label */}
              <span className="text-[11px] font-semibold text-slate-500 mt-2">
                {item.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
