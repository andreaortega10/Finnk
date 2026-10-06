import React, { useState } from 'react';
import { UserPlus, AlertCircle, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export function RegisterPage({ onSwitchToLogin }) {
  const { register } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (!name.trim()) {
      setErrorMsg('Informe seu nome completo.');
      return;
    }
    if (password !== confirmPassword) {
      setErrorMsg('As senhas digitadas não coincidem.');
      return;
    }
    if (password.length < 6) {
      setErrorMsg('A senha deve ter pelo menos 6 caracteres.');
      return;
    }

    setLoading(true);
    try {
      await register(name.trim(), email.trim(), password);
    } catch (err) {
      setErrorMsg(err.message || 'Erro ao realizar cadastro.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-rose-50 via-white to-pink-50">
      <div className="max-w-md w-full bg-white rounded-3xl shadow-2xl p-7 sm:p-9 border border-pink-100 relative">
        <div className="text-center mb-7">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-[#D83A6F] to-[#FB7185] flex items-center justify-center text-white font-black text-2xl mx-auto mb-3 shadow-lg shadow-pink-200">
            F
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Criar Conta</h1>
          <p className="text-xs font-semibold text-[#D83A6F] uppercase tracking-wider mt-0.5">
            Comece a organizar suas finanças hoje
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
            <label className="block text-xs font-semibold text-slate-700 mb-1">Nome Completo</label>
            <input
              type="text"
              placeholder="Ex.: Mariana Silva"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-3 rounded-2xl border border-slate-200 focus:border-[#D83A6F] focus:ring-2 focus:ring-pink-100 text-sm outline-none font-medium"
              required
            />
          </div>

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

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Senha</label>
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 rounded-2xl border border-slate-200 focus:border-[#D83A6F] focus:ring-2 focus:ring-pink-100 text-sm outline-none font-medium"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Confirmar Senha</label>
              <input
                type="password"
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-4 py-3 rounded-2xl border border-slate-200 focus:border-[#D83A6F] focus:ring-2 focus:ring-pink-100 text-sm outline-none font-medium"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 rounded-2xl bg-[#D83A6F] hover:bg-[#C22A5E] text-white font-bold text-sm shadow-lg shadow-pink-200 transition-all flex items-center justify-center space-x-2 active:scale-98 disabled:opacity-70"
          >
            <UserPlus className="w-4 h-4" />
            <span>{loading ? 'Criando conta...' : 'Cadastrar e Entrar'}</span>
          </button>
        </form>

        <p className="text-center text-xs text-slate-500 mt-6">
          Já tem uma conta?{' '}
          <button
            type="button"
            onClick={onSwitchToLogin}
            className="font-bold text-[#D83A6F] hover:underline"
          >
            Fazer login
          </button>
        </p>
      </div>
    </div>
  );
}
