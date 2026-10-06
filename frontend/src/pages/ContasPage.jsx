import React, { useState, useEffect } from 'react';
import { Landmark, Plus, Edit2, Trash2, TrendingUp, Clock, AlertCircle } from 'lucide-react';
import { api } from '../services/api';
import { formatCurrency } from '../utils/helpers';
import { AccountModal } from '../components/Modals/AccountModal';

export function ContasPage() {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAccount, setEditingAccount] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await api.accounts.list();
      setAccounts(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleDelete = async (id) => {
    if (!window.confirm('Deseja realmente desativar esta conta financeira?')) return;
    try {
      await api.accounts.delete(id);
      loadData();
    } catch (err) {
      alert(err.message || 'Erro ao desativar conta.');
    }
  };

  return (
    <div className="space-y-6 pb-20 md:pb-8 px-4 sm:px-6 max-w-5xl mx-auto animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">Contas Financeiras</h2>
          <p className="text-xs text-slate-500">
            Cadastre suas contas (Corrente, Carteira, Poupança). Sem integração bancária — controle 100% manual.
          </p>
        </div>

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
                >
                  <Edit2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDelete(acc.id)}
                  className="p-1.5 text-slate-300 hover:text-rose-600 transition-colors rounded-lg hover:bg-rose-50"
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
                  <span>Saldo Atual:</span>
                </span>
                <span className="font-black text-sm text-slate-900">{formatCurrency(acc.current_balance)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-indigo-600 font-semibold flex items-center space-x-1">
                  <Clock className="w-3.5 h-3.5 text-indigo-500" />
                  <span>Saldo Projetado:</span>
                </span>
                <span className="font-bold text-indigo-700">{formatCurrency(acc.projected_balance)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {accounts.length === 0 && (
        <div className="pastel-card rounded-3xl p-12 text-center">
          <Landmark className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="font-bold text-slate-700 text-sm">Nenhuma conta cadastrada.</h3>
          <p className="text-xs text-slate-400 mt-1">Cadastre sua primeira conta financeira para registrar lançamentos.</p>
        </div>
      )}

      {/* Modal */}
      <AccountModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={loadData}
        editAccount={editingAccount}
      />
    </div>
  );
}
