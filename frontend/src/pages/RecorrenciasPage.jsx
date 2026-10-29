import React, { useState, useEffect } from 'react';
import { Clock, Plus, Pause, Play, Trash2, Calendar, Tag } from 'lucide-react';
import { api } from '../services/api';
import { formatCurrency, formatDate, getCategoryIcon } from '../utils/helpers';
import { NewCompromissoModal } from '../components/Modals/NewCompromissoModal';

export function RecorrenciasPage() {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await api.recurring.list();
      setRules(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleToggle = async (ruleId) => {
    try {
      await api.recurring.toggle(ruleId);
      loadData();
    } catch (err) {
      alert(err.message || 'Erro ao alternar status da recorrência.');
    }
  };

  const handleDelete = async (ruleId) => {
    if (!window.confirm('Deseja realmente encerrar esta recorrência e remover lançamentos futuros pendentes?')) return;
    try {
      await api.recurring.delete(ruleId);
      loadData();
    } catch (err) {
      alert(err.message || 'Erro ao excluir recorrência.');
    }
  };

  return (
    <div className="space-y-6 pb-20 md:pb-8 px-4 sm:px-6 max-w-5xl mx-auto animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">Despesas & Receitas Recorrentes</h2>
          <p className="text-xs text-slate-500">Lançamentos automáticos gerados com 3 meses de antecedência.</p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center space-x-2 px-4 py-2.5 rounded-2xl bg-[#D83A6F] hover:bg-[#C22A5E] text-white font-bold text-xs shadow-md shadow-pink-200 transition-all active:scale-95"
        >
          <Plus className="w-4 h-4 stroke-[2.5]" />
          <span>Nova Recorrência</span>
        </button>
      </div>

      {/* Rules List */}
      <div className="pastel-card rounded-3xl p-5 sm:p-6">
        <div className="divide-y divide-slate-100">
          {rules.map((r) => {
            const isIncome = r.type === 'RECEITA';
            return (
              <div 
                key={r.id} 
                className="py-4 px-3 sm:px-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 group hover:bg-slate-50/80 rounded-2xl transition-colors border border-transparent hover:border-slate-100"
              >
                {/* Info Column */}
                <div className="flex items-start space-x-3.5 min-w-0 flex-1">
                  <div className={`w-11 h-11 rounded-2xl flex items-center justify-center shrink-0 mt-0.5 ${
                    isIncome ? 'bg-emerald-50 text-emerald-600' : 'bg-pink-50 text-[#D83A6F]'
                  }`}>
                    {getCategoryIcon(r.category_name, "w-5 h-5")}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-bold text-slate-800 break-words leading-snug">
                        {r.title}
                      </span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full shrink-0 ${
                        r.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'
                      }`}>
                        {r.is_active ? 'Ativa' : 'Pausada'}
                      </span>
                    </div>

                    <div className="text-xs text-slate-500 mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 leading-relaxed">
                      <span className="inline-flex items-center font-medium bg-slate-100/70 px-2 py-0.5 rounded-md text-slate-600">
                        Todo dia {r.due_day} • {r.frequency?.toLowerCase() || 'mensal'}
                      </span>
                      {r.category_name && (
                        <span className="text-slate-500">
                          Categoria: <strong className="text-slate-700 font-semibold">{r.category_name}</strong>
                        </span>
                      )}
                      {r.next_due_date && (
                        <span className="text-slate-500">
                          Próximo: <strong className="text-slate-700 font-semibold">{formatDate(r.next_due_date)}</strong>
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Amount & Actions */}
                <div className="flex items-center justify-between sm:justify-end space-x-3 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-100">
                  <span className={`text-base sm:text-lg font-black tracking-tight ${
                    isIncome ? 'text-emerald-600' : 'text-slate-900'
                  }`}>
                    {isIncome ? '+ ' : '- '}{formatCurrency(r.amount)}
                  </span>

                  <div className="flex items-center space-x-1.5">
                    <button
                      onClick={() => handleToggle(r.id)}
                      className={`p-2.5 rounded-xl border text-xs font-bold transition-all active:scale-95 cursor-pointer ${
                        r.is_active
                          ? 'border-amber-200 text-amber-700 hover:bg-amber-50'
                          : 'border-emerald-200 text-emerald-700 hover:bg-emerald-50'
                      }`}
                      title={r.is_active ? 'Pausar recorrência' : 'Retomar recorrência'}
                      aria-label={r.is_active ? 'Pausar recorrência' : 'Retomar recorrência'}
                    >
                      {r.is_active ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                    </button>

                    <button
                      onClick={() => handleDelete(r.id)}
                      className="p-2.5 text-slate-400 hover:text-rose-600 transition-colors rounded-xl hover:bg-rose-50 active:scale-95 cursor-pointer"
                      title="Encerrar recorrência"
                      aria-label="Encerrar recorrência"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
          {rules.length === 0 && (
            <div className="text-center py-12">
              <Clock className="w-10 h-10 text-slate-300 mx-auto mb-2" />
              <p className="text-sm font-semibold text-slate-600">Nenhuma recorrência cadastrada.</p>
              <p className="text-xs text-slate-400 mt-0.5">Cadastre aluguel, assinaturas, salários ou outros compromissos periódicos.</p>
            </div>
          )}
        </div>
      </div>

      <NewCompromissoModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={loadData}
        defaultIsRecurring={true}
      />
    </div>
  );
}
