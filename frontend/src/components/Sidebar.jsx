import React from 'react';
import {
  Home,
  BarChart3,
  Calendar,
  CreditCard,
  ArrowLeftRight,
  PlusCircle,
  Clock,
  Layers,
  PieChart,
  Landmark,
  Tag,
  History,
  Bell,
  Settings,
  LogOut,
  ShieldCheck,
  HelpCircle
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export function Sidebar({ activeTab, setActiveTab }) {
  const { logout, user } = useAuth();

  const menuSections = [
    {
      title: 'Principal',
      items: [
        { id: 'inicio', label: 'Início', icon: Home },
        { id: 'dashboard', label: 'Análise Geral', icon: BarChart3 },
        { id: 'compromissos', label: 'Despesas', icon: Calendar },
        { id: 'cartoes', label: 'Cartões & Faturas', icon: CreditCard },
        { id: 'transacoes', label: 'Transações & Receitas', icon: ArrowLeftRight },
      ]
    },
    {
      title: 'Planejamento',
      items: [
        { id: 'parcelamentos', label: 'Compras Parceladas', icon: Layers },
        { id: 'recorrencias', label: 'Recorrências', icon: Clock },
        { id: 'orcamentos', label: 'Orçamentos', icon: PieChart },
      ]
    },
    {
      title: 'Organização',
      items: [
        { id: 'contas', label: 'Contas Financeiras', icon: Landmark },
        { id: 'categorias', label: 'Categorias', icon: Tag },
        { id: 'historico', label: 'Histórico & Auditoria', icon: History },
        { id: 'alertas', label: 'Central de Alertas', icon: Bell },
        { id: 'ajuda', label: 'Como Utilizar', icon: HelpCircle },
        { id: 'configuracoes', label: 'Configurações', icon: Settings },
      ]
    }
  ];

  return (
    <aside className="hidden md:flex flex-col w-64 bg-white border-r border-slate-100 h-screen sticky top-0 px-4 py-6 justify-between select-none">
      <div>
        {/* Brand Logo */}
        <div className="flex items-center space-x-3 px-3 mb-8">
          <img src="/icon.jpg" alt="FINNK Logo" className="w-10 h-10 rounded-xl object-cover shadow-md shadow-pink-200" />
          <div>
            <span className="text-xl font-black tracking-tight text-slate-800">FINNK</span>
            <span className="block text-[10px] uppercase tracking-wider font-semibold text-[#D83A6F]">
              Organizador Financeiro
            </span>
          </div>
        </div>

        {/* Navigation Sections */}
        <div className="space-y-6 overflow-y-auto max-h-[calc(100vh-220px)] pr-1">
          {menuSections.map((section, idx) => (
            <div key={idx}>
              <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider px-3 mb-2">
                {section.title}
              </h3>
              <div className="space-y-1">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = activeTab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => setActiveTab(item.id)}
                      className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl font-medium text-sm transition-all ${
                        isActive
                          ? 'bg-[#FFF0F4] text-[#D83A6F] font-bold shadow-xs'
                          : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                      }`}
                    >
                      <Icon className={`w-4 h-4 ${isActive ? 'stroke-[2.5px] text-[#D83A6F]' : 'stroke-[1.8px] text-slate-400'}`} />
                      <span>{item.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer / Logout */}
      <div className="pt-4 border-t border-slate-100">
        <button
          onClick={logout}
          className="w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-sm font-medium text-slate-500 hover:text-rose-600 hover:bg-rose-50 transition-colors"
        >
          <LogOut className="w-4 h-4 stroke-[1.8]" />
          <span>Sair da conta</span>
        </button>
      </div>
    </aside>
  );
}

