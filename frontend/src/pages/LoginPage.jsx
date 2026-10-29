import React, { useState } from 'react';
import { LogIn, AlertCircle, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { loginWithGoogleFirebase } from '../services/firebase';

export function LoginPage({ onSwitchToRegister }) {
  const { login, loginGoogle } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  React.useEffect(() => {
    // Pré-aquece o backend em segundo plano enquanto o usuário preenche a tela
    api.auth.ping();
  }, []);

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

  const handleGoogleLogin = async () => {
    setErrorMsg('');
    setGoogleLoading(true);
    try {
      const googleUser = await loginWithGoogleFirebase();
      await loginGoogle(googleUser);
    } catch (err) {
      setErrorMsg(err.message || 'Erro ao autenticar com Google.');
    } finally {
      setGoogleLoading(false);
    }
  };

  const handleForgotPassword = async () => {
    if (!email) {
      alert('Informe seu e-mail para recuperar a senha.');
      return;
    }
    try {
      const res = await api.auth.forgotPassword({ email });
      alert(res.message);
    } catch (err) {
      alert(err.message || 'Erro ao solicitar recuperação.');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-rose-50 via-white to-pink-50">
      <div className="max-w-md w-full bg-white rounded-3xl shadow-2xl p-7 sm:p-9 border border-pink-100 relative">
        {/* Brand Header */}
        <div className="text-center mb-6">
          <img src="/icon.jpg" alt="FINNK Logo" className="w-16 h-16 rounded-2xl object-cover mx-auto mb-3 shadow-lg shadow-pink-200" />
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

        {/* Continuar com Google */}
        <button
          type="button"
          onClick={handleGoogleLogin}
          disabled={googleLoading || loading}
          className="w-full py-3 rounded-2xl bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-bold text-xs shadow-xs transition-all flex items-center justify-center space-x-2.5 active:scale-98 disabled:opacity-70 cursor-pointer"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
          </svg>
          <span>{googleLoading ? 'Autenticando com Google...' : 'Continuar com Google'}</span>
        </button>

        <div className="relative my-4">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-slate-200" />
          </div>
          <div className="relative flex justify-center text-[11px] uppercase">
            <span className="bg-white px-3 text-slate-400 font-semibold">ou com e-mail</span>
          </div>
        </div>

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
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 pr-11 rounded-2xl border border-slate-200 focus:border-[#D83A6F] focus:ring-2 focus:ring-pink-100 text-sm outline-none font-medium"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3.5 top-3 text-slate-400 hover:text-slate-600 transition-colors p-0.5"
                title={showPassword ? "Ocultar senha" : "Ver senha"}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || googleLoading}
            className="w-full py-3.5 rounded-2xl bg-[#D83A6F] hover:bg-[#C22A5E] text-white font-bold text-sm shadow-lg shadow-pink-200 transition-all flex items-center justify-center space-x-2 active:scale-98 disabled:opacity-70 cursor-pointer"
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <LogIn className="w-4 h-4" />
            )}
            <span>{loading ? 'Entrando com segurança...' : 'Entrar no FINNK'}</span>
          </button>
        </form>

        {/* Switch to Register */}
        <p className="text-center text-xs text-slate-500 mt-5">
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
