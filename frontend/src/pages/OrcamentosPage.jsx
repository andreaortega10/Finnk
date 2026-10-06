import React, { useState, useEffect } from 'react';
import { PieChart, Plus, Trash2, ChevronLeft, ChevronRight, AlertTriangle, ShieldCheck } from 'lucide-react';
import { api } from '../services/api';
import { formatCurrency, getCategoryIcon } from '../utils/helpers';
import { BudgetModal } from '../components/Modals/BudgetModal';

export function OrcamentosPage() {
  const [budgets, setBudgets] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [bList, cList] = await Promise.all([
        api.budgets.list(selectedMonth, selectedYear),
        api.categories.list('DESPESA'),
      ]);
      setBudgets(bList);
      setCategories(cList);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedMonth, selectedYear]);

  const handlePrevMonth = () => {
    if (selectedMonth === 1) {
      setSelectedMonth(12);
      setSelectedYear(selectedYear - 1);
    } else {
      setSelectedMonth(selectedMonth - 1);
    }
  };

  const handleNextMonth = () => {
    if (selectedMonth === 12) {
      setSelectedMonth(1);
      setSelectedYear(selectedYear + 1);
    } else {
      setSelectedMonth(selectedMonth + 1);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Deseja excluir este orçamento?')) return;
    try {
      await api.budgets.delete(id);
      loadData();
    } catch (err) {
      alert(err.message || 'Erro ao excluir orçamento.');
    }
  };

  return (
    <div className="space-y-6 pb-20 md:pb-8 px-4 sm:px-6 max-w-5xl mx-auto animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">Orçamentos & Metas de Gastos</h2>
          <p className="text-xs text-slate-500">Defina limites mensais por categoria e acompanhe seus gastos em tempo real.</p>
        </div>

        <div className="flex items-center space-x-2">
          {/* Month Picker */}
          <div className="flex items-center bg-white border border-slate-200 rounded-full px-3 py-1.5 shadow-2xs">
            <button onClick={handlePrevMonth} className="p-1 rounded-full text-slate-500 hover:text-[#D83A6F]">
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-xs font-bold text-slate-800 px-2 select-none">
              Mês {selectedMonth}/{selectedYear}
            </span>
            <button onClick={handleNextMonth} className="p-1 rounded-full text-slate-500 hover:text-[#D83A6F]">
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-2xl bg-[#D83A6F] hover:bg-[#C22A5E] text-white font-bold text-xs shadow-md shadow-pink-200 transition-all active:scale-95"
          >
            <Plus className="w-4 h-4 stroke-[2.5]" />
            <span>Definir Orçamento</span>
          </button>
        </div>
      </div>

      {/* Budget Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {budgets.map((b) => {
          const isExceeded = b.is_exceeded;
          const isWarning = b.is_warning;

          return (
            <div
              key={b.id}
              className={`pastel-card rounded-3xl p-5 space-y-4 border-2 transition-all ${
                isExceeded
                  ? 'border-rose-300 bg-rose-50/20'
                  : isWarning
                  ? 'border-amber-300 bg-amber-50/20'
                  : 'border-transparent'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <div
                    className="w-11 h-11 rounded-2xl flex items-center justify-center text-white"
                    style={{ backgroundColor: b.category_color || '#D83A6F' }}
                  >
                    {getCategoryIcon(b.category_icon || b.category_name, "w-5 h-5")}
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-slate-900">{b.category_name}</h3>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full inline-block mt-0.5 ${
                      isExceeded
                        ? 'bg-rose-100 text-rose-700'
                        : isWarning
                        ? 'bg-amber-100 text-amber-700'
                        : 'bg-emerald-100 text-emerald-700'
                    }`}>
                      {isExceeded ? 'Limite Ultrapassado' : isWarning ? 'Atenção (>= 80%)' : 'Dentro da Meta'}
                    </span>
                  </div>
                </div>

                <button
                  onClick={() => handleDelete(b.id)}
                  className="p-1.5 text-slate-300 hover:text-rose-600 transition-colors rounded-lg hover:bg-rose-50"
                  title="Excluir Orçamento"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              {/* Progress Bar */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-slate-500">Utilizado: {formatCurrency(b.spent_amount)}</span>
                  <span className="text-slate-800">Limite: {formatCurrency(b.monthly_limit)}</span>
                </div>
                <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                  <div
                    style={{ width: `${Math.min(b.percentage_used, 100)}%` }}
                    className={`h-full rounded-full transition-all duration-500 ${
                      isExceeded ? 'bg-rose-500' : isWarning ? 'bg-amber-500' : 'bg-emerald-500'
                    }`}
                  />
                </div>
                <div className="flex justify-between text-[11px] font-medium text-slate-400">
                  <span>{b.percentage_used}% consumido</span>
                  <span>Restante: {formatCurrency(b.remaining_amount)}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {budgets.length === 0 && (
        <div className="pastel-card rounded-3xl p-12 text-center">
          <PieChart className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="font-bold text-slate-700 text-sm">Nenhum orçamento configurado para este mês.</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
            Defina metas de gastos por categoria para receber notificações antes de estourar seus limites.
          </p>
        </div>
      )}

      {/* Modal */}
      <BudgetModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={loadData}
        currentMonth={selectedMonth}
        currentYear={selectedYear}
        categories={categories}
      />
    </div>
  );
}
