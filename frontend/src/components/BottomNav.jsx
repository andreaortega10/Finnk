import React from 'react';
import { Home, BarChart3, Calendar, CreditCard, ArrowLeftRight, Settings } from 'lucide-react';

export function BottomNav({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'inicio', label: 'Início', icon: Home },
    { id: 'dashboard', label: 'Análise Geral', icon: BarChart3 },
    { id: 'compromissos', label: 'Despesas', icon: Calendar, highlight: true },
    { id: 'cartoes', label: 'Cartões', icon: CreditCard },
    { id: 'transacoes', label: 'Transações', icon: ArrowLeftRight },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 bg-white/95 backdrop-blur-md border-t border-slate-100 shadow-lg px-2 py-1.5 md:hidden">
      <div className="grid grid-cols-5 items-end max-w-md mx-auto relative">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;

          if (item.highlight) {
            return (
              <div key={item.id} className="flex flex-col items-center justify-center relative -top-4">
                <button
                  type="button"
                  onClick={() => setActiveTab(item.id)}
                  aria-label={item.label}
                  className="flex flex-col items-center justify-center group focus:outline-none cursor-pointer"
                >
                  <div className={`w-13 h-13 rounded-full flex items-center justify-center shadow-lg transition-all transform active:scale-95 ${
                    isActive 
                      ? 'bg-[#D83A6F] text-white shadow-pink-300 ring-4 ring-pink-100' 
                      : 'bg-gradient-to-tr from-[#D83A6F] to-[#F472B6] text-white shadow-pink-200'
                  }`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <span className={`text-[11px] font-bold mt-1 text-center transition-colors ${
                    isActive ? 'text-[#D83A6F]' : 'text-slate-600'
                  }`}>
                    {item.label}
                  </span>
                </button>
              </div>
            );
          }

          return (
            <button
              key={item.id}
              type="button"
              onClick={() => setActiveTab(item.id)}
              className={`flex flex-col items-center justify-center py-1 px-1 rounded-xl transition-all min-h-[44px] cursor-pointer ${
                isActive ? 'text-[#D83A6F]' : 'text-slate-400 hover:text-slate-600'
              }`}
            >
              <Icon className={`w-5 h-5 ${isActive ? 'stroke-[2.5px]' : 'stroke-[1.8px]'}`} />
              <span className={`text-[10px] mt-0.5 text-center font-medium truncate w-full ${isActive ? 'font-bold text-[#D83A6F]' : 'text-slate-500'}`}>
                {item.label}
              </span>
              {isActive && (
                <div className="w-1.5 h-1.5 bg-[#D83A6F] rounded-full mt-0.5" />
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
