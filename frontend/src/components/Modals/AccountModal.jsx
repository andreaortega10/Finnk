import React, { useState, useEffect } from 'react';
import { X, Landmark, DollarSign, AlertCircle } from 'lucide-react';
import { api } from '../../services/api';

export function AccountModal({ isOpen, onClose, onSuccess, editAccount = null }) {
  const [name, setName] = useState('');
  const [type, setType] = useState('CORRENTE');
  const [initialBalance, setInitialBalance] = useState('');
  const [color, setColor] = useState('#3B82F6');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (isOpen) {
      if (editAccount) {
        setName(editAccount.name);
        setType(editAccount.type);
        setInitialBalance(String(editAccount.initial_balance));
        setColor(editAccount.color || '#3B82F6');
      } else {
        setName('');
        setType('CORRENTE');
        setInitialBalance('0');
        setColor('#3B82F6');
      }
      setErrorMsg('');
    }
  }, [isOpen, editAccount]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (!name.trim()) {
      setErrorMsg('Informe o nome da conta.');
      return;
    }

    const numBalance = parseFloat(initialBalance.replace(',', '.')) || 0;

    setLoading(true);
    try {
      if (editAccount) {
        await api.accounts.update(editAccount.id, {
          name: name.trim(),
          type,
          color,
          initial_balance: numBalance,
        });
      } else {
        await api.accounts.create({
          name: name.trim(),
          type,
          color,
          initial_balance: numBalance,
        });
      }
      onSuccess();
      onClose();
    } catch (err) {
      setErrorMsg(err.message || 'Erro ao salvar conta.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-fadeIn">
      <div className="bg-white rounded-3xl shadow-2xl max-w-md w-full p-6 relative border border-slate-100">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center">
              <Landmark className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-800">
                {editAccount ? 'Editar Conta' : 'Nova Conta Financeira'}
              </h3>
              <p className="text-[11px] text-slate-500">Sem integração bancária (controle manual).</p>
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
            <label className="block text-xs font-semibold text-slate-700 mb-1">Nome da Conta *</label>
            <input
              type="text"
              placeholder="Ex.: Conta Corrente, Carteira, Poupança..."
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 text-sm outline-none font-medium"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Tipo</label>
              <select
                value={type}
                onChange={(e) => setType(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 text-sm outline-none bg-white font-medium"
              >
                <option value="CORRENTE">Conta Corrente</option>
                <option value="CARTEIRA">Carteira / Dinheiro</option>
                <option value="POUPANCA">Poupança</option>
                <option value="OUTROS">Outros</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Saldo Inicial</label>
              <div className="relative">
                <span className="absolute left-3 top-2.5 text-xs text-slate-400 font-bold">R$</span>
                <input
                  type="text"
                  placeholder="0,00"
                  value={initialBalance}
                  onChange={(e) => setInitialBalance(e.target.value)}
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-slate-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 text-sm outline-none font-bold"
                />
              </div>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">Cor da Conta</label>
            <div className="flex items-center space-x-2">
              {['#3B82F6', '#10B981', '#D83A6F', '#8B5CF6', '#F59E0B', '#1E293B'].map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setColor(c)}
                  style={{ backgroundColor: c }}
                  className={`w-7 h-7 rounded-full transition-transform ${
                    color === c ? 'scale-125 ring-2 ring-offset-2 ring-slate-400' : 'hover:scale-110'
                  }`}
                />
              ))}
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
              className="w-2/3 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-md shadow-blue-200 transition-all flex items-center justify-center"
            >
              {loading ? 'Salvando...' : 'Salvar Conta'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
