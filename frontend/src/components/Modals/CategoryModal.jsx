import React, { useState, useEffect } from 'react';
import { X, Tag, AlertCircle } from 'lucide-react';
import { api } from '../../services/api';

export function CategoryModal({ isOpen, onClose, onSuccess, type = 'DESPESA' }) {
  const [name, setName] = useState('');
  const [icon, setIcon] = useState('Tag');
  const [color, setColor] = useState('#D83A6F');
  const [categoryType, setCategoryType] = useState(type);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (isOpen) {
      setName('');
      setIcon('Tag');
      setColor(type === 'RECEITA' ? '#10B981' : '#D83A6F');
      setCategoryType(type);
      setErrorMsg('');
    }
  }, [isOpen, type]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (!name.trim()) {
      setErrorMsg('Informe o nome da categoria.');
      return;
    }

    setLoading(true);
    try {
      await api.categories.create({
        name: name.trim(),
        icon,
        color,
        type: categoryType,
      });
      onSuccess();
      onClose();
    } catch (err) {
      setErrorMsg(err.message || 'Erro ao criar categoria.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-fadeIn">
      <div className="bg-white rounded-3xl shadow-2xl max-w-md w-full p-6 relative border border-slate-100">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-pink-50 text-[#D83A6F] flex items-center justify-center">
              <Tag className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-800">Nova Categoria</h3>
              <p className="text-[11px] text-slate-500">Personalize a organização dos seus lançamentos.</p>
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
            <label className="block text-xs font-semibold text-slate-700 mb-1">Nome da Categoria *</label>
            <input
              type="text"
              placeholder="Ex.: Pet Shop, Cursos, Farmácia..."
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-[#D83A6F] focus:ring-2 focus:ring-pink-100 text-sm outline-none font-medium"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Tipo de Lançamento</label>
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={() => setCategoryType('DESPESA')}
                className={`flex-1 py-2 rounded-xl text-xs font-bold transition-all ${
                  categoryType === 'DESPESA' ? 'bg-[#D83A6F] text-white' : 'bg-slate-100 text-slate-600'
                }`}
              >
                Despesa
              </button>
              <button
                type="button"
                onClick={() => setCategoryType('RECEITA')}
                className={`flex-1 py-2 rounded-xl text-xs font-bold transition-all ${
                  categoryType === 'RECEITA' ? 'bg-emerald-600 text-white' : 'bg-slate-100 text-slate-600'
                }`}
              >
                Receita
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">Cor</label>
            <div className="flex items-center space-x-2">
              {['#D83A6F', '#E04D74', '#F97316', '#F59E0B', '#10B981', '#06B6D4', '#3B82F6', '#8B5CF6', '#1E293B'].map((c) => (
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
              className="w-2/3 py-2.5 rounded-xl bg-[#D83A6F] hover:bg-[#C22A5E] text-white font-bold text-xs shadow-md shadow-pink-200 transition-all flex items-center justify-center"
            >
              {loading ? 'Criando...' : 'Criar Categoria'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
