import React, { useState, useEffect } from 'react';
import {
  Settings,
  User,
  Lock,
  Bell,
  Database,
  ShieldAlert,
  Save,
  Sparkles,
  Download,
  Trash2,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

export function ConfiguracoesPage() {
  const { user, updateProfile, logout } = useAuth();

  // Profile fields
  const [name, setName] = useState(user?.name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [defaultCurrency, setDefaultCurrency] = useState(user?.default_currency || 'BRL');
  const [alertDaysBefore, setAlertDaysBefore] = useState(user?.alert_days_before || 3);

  // Password fields
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [loadingProfile, setLoadingProfile] = useState(false);
  const [loadingPassword, setLoadingPassword] = useState(false);
  const [loadingDemo, setLoadingDemo] = useState(false);
  const [feedbackMsg, setFeedbackMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (user) {
      setName(user.name);
      setEmail(user.email);
      setDefaultCurrency(user.default_currency || 'BRL');
      setAlertDaysBefore(user.alert_days_before || 3);
    }
  }, [user]);

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setFeedbackMsg('');
    setErrorMsg('');
    setLoadingProfile(true);

    try {
      await updateProfile({
        name: name.trim(),
        email: email.trim(),
        default_currency: defaultCurrency,
        alert_days_before: parseInt(alertDaysBefore, 10),
      });
      setFeedbackMsg('Perfil atualizado com sucesso!');
    } catch (err) {
      setErrorMsg(err.message || 'Erro ao atualizar perfil.');
    } finally {
      setLoadingProfile(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setFeedbackMsg('');
    setErrorMsg('');

    if (newPassword !== confirmPassword) {
      setErrorMsg('A nova senha e a confirmação não coincidem.');
      return;
    }
    if (newPassword.length < 6) {
      setErrorMsg('A nova senha deve ter no mínimo 6 caracteres.');
      return;
    }

    setLoadingPassword(true);
    try {
      await api.auth.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setFeedbackMsg('Senha alterada com sucesso!');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setErrorMsg(err.message || 'Erro ao alterar senha.');
    } finally {
      setLoadingPassword(false);
    }
  };

  const handleSeedDemo = async () => {
    if (!window.confirm('Deseja carregar os dados de demonstração (contas, cartões, despesas, aluguel, smartphone parcelado da Mariana)?')) return;
    setLoadingDemo(true);
    try {
      await api.auth.seedDemo();
      setFeedbackMsg('Dados de demonstração carregados com sucesso! Acesse Início ou Dashboard para visualizar.');
    } catch (err) {
      setErrorMsg(err.message || 'Erro ao carregar dados demonstrativos.');
    } finally {
      setLoadingDemo(false);
    }
  };

  const handleDeleteAccount = async () => {
    const confirmName = window.prompt('Para excluir definitivamente sua conta e todos os dados conforme a LGPD, digite "EXCLUIR":');
    if (confirmName !== 'EXCLUIR') return;

    try {
      await api.user.deleteAccount();
      alert('Sua conta foi excluída com sucesso.');
      logout();
    } catch (err) {
      alert(err.message || 'Erro ao excluir conta.');
    }
  };

  return (
    <div className="space-y-6 pb-20 md:pb-8 px-4 sm:px-6 max-w-5xl mx-auto animate-fadeIn">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-black text-slate-900 tracking-tight">Configurações & Perfil</h2>
        <p className="text-xs text-slate-500">Gerencie seus dados pessoais, alertas, preferências e segurança.</p>
      </div>

      {feedbackMsg && (
        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold flex items-center space-x-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
          <span>{feedbackMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-bold flex items-center space-x-2">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 1. Profile & Preferences */}
        <div className="pastel-card rounded-3xl p-6">
          <div className="flex items-center space-x-2.5 mb-5 pb-3 border-b border-slate-100">
            <User className="w-5 h-5 text-[#D83A6F]" />
            <h3 className="font-bold text-sm text-slate-800">Dados Pessoais & Moeda</h3>
          </div>

          <form onSubmit={handleUpdateProfile} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Nome Completo</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-[#D83A6F] text-xs outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">E-mail</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-[#D83A6F] text-xs outline-none"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Moeda Padrão</label>
                <select
                  value={defaultCurrency}
                  onChange={(e) => setDefaultCurrency(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs outline-none bg-white font-medium"
                >
                  <option value="BRL">BRL (R$)</option>
                  <option value="USD">USD ($)</option>
                  <option value="EUR">EUR (€)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Avisar Antes (Dias)</label>
                <input
                  type="number"
                  min={1}
                  max={30}
                  value={alertDaysBefore}
                  onChange={(e) => setAlertDaysBefore(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs outline-none font-bold text-center"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loadingProfile}
              className="w-full py-2.5 rounded-xl bg-[#D83A6F] hover:bg-[#C22A5E] text-white font-bold text-xs shadow-md shadow-pink-200 transition-all flex items-center justify-center space-x-2"
            >
              <Save className="w-4 h-4" />
              <span>{loadingProfile ? 'Salvando...' : 'Salvar Alterações'}</span>
            </button>
          </form>
        </div>

        {/* 2. Change Password */}
        <div className="pastel-card rounded-3xl p-6">
          <div className="flex items-center space-x-2.5 mb-5 pb-3 border-b border-slate-100">
            <Lock className="w-5 h-5 text-indigo-600" />
            <h3 className="font-bold text-sm text-slate-800">Segurança & Senha</h3>
          </div>

          <form onSubmit={handleChangePassword} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Senha Atual</label>
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Nova Senha</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Confirmar Nova Senha</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs outline-none"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loadingPassword}
              className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-md shadow-indigo-200 transition-all flex items-center justify-center space-x-2"
            >
              <Lock className="w-4 h-4" />
              <span>{loadingPassword ? 'Alterando...' : 'Alterar Senha'}</span>
            </button>
          </form>
        </div>
      </div>

      {/* 3. Demo Data & LGPD Options */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Demo Data Loader */}
        <div className="pastel-card rounded-3xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2.5 mb-2">
              <Sparkles className="w-5 h-5 text-purple-600" />
              <h3 className="font-bold text-sm text-slate-800">Dados de Demonstração (Mock Mariana)</h3>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed mb-4">
              Carrega os dados dos protótipos de alta fidelidade: Contas (Corrente, Carteira), Cartões (Nubank, Elo), Compromissos (Aluguel, Internet, Netflix, Salário), Compra Parcelada e Orçamentos.
            </p>
          </div>

          <button
            onClick={handleSeedDemo}
            disabled={loadingDemo}
            className="w-full py-3 rounded-2xl bg-purple-50 border border-purple-200 text-purple-800 font-bold text-xs hover:bg-purple-100 transition-all flex items-center justify-center space-x-2"
          >
            <Sparkles className="w-4 h-4 text-purple-600" />
            <span>{loadingDemo ? 'Carregando dados...' : 'Carregar Dados do Protótipo'}</span>
          </button>
        </div>

        {/* Reset Data */}
        <div className="pastel-card rounded-3xl p-6 flex flex-col justify-between border-orange-100 bg-orange-50/20">
          <div>
            <div className="flex items-center space-x-2.5 mb-2">
              <AlertCircle className="w-5 h-5 text-orange-600" />
              <h3 className="font-bold text-sm text-orange-900">Resetar Dados</h3>
            </div>
            <p className="text-xs text-orange-700/80 leading-relaxed mb-4">
              Apaga todas as suas contas, transações, cartões e registros, mas mantém sua conta e dados de acesso intactos.
            </p>
          </div>

          <button
            onClick={async () => {
              if (window.confirm('Tem certeza? Isso apagará todos os dados financeiros. Sua conta será mantida.')) {
                if (window.confirm('Essa ação é irreversível. Deseja mesmo continuar?')) {
                  try {
                    await api.user.resetData();
                    setFeedbackMsg('Todos os dados foram resetados com sucesso.');
                    window.location.reload();
                  } catch (e) {
                    setErrorMsg('Erro ao resetar dados.');
                  }
                }
              }
            }}
            className="w-full py-3 rounded-2xl bg-white border border-orange-200 text-orange-700 font-bold text-xs hover:bg-orange-600 hover:text-white transition-all shadow-xs"
          >
            Resetar Todos os Dados
          </button>
        </div>

        {/* LGPD Account Erasure */}
        <div className="pastel-card rounded-3xl p-6 flex flex-col justify-between border-rose-100 bg-rose-50/20">
          <div>
            <div className="flex items-center space-x-2.5 mb-2">
              <Trash2 className="w-5 h-5 text-rose-600" />
              <h3 className="font-bold text-sm text-rose-900">Gerenciamento de Conta & LGPD</h3>
            </div>
            <p className="text-xs text-rose-700/80 leading-relaxed mb-4">
              Direito de esquecimento: Exclui permanentemente sua conta, transações, compromissos, cartões e registros de auditoria dos servidores.
            </p>
          </div>

          <button
            onClick={handleDeleteAccount}
            className="w-full py-3 rounded-2xl bg-white border border-rose-200 text-rose-700 font-bold text-xs hover:bg-rose-600 hover:text-white transition-all shadow-xs"
          >
            Excluir Minha Conta Definitivamente
          </button>
        </div>
      </div>
    </div>
  );
}
