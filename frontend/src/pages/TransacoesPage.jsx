import React, { useState, useEffect } from 'react';
import {
  ArrowLeftRight,
  ArrowDownLeft,
  ArrowUpRight,
  Plus,
  Search,
  Filter,
  Trash2,
  Calendar,
  DollarSign
} from 'lucide-react';
import { api } from '../services/api';
import { formatCurrency, formatDate, getCategoryIcon } from '../utils/helpers';
import { NewEntryModal } from '../components/Modals/NewEntryModal';
import { NewCompromissoModal } from '../components/Modals/NewCompromissoModal';

export function TransacoesPage({ initialFilter }) {
  const [tabType, setTabType] = useState(''); // '' (Todas) | 'RECEITA' | 'DESPESA'
  const [transactions, setTransactions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStatus, setSelectedStatus] = useState(initialFilter || '');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [dateFilter, setDateFilter] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [loading, setLoading] = useState(true);

  // Modals
  const [isEntryModalOpen, setIsEntryModalOpen] = useState(false);
  const [isExpenseModalOpen, setIsExpenseModalOpen] = useState(false);

  useEffect(() => {
    let sDate = '';
    let eDate = '';
    const date = new Date();
    
    if (dateFilter === 'HOJE') {
      sDate = date.toISOString().split('T')[0];
      eDate = sDate;
    } else if (dateFilter === 'SEMANA') {
      const firstDay = new Date(date.setDate(date.getDate() - date.getDay()));
      const lastDay = new Date(date.setDate(firstDay.getDate() + 6));
      sDate = firstDay.toISOString().split('T')[0];
      eDate = lastDay.toISOString().split('T')[0];
    } else if (dateFilter === 'MES') {
      const firstDay = new Date(date.getFullYear(), date.getMonth(), 1);
      const lastDay = new Date(date.getFullYear(), date.getMonth() + 1, 0);
      sDate = firstDay.toISOString().split('T')[0];
      eDate = lastDay.toISOString().split('T')[0];
    } else if (dateFilter === 'MES_ANT') {
      const firstDay = new Date(date.getFullYear(), date.getMonth() - 1, 1);
      const lastDay = new Date(date.getFullYear(), date.getMonth(), 0);
      sDate = firstDay.toISOString().split('T')[0];
      eDate = lastDay.toISOString().split('T')[0];
    }
    if (dateFilter === 'PERSONALIZADO') {
      return;
    }
    
    setStartDate(sDate);
    setEndDate(eDate);
  }, [dateFilter]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [txs, cats, accs] = await Promise.all([
        api.transactions.list({
          type: tabType || undefined,
          status_filter: selectedStatus || undefined,
          category_id: selectedCategory || undefined,
          search: searchTerm || undefined,
          start_date: startDate || undefined,
          end_date: endDate || undefined,
        }),
        api.categories.list(),
        api.accounts.list(),
      ]);
      setTransactions(txs);
      setCategories(cats);
      setAccounts(accs);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [tabType, selectedStatus, selectedCategory, searchTerm, startDate, endDate]);

  const handleToggleStatus = async (txId, currentStatus, txType) => {
    let nextStatus = 'PENDENTE';
    if (currentStatus === 'PENDENTE' || currentStatus === 'ATRASADA') {
      nextStatus = txType === 'RECEITA' ? 'RECEBIDA' : 'PAGA';
    } else {
      nextStatus = 'PENDENTE';
    }

    try {
      await api.transactions.updateStatus(txId, nextStatus);
      loadData();
    } catch (err) {
      alert(err.message || 'Erro ao alterar status.');
    }
  };

  const handleDelete = async (txId) => {
    if (!window.confirm('Deseja realmente excluir esta transação?')) return;
    try {
      await api.transactions.delete(txId);
      loadData();
    } catch (err) {
      alert(err.message || 'Erro ao excluir transação.');
    }
  };

  return (
    <div className="space-y-6 pb-20 md:pb-8 px-4 sm:px-6 max-w-5xl mx-auto animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">Transações & Receitas</h2>
          <p className="text-xs text-slate-500">Histórico de todas as movimentações financeiras manuais.</p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsEntryModalOpen(true)}
            className="flex items-center space-x-2 px-3.5 py-2.5 rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-md shadow-emerald-200 transition-all active:scale-95"
          >
            <ArrowDownLeft className="w-4 h-4 stroke-[2.5]" />
            <span>Nova Entrada</span>
          </button>

          <button
            onClick={() => setIsExpenseModalOpen(true)}
            className="flex items-center space-x-2 px-3.5 py-2.5 rounded-2xl bg-[#D83A6F] hover:bg-[#C22A5E] text-white font-bold text-xs shadow-md shadow-pink-200 transition-all active:scale-95"
          >
            <ArrowUpRight className="w-4 h-4 stroke-[2.5]" />
            <span>Nova Despesa</span>
          </button>
        </div>
      </div>

      {/* Tabs & Search Filter Card */}
      <div className="pastel-card rounded-3xl p-5 sm:p-6 space-y-4">
        {/* Type Tabs */}
        <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
          <button
            onClick={() => setTabType('')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              tabType === '' ? 'bg-[#D83A6F] text-white shadow-xs' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            Todas
          </button>
          <button
            onClick={() => setTabType('RECEITA')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              tabType === 'RECEITA' ? 'bg-emerald-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            Entradas / Receitas
          </button>
          <button
            onClick={() => setTabType('DESPESA')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              tabType === 'DESPESA' ? 'bg-[#D83A6F] text-white shadow-xs' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            Despesas
          </button>
        </div>

        {/* Toolbar */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Buscar transação..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3.5 py-2 rounded-xl border border-slate-200 focus:border-[#D83A6F] text-xs outline-none bg-slate-50/50"
            />
          </div>

          <select
            value={dateFilter}
            onChange={(e) => setDateFilter(e.target.value)}
            className="px-3 py-2 rounded-xl border border-slate-200 text-xs outline-none bg-white font-medium text-slate-700"
          >
            <option value="">Todas as datas</option>
            <option value="HOJE">Hoje</option>
            <option value="SEMANA">Esta Semana</option>
            <option value="MES">Este Mês</option>
            <option value="MES_ANT">Mês Anterior</option>
            <option value="PERSONALIZADO">Personalizado</option>
          </select>

          {dateFilter === 'PERSONALIZADO' && (
            <div className="flex items-center space-x-2">
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="px-3 py-2 rounded-xl border border-slate-200 text-xs outline-none bg-white font-medium text-slate-700"
              />
              <span className="text-slate-400">até</span>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="px-3 py-2 rounded-xl border border-slate-200 text-xs outline-none bg-white font-medium text-slate-700"
              />
            </div>
          )}

          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-3 py-2 rounded-xl border border-slate-200 text-xs outline-none bg-white font-medium text-slate-700"
          >
            <option value="">Todos os status</option>
            <option value="PAGA">Pagas / Recebidas</option>
            <option value="PENDENTE">Pendentes</option>
            <option value="ATRASADA">Atrasadas</option>
          </select>

          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-2 rounded-xl border border-slate-200 text-xs outline-none bg-white font-medium text-slate-700"
          >
            <option value="">Todas as categorias</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Transactions List */}
      <div className="pastel-card rounded-3xl p-5 sm:p-6">
        <div className="divide-y divide-slate-100">
          {transactions.map((t) => {
            const isIncome = t.type === 'RECEITA';
            const isPaid = t.status === 'PAGA' || t.status === 'RECEBIDA';

            return (
              <div key={t.id} className="py-3.5 flex items-center justify-between gap-3 group hover:bg-slate-50/60 px-3 rounded-2xl transition-colors">
                <div className="flex items-center space-x-3.5 min-w-0">
                  <div className={`w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 ${
                    isIncome ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-[#D83A6F]'
                  }`}>
                    {getCategoryIcon(t.category_icon || t.category_name, "w-5 h-5")}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-bold text-slate-800 break-words whitespace-normal line-clamp-2">
                      {t.title}
                      {t.is_installment && (
                        <span className="inline-block ml-2 text-[10px] font-bold bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full align-middle">
                          Parcela {t.installment_number}/{t.total_installments}
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-slate-400 mt-0.5 flex items-center space-x-2">
                      <span>{formatDate(t.date)}</span>
                      <span>• {t.category_name}</span>
                      {t.account_name && <span>• {t.account_name}</span>}
                      {t.credit_card_name && <span>• {t.credit_card_name}</span>}
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-3 shrink-0">
                  <span className={`text-sm font-black ${
                    isIncome ? 'text-emerald-600' : 'text-slate-900'
                  }`}>
                    {isIncome ? '+ ' : '- '}{formatCurrency(t.amount)}
                  </span>

                  <button
                    onClick={() => handleToggleStatus(t.id, t.status, t.type)}
                    className={`pastel-badge text-xs font-bold cursor-pointer transition-all active:scale-95 ${
                      isPaid
                        ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
                        : t.status === 'ATRASADA'
                        ? 'bg-rose-50 text-rose-700 hover:bg-rose-100'
                        : 'bg-amber-50 text-amber-700 hover:bg-amber-100'
                    }`}
                  >
                    {isPaid ? (isIncome ? 'Recebida' : 'Paga') : t.status === 'ATRASADA' ? 'Atrasada' : 'Pendente'}
                  </button>

                  <button
                    onClick={() => handleDelete(t.id)}
                    className="p-1.5 text-slate-300 hover:text-rose-600 transition-colors rounded-lg hover:bg-rose-50"
                    title="Excluir"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
          {transactions.length === 0 && (
            <div className="text-center py-12">
              <ArrowLeftRight className="w-10 h-10 text-slate-300 mx-auto mb-2" />
              <p className="text-sm font-semibold text-slate-600">Tudo limpo por aqui. Que tal registrar sua primeira movimentação?</p>
              <p className="text-xs text-slate-400 mt-0.5">Registre entradas ou despesas para movimentar seus saldos.</p>
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      <NewEntryModal
        isOpen={isEntryModalOpen}
        onClose={() => setIsEntryModalOpen(false)}
        onSuccess={loadData}
      />
      <NewCompromissoModal
        isOpen={isExpenseModalOpen}
        onClose={() => setIsExpenseModalOpen(false)}
        onSuccess={loadData}
      />
    </div>
  );
}
