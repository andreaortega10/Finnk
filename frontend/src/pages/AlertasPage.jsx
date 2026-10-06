import React, { useState, useEffect } from 'react';
import { Bell, CheckCheck, Trash2, Calendar, AlertTriangle, Clock, ShieldAlert } from 'lucide-react';
import { api } from '../services/api';
import { formatDate } from '../utils/helpers';

export function AlertasPage() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await api.alerts.list();
      setAlerts(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleMarkRead = async (id) => {
    try {
      await api.alerts.markRead(id);
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.alerts.markAllRead();
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.alerts.delete(id);
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const getAlertIcon = (type) => {
    switch (type) {
      case 'VENCIMENTO_PROXIMO':
        return <Calendar className="w-5 h-5 text-indigo-500" />;
      case 'COMPROMISSO_VENCIDO':
        return <AlertTriangle className="w-5 h-5 text-rose-500" />;
      case 'ORCAMENTO_ATINGIDO':
      case 'ORCAMENTO_ULTRAPASSADO':
        return <ShieldAlert className="w-5 h-5 text-amber-500" />;
      default:
        return <Bell className="w-5 h-5 text-pink-500" />;
    }
  };

  return (
    <div className="space-y-6 pb-20 md:pb-8 px-4 sm:px-6 max-w-5xl mx-auto animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">Central de Alertas & Notificações</h2>
          <p className="text-xs text-slate-500">
            Avisos preventivos de vencimentos (3 e 1 dia antes), pendências atrasadas e limites de orçamento.
          </p>
        </div>

        {alerts.some(a => !a.is_read) && (
          <button
            onClick={handleMarkAllRead}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-2xl bg-white border border-slate-200 text-slate-700 hover:text-[#D83A6F] font-bold text-xs shadow-2xs transition-all active:scale-95"
          >
            <CheckCheck className="w-4 h-4" />
            <span>Marcar todos como lidos</span>
          </button>
        )}
      </div>

      {/* Alerts List */}
      <div className="pastel-card rounded-3xl p-5 sm:p-6 space-y-3">
        {alerts.map((a) => (
          <div
            key={a.id}
            className={`p-4 rounded-2xl border transition-all flex items-start justify-between gap-4 ${
              !a.is_read
                ? 'bg-pink-50/40 border-pink-100 shadow-2xs'
                : 'bg-white border-slate-100 opacity-80'
            }`}
          >
            <div className="flex items-start space-x-3.5">
              <div className="w-10 h-10 rounded-2xl bg-white border border-slate-100 flex items-center justify-center shrink-0 shadow-2xs">
                {getAlertIcon(a.type)}
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-900">{a.title}</h4>
                <p className="text-xs text-slate-600 mt-0.5 leading-relaxed">{a.message}</p>
                <span className="text-[10px] text-slate-400 mt-1 block">
                  {new Date(a.created_at).toLocaleString('pt-BR')}
                </span>
              </div>
            </div>

            <div className="flex items-center space-x-1 shrink-0">
              {!a.is_read && (
                <button
                  onClick={() => handleMarkRead(a.id)}
                  className="px-2.5 py-1 rounded-xl bg-white border border-pink-200 text-[#D83A6F] font-bold text-[11px] hover:bg-pink-50 transition-all shadow-2xs"
                >
                  Lido
                </button>
              )}
              <button
                onClick={() => handleDelete(a.id)}
                className="p-1.5 text-slate-300 hover:text-rose-600 transition-colors rounded-lg hover:bg-rose-50"
                title="Excluir Alerta"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}

        {alerts.length === 0 && (
          <div className="text-center py-12">
            <Bell className="w-10 h-10 text-slate-300 mx-auto mb-2" />
            <p className="text-sm font-semibold text-slate-600">Nenhum alerta no momento.</p>
            <p className="text-xs text-slate-400 mt-0.5">Suas notificações de vencimento e orçamentos aparecerão aqui.</p>
          </div>
        )}
      </div>
    </div>
  );
}
