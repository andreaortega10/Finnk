import React, { useState, useEffect } from 'react';
import { X, ArrowDownLeft, DollarSign, Calendar, Tag, Wallet, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react';
import { api } from '../../services/api';

export function NewEntryModal({ isOpen, onClose, onSuccess }) {
  const [title, setTitle] = useState('');
  const [amount, setAmount] = useState('');
  const [date, setDate] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [accountId, setAccountId] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('PIX');
  const [isRecurring, setIsRecurring] = useState(false);
  const [description, setDescription] = useState('');

  const [categories, setCategories] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);

  useEffect(() => {
    if (isOpen) {
      async function load() {
        try {
          const [cats, accs] = await Promise.all([
            api.categories.list('RECEITA'),
            api.accounts.list(),
          ]);
          setCategories(cats);
          setAccounts(accs);
          if (cats.length > 0) setCategoryId(cats[0].id);
          if (accs.length > 0) setAccountId(accs[0].id);
        } catch (err) {
          console.error(err);
        }
      }
      load();
      setDate(new Date().toISOString().split('T')[0]);
      setErrorMsg('');
      setShowSuccess(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (!title.trim()) {
      setErrorMsg('Informe o título da entrada.');
      return;
    }
    const numAmount = parseFloat(amount.replace(',', '.'));
    if (isNaN(numAmount) || numAmount <= 0) {
      setErrorMsg('O valor da entrada deve ser maior que zero (RN02).');
      return;
    }
    if (!categoryId) {
      setErrorMsg('Selecione uma categoria de receita.');
      return;
    }

    setLoading(true);
    try {
      if (isRecurring) {
        const dueDay = parseInt(date.split('-')[2], 10) || 5;
        await api.recurring.create({
          title: title.trim(),
          description: description.trim() || undefined,
          amount: numAmount,
          type: 'RECEITA',
          frequency: 'MENSAL',
          due_day: dueDay,
          start_date: date,
          category_id: parseInt(categoryId, 10),
          account_id: accountId ? parseInt(accountId, 10) : undefined
        });
      } else {
        await api.transactions.create({
          title: title.trim(),
          description: description.trim() || undefined,
          amount: numAmount,
          date: date,
          type: 'RECEITA',
          category_id: parseInt(categoryId, 10),
          account_id: accountId ? parseInt(accountId, 10) : undefined,
          status: date > new Date().toISOString().split('T')[0] ? 'PENDENTE' : 'RECEBIDA',
          payment_method: paymentMethod
        });
      }

      setShowSuccess(true);
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1000);
    } catch (err) {
      setErrorMsg(err.message || 'Erro ao registrar entrada.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/40 backdrop-blur-xs overflow-y-auto animate-fadeIn">
      <div className="bg-white rounded-3xl shadow-2xl max-w-lg w-full p-5 sm:p-7 relative border border-emerald-100 my-auto">
        <div className="flex items-start justify-between mb-5">
          <div className="flex items-start space-x-3">
            <div className="w-12 h-12 rounded-2xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600 shrink-0">
              <ArrowDownLeft className="w-6 h-6 stroke-[2]" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900 tracking-tight">Nova Entrada</h2>
              <p className="text-xs text-slate-500 mt-0.5">Registre salários, vendas, prestação de serviços ou outras receitas.</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-full text-slate-400 hover:text-slate-700 hover:bg-slate-100">
            <X className="w-5 h-5" />
          </button>
        </div>

        {showSuccess && (
          <div className="mb-4 p-3.5 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 flex items-center space-x-3 text-xs font-bold">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <span>Entrada registrada com sucesso!</span>
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
            <label className="block text-xs font-semibold text-slate-700 mb-1">Título / Descrição *</label>
            <input
              type="text"
              placeholder="Ex.: Salário mensal, Freelance, Venda..."
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 text-sm outline-none font-medium"
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Valor *</label>
              <div className="relative">
                <span className="absolute left-3.5 top-2.5 text-xs font-bold text-slate-400">R$</span>
                <input
                  type="text"
                  inputMode="decimal"
                  placeholder="0,00"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 text-sm outline-none font-bold text-emerald-700"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Data de Recebimento *</label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 text-sm outline-none"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Categoria *</label>
              <select
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 text-sm outline-none bg-white"
                required
              >
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Forma de Recebimento</label>
              <select
                value={paymentMethod}
                onChange={(e) => setPaymentMethod(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 text-sm outline-none bg-white font-medium"
              >
                <option value="PIX">Pix</option>
                <option value="CARTAO">Cartão</option>
                <option value="DINHEIRO">Dinheiro</option>
                <option value="TRANSFERENCIA">Transferência</option>
                <option value="OUTRO">Outro</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Conta de Destino</label>
            <select
              value={accountId}
              onChange={(e) => setAccountId(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 text-sm outline-none bg-white"
            >
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>{a.name} ({a.type})</option>
              ))}
            </select>
          </div>

          {/* Recorrente Toggle */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">Receita Recorrente?</label>
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={() => setIsRecurring(false)}
                className={`flex-1 py-2 rounded-xl text-xs font-bold transition-all ${
                  !isRecurring ? 'bg-emerald-600 text-white shadow-xs' : 'bg-white border border-emerald-200 text-slate-600 hover:bg-emerald-50'
                }`}
              >
                Não
              </button>
              <button
                type="button"
                onClick={() => setIsRecurring(true)}
                className={`flex-1 py-2 rounded-xl text-xs font-bold transition-all ${
                  isRecurring ? 'bg-emerald-600 text-white shadow-xs' : 'bg-white border border-emerald-200 text-slate-600 hover:bg-emerald-50'
                }`}
              >
                Sim (Mensal)
              </button>
            </div>
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
              className="w-2/3 py-3 rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm shadow-md shadow-emerald-200 transition-all flex items-center justify-center space-x-2"
            >
              <span>{loading ? 'Salvando...' : 'Confirmar Entrada'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
