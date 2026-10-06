import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Clock,
  AlertCircle,
  CreditCard,
  Landmark,
  ChevronLeft,
  ChevronRight,
  ShieldAlert
} from 'lucide-react';
import { api } from '../services/api';
import { CategoryDonutChart } from '../components/Charts/CategoryDonutChart';
import { MonthlyEvolutionChart } from '../components/Charts/MonthlyEvolutionChart';
import { formatCurrency } from '../utils/helpers';

export function DashboardPage({ onNavigate }) {
  const [analytics, setAnalytics] = useState(null);
  const [currentMonth, setCurrentMonth] = useState(new Date().getMonth() + 1);
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await api.dashboard.getAnalytics(currentMonth, currentYear);
      setAnalytics(data);
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

  if (loading && !analytics) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-10 h-10 border-4 border-pink-200 border-t-[#D83A6F] rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-20 md:pb-8 px-4 sm:px-6 max-w-5xl mx-auto animate-fadeIn">
      {/* Header with Month Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">
            Dashboard Analítico
          </h2>
          <p className="text-xs text-slate-500">
            Visão consolidada de saldos, evolução mensal, categorias e obrigações.
          </p>
        </div>

        <div className="flex items-center bg-white border border-slate-200 rounded-full px-3 py-1.5 shadow-2xs self-start sm:self-auto">
          <button
            onClick={handlePrevMonth}
            className="p-1 rounded-full text-slate-500 hover:text-[#D83A6F] transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="text-xs font-bold text-slate-800 px-3 select-none">
            {analytics?.selected_period}
          </span>
          <button
            onClick={handleNextMonth}
            className="p-1 rounded-full text-slate-500 hover:text-[#D83A6F] transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Balances Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Saldo Atual */}
        <div className="pastel-card rounded-3xl p-5 border-l-4 border-l-emerald-500">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500">Saldo Atual (Real)</span>
            <div className="w-8 h-8 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <TrendingUp className="w-4 h-4 stroke-[2.2]" />
            </div>
          </div>
          <div className="text-2xl font-black text-slate-900">
            {formatCurrency(analytics?.current_balance)}
          </div>
          <span className="text-[11px] text-slate-400 mt-1 block">
            Saldo inicial + receitas pagas - despesas pagas
          </span>
        </div>

        {/* Saldo Projetado */}
        <div className="pastel-card rounded-3xl p-5 border-l-4 border-l-indigo-500">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500">Saldo Projetado (Futuro)</span>
            <div className="w-8 h-8 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <Clock className="w-4 h-4 stroke-[2.2]" />
            </div>
          </div>
          <div className="text-2xl font-black text-slate-900">
            {formatCurrency(analytics?.projected_balance)}
          </div>
          <span className="text-[11px] text-slate-400 mt-1 block">
            Considera lançamentos futuros pendentes
          </span>
        </div>

        {/* Receitas Recebidas vs Previstas */}
        <div className="pastel-card rounded-3xl p-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500">Receitas do Período</span>
            <div className="w-8 h-8 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="text-xl font-bold text-emerald-600">
            {formatCurrency(analytics?.total_income_received)}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            + {formatCurrency(analytics?.total_income_expected)} previstas
          </div>
        </div>

        {/* Despesas Pagas vs Pendentes */}
        <div className="pastel-card rounded-3xl p-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500">Despesas do Período</span>
            <div className="w-8 h-8 rounded-full bg-rose-50 text-[#D83A6F] flex items-center justify-center">
              <TrendingDown className="w-4 h-4" />
            </div>
          </div>
          <div className="text-xl font-bold text-slate-900">
            {formatCurrency(analytics?.total_expense_paid)}
          </div>
          <div className="text-[11px] text-rose-500 font-semibold mt-1">
            + {formatCurrency(analytics?.total_expense_pending)} a pagar
          </div>
        </div>
      </div>

      {/* 2. Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Evolução Mensal (2 cols) */}
        <div className="pastel-card rounded-3xl p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-slate-800">Evolução Mensal (Receitas vs Despesas)</h2>
              <p className="text-xs text-slate-400">Comparativo dos últimos 6 meses</p>
            </div>
          </div>
          <MonthlyEvolutionChart data={analytics?.monthly_evolution} />
        </div>

        {/* Gastos por Categoria (1 col) */}
        <div className="pastel-card rounded-3xl p-6 flex flex-col justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-800 mb-1">Gastos por Categoria</h2>
            <p className="text-xs text-slate-400 mb-4">Distribuição percentual</p>
            <CategoryDonutChart
              data={analytics?.category_distribution}
              totalAmount={analytics?.total_expense_paid + analytics?.total_expense_pending}
            />
          </div>
          <div className="space-y-2 mt-4 max-h-36 overflow-y-auto pr-1">
            {analytics?.category_distribution?.map((cat) => (
              <div key={cat.category_id} className="flex items-center justify-between text-xs">
                <div className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: cat.color }} />
                  <span className="text-slate-700 font-medium">{cat.name}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-slate-400">{cat.percentage}%</span>
                  <span className="font-bold text-slate-800">{formatCurrency(cat.amount)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 3. Status Distribution & Accounts Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Status dos Compromissos */}
        <div className="pastel-card rounded-3xl p-6">
          <h2 className="text-sm font-bold text-slate-800 mb-4">
            Distribuição dos Compromissos
          </h2>
          <div className="space-y-3">
            {analytics?.status_distribution?.map((st, i) => {
              const statusKey = st.name === 'Pagos' ? 'PAGA' : st.name === 'Pendentes' ? 'PENDENTE' : 'ATRASADA';
              return (
                <div 
                  key={i} 
                  onClick={() => onNavigate('compromissos', statusKey)}
                  className="flex items-center justify-between p-3.5 rounded-2xl bg-slate-50 border border-slate-100 cursor-pointer hover:bg-pink-50/50 active:scale-95 transition-all"
                >
                  <div className="flex items-center space-x-3">
                    <span className="w-3 h-3 rounded-full" style={{ backgroundColor: st.color }} />
                    <div>
                      <div className="text-xs font-bold text-slate-800">{st.name}</div>
                      <div className="text-[11px] text-slate-500">{st.count} itens</div>
                    </div>
                  </div>
                  <div className="text-sm font-bold text-slate-800">
                    {formatCurrency(st.amount)}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Saldos por Conta */}
        <div className="pastel-card rounded-3xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold text-slate-800">Contas Financeiras</h2>
            <button
              onClick={() => onNavigate('contas')}
              className="text-xs font-bold text-[#D83A6F] hover:underline"
            >
              Ver todas
            </button>
          </div>
          <div className="space-y-3">
            {analytics?.accounts_balance?.map((acc) => (
              <div key={acc.id} className="flex items-center justify-between p-3.5 rounded-2xl bg-slate-50 border border-slate-100">
                <div className="flex items-center space-x-3">
                  <div className="w-9 h-9 rounded-xl flex items-center justify-center text-white font-bold text-xs" style={{ backgroundColor: acc.color }}>
                    <Landmark className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-800">{acc.name}</div>
                    <div className="text-[11px] text-slate-500">{acc.type}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs font-bold text-slate-900">{formatCurrency(acc.current_balance)}</div>
                  <div className="text-[10px] text-indigo-600 font-semibold">Proj: {formatCurrency(acc.projected_balance)}</div>
                </div>
              </div>
            ))}
            {(!analytics?.accounts_balance || analytics.accounts_balance.length === 0) && (
              <p className="text-xs text-slate-400 text-center py-4">Nenhuma conta cadastrada.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
