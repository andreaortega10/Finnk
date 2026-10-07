import React from 'react';
import {
  Home, BarChart3, Calendar, CreditCard, ArrowLeftRight,
  Clock, PieChart, Landmark, Tag, Bell, Settings, LogOut, X, HelpCircle
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export function Drawer({ isOpen, onClose, activeTab, setActiveTab }) {
  const { logout } = useAuth();

  const menuSections = [
    {
      title: 'Principal',
      items: [
        { id: 'inicio', label: 'Início', icon: Home },
        { id: 'dashboard', label: 'Análise Geral', icon: BarChart3 },
        { id: 'compromissos', label: 'Despesas', icon: Calendar },
        { id: 'transacoes', label: 'Transações', icon: ArrowLeftRight },
        { id: 'cartoes', label: 'Cartões', icon: CreditCard },
      ]
    },
    {
      title: 'Planejamento',
      items: [
        { id: 'recorrencias', label: 'Recorrências', icon: Clock },
        { id: 'orcamentos', label: 'Orçamentos', icon: PieChart },
      ]
    },
    {
      title: 'Organização',
      items: [
        { id: 'contas', label: 'Contas', icon: Landmark },
        { id: 'categorias', label: 'Categorias', icon: Tag },
        { id: 'ajuda', label: 'Como Utilizar', icon: HelpCircle },
      ]
    }
  ];

  const handleNav = (id) => {
    setActiveTab(id);
    onClose();
  };

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/40 z-40 transition-opacity"
          onClick={onClose}
        />
      )}

      {/* Drawer Panel */}
      <div 
        className={`fixed inset-y-0 left-0 w-72 bg-white shadow-2xl z-50 transform transition-transform duration-300 ease-in-out ${isOpen ? 'translate-x-0' : '-translate-x-full'} flex flex-col`}
      >
        <div className="flex items-center justify-between px-5 py-6 border-b border-slate-100">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#D83A6F] to-[#FB7185] flex items-center justify-center text-white font-black text-xl shadow-md shadow-pink-200">
              F
            </div>
            <div>
              <span className="text-xl font-black tracking-tight text-slate-800">FINNK</span>
            </div>
          </div>
          <button onClick={onClose} className="p-2 text-slate-400 hover:bg-slate-100 rounded-full">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-8">
          {menuSections.map((section, idx) => (
            <div key={idx}>
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider px-3 mb-3">
                {section.title}
              </h3>
              <div className="space-y-1">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = activeTab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => handleNav(item.id)}
                      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-2xl font-medium text-[15px] transition-all active:scale-95 ${
                        isActive
                          ? 'bg-[#FFF0F4] text-[#D83A6F] font-bold'
                          : 'text-slate-600 hover:bg-slate-50'
                      }`}
                    >
                      <Icon className={`w-5 h-5 ${isActive ? 'stroke-[2.5px] text-[#D83A6F]' : 'stroke-[1.8px] text-slate-400'}`} />
                      <span>{item.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        <div className="p-4 border-t border-slate-100">
          <button
            onClick={() => { handleNav('configuracoes'); }}
            className="w-full flex items-center space-x-3 px-4 py-3 rounded-2xl text-[15px] font-medium text-slate-600 hover:bg-slate-50 mb-2 active:scale-95"
          >
            <Settings className="w-5 h-5 stroke-[1.8] text-slate-400" />
            <span>Configurações</span>
          </button>
          <button
            onClick={logout}
            className="w-full flex items-center space-x-3 px-4 py-3 rounded-2xl text-[15px] font-medium text-rose-600 hover:bg-rose-50 active:scale-95"
          >
            <LogOut className="w-5 h-5 stroke-[1.8]" />
            <span>Sair da conta</span>
          </button>
        </div>
      </div>
    </>
  );
}
