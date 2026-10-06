import React, { useState, useEffect } from 'react';
import {
  CreditCard as CardIcon,
  Plus,
  Layers,
  FileText,
  Calendar,
  AlertCircle,
  CheckCircle2,
  Trash2,
  ChevronRight,
  Sparkles
} from 'lucide-react';
import { api } from '../services/api';
import { formatCurrency, formatDate } from '../utils/helpers';
import { CardModal } from '../components/Modals/CardModal';
import { NewInstallmentModal } from '../components/Modals/NewInstallmentModal';

export function CartoesPage() {
  const [cards, setCards] = useState([]);
  const [selectedCard, setSelectedCard] = useState(null);
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [invoice, setInvoice] = useState(null);
  const [installments, setInstallments] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [isCardModalOpen, setIsCardModalOpen] = useState(false);
  const [cardToEdit, setCardToEdit] = useState(null);
  const [isInstallmentModalOpen, setIsInstallmentModalOpen] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [cardsList, instList] = await Promise.all([
        api.cards.list(),
        api.installments.list(),
      ]);
      setCards(cardsList);
      setInstallments(instList);

      const activeCard = selectedCard || cardsList[0];
      if (activeCard) {
        setSelectedCard(activeCard);
        const inv = await api.cards.getInvoices(activeCard.id, selectedMonth, selectedYear);
        setInvoice(inv);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedMonth, selectedYear]);

  const handleSelectCard = async (card) => {
    setSelectedCard(card);
    try {
      const inv = await api.cards.getInvoices(card.id, selectedMonth, selectedYear);
      setInvoice(inv);
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteCard = async (cardId) => {
    if (!window.confirm('Deseja realmente excluir este cartão?')) return;
    try {
      await api.cards.delete(cardId);
      setSelectedCard(null);
      loadData();
    } catch (err) {
      alert(err.message || 'Erro ao excluir cartão.');
    }
  };

  const handleDeleteInstallment = async (instId, paidCount) => {
    let mode = 'FUTURE_ONLY';
    let forcePaid = false;

    if (paidCount > 0) {
      const choice = window.confirm(
        `Este parcelamento já possui ${paidCount} parcela(s) paga(s).\n\nClique em OK para excluir APENAS as parcelas futuras pendentes (recomendado para preservar o histórico financeiro).\n\nOu clique em Cancelar e escolha exclusão total.`
      );
      if (!choice) {
        const forceChoice = window.confirm('Deseja realmente APAGAR TODO O HISTÓRICO deste parcelamento (inclusive parcelas pagas)?');
        if (!forceChoice) return;
        mode = 'ALL';
        forcePaid = true;
      }
    } else {
      if (!window.confirm('Deseja excluir este parcelamento?')) return;
      mode = 'ALL';
    }

    try {
      await api.installments.delete(instId, mode, forcePaid);
      loadData();
    } catch (err) {
      alert(err.message || 'Erro ao excluir parcelamento.');
    }
  };

  return (
    <div className="space-y-6 pb-20 md:pb-8 px-4 sm:px-6 max-w-5xl mx-auto animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">Cartões de Crédito & Faturas</h2>
          <p className="text-xs text-slate-500">Acompanhe limites, faturas e compras parceladas.</p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsCardModalOpen(true)}
            className="flex items-center space-x-2 px-3.5 py-2.5 rounded-2xl bg-white border border-slate-200 text-slate-700 hover:text-[#D83A6F] hover:border-pink-200 font-bold text-xs shadow-2xs transition-all active:scale-95"
          >
            <Plus className="w-4 h-4 stroke-[2.5]" />
            <span>Novo Cartão</span>
          </button>

          <button
            onClick={() => setIsInstallmentModalOpen(true)}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-2xl bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs shadow-md shadow-purple-200 transition-all active:scale-95"
          >
            <Layers className="w-4 h-4 stroke-[2.5]" />
            <span>Compra Parcelada</span>
          </button>
        </div>
      </div>

      {/* Visual Cards Carousel */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {cards.map((c) => {
          const isSelected = selectedCard?.id === c.id;
          const usedPct = c.limit_total > 0 ? (((c.limit_total - c.available_limit) / c.limit_total) * 100) : 0;

          return (
            <div
              key={c.id}
              onClick={() => handleSelectCard(c)}
              style={{ backgroundColor: c.color || '#820AD1' }}
              className={`rounded-3xl p-5 text-white shadow-lg relative cursor-pointer transition-all transform hover:-translate-y-1 ${
                isSelected ? 'ring-4 ring-pink-300 shadow-xl' : 'opacity-90'
              }`}
            >
              <div className="flex items-center justify-between mb-6">
                <div>
                  <span className="text-[10px] uppercase font-bold tracking-widest text-white/80">FINNK CARD</span>
                  <div className="text-lg font-black">{c.name}</div>
                </div>
                <div className="bg-white/20 backdrop-blur-md px-3 py-1 rounded-full text-xs font-bold uppercase">
                  {c.brand}
                </div>
              </div>

              <div className="font-mono text-sm tracking-widest text-white/90 mb-4">
                •••• •••• •••• {c.last_four_digits}
              </div>

              <div className="space-y-1.5 text-xs border-t border-white/20 pt-3">
                <div className="flex justify-between">
                  <span className="text-white/70">Limite Disponível:</span>
                  <span className="font-bold">{formatCurrency(c.available_limit)}</span>
                </div>
                <div className="w-full bg-white/20 h-1.5 rounded-full overflow-hidden">
                  <div style={{ width: `${Math.min(usedPct, 100)}%` }} className="bg-white h-full rounded-full" />
                </div>
                <div className="flex justify-between text-[10px] text-white/70 pt-0.5">
                  <span>Fechamento: dia {c.closing_day}</span>
                  <span>Vencimento: dia {c.due_day}</span>
                </div>
                {isSelected && (
                  <div className="flex justify-end space-x-2 pt-2 border-t border-white/10 mt-2">
                    <button
                      onClick={(e) => { e.stopPropagation(); setCardToEdit(c); setIsCardModalOpen(true); }}
                      className="px-2 py-1 bg-white/20 rounded-md text-white text-[10px] font-bold hover:bg-white/30"
                    >
                      EDITAR
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleDeleteCard(c.id); }}
                      className="px-2 py-1 bg-rose-500/80 rounded-md text-white text-[10px] font-bold hover:bg-rose-600/80"
                    >
                      EXCLUIR
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Invoice Section for Selected Card */}
      {selectedCard && invoice && (
        <div className="pastel-card rounded-3xl p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-100">
            <div>
              <span className="text-xs font-semibold text-slate-400">Fatura do Cartão</span>
              <div className="text-xl font-black text-slate-900">{selectedCard.name} (Final {selectedCard.last_four_digits})</div>
              <p className="text-xs text-slate-500">Vencimento: {formatDate(invoice.due_date?.toString())}</p>
            </div>

            <div className="text-right">
              <span className="text-xs font-semibold text-slate-400">Total da Fatura</span>
              <div className="text-2xl font-black text-slate-900">{formatCurrency(invoice.total_amount)}</div>
              <span className={`pastel-badge text-[10px] font-bold mt-1 ${
                invoice.status === 'PAGA' ? 'bg-emerald-50 text-emerald-700' : 'bg-pink-50 text-[#D83A6F]'
              }`}>
                Fatura {invoice.status}
              </span>
            </div>
          </div>

          {/* Invoice Items List */}
          <div className="pt-4">
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">Compras nesta fatura</h4>
            <div className="divide-y divide-slate-100">
              {invoice.items?.map((item) => (
                <div key={item.id} className="py-3 flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 rounded-full bg-pink-50 text-[#D83A6F] flex items-center justify-center font-bold">
                      <CardIcon className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="font-bold text-slate-800">{item.title}</div>
                      <div className="text-[11px] text-slate-400">{formatDate(item.date)} • {item.category_name}</div>
                    </div>
                  </div>
                  <div className="font-bold text-slate-900">
                    {formatCurrency(item.amount)}
                  </div>
                </div>
              ))}
              {(!invoice.items || invoice.items.length === 0) && (
                <p className="text-xs text-slate-400 text-center py-6">Nenhum gasto nesta fatura.</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Compras Parceladas Management Section */}
      <div className="pastel-card rounded-3xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Layers className="w-5 h-5 text-purple-600" />
            <h3 className="font-bold text-slate-800">Compras Parceladas Ativas</h3>
          </div>
          <span className="text-xs text-slate-400">{installments.length} compras</span>
        </div>

        <div className="space-y-4">
          {installments.map((inst) => {
            const pctPaid = inst.total_installments > 0 ? (inst.paid_count / inst.total_installments) * 100 : 0;
            return (
              <div key={inst.id} className="p-4 rounded-2xl bg-slate-50 border border-slate-100 space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="font-bold text-sm text-slate-900">{inst.title}</h4>
                    <p className="text-xs text-slate-500">
                      {inst.credit_card_name} • Compra em {formatDate(inst.purchase_date)}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="font-black text-sm text-slate-900">{formatCurrency(inst.total_amount)}</div>
                    <span className="text-xs font-bold text-purple-600">
                      {inst.paid_count}/{inst.total_installments} parcelas pagas
                    </span>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                  <div style={{ width: `${pctPaid}%` }} className="bg-purple-600 h-full rounded-full transition-all" />
                </div>

                <div className="flex items-center justify-between text-xs pt-1">
                  <span className="text-slate-500 font-medium">
                    Restante a pagar: <strong className="text-slate-800">{formatCurrency(inst.pending_amount)}</strong>
                  </span>
                  <button
                    onClick={() => handleDeleteInstallment(inst.id, inst.paid_count)}
                    className="text-xs font-semibold text-rose-600 hover:underline flex items-center space-x-1"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Excluir</span>
                  </button>
                </div>
              </div>
            );
          })}
          {installments.length === 0 && (
            <p className="text-xs text-slate-400 text-center py-6">Nenhuma compra parcelada registrada.</p>
          )}
        </div>
      </div>

      {/* Modals */}
      <CardModal
        isOpen={isCardModalOpen}
        onClose={() => { setIsCardModalOpen(false); setCardToEdit(null); }}
        onSuccess={loadData}
        editCard={cardToEdit}
      />
      <NewInstallmentModal
        isOpen={isInstallmentModalOpen}
        onClose={() => setIsInstallmentModalOpen(false)}
        onSuccess={loadData}
      />
    </div>
  );
}
