import React, { useState, useEffect } from 'react';
import {
  X,
  Type,
  DollarSign,
  Calendar as CalendarIcon,
  Tag,
  CheckCircle2,
  RefreshCw,
  FileText,
  Wallet,
  AlertCircle
} from 'lucide-react';
import { api } from '../../services/api';

export function NewCompromissoModal({ isOpen, onClose, onSuccess, initialCategories = [] }) {
  const [title, setTitle] = useState('');
  const [amount, setAmount] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [status, setStatus] = useState('PENDENTE');
  const [isRecurring, setIsRecurring] = useState(false);
  const [description, setDescription] = useState('');
  
  const [categories, setCategories] = useState(initialCategories);
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [showSuccessBanner, setShowSuccessBanner] = useState(false);

  useEffect(() => {
    if (isOpen) {
      // Carrega categorias de despesa e contas
      async function loadData() {
        try {
          const [cats, accs] = await Promise.all([
            api.categories.list('DESPESA'),
            api.accounts.list(),
          ]);
          setCategories(cats);
          setAccounts(accs);
          if (cats.length > 0) setCategoryId(cats[0].id);
          if (accs.length > 0) setSelectedAccount(accs[0].id);
        } catch (err) {
          console.error(err);
        }
      }
      loadData();
      
      // Data padrão: hoje formatada em YYYY-MM-DD
      const today = new Date().toISOString().split('T')[0];
      setDueDate(today);
      setErrorMsg('');
      setShowSuccessBanner(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (!title.trim()) {
      setErrorMsg('Por favor, informe o título do compromisso.');
      return;
    }
    const numAmount = parseFloat(amount.replace(',', '.'));
    if (isNaN(numAmount) || numAmount <= 0) {
      setErrorMsg('O valor deve ser maior que zero (RN02).');
      return;
    }
    if (!dueDate) {
      setErrorMsg('Por favor, informe a data de vencimento.');
      return;
    }
    if (!categoryId) {
      setErrorMsg('Por favor, selecione uma categoria.');
      return;
    }

    setLoading(true);
    try {
      if (isRecurring) {
        // Cadastra como regra de recorrência (RN09)
        const dueDay = parseInt(dueDate.split('-')[2], 10) || 10;
        await api.recurring.create({
          title: title.trim(),
          description: description.trim() || undefined,
          amount: numAmount,
          type: 'DESPESA',
          frequency: 'MENSAL',
          due_day: dueDay,
          start_date: dueDate,
          category_id: parseInt(categoryId, 10),
          account_id: selectedAccount ? parseInt(selectedAccount, 10) : undefined
        });
      } else {
        // Cadastra como transação de compromisso
        await api.transactions.create({
          title: title.trim(),
          description: description.trim() || undefined,
          amount: numAmount,
          date: dueDate,
          type: 'DESPESA',
          category_id: parseInt(categoryId, 10),
          account_id: selectedAccount ? parseInt(selectedAccount, 10) : undefined,
          status: status,
          payment_method: 'BOLETO'
        });
      }

      setShowSuccessBanner(true);
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1200);
    } catch (err) {
      setErrorMsg(err.message || 'Erro ao salvar compromisso.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/40 backdrop-blur-xs overflow-y-auto animate-fadeIn">
      <div className="bg-white rounded-3xl shadow-2xl max-w-lg w-full p-5 sm:p-7 relative border border-pink-100 my-auto">
        {/* Top Header Card */}
        <div className="flex items-start justify-between mb-5">
          <div className="flex items-start space-x-3">
            <div className="w-12 h-12 rounded-2xl bg-pink-50 border border-pink-100 flex items-center justify-center text-[#D83A6F] shrink-0 mt-0.5">
              <CalendarIcon className="w-6 h-6 stroke-[1.8]" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900 tracking-tight">
                Novo Compromisso
              </h2>
              <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">
                Cadastre aqui suas contas e compromissos financeiros para manter suas finanças em dia.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Success Banner */}
        {showSuccessBanner && (
          <div className="mb-4 p-3.5 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 flex items-center space-x-3 animate-fadeIn">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <div className="text-xs">
              <div className="font-bold">Compromisso cadastrado com sucesso!</div>
              <div className="text-emerald-700">O compromisso foi adicionado à sua lista.</div>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {errorMsg && (
          <div className="mb-4 p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 flex items-center space-x-3 text-xs">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Form Formatted identically to Mockups */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Título */}
          <div className="flex items-start space-x-3">
            <div className="w-10 h-10 rounded-full bg-pink-50 flex items-center justify-center text-[#D83A6F] font-bold text-sm shrink-0 mt-1">
              T
            </div>
            <div className="flex-1">
              <div className="flex justify-between items-center mb-1">
                <label className="text-xs font-semibold text-slate-700">Título *</label>
                <span className="text-[10px] text-slate-400">{title.length}/50</span>
              </div>
              <input
                type="text"
                maxLength={50}
                placeholder="Ex.: Conta de luz, Aluguel, Internet..."
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-[#D83A6F] focus:ring-2 focus:ring-pink-100 text-sm outline-none transition-all placeholder:text-slate-400"
                required
              />
            </div>
          </div>

          {/* Valor */}
          <div className="flex items-start space-x-3">
            <div className="w-10 h-10 rounded-full bg-pink-50 flex items-center justify-center text-[#D83A6F] shrink-0 mt-1">
              <DollarSign className="w-4 h-4 stroke-[2.5]" />
            </div>
            <div className="flex-1">
              <label className="block text-xs font-semibold text-slate-700 mb-1">Valor *</label>
              <div className="relative">
                <span className="absolute left-3.5 top-2.5 text-xs font-bold text-slate-400">R$</span>
                <input
                  type="text"
                  inputMode="decimal"
                  placeholder="0,00"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-[#D83A6F] focus:ring-2 focus:ring-pink-100 text-sm outline-none transition-all font-semibold text-slate-800"
                  required
                />
              </div>
            </div>
          </div>

          {/* Vencimento */}
          <div className="flex items-start space-x-3">
            <div className="w-10 h-10 rounded-full bg-pink-50 flex items-center justify-center text-[#D83A6F] shrink-0 mt-1">
              <CalendarIcon className="w-4 h-4" />
            </div>
            <div className="flex-1">
              <label className="block text-xs font-semibold text-slate-700 mb-1">Vencimento *</label>
              <input
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-[#D83A6F] focus:ring-2 focus:ring-pink-100 text-sm outline-none transition-all text-slate-800"
                required
              />
            </div>
          </div>

          {/* Categoria */}
          <div className="flex items-start space-x-3">
            <div className="w-10 h-10 rounded-full bg-pink-50 flex items-center justify-center text-[#D83A6F] shrink-0 mt-1">
              <Tag className="w-4 h-4" />
            </div>
            <div className="flex-1">
              <label className="block text-xs font-semibold text-slate-700 mb-1">Categoria *</label>
              <select
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-[#D83A6F] focus:ring-2 focus:ring-pink-100 text-sm outline-none transition-all bg-white text-slate-800"
                required
              >
                <option value="">Selecione uma categoria</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Status */}
          <div className="flex items-start space-x-3">
            <div className="w-10 h-10 rounded-full bg-pink-50 flex items-center justify-center text-[#D83A6F] shrink-0 mt-1">
              <CheckCircle2 className="w-4 h-4" />
            </div>
            <div className="flex-1">
              <label className="block text-xs font-semibold text-slate-700 mb-1">Status *</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-[#D83A6F] focus:ring-2 focus:ring-pink-100 text-sm outline-none transition-all bg-white text-slate-800"
              >
                <option value="PENDENTE">Pendente</option>
                <option value="PAGA">Pago</option>
                <option value="ATRASADA">Atrasado</option>
              </select>
            </div>
          </div>

          {/* Recorrente? (Toggle Pills matching mockup) */}
          <div className="flex items-start space-x-3">
            <div className="w-10 h-10 rounded-full bg-pink-50 flex items-center justify-center text-[#D83A6F] shrink-0 mt-1">
              <RefreshCw className="w-4 h-4" />
            </div>
            <div className="flex-1">
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">Recorrente?</label>
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => setIsRecurring(false)}
                  className={`flex-1 py-2 rounded-xl text-xs font-bold transition-all ${
                    !isRecurring
                      ? 'bg-[#D83A6F] text-white shadow-xs'
                      : 'bg-white border border-pink-200 text-slate-600 hover:bg-pink-50'
                  }`}
                >
                  Não
                </button>
                <button
                  type="button"
                  onClick={() => setIsRecurring(true)}
                  className={`flex-1 py-2 rounded-xl text-xs font-bold transition-all ${
                    isRecurring
                      ? 'bg-[#D83A6F] text-white shadow-xs'
                      : 'bg-white border border-pink-200 text-slate-600 hover:bg-pink-50'
                  }`}
                >
                  Sim
                </button>
              </div>
            </div>
          </div>

          {/* Conta Vinculada */}
          {accounts.length > 0 && (
            <div className="flex items-start space-x-3">
              <div className="w-10 h-10 rounded-full bg-pink-50 flex items-center justify-center text-[#D83A6F] shrink-0 mt-1">
                <Wallet className="w-4 h-4" />
              </div>
              <div className="flex-1">
                <label className="block text-xs font-semibold text-slate-700 mb-1">Conta Financeira</label>
                <select
                  value={selectedAccount}
                  onChange={(e) => setSelectedAccount(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-[#D83A6F] focus:ring-2 focus:ring-pink-100 text-sm outline-none transition-all bg-white text-slate-800"
                >
                  <option value="">Nenhuma / Definir depois</option>
                  {accounts.map((acc) => (
                    <option key={acc.id} value={acc.id}>
                      {acc.name} ({acc.type})
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}

          {/* Descrição */}
          <div className="flex items-start space-x-3">
            <div className="w-10 h-10 rounded-full bg-pink-50 flex items-center justify-center text-[#D83A6F] shrink-0 mt-1">
              <FileText className="w-4 h-4" />
            </div>
            <div className="flex-1">
              <div className="flex justify-between items-center mb-1">
                <label className="text-xs font-semibold text-slate-700">Descrição (opcional)</label>
                <span className="text-[10px] text-slate-400">{description.length}/200</span>
              </div>
              <textarea
                maxLength={200}
                rows={2}
                placeholder="Ex.: Conta de internet, aluguel residencial..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-3.5 py-2 rounded-xl border border-slate-200 focus:border-[#D83A6F] focus:ring-2 focus:ring-pink-100 text-sm outline-none transition-all placeholder:text-slate-400 resize-none"
              />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="pt-2 space-y-2 sm:space-y-0 sm:flex sm:space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="w-full sm:w-1/3 py-3 rounded-2xl border border-pink-200 text-[#D83A6F] font-bold text-sm hover:bg-pink-50 transition-all active:scale-98"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="w-full sm:w-2/3 py-3 rounded-2xl bg-[#D83A6F] hover:bg-[#C22A5E] text-white font-bold text-sm shadow-md shadow-pink-200 transition-all active:scale-98 flex items-center justify-center space-x-2 disabled:opacity-70"
            >
              <Wallet className="w-4 h-4" />
              <span>{loading ? 'Cadastrando...' : 'Cadastrar compromisso'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
