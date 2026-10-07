import React, { useState, useEffect } from 'react';
import { X, CreditCard, DollarSign, AlertCircle } from 'lucide-react';
import { api } from '../../services/api';

export function CardModal({ isOpen, onClose, onSuccess, editCard = null }) {
  const [name, setName] = useState('');
  const [brand, setBrand] = useState('MASTERCARD');
  const [lastFour, setLastFour] = useState('');
  const [limitTotal, setLimitTotal] = useState('');
  const [closingDay, setClosingDay] = useState(5);
  const [dueDay, setDueDay] = useState(12);
  const [color, setColor] = useState('#820AD1');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (isOpen) {
      if (editCard) {
        setName(editCard.name);
        setBrand(editCard.brand);
        setLastFour(editCard.last_four_digits);
        setLimitTotal(String(editCard.limit_total));
        setClosingDay(editCard.closing_day);
        setDueDay(editCard.due_day);
        setColor(editCard.color || '#820AD1');
      } else {
        setName('');
        setBrand('NUBANK');
        setLastFour('');
        setLimitTotal('3000');
        setClosingDay(5);
        setDueDay(12);
        setColor('#820AD1');
      }
      setErrorMsg('');
    }
  }, [isOpen, editCard]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (!name.trim()) {
      setErrorMsg('Informe o nome/apelido do cartão.');
      return;
    }
    const numLimit = parseFloat(limitTotal.replace(',', '.'));
    if (isNaN(numLimit) || numLimit <= 0) {
      setErrorMsg('Informe um limite válido maior que zero.');
      return;
    }

    setLoading(true);
    try {
      if (editCard) {
        await api.cards.update(editCard.id, {
          name: name.trim(),
          brand,
          last_four_digits: lastFour.slice(-4),
          limit_total: numLimit,
          closing_day: parseInt(closingDay, 10),
          due_day: parseInt(dueDay, 10),
          color,
        });
      } else {
        await api.cards.create({
          name: name.trim(),
          brand,
          last_four_digits: lastFour.slice(-4),
          limit_total: numLimit,
          closing_day: parseInt(closingDay, 10),
          due_day: parseInt(dueDay, 10),
          color,
        });
      }
      onSuccess();
      onClose();
    } catch (err) {
      setErrorMsg(err.message || 'Erro ao salvar cartão.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-fadeIn">
      <div className="bg-white rounded-3xl shadow-2xl max-w-md w-full p-6 relative border border-slate-100">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-purple-50 text-purple-600 flex items-center justify-center">
              <CreditCard className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-800">
                {editCard ? 'Editar Cartão' : 'Novo Cartão de Crédito'}
              </h3>
              <p className="text-[11px] text-slate-500">Controle manual de faturas e compras.</p>
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
            <label className="block text-xs font-semibold text-slate-700 mb-1">Nome do Cartão *</label>
            <input
              type="text"
              placeholder="Ex.: Nubank Roxinho, Inter Black..."
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-100 text-sm outline-none font-medium"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Bandeira</label>
              <select
                value={brand}
                onChange={(e) => {
                  setBrand(e.target.value);
                  if (e.target.value === 'NUBANK') setColor('#820AD1');
                  else if (e.target.value === 'ELO') setColor('#1E293B');
                  else if (e.target.value === 'INTER') setColor('#FF7A00');
                  else if (e.target.value === 'MASTERCARD') setColor('#EB001B');
                }}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-100 text-sm outline-none bg-white font-medium"
              >
                <option value="NUBANK">Nubank</option>
                <option value="ELO">Elo</option>
                <option value="MASTERCARD">Mastercard</option>
                <option value="VISA">Visa</option>
                <option value="INTER">Inter</option>
                <option value="OUTROS">Outros</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Últimos 4 dígitos</label>
              <input
                type="text"
                maxLength={4}
                placeholder="4582"
                value={lastFour}
                onChange={(e) => setLastFour(e.target.value.replace(/\D/g, ''))}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-100 text-sm outline-none font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Limite Total *</label>
            <div className="relative">
              <span className="absolute left-3 top-2.5 text-xs text-slate-400 font-bold">R$</span>
              <input
                type="text"
                inputMode="decimal"
                placeholder="0,00"
                value={limitTotal}
                onChange={(e) => setLimitTotal(e.target.value)}
                className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-slate-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-100 text-sm outline-none font-bold"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Dia de Fechamento</label>
              <input
                type="number"
                min={1}
                max={31}
                value={closingDay}
                onChange={(e) => setClosingDay(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-100 text-sm outline-none font-bold text-center"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Dia de Vencimento</label>
              <input
                type="number"
                min={1}
                max={31}
                value={dueDay}
                onChange={(e) => setDueDay(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-100 text-sm outline-none font-bold text-center"
              />
            </div>
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
              className="w-2/3 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs shadow-md shadow-purple-200 transition-all flex items-center justify-center"
            >
              {loading ? 'Salvando...' : 'Salvar Cartão'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
