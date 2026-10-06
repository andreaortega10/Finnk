import React, { useState, useEffect } from 'react';
import { X, Layers, CreditCard, DollarSign, Calendar, Tag, AlertCircle, CheckCircle2 } from 'lucide-react';
import { api } from '../../services/api';
import { formatCurrency } from '../../utils/helpers';

export function NewInstallmentModal({ isOpen, onClose, onSuccess }) {
  const [title, setTitle] = useState('');
  const [totalAmount, setTotalAmount] = useState('');
  const [purchaseDate, setPurchaseDate] = useState('');
  const [firstDueDate, setFirstDueDate] = useState('');
  const [totalInstallments, setTotalInstallments] = useState(3);
  const [cardId, setCardId] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [description, setDescription] = useState('');

  const [cards, setCards] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);

  useEffect(() => {
    if (isOpen) {
      async function load() {
        try {
          const [cList, catList] = await Promise.all([
            api.cards.list(),
            api.categories.list('DESPESA'),
          ]);
          setCards(cList);
          setCategories(catList);
          if (cList.length > 0) setCardId(cList[0].id);
          if (catList.length > 0) setCategoryId(catList[0].id);
        } catch (err) {
          console.error(err);
        }
      }
      load();
      const today = new Date().toISOString().split('T')[0];
      setPurchaseDate(today);
      setFirstDueDate(today);
      setErrorMsg('');
      setShowSuccess(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const numAmount = parseFloat(totalAmount.replace(',', '.')) || 0;
  const baseInstallment = totalInstallments > 0 ? (numAmount / totalInstallments) : 0;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (!title.trim()) {
      setErrorMsg('Informe o título da compra parcelada.');
      return;
    }
    if (numAmount <= 0) {
      setErrorMsg('O valor total deve ser maior que zero (RN02).');
      return;
    }
    if (!cardId) {
      setErrorMsg('Selecione o cartão de crédito.');
      return;
    }
    if (!categoryId) {
      setErrorMsg('Selecione uma categoria.');
      return;
    }

    setLoading(true);
    try {
      await api.installments.create({
        title: title.trim(),
        description: description.trim() || undefined,
        total_amount: numAmount,
        purchase_date: purchaseDate,
        first_due_date: firstDueDate,
        total_installments: parseInt(totalInstallments, 10),
        credit_card_id: parseInt(cardId, 10),
        category_id: parseInt(categoryId, 10),
      });

      setShowSuccess(true);
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1000);
    } catch (err) {
      setErrorMsg(err.message || 'Erro ao registrar compra parcelada.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/40 backdrop-blur-xs overflow-y-auto animate-fadeIn">
      <div className="bg-white rounded-3xl shadow-2xl max-w-lg w-full p-5 sm:p-7 relative border border-purple-100 my-auto">
        <div className="flex items-start justify-between mb-5">
          <div className="flex items-start space-x-3">
            <div className="w-12 h-12 rounded-2xl bg-purple-50 border border-purple-100 flex items-center justify-center text-purple-600 shrink-0">
              <Layers className="w-6 h-6 stroke-[1.8]" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900 tracking-tight">Nova Compra Parcelada</h2>
              <p className="text-xs text-slate-500 mt-0.5">Registre compras parceladas no cartão para acompanhamento das faturas e parcelas futuras.</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-full text-slate-400 hover:text-slate-700 hover:bg-slate-100">
            <X className="w-5 h-5" />
          </button>
        </div>

        {showSuccess && (
          <div className="mb-4 p-3.5 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 flex items-center space-x-3 text-xs font-bold">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <span>Compra parcelada e parcelas geradas com sucesso!</span>
          </div>
        )}

        {errorMsg && (
          <div className="mb-4 p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 flex items-center space-x-3 text-xs">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Título da Compra *</label>
            <input
              type="text"
              placeholder="Ex.: Smartphone, Notebook, Passagens..."
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-100 text-sm outline-none font-medium"
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Valor Total da Compra *</label>
              <div className="relative">
                <span className="absolute left-3.5 top-2.5 text-xs font-bold text-slate-400">R$</span>
                <input
                  type="text"
                  inputMode="decimal"
                  placeholder="0,00"
                  value={totalAmount}
                  onChange={(e) => setTotalAmount(e.target.value)}
                  className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-100 text-sm outline-none font-bold text-slate-800"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Número de Parcelas *</label>
              <select
                value={totalInstallments}
                onChange={(e) => setTotalInstallments(parseInt(e.target.value, 10))}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-100 text-sm outline-none bg-white font-bold text-purple-700"
              >
                {[2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 18, 24, 36, 48].map((n) => (
                  <option key={n} value={n}>{n}x parcelas</option>
                ))}
              </select>
            </div>
          </div>

          {/* Preview do Parcelamento */}
          {numAmount > 0 && (
            <div className="p-3.5 rounded-2xl bg-purple-50 border border-purple-100 flex items-center justify-between text-xs">
              <span className="font-semibold text-purple-900">Previsão das parcelas:</span>
              <span className="font-bold text-purple-700 text-sm">
                {totalInstallments}x de {formatCurrency(baseInstallment)}
              </span>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Cartão de Crédito *</label>
              <select
                value={cardId}
                onChange={(e) => setCardId(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-100 text-sm outline-none bg-white"
                required
              >
                {cards.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} (Final {c.last_four_digits})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Categoria *</label>
              <select
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-100 text-sm outline-none bg-white"
                required
              >
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Data da Compra *</label>
              <input
                type="date"
                value={purchaseDate}
                onChange={(e) => setPurchaseDate(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-100 text-sm outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">1ª Parcela (Vencimento) *</label>
              <input
                type="date"
                value={firstDueDate}
                onChange={(e) => setFirstDueDate(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-100 text-sm outline-none"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Observações (opcional)</label>
            <textarea
              rows={2}
              placeholder="Ex.: Garantia estendida, loja oficial..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3.5 py-2 rounded-xl border border-slate-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-100 text-sm outline-none resize-none"
            />
          </div>

          <div className="pt-2 flex space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="w-1/3 py-3 rounded-2xl border border-slate-200 text-slate-600 font-bold text-sm hover:bg-slate-50 transition-all"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="w-2/3 py-3 rounded-2xl bg-purple-600 hover:bg-purple-700 text-white font-bold text-sm shadow-md shadow-purple-200 transition-all flex items-center justify-center space-x-2"
            >
              <span>{loading ? 'Calculando parcelas...' : 'Gerar Parcelamento'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
