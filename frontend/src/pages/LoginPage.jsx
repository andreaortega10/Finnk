import React, { useState } from 'react';
import { LogIn, Sparkles, AlertCircle, ArrowRight, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

export function LoginPage({ onSwitchToRegister }) {
  const { login } = useAuth();
  const [email, setEmail] = useState('mariana@finnk.com');
  const [password, setPassword] = useState('123456');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [forgotSent, setForgotSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setLoading(true);

    try {
      await login(email.trim(), password);
    } catch (err) {
      setErrorMsg(err.message || 'Erro ao realizar login.');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoQuickLogin = async () => {
    setEmail('mariana@finnk.com');
    setPassword('123456');
    setLoading(true);
    setErrorMsg('');

    try {
      // Tenta login direto
      await login('mariana@finnk.com', '123456');
    } catch (err) {
      // Se não existir, registra e popula demo
      try {
        await api.auth.register({
          name: 'Mariana Silva',
          email: 'mariana@finnk.com',
          password: '123456',
        });
        await login('mariana@finnk.com', '123456');
        await api.auth.seedDemo();
      } catch (regErr) {
        setErrorMsg('Erro ao preparar conta de demonstração.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async () => {
    if (!email) {
      alert('Informe seu e-mail para recuperar a senha.');
      return;
    }
    try {
      const res = await api.auth.forgotPassword({ email });
      setForgotSent(true);
      alert(res.message);
    } catch (err) {
      alert(err.message || 'Erro ao solicitar recuperação.');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-rose-50 via-white to-pink-50">
      <div className="max-w-md w-full bg-white rounded-3xl shadow-2xl p-7 sm:p-9 border border-pink-100 relative">
        {/* Brand Header */}
        <div className="text-center mb-7">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-[#D83A6F] to-[#FB7185] flex items-center justify-center text-white font-black text-2xl mx-auto mb-3 shadow-lg shadow-pink-200">
            F
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">FINNK</h1>
          <p className="text-xs font-semibold text-[#D83A6F] uppercase tracking-wider mt-0.5">
            Suas contas em dia, sua mente em paz.
          </p>
        </div>

        {errorMsg && (
          <div className="mb-4 p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">E-mail</label>
            <input
              type="email"
              placeholder="seu@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 rounded-2xl border border-slate-200 focus:border-[#D83A6F] focus:ring-2 focus:ring-pink-100 text-sm outline-none font-medium"
              required
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-xs font-semibold text-slate-700">Senha</label>
              <button
                type="button"
                onClick={handleForgotPassword}
                className="text-[11px] font-semibold text-[#D83A6F] hover:underline"
              >
                Esqueceu a senha?
              </button>
            </div>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 rounded-2xl border border-slate-200 focus:border-[#D83A6F] focus:ring-2 focus:ring-pink-100 text-sm outline-none font-medium"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 rounded-2xl bg-[#D83A6F] hover:bg-[#C22A5E] text-white font-bold text-sm shadow-lg shadow-pink-200 transition-all flex items-center justify-center space-x-2 active:scale-98 disabled:opacity-70"
          >
            <LogIn className="w-4 h-4" />
            <span>{loading ? 'Entrando...' : 'Entrar no FINNK'}</span>
          </button>
        </form>

        {/* Demo Fast Login */}
        <div className="mt-5 pt-4 border-t border-slate-100">
          <button
            type="button"
            onClick={handleDemoQuickLogin}
            disabled={loading}
            className="w-full py-3 rounded-2xl bg-purple-50 hover:bg-purple-100 text-purple-800 font-bold text-xs transition-all flex items-center justify-center space-x-2 border border-purple-200/60"
          >
            <Sparkles className="w-4 h-4 text-purple-600" />
            <span>Entrar com Conta de Teste (Mariana Silva)</span>
          </button>
        </div>

        {/* Switch to Register */}
        <p className="text-center text-xs text-slate-500 mt-6">
          Ainda não tem conta?{' '}
          <button
            type="button"
            onClick={onSwitchToRegister}
            className="font-bold text-[#D83A6F] hover:underline"
          >
            Cadastre-se gratuitamente
          </button>
        </p>
      </div>
    </div>
  );
}
