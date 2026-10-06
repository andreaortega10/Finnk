import React, { useState, useEffect } from 'react';
import { Tag, Plus, Eye, EyeOff, Trash2, Lock, AlertCircle } from 'lucide-react';
import { api } from '../services/api';
import { getCategoryIcon } from '../utils/helpers';
import { CategoryModal } from '../components/Modals/CategoryModal';

export function CategoriasPage() {
  const [categories, setCategories] = useState([]);
  const [activeTab, setActiveTab] = useState('DESPESA'); // 'DESPESA' | 'RECEITA'
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await api.categories.list(activeTab, true);
      setCategories(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const handleToggleHide = async (cat) => {
    try {
      await api.categories.update(cat.id, { is_hidden: !cat.is_hidden });
      loadData();
    } catch (err) {
      alert(err.message || 'Erro ao alterar visibilidade.');
    }
  };

  const handleDelete = async (cat) => {
    if (cat.is_system_default) {
      alert('Categorias padrão do sistema não podem ser excluídas (RN13). Você pode ocultá-la.');
      return;
    }
    if (!window.confirm(`Deseja realmente excluir a categoria "${cat.name}"?`)) return;

    try {
      await api.categories.delete(cat.id);
      loadData();
    } catch (err) {
      alert(err.message || 'Erro ao excluir categoria.');
    }
  };

  return (
    <div className="space-y-6 pb-20 md:pb-8 px-4 sm:px-6 max-w-5xl mx-auto animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">Categorias</h2>
          <p className="text-xs text-slate-500">
            Categorias padrão protegidas pelo sistema (RN13) e categorias personalizadas.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center space-x-2 px-4 py-2.5 rounded-2xl bg-[#D83A6F] hover:bg-[#C22A5E] text-white font-bold text-xs shadow-md shadow-pink-200 transition-all active:scale-95"
        >
          <Plus className="w-4 h-4 stroke-[2.5]" />
          <span>Nova Categoria</span>
        </button>
      </div>

      {/* Tabs */}
      <div className="pastel-card rounded-3xl p-5 sm:p-6 space-y-4">
        <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
          <button
            onClick={() => setActiveTab('DESPESA')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'DESPESA' ? 'bg-[#D83A6F] text-white shadow-xs' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            Categorias de Despesas
          </button>
          <button
            onClick={() => setActiveTab('RECEITA')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'RECEITA' ? 'bg-emerald-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            Categorias de Receitas
          </button>
        </div>

        {/* Categories Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 pt-2">
          {categories.map((cat) => (
            <div
              key={cat.id}
              className={`p-4 rounded-2xl border transition-all flex items-center justify-between ${
                cat.is_hidden
                  ? 'bg-slate-50/50 border-slate-200 opacity-60'
                  : 'bg-white border-slate-100 shadow-2xs hover:border-pink-200'
              }`}
            >
              <div className="flex items-center space-x-3">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center text-white"
                  style={{ backgroundColor: cat.color || '#D83A6F' }}
                >
                  {getCategoryIcon(cat.icon || cat.name, "w-5 h-5")}
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-800 flex items-center space-x-1">
                    <span>{cat.name}</span>
                    {cat.is_system_default && (
                      <Lock className="w-3 h-3 text-slate-400" title="Categoria padrão do sistema" />
                    )}
                  </div>
                  <span className="text-[10px] text-slate-400">
                    {cat.is_system_default ? 'Padrão' : 'Personalizada'}
                  </span>
                </div>
              </div>

              <div className="flex items-center space-x-1">
                <button
                  onClick={() => handleToggleHide(cat)}
                  className="p-1.5 text-slate-400 hover:text-slate-700 transition-colors rounded-lg"
                  title={cat.is_hidden ? 'Exibir categoria' : 'Ocultar categoria'}
                >
                  {cat.is_hidden ? <EyeOff className="w-4 h-4 text-slate-400" /> : <Eye className="w-4 h-4" />}
                </button>

                {!cat.is_system_default && (
                  <button
                    onClick={() => handleDelete(cat)}
                    className="p-1.5 text-slate-300 hover:text-rose-600 transition-colors rounded-lg hover:bg-rose-50"
                    title="Excluir categoria"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Modal */}
      <CategoryModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={loadData}
        type={activeTab}
      />
    </div>
  );
}
