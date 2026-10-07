import React from 'react';
import { Book, CheckCircle2, Calendar, Target, DollarSign, Bell } from 'lucide-react';

export function HelpPage() {
  return (
    <div className="space-y-6 pb-20 md:pb-8 px-4 sm:px-6 max-w-5xl mx-auto animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">Como Utilizar o FINNK</h2>
          <p className="text-xs text-slate-500">Guia rápido para tirar o melhor proveito do organizador.</p>
        </div>
      </div>

      <div className="pastel-card rounded-3xl p-5 sm:p-6 space-y-6">
        <div className="flex items-start space-x-4">
          <div className="w-10 h-10 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
            <DollarSign className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-800">1. Registre as Contas</h3>
            <p className="text-sm text-slate-600 mt-1">
              Primeiro, vá em "Contas Financeiras" e cadastre onde seu dinheiro fica (conta corrente, carteira). 
              Em seguida, vá em "Cartões & Faturas" e cadastre seus cartões de crédito.
            </p>
          </div>
        </div>

        <div className="flex items-start space-x-4">
          <div className="w-10 h-10 rounded-full bg-pink-50 text-[#D83A6F] flex items-center justify-center shrink-0">
            <Calendar className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-800">2. Lançamentos</h3>
            <p className="text-sm text-slate-600 mt-1">
              Registre tudo o que entra (Receitas) e sai (Despesas) na aba de "Transações & Receitas" ou "Despesas".
              Use a opção de lançamentos recorrentes para contas fixas ou receitas que caem todo mês.
            </p>
          </div>
        </div>

        <div className="flex items-start space-x-4">
          <div className="w-10 h-10 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center shrink-0">
            <Target className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-800">3. Acompanhe a Análise Geral</h3>
            <p className="text-sm text-slate-600 mt-1">
              A Análise Geral mostrará resumos claros do seu dinheiro, como os maiores gastos por categoria 
              e projeção do saldo futuro.
            </p>
          </div>
        </div>

        <div className="flex items-start space-x-4">
          <div className="w-10 h-10 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
            <Bell className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-800">4. Alertas</h3>
            <p className="text-sm text-slate-600 mt-1">
              Fique de olho nos alertas no topo (sino) para ver quando uma conta está vencendo, estourando o limite, 
              ou atrasada.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
