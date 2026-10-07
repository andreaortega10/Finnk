import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Header } from './components/Header';
import { BottomNav } from './components/BottomNav';
import { Drawer } from './components/Drawer';
import { HomePage } from './pages/HomePage';
import { DashboardPage } from './pages/DashboardPage';
import { CompromissosPage } from './pages/CompromissosPage';
import { CartoesPage } from './pages/CartoesPage';
import { TransacoesPage } from './pages/TransacoesPage';
import { RecorrenciasPage } from './pages/RecorrenciasPage';
import { OrcamentosPage } from './pages/OrcamentosPage';
import { ContasPage } from './pages/ContasPage';
import { CategoriasPage } from './pages/CategoriasPage';
import { AlertasPage } from './pages/AlertasPage';
import { HistoricoPage } from './pages/HistoricoPage';
import { ConfiguracoesPage } from './pages/ConfiguracoesPage';
import { HelpPage } from './pages/HelpPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { api } from './services/api';

function MainLayout() {
  const { user, loading } = useAuth();
  const [activeTab, setActiveTab] = useState('inicio');
  const [navParam, setNavParam] = useState(null);
  const [authMode, setAuthMode] = useState('login'); // 'login' | 'register'
  const [unreadAlertsCount, setUnreadAlertsCount] = useState(0);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  useEffect(() => {
    if (user) {
      async function checkAlerts() {
        try {
          const alerts = await api.alerts.list();
          const unread = alerts.filter((a) => !a.is_read).length;
          setUnreadAlertsCount(unread);
        } catch (e) {
          // ignore
        }
      }
      checkAlerts();
    }
  }, [user, activeTab]);

  const handleNavigate = (tab, param = null) => {
    setNavParam(param);
    setActiveTab(tab);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="w-12 h-12 border-4 border-pink-200 border-t-[#D83A6F] rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) {
    if (authMode === 'register') {
      return <RegisterPage onSwitchToLogin={() => setAuthMode('login')} />;
    }
    return <LoginPage onSwitchToRegister={() => setAuthMode('register')} />;
  }

  const renderCurrentPage = () => {
    switch (activeTab) {
      case 'inicio':
        return <HomePage onNavigate={handleNavigate} />;
      case 'dashboard':
        return <DashboardPage onNavigate={handleNavigate} />;
      case 'compromissos':
        return <CompromissosPage initialFilter={navParam} />;
      case 'cartoes':
        return <CartoesPage />;
      case 'transacoes':
        return <TransacoesPage initialFilter={navParam} />;
      case 'parcelamentos': // Redirect to cartoes
        return <CartoesPage />;
      case 'recorrencias':
        return <RecorrenciasPage />;
      case 'orcamentos':
        return <OrcamentosPage />;
      case 'contas':
        return <ContasPage />;
      case 'categorias':
        return <CategoriasPage />;
      case 'alertas':
        return <AlertasPage />;
      case 'historico':
        return <HistoricoPage />;
      case 'configuracoes':
        return <ConfiguracoesPage />;
      case 'ajuda':
        return <HelpPage />;
      default:
        return <HomePage onNavigate={(tab) => setActiveTab(tab)} />;
    }
  };

  return (
    <div className="min-h-screen bg-[#F8F9FA] flex flex-col text-slate-800 pb-16">
      <Drawer 
        isOpen={isDrawerOpen} 
        onClose={() => setIsDrawerOpen(false)} 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
      />

      <div className="flex-1 flex flex-col min-w-0 max-w-full overflow-x-hidden">
        <Header
          onOpenDrawer={() => setIsDrawerOpen(true)}
          onOpenAlerts={() => setActiveTab('alertas')}
          onOpenSettings={() => setActiveTab('configuracoes')}
          unreadAlertsCount={unreadAlertsCount}
        />

        <main className="flex-1">
          {renderCurrentPage()}
        </main>
      </div>

      <BottomNav activeTab={activeTab} setActiveTab={setActiveTab} />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <MainLayout />
    </AuthProvider>
  );
}
