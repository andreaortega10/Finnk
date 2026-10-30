import React, { useState, useEffect } from 'react';
import {
  Landmark,
  Plus,
  Edit2,
  Trash2,
  TrendingUp,
  TrendingDown,
  Clock,
  ArrowRightLeft,
  Calendar,
  X
} from 'lucide-react';
import { api } from '../services/api';
import { formatCurrency } from '../utils/helpers';
import { AccountModal } from '../components/Modals/AccountModal';

export function ContasPage() {
  const [accounts, setAccounts] = useState([]);
  const [projectionSummary, setProjectionSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAccount, setEditingAccount] = useState(null);

  // Horizonte de projeção: 'MONTH' | '7' | '30' | '90' | 'CUSTOM'
  const [horizonMode, setHorizonMode] = useState('MONTH');
  const [customStartDate, setCustomStartDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [customEndDate, setCustomEndDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 30);
    return d.toISOString().split('T')[0];
  });

  // Modal de transferência entre contas
  const [isTransferOpen, setIsTransferOpen] = useState(false);
  const [transferData, setTransferData] = useState({
    origin_account_id: '',
    destination_account_id: '',
    amount: '',
    date: new Date().toISOString().split('T')[0],
    description: ''
  });
  const [transferSubmitting, setTransferSubmitting] = useState(false);

  const buildProjectionParams = () => {
    if (horizonMode === '7' || horizonMode === '30' || horizonMode === '90') {
      return { horizon_days: Number(horizonMode) };
    }
    if (horizonMode === 'CUSTOM' && customEndDate) {
      return { start_date: customStartDate, end_date: customEndDate };
    }
    const now = new Date();
    return { month: now.getMonth() + 1, year: now.getFullYear() };
  };

  const loadData = async () => {
    try {
      setLoading(true);
      const params = buildProjectionParams();
      const proj = await api.accounts.getProjections(params);
      setProjectionSummary(proj);
      setAccounts(proj.accounts || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [horizonMode, customStartDate, customEndDate]);

  const handleDelete = async (id) => {
    if (!window.confirm('Deseja realmente desativar esta conta financeira?')) return;
    try {
      await api.accounts.delete(id);
      loadData();
    } catch (err) {
      alert(err.message || 'Erro ao desativar conta.');
    }
  };

  const handleOpenTransfer = () => {
    setTransferData({
      origin_account_id: accounts[0]?.id || '',
      destination_account_id: accounts[1]?.id || '',
      amount: '',
      date: new Date().toISOString().split('T')[0],
      description: ''
    });
    setIsTransferOpen(true);
  };

  const handleSubmitTransfer = async (e) => {
    e.preventDefault();
    if (!transferData.origin_account_id || !transferData.destination_account_id) {
      alert('Selecione as contas de origem e destino.');
      return;
    }
    if (Number(transferData.origin_account_id) === Number(transferData.destination_account_id)) {
      alert('A conta de origem e a conta de destino devem ser diferentes.');
      return;
    }
    try {
      setTransferSubmitting(true);
      await api.accounts.transfer({
        origin_account_id: Number(transferData.origin_account_id),
        destination_account_id: Number(transferData.destination_account_id),
        amount: parseFloat(transferData.amount),
        date: transferData.date,
        description: transferData.description
      });
      setIsTransferOpen(false);
      loadData();
    } catch (err) {
      alert(err.message || 'Erro ao realizar transferência.');
    } finally {
      setTransferSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 pb-20 md:pb-8 px-4 sm:px-6 max-w-5xl mx-auto animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">Contas Financeiras</h2>
          <p className="text-xs text-slate-500">
            Cada conta possui seu próprio saldo atual e projetado. Somente movimentações vinculadas a ela alteram seu saldo.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {accounts.length >= 2 && (
            <button
              onClick={handleOpenTransfer}
              className="flex items-center space-x-2 px-4 py-2.5 rounded-2xl bg-white border border-slate-200 hover:border-indigo-300 text-slate-700 font-bold text-xs shadow-2xs transition-all active:scale-95"
            >
              <ArrowRightLeft className="w-4 h-4 text-indigo-600" />
              <span>Transferir entre Contas</span>
            </button>
          )}
          <button
            onClick={() => {
              setEditingAccount(null);
              setIsModalOpen(true);
            }}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-2xl bg-[#D83A6F] hover:bg-[#C22A5E] text-white font-bold text-xs shadow-md shadow-pink-200 transition-all active:scale-95"
          >
            <Plus className="w-4 h-4 stroke-[2.5]" />
            <span>Nova Conta</span>
          </button>
        </div>
      </div>

      {/* Seletor de Horizonte de Projeção (Fim do Mês, 7, 30, 90 dias e Personalizado) */}
      <div className="pastel-card rounded-3xl p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <Calendar className="w-4 h-4 text-[#D83A6F]" />
            <span className="text-xs font-bold text-slate-800">
              Horizonte de Projeção: <span className="text-[#D83A6F]">{projectionSummary?.period_label || 'Mês Atual'}</span>
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-1.5">
            {[
              { id: 'MONTH', label: 'Fim do Mês' },
              { id: '7', label: '7 dias' },
              { id: '30', label: '30 dias' },
              { id: '90', label: '90 dias' },
              { id: 'CUSTOM', label: 'Personalizado' }
            ].map((opt) => (
              <button
                key={opt.id}
                onClick={() => setHorizonMode(opt.id)}
                className={`px-3 py-1.5 rounded-full text-xs font-bold transition-all ${
                  horizonMode === opt.id
                    ? 'bg-[#D83A6F] text-white shadow-xs'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {horizonMode === 'CUSTOM' && (
          <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-slate-100">
            <div className="flex items-center space-x-2">
              <label className="text-xs font-semibold text-slate-600">De:</label>
              <input
                type="date"
                value={customStartDate}
                onChange={(e) => setCustomStartDate(e.target.value)}
                className="px-3 py-1.5 rounded-xl border border-slate-200 text-xs font-medium text-slate-800"
              />
            </div>
            <div className="flex items-center space-x-2">
              <label className="text-xs font-semibold text-slate-600">Até:</label>
              <input
                type="date"
                value={customEndDate}
                onChange={(e) => setCustomEndDate(e.target.value)}
                className="px-3 py-1.5 rounded-xl border border-slate-200 text-xs font-medium text-slate-800"
              />
            </div>
          </div>
        )}

        {projectionSummary && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 border-t border-slate-100">
            <div className="p-3 rounded-2xl bg-emerald-50/50 border border-emerald-100">
              <span className="text-[11px] font-semibold text-slate-500 block">Saldo Atual (Real)</span>
              <span className="text-base font-black text-slate-900">{formatCurrency(projectionSummary.current_balance)}</span>
              <span className="text-[10px] text-slate-400 block mt-0.5">Ref: {projectionSummary.reference_date}</span>
            </div>
            <div className="p-3 rounded-2xl bg-blue-50/40 border border-blue-100">
              <span className="text-[11px] font-semibold text-slate-500 block">+ Entradas Previstas</span>
              <span className="text-base font-bold text-emerald-600">+{formatCurrency(projectionSummary.projected_incomes)}</span>
              <span className="text-[10px] text-slate-400 block mt-0.5">Receitas pendentes</span>
            </div>
            <div className="p-3 rounded-2xl bg-rose-50/40 border border-rose-100">
              <span className="text-[11px] font-semibold text-slate-500 block">- Saídas Previstas</span>
              <span className="text-base font-bold text-rose-600">-{formatCurrency(projectionSummary.projected_expenses)}</span>
              <span className="text-[10px] text-slate-400 block mt-0.5">{projectionSummary.projected_commitments_count} compromisso(s)</span>
            </div>
            <div className="p-3 rounded-2xl bg-indigo-50/60 border border-indigo-100">
              <span className="text-[11px] font-semibold text-indigo-700 block">= Saldo Projetado</span>
              <span className="text-base font-black text-indigo-800">{formatCurrency(projectionSummary.projected_balance)}</span>
              <span className="text-[10px] text-indigo-500 block mt-0.5">Até {projectionSummary.end_date}</span>
            </div>
          </div>
        )}
      </div>

      {/* Accounts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {accounts.map((acc) => (
          <div key={acc.id} className="pastel-card rounded-3xl p-6 space-y-4 relative group hover:shadow-md transition-all">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <div
                  className="w-12 h-12 rounded-2xl flex items-center justify-center text-white font-bold shadow-xs"
                  style={{ backgroundColor: acc.color || '#3B82F6' }}
                >
                  <Landmark className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="font-bold text-base text-slate-900">{acc.name}</h3>
                  <span className="text-xs text-slate-400 uppercase font-semibold">{acc.type}</span>
                </div>
              </div>

              <div className="flex items-center space-x-1">
                <button
                  onClick={() => {
                    setEditingAccount(acc);
                    setIsModalOpen(true);
                  }}
                  className="p-1.5 text-slate-300 hover:text-slate-700 transition-colors rounded-lg hover:bg-slate-100"
                  title="Editar Conta"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDelete(acc.id)}
                  className="p-1.5 text-slate-300 hover:text-rose-600 transition-colors rounded-lg hover:bg-rose-50"
                  title="Desativar Conta"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="space-y-2 pt-2 border-t border-slate-100 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Saldo Inicial:</span>
                <span className="font-semibold text-slate-600">{formatCurrency(acc.initial_balance)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-600 font-bold flex items-center space-x-1">
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
                  <span>Saldo Atual (Real):</span>
                </span>
                <span className="font-black text-sm text-slate-900">{formatCurrency(acc.current_balance)}</span>
              </div>

              <div className="flex justify-between items-center text-[11px] text-slate-500 pt-1">
                <span>+ Entradas Previstas:</span>
                <span className="font-semibold text-emerald-600">+{formatCurrency(acc.projected_incomes || 0)}</span>
              </div>
              <div className="flex justify-between items-center text-[11px] text-slate-500">
                <span>- Saídas Previstas:</span>
                <span className="font-semibold text-rose-500">-{formatCurrency(acc.projected_expenses || 0)}</span>
              </div>

              <div className="flex justify-between items-center pt-1.5 border-t border-slate-100">
                <span className="text-indigo-600 font-semibold flex items-center space-x-1">
                  <Clock className="w-3.5 h-3.5 text-indigo-500" />
                  <span>Saldo Projetado:</span>
                </span>
                <span className="font-bold text-sm text-indigo-700">{formatCurrency(acc.projected_balance)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {accounts.length === 0 && !loading && (
        <div className="pastel-card rounded-3xl p-12 text-center">
          <Landmark className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="font-bold text-slate-700 text-sm">Nenhuma conta cadastrada.</h3>
          <p className="text-xs text-slate-400 mt-1">Cadastre sua primeira conta financeira para registrar lançamentos.</p>
        </div>
      )}

      {/* Modal de Nova / Editar Conta */}
      <AccountModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={loadData}
        editAccount={editingAccount}
      />

      {/* Modal de Transferência entre Contas */}
      {isTransferOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-3xl p-6 w-full max-w-md shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="w-9 h-9 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
                  <ArrowRightLeft className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Transferência entre Contas</h3>
                  <p className="text-[11px] text-slate-400">Move saldo entre contas sem contar como receita ou despesa</p>
                </div>
              </div>
              <button
                onClick={() => setIsTransferOpen(false)}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-full"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmitTransfer} className="space-y-3.5 text-xs">
              <div>
                <label className="block font-bold text-slate-700 mb-1">Conta de Origem (Sai o valor)</label>
                <select
                  value={transferData.origin_account_id}
                  onChange={(e) => setTransferData({ ...transferData, origin_account_id: e.target.value })}
                  required
                  className="w-full px-3.5 py-2.5 rounded-2xl border border-slate-200 font-medium text-slate-800"
                >
                  <option value="">Selecione...</option>
                  {accounts.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.name} (Atual: {formatCurrency(a.current_balance)})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Conta de Destino (Entra o valor)</label>
                <select
                  value={transferData.destination_account_id}
                  onChange={(e) => setTransferData({ ...transferData, destination_account_id: e.target.value })}
                  required
                  className="w-full px-3.5 py-2.5 rounded-2xl border border-slate-200 font-medium text-slate-800"
                >
                  <option value="">Selecione...</option>
                  {accounts.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.name} (Atual: {formatCurrency(a.current_balance)})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-slate-700 mb-1">Valor (R$)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    required
                    value={transferData.amount}
                    onChange={(e) => setTransferData({ ...transferData, amount: e.target.value })}
                    placeholder="0,00"
                    className="w-full px-3.5 py-2.5 rounded-2xl border border-slate-200 font-medium text-slate-800"
                  />
                </div>
                <div>
                  <label className="block font-bold text-slate-700 mb-1">Data</label>
                  <input
                    type="date"
                    required
                    value={transferData.date}
                    onChange={(e) => setTransferData({ ...transferData, date: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-2xl border border-slate-200 font-medium text-slate-800"
                  />
                </div>
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Descrição (opcional)</label>
                <input
                  type="text"
                  value={transferData.description}
                  onChange={(e) => setTransferData({ ...transferData, description: e.target.value })}
                  placeholder="Ex: Aplicação para reserva de emergência"
                  className="w-full px-3.5 py-2.5 rounded-2xl border border-slate-200 font-medium text-slate-800"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsTransferOpen(false)}
                  className="px-4 py-2 rounded-2xl border border-slate-200 text-slate-600 font-bold"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={transferSubmitting}
                  className="px-5 py-2 rounded-2xl bg-[#D83A6F] hover:bg-[#C22A5E] text-white font-bold shadow-sm disabled:opacity-50"
                >
                  {transferSubmitting ? 'Transferindo...' : 'Confirmar Transferência'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
