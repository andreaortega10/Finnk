import React, { useState, useEffect } from 'react';
import { History, Download, ShieldCheck, Filter, ArrowUpRight, ArrowDownLeft, Trash2, Edit2, PlusCircle } from 'lucide-react';
import { api } from '../services/api';
import { formatDate } from '../utils/helpers';

export function HistoricoPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await api.user.getAuditLogs();
      setLogs(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleExportLGPD = async () => {
    try {
      setExporting(true);
      const data = await api.user.exportData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `finnk_dados_pessoais_lgpd_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(err.message || 'Erro ao exportar dados.');
    } finally {
      setExporting(false);
    }
  };

  const getActionBadge = (action) => {
    switch (action) {
      case 'CREATE':
        return <span className="pastel-badge bg-emerald-50 text-emerald-700">Criação</span>;
      case 'UPDATE':
        return <span className="pastel-badge bg-blue-50 text-blue-700">Atualização</span>;
      case 'DELETE':
      case 'DELETE_ALL':
      case 'DELETE_FUTURE_ONLY':
        return <span className="pastel-badge bg-rose-50 text-rose-700">Exclusão</span>;
      case 'STATUS_CHANGE':
        return <span className="pastel-badge bg-purple-50 text-purple-700">Status</span>;
      default:
        return <span className="pastel-badge bg-slate-100 text-slate-700">{action}</span>;
    }
  };

  return (
    <div className="space-y-6 pb-20 md:pb-8 px-4 sm:px-6 max-w-5xl mx-auto animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">Histórico Financeiro & Auditoria</h2>
          <p className="text-xs text-slate-500">
            Rastreabilidade de todas as operações financeiras e conformidade com a LGPD (RNF04, RNF10).
          </p>
        </div>

        <button
          onClick={handleExportLGPD}
          disabled={exporting}
          className="flex items-center space-x-2 px-4 py-2.5 rounded-2xl bg-white border border-slate-200 text-slate-700 hover:text-[#D83A6F] hover:border-pink-200 font-bold text-xs shadow-2xs transition-all active:scale-95"
        >
          <Download className="w-4 h-4" />
          <span>{exporting ? 'Exportando...' : 'Exportar Dados (LGPD)'}</span>
        </button>
      </div>

      {/* Logs Card */}
      <div className="pastel-card rounded-3xl p-5 sm:p-6 space-y-3">
        <div className="flex items-center space-x-2 pb-3 border-b border-slate-100">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Log de Operações e Modificações</h3>
        </div>

        <div className="divide-y divide-slate-100">
          {logs.map((log) => (
            <div key={log.id} className="py-3 flex items-center justify-between text-xs">
              <div className="flex items-center space-x-3 min-w-0">
                <div className="w-8 h-8 rounded-xl bg-slate-100 flex items-center justify-center font-bold text-slate-500 text-[10px]">
                  {log.entity_type?.slice(0, 3)}
                </div>
                <div className="min-w-0">
                  <div className="font-bold text-slate-800 flex items-center space-x-2 truncate">
                    <span>{log.entity_type} #{log.entity_id}</span>
                    {getActionBadge(log.action)}
                  </div>
                  {log.details_json && (
                    <div className="text-[11px] text-slate-400 font-mono truncate max-w-md">
                      {log.details_json}
                    </div>
                  )}
                </div>
              </div>

              <span className="text-[10px] text-slate-400 font-medium shrink-0">
                {new Date(log.created_at).toLocaleString('pt-BR')}
              </span>
            </div>
          ))}
          {logs.length === 0 && (
            <div className="text-center py-12 text-slate-400 text-xs">
              Nenhum registro de auditoria registrado ainda.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
