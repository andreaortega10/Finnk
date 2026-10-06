import React from 'react';
import { Bell, Settings, Menu } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export function Header({ onOpenAlerts, onOpenSettings, onOpenDrawer, unreadAlertsCount = 0 }) {
  const { user } = useAuth();

  const getInitials = (name) => {
    if (!name) return 'FN';
    const parts = name.trim().split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return parts[0].slice(0, 2).toUpperCase();
  };

  return (
    <header className="flex items-center justify-between py-4 px-4 sm:px-6 bg-transparent">
      {/* Left side (Menu + User Info) */}
      <div className="flex items-center space-x-3.5">
        <button
          onClick={onOpenDrawer}
          className="p-2 -ml-2 rounded-full bg-transparent text-slate-600 hover:bg-slate-100 transition-colors"
        >
          <Menu className="w-6 h-6" />
        </button>
        <div className="w-11 h-11 rounded-full bg-gradient-to-tr from-[#D83A6F] to-[#FB7185] flex items-center justify-center text-white font-bold text-base shadow-sm ring-2 ring-pink-100">
          {getInitials(user?.name)}
        </div>
        <div>
          <h1 className="text-xl font-bold text-slate-800 tracking-tight">
            Olá, {user?.name?.split(' ')[0] || 'Usuário'}!
          </h1>
          <p className="text-xs text-slate-500 font-normal">
            Aqui está o resumo da sua vida financeira.
          </p>
        </div>
      </div>

      {/* Top Actions */}
      <div className="flex items-center space-x-2">
        <button
          onClick={onOpenAlerts}
          className="relative p-2.5 rounded-full bg-white border border-slate-100 text-slate-600 hover:text-[#D83A6F] hover:border-pink-200 transition-all shadow-xs active:scale-95"
          title="Central de Alertas"
        >
          <Bell className="w-5 h-5 stroke-[1.8]" />
          {unreadAlertsCount > 0 && (
            <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-rose-500 rounded-full ring-2 ring-white animate-pulse" />
          )}
        </button>

        <button
          onClick={onOpenSettings}
          className="p-2.5 rounded-full bg-white border border-slate-100 text-slate-600 hover:text-[#D83A6F] hover:border-pink-200 transition-all shadow-xs active:scale-95"
          title="Configurações"
        >
          <Settings className="w-5 h-5 stroke-[1.8]" />
        </button>
      </div>
    </header>
  );
}
