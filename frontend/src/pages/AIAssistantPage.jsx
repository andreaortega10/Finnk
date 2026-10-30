import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  Send,
  Trash2,
  Bot,
  User,
  Clock,
  ShieldCheck,
  AlertCircle,
  HelpCircle,
  ArrowRight,
  RefreshCw,
  Loader2
} from 'lucide-react';
import { api } from '../services/api';

export function AIAssistantPage({ onNavigate }) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [fetchingHistory, setFetchingHistory] = useState(true);
  const [aiStatus, setAiStatus] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  const messagesEndRef = useRef(null);

  const suggestedQuestions = [
    'Quanto gastei neste mês?',
    'Quais categorias concentram meus gastos?',
    'Como meus gastos mudaram em relação ao mês anterior?',
    'Quais compromissos vencem em breve?',
    'Qual é a diferença entre saldo atual e projetado?',
    'Quais compras parceladas estão ativas?'
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    async function initData() {
      try {
        setFetchingHistory(true);
        const [statusData, historyData] = await Promise.all([
          api.ai.getStatus().catch(() => null),
          api.ai.getHistory().catch(() => []),
        ]);
        setAiStatus(statusData);
        setMessages(historyData || []);
      } catch (err) {
        console.error(err);
      } finally {
        setFetchingHistory(false);
      }
    }
    initData();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (textToSend) => {
    const text = (textToSend || inputMessage).trim();
    if (!text || loading) return;

    setErrorMsg('');
    setInputMessage('');

    // Adiciona a mensagem do usuário imediatamente na interface
    const tempUserMsg = {
      id: Date.now(),
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setLoading(true);

    try {
      const response = await api.ai.chat(text);
      const assistantMsg = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.reply,
        period_analyzed: response.period_analyzed,
        created_at: response.timestamp || new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setErrorMsg(err.message || 'Não foi possível obter resposta da IA no momento. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  const handleClearHistory = async () => {
    try {
      await api.ai.clearHistory();
      setMessages([]);
      setShowClearConfirm(false);
    } catch (err) {
      setErrorMsg('Erro ao excluir histórico de conversas.');
    }
  };

  return (
    <div className="space-y-4 pb-20 md:pb-8 px-3 sm:px-6 max-w-4xl mx-auto animate-fadeIn flex flex-col h-[calc(100vh-120px)] sm:h-[calc(100vh-100px)]">
      {/* Header do Assistente */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-4 sm:p-5 rounded-3xl border border-slate-100 shadow-xs shrink-0">
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-[#D83A6F] to-[#FB7185] flex items-center justify-center text-white shadow-md shadow-pink-200 shrink-0">
            <Sparkles className="w-6 h-6 stroke-[2]" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-black text-slate-800 tracking-tight">
                Assistente Finnk
              </h1>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-pink-100 text-[#D83A6F]">
                IA Segura
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Tire dúvidas e compreenda seus indicadores financeiros em linguagem natural.
            </p>
          </div>
        </div>

        {/* Badges de Status & Ações */}
        <div className="flex items-center space-x-2 self-start sm:self-auto">
          {aiStatus?.is_demo ? (
            <span className="text-[11px] font-semibold text-amber-700 bg-amber-50 border border-amber-200 px-2.5 py-1 rounded-xl flex items-center space-x-1.5">
              <span>Modo Demonstração (Sintético)</span>
            </span>
          ) : (
            <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-xl flex items-center space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>{aiStatus?.model ? `${aiStatus.model} (Gratuito)` : 'Google Gemini (Gratuito)'}</span>
            </span>
          )}

          {messages.length > 0 && (
            <button
              onClick={() => setShowClearConfirm(true)}
              className="p-2 rounded-xl text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
              title="Excluir histórico de conversas"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Modal de confirmação para limpar histórico */}
      {showClearConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-fadeIn">
          <div className="bg-white rounded-3xl p-6 max-w-sm w-full shadow-2xl border border-slate-100 text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto">
              <Trash2 className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Limpar histórico de conversas?</h3>
              <p className="text-xs text-slate-500 mt-1">
                Todas as mensagens do chat serão excluídas permanentemente do servidor. Suas transações e saldos não serão afetados.
              </p>
            </div>
            <div className="flex items-center space-x-2 justify-center pt-2">
              <button
                onClick={() => setShowClearConfirm(false)}
                className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleClearHistory}
                className="px-4 py-2 rounded-xl bg-rose-600 text-white text-xs font-semibold hover:bg-rose-700 transition-colors shadow-sm"
              >
                Confirmar e Limpar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Área de Mensagens (Scrollável) */}
      <div className="flex-1 overflow-y-auto px-1 sm:px-2 space-y-4 pr-2">
        {fetchingHistory ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-3">
            <Loader2 className="w-8 h-8 text-[#D83A6F] animate-spin" />
            <p className="text-xs text-slate-400">Carregando histórico do assistente...</p>
          </div>
        ) : messages.length === 0 ? (
          /* Empty State com boas-vindas e perguntas sugeridas */
          <div className="flex flex-col items-center justify-center py-6 sm:py-10 text-center space-y-5">
            <div className="w-16 h-16 rounded-3xl bg-pink-50 border border-pink-100 flex items-center justify-center text-[#D83A6F] shadow-sm">
              <Bot className="w-8 h-8 stroke-[1.8]" />
            </div>
            <div className="max-w-md space-y-1.5 px-4">
              <h2 className="text-lg font-bold text-slate-800">Olá! Como posso ajudar você hoje?</h2>
              <p className="text-xs text-slate-500 leading-relaxed">
                Eu tenho acesso aos cálculos oficiais e indicadores do seu Finnk. Posso analisar seus gastos, comparar meses, explicar seu saldo projetado e listar seus compromissos futuros.
              </p>
            </div>

            {/* Chips de perguntas sugeridas */}
            <div className="w-full max-w-lg space-y-2 pt-2">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
                Sugestões de perguntas rápidas:
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-left">
                {suggestedQuestions.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(q)}
                    className="flex items-center justify-between p-3 rounded-2xl bg-white border border-slate-200/80 hover:border-[#D83A6F] hover:bg-pink-50/40 text-xs font-semibold text-slate-700 transition-all text-left group active:scale-95 shadow-2xs"
                  >
                    <span className="line-clamp-2 pr-2">{q}</span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-[#D83A6F] shrink-0" />
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center space-x-2 text-[11px] text-slate-400 bg-slate-100/80 px-3 py-1.5 rounded-full">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>Acesso estritamente de consulta (leitura). Seus dados não são modificados.</span>
            </div>
          </div>
        ) : (
          /* Lista de Mensagens */
          messages.map((m) => {
            const isUser = m.role === 'user';
            return (
              <div
                key={m.id}
                className={`flex items-start space-x-2.5 sm:space-x-3 ${isUser ? 'justify-end' : 'justify-start'}`}
              >
                {!isUser && (
                  <div className="w-8 h-8 rounded-full bg-pink-100 text-[#D83A6F] flex items-center justify-center shrink-0 mt-0.5">
                    <Sparkles className="w-4 h-4 stroke-[2]" />
                  </div>
                )}

                <div
                  className={`max-w-[85%] sm:max-w-xl rounded-2xl p-3.5 sm:p-4 text-xs sm:text-sm leading-relaxed shadow-2xs ${
                    isUser
                      ? 'bg-[#D83A6F] text-white rounded-tr-xs'
                      : 'bg-white border border-slate-100 text-slate-800 rounded-tl-xs whitespace-pre-wrap'
                  }`}
                >
                  {m.content}

                  {m.period_analyzed && !isUser && (
                    <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400">
                      <span>Período: {m.period_analyzed}</span>
                      <span>Fonte: Cálculos oficiais Finnk</span>
                    </div>
                  )}
                </div>

                {isUser && (
                  <div className="w-8 h-8 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center shrink-0 mt-0.5">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            );
          })
        )}

        {/* Indicador de Carregamento da IA */}
        {loading && (
          <div className="flex items-start space-x-2.5 sm:space-x-3 justify-start animate-pulse">
            <div className="w-8 h-8 rounded-full bg-pink-100 text-[#D83A6F] flex items-center justify-center shrink-0">
              <Sparkles className="w-4 h-4 stroke-[2]" />
            </div>
            <div className="bg-white border border-slate-100 rounded-2xl p-3.5 text-xs text-slate-500 shadow-2xs flex items-center space-x-2">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-[#D83A6F]" />
              <span>O Assistente Finnk está analisando suas finanças...</span>
            </div>
          </div>
        )}

        {/* Banner de Erro */}
        {errorMsg && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-2xl text-xs text-rose-700 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
              <span>{errorMsg}</span>
            </div>
            <button
              onClick={() => handleSend(inputMessage)}
              className="text-xs font-bold underline hover:text-rose-800 shrink-0 ml-2"
            >
              Tentar novamente
            </button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input de Mensagem Fixo na Base */}
      <div className="bg-white p-2.5 sm:p-3 rounded-2xl border border-slate-200 shadow-sm shrink-0">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center space-x-2"
        >
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Faça uma pergunta sobre suas finanças (ex: Quanto gastei neste mês?)..."
            disabled={loading}
            maxLength={1000}
            className="flex-1 text-xs sm:text-sm px-3 py-2 outline-none text-slate-800 placeholder-slate-400 bg-transparent"
          />

          <button
            type="submit"
            disabled={!inputMessage.trim() || loading}
            className={`p-2.5 rounded-xl transition-all cursor-pointer ${
              inputMessage.trim() && !loading
                ? 'bg-[#D83A6F] text-white hover:bg-[#c02d60] active:scale-95 shadow-sm'
                : 'bg-slate-100 text-slate-400 cursor-not-allowed'
            }`}
            title="Enviar mensagem"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>

        <div className="flex items-center justify-between px-2 pt-1.5 text-[10px] text-slate-400">
          <span>Pressione Enter para enviar</span>
          <span>Cálculos oficiais sem alucinação de valores</span>
        </div>
      </div>
    </div>
  );
}
