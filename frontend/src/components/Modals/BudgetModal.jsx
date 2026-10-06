import React, { useState, useEffect } from 'react';
import { X, PieChart, DollarSign, AlertCircle } from 'lucide-react';
import { api } from '../../services/api';

export function BudgetModal({ isOpen, onClose, onSuccess, currentMonth, currentYear, categories = [] }) {
  const [categoryId, setCategoryId] = useState('');
  const [limitAmount, setLimitAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (isOpen) {
      if (categories.length > 0) setCategoryId(categories[0].id);
      setLimitAmount('');
      setErrorMsg('');
    }
  }, [isOpen, categories]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    const numLimit = parseFloat(limitAmount.replace(',', '.'));
    if (isNaN(numLimit) || numLimit <= 0) {
      setErrorMsg('Informe um limite válido maior que zero.');
      return;
    }

    setLoading(true);
    try {
      await api.budgets.set({
        category_id: parseInt(categoryId, 10),
        month: currentMonth,
        year: currentYear,
        monthly_limit: numLimit,
      });
      onSuccess();
      onClose();
    } catch (err) {
      setErrorMsg(err.message || 'Erro ao definir orçamento.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-fadeIn">
      <div className="bg-white rounded-3xl shadow-2xl max-w-md w-full p-6 relative border border-slate-100">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-pink-50 text-[#D83A6F] flex items-center justify-center">
              <PieChart className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-800">Definir Orçamento</h3>
              <p className="text-[11px] text-slate-500">Mês {currentMonth}/{currentYear}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-full text-slate-400 hover:text-slate-700">
            <X className="w-5 h-5" />
          </button>
        </div>

        {errorMsg && (
          <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Categoria *</label>
            <select
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-[#D83A6F] focus:ring-2 focus:ring-pink-100 text-sm outline-none bg-white font-medium"
              required
            >
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Limite Mensal de Gastos *</label>
            <div className="relative">
              <span className="absolute left-3.5 top-2.5 text-xs text-slate-400 font-bold">R$</span>
              <input
                type="text"
                inputMode="decimal"
                placeholder="Ex.: 600,00"
                value={limitAmount}
                onChange={(e) => setLimitAmount(e.target.value)}
                className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-[#D83A6F] focus:ring-2 focus:ring-pink-100 text-sm outline-none font-bold text-slate-800"
                required
              />
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Você será alertado quando atingir 80% ou ultrapassar 100% deste limite.
            </p>
          </div>

          <div className="pt-2 flex space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="w-1/3 py-2.5 rounded-xl border border-slate-200 text-slate-600 font-bold text-xs hover:bg-slate-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="w-2/3 py-2.5 rounded-xl bg-[#D83A6F] hover:bg-[#C22A5E] text-white font-bold text-xs shadow-md shadow-pink-200 transition-all flex items-center justify-center"
            >
              {loading ? 'Salvando...' : 'Salvar Orçamento'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
