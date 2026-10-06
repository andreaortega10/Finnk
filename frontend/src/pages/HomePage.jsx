import React, { useState, useEffect } from 'react';
import {
  Calendar as CalendarIcon,
  CheckCircle2,
  Clock,
  AlertCircle,
  CreditCard,
  ArrowLeftRight,
  ChevronRight,
  Plus,
  ArrowDownLeft,
  Layers,
  ChevronLeft
} from 'lucide-react';
import { api } from '../services/api';
import { CategoryDonutChart } from '../components/Charts/CategoryDonutChart';
import { formatCurrency, formatDate, getCategoryIcon } from '../utils/helpers';
import { NewCompromissoModal } from '../components/Modals/NewCompromissoModal';
import { NewEntryModal } from '../components/Modals/NewEntryModal';
import { NewInstallmentModal } from '../components/Modals/NewInstallmentModal';

export function HomePage({ onNavigate }) {
  const [summary, setSummary] = useState(null);
  const [currentMonth, setCurrentMonth] = useState(new Date().getMonth() + 1);
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [loading, setLoading] = useState(true);

  // Modals
  const [isCompromissoModalOpen, setIsCompromissoModalOpen] = useState(false);
  const [isEntryModalOpen, setIsEntryModalOpen] = useState(false);
  const [isInstallmentModalOpen, setIsInstallmentModalOpen] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await api.dashboard.getHomeSummary(currentMonth, currentYear);
      setSummary(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [currentMonth, currentYear]);

  const handlePrevMonth = () => {
    if (currentMonth === 1) {
      setCurrentMonth(12);
      setCurrentYear(currentYear - 1);
    } else {
      setCurrentMonth(currentMonth - 1);
    }
  };

  const handleNextMonth = () => {
    if (currentMonth === 12) {
      setCurrentMonth(1);
      setCurrentYear(currentYear + 1);
    } else {
      setCurrentMonth(currentMonth + 1);
    }
  };

  const handleQuickPay = async (txId, currentStatus) => {
    try {
      const nextStatus = currentStatus === 'PAGA' ? 'PENDENTE' : 'PAGA';
      await api.transactions.updateStatus(txId, nextStatus);
      loadData();
    } catch (err) {
      alert(err.message || 'Erro ao alterar status.');
    }
  };

  if (loading && !summary) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-10 h-10 border-4 border-pink-200 border-t-[#D83A6F] rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-5 pb-20 md:pb-8 px-4 sm:px-6 max-w-5xl mx-auto animate-fadeIn">
      {/* 1. Top Summary Card (Total de compromissos no mês) */}
      <div className="pastel-pink-card rounded-3xl p-5 sm:p-6 shadow-xs relative">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start space-x-3.5">
            <div className="w-12 h-12 rounded-2xl bg-white/80 border border-pink-200/60 flex items-center justify-center text-[#D83A6F] shrink-0 shadow-xs">
              <CalendarIcon className="w-6 h-6 stroke-[1.8]" />
            </div>
            <div>
              <span className="text-xs font-semibold text-slate-600 block">
                Total de compromissos (mês)
              </span>
              <div className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight mt-0.5">
                {formatCurrency(summary?.total_commitments_amount)}
              </div>
              <span className="text-xs font-medium text-slate-500 block mt-0.5">
                {summary?.total_commitments_count || 0} compromisso{summary?.total_commitments_count !== 1 ? 's' : ''}
              </span>
            </div>
          </div>

          {/* Month Navigator Pill */}
          <div className="flex items-center bg-white/90 border border-pink-200/60 rounded-full px-3 py-1.5 shadow-2xs self-start sm:self-center">
            <button
              onClick={handlePrevMonth}
              className="p-1 rounded-full text-slate-500 hover:text-[#D83A6F] transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-xs font-bold text-slate-800 px-2 select-none">
              {summary?.month_name}
            </span>
            <button
              onClick={handleNextMonth}
              className="p-1 rounded-full text-slate-500 hover:text-[#D83A6F] transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* 2. Quick Status Metric Cards (4 cards in row/grid) */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Pagos */}
        <div 
          onClick={() => onNavigate('compromissos', 'PAGA')}
          className="pastel-card rounded-2xl p-4 transition-all hover:shadow-md cursor-pointer active:scale-95"
        >
          <div className="flex items-center space-x-2 text-emerald-600 mb-1.5">
            <div className="w-7 h-7 rounded-full bg-emerald-50 flex items-center justify-center">
              <CheckCircle2 className="w-4 h-4 stroke-[2.2]" />
            </div>
            <span className="text-xs font-bold text-slate-600">Pagos</span>
          </div>
          <div className="text-lg font-bold text-slate-900">
            {formatCurrency(summary?.paid_amount)}
          </div>
          <span className="text-[11px] text-slate-500">
            {summary?.paid_count || 0} compromisso{summary?.paid_count !== 1 ? 's' : ''}
          </span>
        </div>

        {/* Pendentes */}
        <div 
          onClick={() => onNavigate('compromissos', 'PENDENTE')}
          className="pastel-card rounded-2xl p-4 transition-all hover:shadow-md cursor-pointer active:scale-95"
        >
          <div className="flex items-center space-x-2 text-amber-500 mb-1.5">
            <div className="w-7 h-7 rounded-full bg-amber-50 flex items-center justify-center">
              <Clock className="w-4 h-4 stroke-[2.2]" />
            </div>
            <span className="text-xs font-bold text-slate-600">Pendentes</span>
          </div>
          <div className="text-lg font-bold text-slate-900">
            {formatCurrency(summary?.pending_amount)}
          </div>
          <span className="text-[11px] text-slate-500">
            {summary?.pending_count || 0} compromisso{summary?.pending_count !== 1 ? 's' : ''}
          </span>
        </div>

        {/* Atrasados */}
        <div 
          onClick={() => onNavigate('compromissos', 'ATRASADA')}
          className="pastel-card rounded-2xl p-4 transition-all hover:shadow-md cursor-pointer active:scale-95"
        >
          <div className="flex items-center space-x-2 text-rose-600 mb-1.5">
            <div className="w-7 h-7 rounded-full bg-rose-50 flex items-center justify-center">
              <AlertCircle className="w-4 h-4 stroke-[2.2]" />
            </div>
            <span className="text-xs font-bold text-rose-600">Atrasados</span>
          </div>
          <div className="text-lg font-bold text-rose-600">
            {formatCurrency(summary?.overdue_amount)}
          </div>
          <span className="text-[11px] text-slate-500">
            {summary?.overdue_count || 0} compromisso{summary?.overdue_count !== 1 ? 's' : ''}
          </span>
        </div>

        {/* Próximo vencimento */}
        <div className="pastel-card rounded-2xl p-4 transition-all hover:shadow-md">
          <div className="flex items-center space-x-2 text-indigo-500 mb-1.5">
            <div className="w-7 h-7 rounded-full bg-indigo-50 flex items-center justify-center">
              <CalendarIcon className="w-4 h-4 stroke-[2.2]" />
            </div>
            <span className="text-xs font-bold text-slate-600">Próximo vencimento</span>
          </div>
          <div className="text-lg font-bold text-slate-900">
            {summary?.next_due_item?.date_formatted || '--/--'}
          </div>
          <span className="text-[11px] text-slate-500 truncate block" title={summary?.next_due_item?.title}>
            {summary?.next_due_item?.title || 'Nenhum pendente'}
          </span>
        </div>
      </div>

      {/* 3. Quick Action Buttons Bar */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-1 scrollbar-none">
        <button
          onClick={() => setIsCompromissoModalOpen(true)}
          className="flex items-center space-x-2 px-4 py-2.5 rounded-2xl bg-[#D83A6F] text-white font-bold text-xs shadow-xs hover:bg-[#C22A5E] active:scale-95 transition-all whitespace-nowrap shrink-0"
        >
          <Plus className="w-4 h-4 stroke-[2.5]" />
          <span>Novo Compromisso</span>
        </button>

        <button
          onClick={() => setIsEntryModalOpen(true)}
          className="flex items-center space-x-2 px-4 py-2.5 rounded-2xl bg-emerald-600 text-white font-bold text-xs shadow-xs hover:bg-emerald-700 active:scale-95 transition-all whitespace-nowrap shrink-0"
        >
          <ArrowDownLeft className="w-4 h-4 stroke-[2.5]" />
          <span>Nova Entrada</span>
        </button>

        <button
          onClick={() => setIsInstallmentModalOpen(true)}
          className="flex items-center space-x-2 px-4 py-2.5 rounded-2xl bg-purple-600 text-white font-bold text-xs shadow-xs hover:bg-purple-700 active:scale-95 transition-all whitespace-nowrap shrink-0"
        >
          <Layers className="w-4 h-4 stroke-[2.5]" />
          <span>Compra Parcelada</span>
        </button>
      </div>

      {/* 4. Middle Section (Despesas por categoria + Resumo dos cartões) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Despesas por Categoria */}
        <div className="pastel-card rounded-3xl p-5 sm:p-6">
          <h2 className="text-sm font-bold text-slate-800 mb-4">
            Despesas por categoria
          </h2>

          <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
            <div className="w-48 shrink-0">
              <CategoryDonutChart
                data={summary?.category_expenses}
                totalAmount={summary?.total_expenses_period}
              />
            </div>

            {/* Breakdown List */}
            <div className="w-full space-y-2.5">
              {summary?.category_expenses?.slice(0, 5).map((cat) => (
                <div key={cat.category_id} className="flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2 min-w-0">
                    <span
                      className="w-2.5 h-2.5 rounded-full shrink-0"
                      style={{ backgroundColor: cat.color }}
                    />
                    <span className="font-semibold text-slate-700 truncate">{cat.name}</span>
                  </div>
                  <div className="flex items-center space-x-3 shrink-0">
                    <span className="text-slate-400 font-medium">{cat.percentage}%</span>
                    <span className="font-bold text-slate-800">{formatCurrency(cat.amount)}</span>
                  </div>
                </div>
              ))}
              {(!summary?.category_expenses || summary.category_expenses.length === 0) && (
                <p className="text-xs text-slate-400 text-center py-4">Nenhum gasto neste mês.</p>
              )}
            </div>
          </div>
        </div>

        {/* Resumo dos Cartões */}
        <div className="pastel-card rounded-3xl p-5 sm:p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <CreditCard className="w-4 h-4 text-[#D83A6F]" />
                <h2 className="text-sm font-bold text-slate-800">Resumo dos cartões</h2>
              </div>
              <button
                onClick={() => onNavigate('cartoes')}
                className="text-[11px] font-bold text-[#D83A6F] hover:underline"
              >
                Gerenciar
              </button>
            </div>

            <div className="space-y-3">
              {summary?.cards_summary?.map((card) => (
                <div
                  key={card.id}
                  onClick={() => onNavigate('cartoes')}
                  className="flex items-center justify-between p-3 rounded-2xl bg-slate-50/70 border border-slate-100/80 hover:bg-pink-50/40 hover:border-pink-200/60 transition-all cursor-pointer group"
                >
                  <div className="flex items-center space-x-3">
                    <div
                      style={{ backgroundColor: card.color || '#820AD1' }}
                      className="w-12 h-8 rounded-lg flex items-center justify-center text-white font-bold text-[10px] shadow-2xs"
                    >
                      {card.brand?.slice(0, 4)}
                    </div>
                    <div>
                      <div className="text-xs font-bold text-slate-800 group-hover:text-[#D83A6F] transition-colors">
                        {card.name}
                      </div>
                      <div className="text-[11px] text-slate-500">
                        Final {card.last_four_digits}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <div className="text-right">
                      <div className="text-[10px] text-slate-400 font-medium">Fatura atual</div>
                      <div className="text-xs font-bold text-slate-800">
                        {formatCurrency(card.current_invoice)}
                      </div>
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-[#D83A6F] transition-transform group-hover:translate-x-0.5" />
                  </div>
                </div>
              ))}
              {(!summary?.cards_summary || summary.cards_summary.length === 0) && (
                <div className="text-center py-6 text-xs text-slate-400">
                  Nenhum cartão cadastrado.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 5. Próximos Vencimentos List */}
      <div className="pastel-card rounded-3xl p-5 sm:p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <CalendarIcon className="w-4 h-4 text-[#D83A6F]" />
            <h2 className="text-sm font-bold text-slate-800">Próximos vencimentos</h2>
          </div>
          <button
            onClick={() => onNavigate('compromissos')}
            className="text-xs font-bold text-[#D83A6F] hover:underline"
          >
            Ver todos
          </button>
        </div>

        <div className="divide-y divide-slate-100">
          {summary?.upcoming_commitments?.map((item) => (
            <div
              key={item.id}
              className="flex items-center justify-between py-3 group hover:bg-slate-50/50 px-2 rounded-xl transition-colors"
            >
              <div className="flex items-center space-x-3 min-w-0">
                <div className="w-9 h-9 rounded-full bg-pink-50 text-[#D83A6F] flex items-center justify-center shrink-0">
                  {getCategoryIcon(item.category_icon || item.category_name, "w-4 h-4")}
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-bold text-slate-800 truncate">{item.title}</div>
                  <div className="text-[11px] text-slate-400">{formatDate(item.date)}</div>
                </div>
              </div>

              <div className="flex items-center space-x-3 shrink-0">
                <span className="text-xs font-bold text-slate-800">
                  {formatCurrency(item.amount)}
                </span>
                <button
                  onClick={() => handleQuickPay(item.id, item.status)}
                  className={`pastel-badge text-[10px] font-bold cursor-pointer transition-all active:scale-95 ${
                    item.status === 'PAGA'
                      ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
                      : item.status === 'ATRASADA'
                      ? 'bg-rose-50 text-rose-700 hover:bg-rose-100'
                      : 'bg-pink-50 text-[#D83A6F] hover:bg-pink-100'
                  }`}
                  title="Clique para alternar status Pago/Pendente"
                >
                  {item.status === 'PAGA' ? 'Pago' : item.status === 'ATRASADA' ? 'Atrasado' : 'Pendente'}
                </button>
                <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-slate-500" />
              </div>
            </div>
          ))}
          {(!summary?.upcoming_commitments || summary.upcoming_commitments.length === 0) && (
            <p className="text-xs text-slate-400 text-center py-4">Nenhum compromisso próximo a vencer.</p>
          )}
        </div>
      </div>

      {/* 6. Últimas Transações */}
      <div className="pastel-card rounded-3xl p-5 sm:p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <ArrowLeftRight className="w-4 h-4 text-[#D83A6F]" />
            <h2 className="text-sm font-bold text-slate-800">Últimas transações</h2>
          </div>
          <button
            onClick={() => onNavigate('transacoes')}
            className="text-xs font-bold text-[#D83A6F] hover:underline"
          >
            Ver todas
          </button>
        </div>

        <div className="divide-y divide-slate-100">
          {summary?.recent_transactions?.map((t) => {
            const isIncome = t.type === 'RECEITA';
            return (
              <div
                key={t.id}
                className="flex items-center justify-between py-3 group hover:bg-slate-50/50 px-2 rounded-xl transition-colors"
              >
                <div className="flex items-center space-x-3 min-w-0">
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 ${
                    isIncome ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-[#D83A6F]'
                  }`}>
                    {getCategoryIcon(t.category_icon || t.category_name, "w-4 h-4")}
                  </div>
                  <div className="min-w-0">
                    <div className="text-xs font-bold text-slate-800 truncate">{t.title}</div>
                    <div className="text-[11px] text-slate-400">
                      {t.account_name || t.credit_card_name || 'Lançamento'} • {formatDate(t.date)}
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-3 shrink-0">
                  <span className={`text-xs font-black ${
                    isIncome ? 'text-emerald-600' : 'text-slate-800'
                  }`}>
                    {isIncome ? '+ ' : '- '}{formatCurrency(t.amount)}
                  </span>
                  <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-slate-500" />
                </div>
              </div>
            );
          })}
          {(!summary?.recent_transactions || summary.recent_transactions.length === 0) && (
            <p className="text-xs text-slate-400 text-center py-4">Nenhuma transação registrada ainda.</p>
          )}
        </div>
      </div>

      {/* Modals */}
      <NewCompromissoModal
        isOpen={isCompromissoModalOpen}
        onClose={() => setIsCompromissoModalOpen(false)}
        onSuccess={loadData}
      />
      <NewEntryModal
        isOpen={isEntryModalOpen}
        onClose={() => setIsEntryModalOpen(false)}
        onSuccess={loadData}
      />
      <NewInstallmentModal
        isOpen={isInstallmentModalOpen}
        onClose={() => setIsInstallmentModalOpen(false)}
        onSuccess={loadData}
      />
    </div>
  );
}
