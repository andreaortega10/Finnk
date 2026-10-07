import React, { useState, useEffect } from 'react';
import {
  Calendar as CalendarIcon,
  List as ListIcon,
  Plus,
  Filter,
  CheckCircle2,
  Clock,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Trash2,
  Edit2,
  Tag,
  Search
} from 'lucide-react';
import { api } from '../services/api';
import { formatCurrency, formatDate, getCategoryIcon } from '../utils/helpers';
import { NewCompromissoModal } from '../components/Modals/NewCompromissoModal';

export function CompromissosPage({ initialFilter }) {
  const [viewMode, setViewMode] = useState('list'); // 'list' | 'calendar'
  const [commitments, setCommitments] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [statusFilter, setStatusFilter] = useState(initialFilter || '');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [txList, catList] = await Promise.all([
        api.transactions.list({
          is_compromisso: true,
          month: selectedMonth,
          year: selectedYear,
          status_filter: statusFilter || undefined,
          category_id: categoryFilter || undefined,
          search: searchTerm || undefined,
        }),
        api.categories.list('DESPESA'),
      ]);
      setCommitments(txList);
      setCategories(catList);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedMonth, selectedYear, statusFilter, categoryFilter, searchTerm]);

  const handlePrevMonth = () => {
    if (selectedMonth === 1) {
      setSelectedMonth(12);
      setSelectedYear(selectedYear - 1);
    } else {
      setSelectedMonth(selectedMonth - 1);
    }
  };

  const handleNextMonth = () => {
    if (selectedMonth === 12) {
      setSelectedMonth(1);
      setSelectedYear(selectedYear + 1);
    } else {
      setSelectedMonth(selectedMonth + 1);
    }
  };

  const handleToggleStatus = async (txId, currentStatus) => {
    try {
      const newStatus = currentStatus === 'PAGA' ? 'PENDENTE' : 'PAGA';
      await api.transactions.updateStatus(txId, newStatus);
      loadData();
    } catch (err) {
      alert(err.message || 'Erro ao alterar status.');
    }
  };

  const handleDelete = async (txId) => {
    if (!window.confirm('Deseja realmente excluir este compromisso?')) return;
    try {
      await api.transactions.delete(txId);
      loadData();
    } catch (err) {
      alert(err.message || 'Erro ao excluir compromisso.');
    }
  };

  const totalAmount = commitments.reduce((acc, curr) => acc + curr.amount, 0);
  const paidCount = commitments.filter(c => c.status === 'PAGA').length;
  const pendingCount = commitments.filter(c => c.status === 'PENDENTE').length;
  const overdueCount = commitments.filter(c => c.status === 'ATRASADA').length;

  return (
    <div className="space-y-5 pb-20 md:pb-8 px-4 sm:px-6 max-w-5xl mx-auto animate-fadeIn">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">Compromissos Financeiros</h2>
          <p className="text-xs text-slate-500">Acompanhe contas a pagar, parcelas e vencimentos.</p>
        </div>

        <div className="flex items-center space-x-2">
          {/* View Mode Toggle */}
          <div className="bg-slate-100 p-1 rounded-2xl flex items-center">
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded-xl text-xs font-bold transition-all ${
                viewMode === 'list' ? 'bg-white text-[#D83A6F] shadow-xs' : 'text-slate-500'
              }`}
              title="Visualização em Lista"
            >
              <ListIcon className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('calendar')}
              className={`p-2 rounded-xl text-xs font-bold transition-all ${
                viewMode === 'calendar' ? 'bg-white text-[#D83A6F] shadow-xs' : 'text-slate-500'
              }`}
              title="Visualização em Calendário"
            >
              <CalendarIcon className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-2xl bg-[#D83A6F] hover:bg-[#C22A5E] text-white font-bold text-xs shadow-md shadow-pink-200 transition-all active:scale-95"
          >
            <Plus className="w-4 h-4 stroke-[2.5]" />
            <span>Novo Compromisso</span>
          </button>
        </div>
      </div>

      {/* Month Navigator & Summary Bar */}
      <div className="pastel-card rounded-3xl p-5 sm:p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div className="flex items-center space-x-3">
            <button onClick={handlePrevMonth} className="p-1.5 rounded-xl border border-slate-200 text-slate-600 hover:text-[#D83A6F]">
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-base font-black text-slate-800 select-none">
              Mês {selectedMonth}/{selectedYear}
            </span>
            <button onClick={handleNextMonth} className="p-1.5 rounded-xl border border-slate-200 text-slate-600 hover:text-[#D83A6F]">
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <div className="flex items-center space-x-4 text-xs">
            <span className="font-semibold text-slate-500">Total: <strong className="text-slate-900 font-bold">{formatCurrency(totalAmount)}</strong></span>
            <span className="text-emerald-600 font-semibold">{paidCount} pagos</span>
            <span className="text-amber-500 font-semibold">{pendingCount} pendentes</span>
            {overdueCount > 0 && <span className="text-rose-600 font-bold">{overdueCount} atrasados</span>}
          </div>
        </div>

        {/* Filter Toolbar */}
        <div className="flex flex-wrap items-center gap-3 pt-4">
          <div className="relative flex-1 min-w-[180px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Buscar compromisso..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3.5 py-2 rounded-xl border border-slate-200 focus:border-[#D83A6F] focus:ring-2 focus:ring-pink-100 text-xs outline-none bg-slate-50/50"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 rounded-xl border border-slate-200 focus:border-[#D83A6F] text-xs outline-none bg-white font-medium text-slate-700"
          >
            <option value="">Todos os status</option>
            <option value="PENDENTE">Pendentes</option>
            <option value="PAGA">Pagos</option>
            <option value="ATRASADA">Atrasados</option>
          </select>

          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-3 py-2 rounded-xl border border-slate-200 focus:border-[#D83A6F] text-xs outline-none bg-white font-medium text-slate-700"
          >
            <option value="">Todas as categorias</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* List View */}
      {viewMode === 'list' && (
        <div className="pastel-card rounded-3xl p-5 sm:p-6">
          <div className="divide-y divide-slate-100">
            {commitments.map((item) => (
              <div key={item.id} className="py-3.5 flex items-center justify-between gap-3 group hover:bg-slate-50/60 px-3 rounded-2xl transition-colors">
                <div className="flex items-center space-x-3.5 min-w-0">
                  <div className="w-10 h-10 rounded-2xl bg-pink-50 text-[#D83A6F] flex items-center justify-center shrink-0">
                    {getCategoryIcon(item.category_icon || item.category_name, "w-5 h-5")}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-bold text-slate-800 break-words whitespace-normal line-clamp-2">
                      {item.title}
                      {item.is_installment && (
                        <span className="inline-block ml-2 text-[10px] font-bold bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full align-middle">
                          {item.installment_number}/{item.total_installments}
                        </span>
                      )}
                      {item.is_recurring && (
                        <span className="inline-block ml-2 text-[10px] font-bold bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full align-middle">
                          Recorrente
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-slate-400 mt-0.5 flex items-center space-x-2">
                      <span>Vencimento: {formatDate(item.date)}</span>
                      {item.account_name && <span>• {item.account_name}</span>}
                      {item.credit_card_name && <span>• {item.credit_card_name}</span>}
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-3 shrink-0">
                  <span className="text-sm font-black text-slate-900">
                    {formatCurrency(item.amount)}
                  </span>
                  <button
                    onClick={() => handleToggleStatus(item.id, item.status)}
                    className={`pastel-badge text-xs font-bold cursor-pointer transition-all active:scale-95 ${
                      item.status === 'PAGA'
                        ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
                        : item.status === 'ATRASADA'
                        ? 'bg-rose-50 text-rose-700 hover:bg-rose-100'
                        : 'bg-amber-50 text-amber-700 hover:bg-amber-100'
                    }`}
                  >
                    {item.status === 'PAGA' ? 'Pago' : item.status === 'ATRASADA' ? 'Atrasado' : 'Pendente'}
                  </button>

                  <button
                    onClick={() => handleDelete(item.id)}
                    className="p-1.5 text-slate-300 hover:text-rose-600 transition-colors rounded-lg hover:bg-rose-50"
                    title="Excluir"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
            {commitments.length === 0 && (
              <div className="text-center py-12">
                <CalendarIcon className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                <p className="text-sm font-semibold text-slate-600">Sem compromissos por enquanto. Aproveite a folga ou cadastre uma despesa!</p>
                <p className="text-xs text-slate-400 mt-0.5">Cadastre suas contas e parcelas para manter tudo sob controle.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Calendar View */}
      {viewMode === 'calendar' && (
        <div className="pastel-card rounded-3xl p-5 sm:p-6">
          <div className="grid grid-cols-7 gap-1 text-center font-bold text-xs text-slate-400 mb-2">
            <div>Dom</div><div>Seg</div><div>Ter</div><div>Qua</div><div>Qui</div><div>Sex</div><div>Sáb</div>
          </div>
          <div className="grid grid-cols-7 gap-1.5">
            {Array.from({ length: 35 }).map((_, idx) => {
              const dayNum = idx + 1;
              if (dayNum > 31) return <div key={idx} className="h-20 bg-slate-50/40 rounded-xl" />;
              
              const dayStr = `${selectedYear}-${String(selectedMonth).padStart(2, '0')}-${String(dayNum).padStart(2, '0')}`;
              const dayItems = commitments.filter(c => c.date === dayStr);

              return (
                <div key={idx} className="min-h-20 p-1.5 rounded-xl border border-slate-100 bg-white hover:border-pink-200 transition-all flex flex-col justify-between">
                  <span className="text-[11px] font-bold text-slate-600">{dayNum}</span>
                  <div className="space-y-1 overflow-hidden">
                    {dayItems.slice(0, 2).map(item => (
                      <div
                        key={item.id}
                        onClick={() => handleToggleStatus(item.id, item.status)}
                        className={`text-[9px] font-semibold truncate px-1 py-0.5 rounded cursor-pointer ${
                          item.status === 'PAGA' ? 'bg-emerald-100 text-emerald-800' : 'bg-pink-100 text-[#D83A6F]'
                        }`}
                        title={`${item.title} - ${formatCurrency(item.amount)} (${item.status})`}
                      >
                        {item.title}
                      </div>
                    ))}
                    {dayItems.length > 2 && (
                      <span className="text-[8px] font-bold text-slate-400">+{dayItems.length - 2} mais</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Modal */}
      <NewCompromissoModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={loadData}
        initialCategories={categories}
      />
    </div>
  );
}
