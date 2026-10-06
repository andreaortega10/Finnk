import React from 'react';
import { Home, BarChart3, Calendar, CreditCard, ArrowLeftRight, Settings } from 'lucide-react';

export function BottomNav({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'inicio', label: 'Início', icon: Home },
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    { id: 'compromissos', label: 'Compromissos', icon: Calendar, highlight: true },
    { id: 'cartoes', label: 'Cartões', icon: CreditCard },
    { id: 'transacoes', label: 'Transações', icon: ArrowLeftRight },
    { id: 'configuracoes', label: 'Configurações', icon: Settings },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 bg-white/95 backdrop-blur-md border-t border-slate-100 shadow-lg px-2 py-1.5 md:hidden">
      <div className="flex items-center justify-around max-w-md mx-auto relative">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;

          if (item.highlight) {
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className="flex flex-col items-center justify-center -mt-6 group focus:outline-none"
              >
                <div className={`w-14 h-14 rounded-full flex items-center justify-center shadow-lg transition-all transform active:scale-95 ${
                  isActive 
                    ? 'bg-[#D83A6F] text-white shadow-pink-300 ring-4 ring-pink-100' 
                    : 'bg-gradient-to-tr from-[#D83A6F] to-[#F472B6] text-white shadow-pink-200'
                }`}>
                  <Icon className="w-6 h-6" />
                </div>
                <span className={`text-[11px] font-semibold mt-1 transition-colors ${
                  isActive ? 'text-[#D83A6F]' : 'text-slate-500'
                }`}>
                  {item.label}
                </span>
              </button>
            );
          }

          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex flex-col items-center justify-center py-1 px-2 rounded-xl transition-all ${
                isActive ? 'text-[#D83A6F]' : 'text-slate-400 hover:text-slate-600'
              }`}
            >
              <Icon className={`w-5 h-5 ${isActive ? 'stroke-[2.5px]' : 'stroke-[1.8px]'}`} />
              <span className={`text-[10px] mt-0.5 font-medium ${isActive ? 'font-semibold text-[#D83A6F]' : 'text-slate-500'}`}>
                {item.label}
              </span>
              {isActive && (
                <div className="w-1 h-1 bg-[#D83A6F] rounded-full mt-0.5" />
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
