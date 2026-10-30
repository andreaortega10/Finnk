import React from 'react';
import {
  DollarSign,
  Calendar,
  TrendingUp,
  Landmark,
  CreditCard,
  PieChart,
  BarChart3,
  Bot,
  CheckCircle2,
  AlertTriangle,
  ArrowRightLeft,
  Info
} from 'lucide-react';

export function HelpPage() {
  return (
    <div className="space-y-6 pb-20 md:pb-8 px-4 sm:px-6 max-w-5xl mx-auto animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">Central de Ajuda — Como Utilizar o Finnk</h2>
          <p className="text-xs text-slate-500">
            Manual completo das regras financeiras, saldos, projeções, recorrências, cartões, orçamentos e assistente de IA.
          </p>
        </div>
      </div>

      {/* 1. Primeiros Passos */}
      <div className="pastel-card rounded-3xl p-5 sm:p-6 space-y-4">
        <div className="flex items-start space-x-4">
          <div className="w-11 h-11 rounded-2xl bg-pink-50 text-[#D83A6F] flex items-center justify-center shrink-0">
            <DollarSign className="w-6 h-6" />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-black text-slate-900">1. Primeiros Passos</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              O Finnk é um organizador financeiro pessoal com controle 100% transparente e determinístico. Para começar:
            </p>
            <ul className="text-xs text-slate-600 space-y-1.5 list-disc pl-4">
              <li><strong>Cadastre suas Contas Financeiras:</strong> informe suas contas (Conta Corrente, Poupança, Carteira) e o saldo inicial real de cada uma.</li>
              <li><strong>Configure seus Cartões de Crédito:</strong> defina o limite total, o dia de fechamento e o dia de vencimento da fatura.</li>
              <li><strong>Registre Receitas, Despesas e Compromissos:</strong> classifique cada movimentação por categoria, conta ou cartão, data de movimentação e data de vencimento (opcional).</li>
              <li><strong>Defina seus Orçamentos Mensais:</strong> estipule tetos de gastos por categoria para acompanhar seu consumo percentual em tempo real.</li>
            </ul>
          </div>
        </div>
      </div>

      {/* 2. Saldos Atuais e Saldos Projetados (Unificados) */}
      <div className="pastel-card rounded-3xl p-5 sm:p-6 space-y-4 border-l-4 border-l-emerald-500">
        <div className="flex items-start space-x-4">
          <div className="w-11 h-11 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div className="space-y-3 w-full">
            <h3 className="text-lg font-black text-slate-900">2. Saldo Atual (Real) vs. Saldo Projetado</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              O Finnk unifica os conceitos de <strong>Saldo Projetado</strong> e <strong>Saldo Futuro</strong> sob uma única regra contábil rigorosa em todas as telas:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="p-3.5 rounded-2xl bg-emerald-50/60 border border-emerald-100 space-y-1">
                <span className="font-black text-emerald-800 block">Saldo Atual (Real)</span>
                <p className="text-slate-600">
                  Representa o dinheiro efetivamente disponível hoje. Calcula: <strong>Saldo Inicial + Receitas Efetivadas (Recebidas) − Despesas Efetivadas (Pagas)</strong> até a data de hoje. Não inclui previsões futuras nem parcelas em aberto.
                </p>
              </div>
              <div className="p-3.5 rounded-2xl bg-indigo-50/60 border border-indigo-100 space-y-1">
                <span className="font-black text-indigo-800 block">Saldo Projetado (Estimativa Futura)</span>
                <p className="text-slate-600">
                  Estimativa do saldo em uma data ou período específico (Fim do Mês, 7, 30, 90 dias ou personalizado), partindo do <strong>Saldo Atual + Receitas Previstas − Despesas Pendentes/Atrasadas</strong> até a data de referência.
                </p>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs space-y-1.5">
              <span className="font-bold text-slate-800 flex items-center gap-1.5">
                <Info className="w-4 h-4 text-[#D83A6F]" />
                <span>Exemplo Numérico Prático:</span>
              </span>
              <p className="text-slate-600">
                Suponha que você tenha <strong>Saldo Atual de R$ 2.000,00</strong>, um <strong>salário previsto de R$ 3.000,00 no dia 5</strong> e uma <strong>despesa prevista de R$ 500,00 no dia 8</strong>:
              </p>
              <ul className="list-disc pl-4 text-slate-700 space-y-1">
                <li><strong>Antes do dia 5 (antes do recebimento):</strong> o <strong>Saldo Atual permanece R$ 2.000,00</strong> (pois previsão não é dinheiro em conta).</li>
                <li><strong>Projeção após o dia 5:</strong> o <strong>Saldo Projetado passa para R$ 5.000,00</strong> (R$ 2.000,00 + R$ 3.000,00 previstos).</li>
                <li><strong>Projeção após o dia 8:</strong> o <strong>Saldo Projetado passa para R$ 4.500,00</strong> (R$ 5.000,00 − R$ 500,00 previstos).</li>
              </ul>
              <p className="text-[11px] font-semibold text-amber-700 pt-1">
                Importante: Previsão não é garantia de recebimento ou pagamento. O Saldo Atual só muda quando a transação é confirmada como Recebida ou Paga.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Recorrências */}
      <div className="pastel-card rounded-3xl p-5 sm:p-6 space-y-4">
        <div className="flex items-start space-x-4">
          <div className="w-11 h-11 rounded-2xl bg-purple-50 text-purple-600 flex items-center justify-center shrink-0">
            <Calendar className="w-6 h-6" />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-black text-slate-900">3. Recorrências, Periodicidades, Encerramento e Confirmação</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              As regras de recorrência automatizam a previsão de receitas e despesas que se repetem (como salário, aluguel, internet e academia):
            </p>
            <ul className="text-xs text-slate-600 space-y-1.5 list-disc pl-4">
              <li><strong>Recorrências são Previsões:</strong> ao cadastrar um salário mensal ou conta fixa, os lançamentos futuros são gerados com status <strong>PENDENTE</strong>. Eles afetam apenas o <strong>Saldo Projetado</strong> do respectivo período e <strong>nunca aumentam o Saldo Atual</strong> antes da confirmação.</li>
              <li><strong>Periodicidades Suportadas:</strong> Mensal, Semanal e Anual, respeitando a data de início, o dia de vencimento e o dia de alerta.</li>
              <li><strong>Data de Encerramento e Horizonte Limitado:</strong> você pode definir uma data final (<em>Repetir até</em>). Caso não informe data de encerramento, o sistema adota um horizonte automático limitado de <strong>6 meses à frente</strong>, evitando criar registros infinitos sem critério.</li>
              <li><strong>Confirmação, Edição e Cancelamento:</strong> confirmar o recebimento ou pagamento atualiza o próprio lançamento para <em>RECEBIDA</em> ou <em>PAGA</em> sem duplicar registros. Alterar o valor ou desativar a recorrência atualiza apenas as ocorrências futuras pendentes, preservando o histórico já efetivado.</li>
            </ul>
          </div>
        </div>
      </div>

      {/* 4. Contas Financeiras e Transferências */}
      <div className="pastel-card rounded-3xl p-5 sm:p-6 space-y-4">
        <div className="flex items-start space-x-4">
          <div className="w-11 h-11 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0">
            <Landmark className="w-6 h-6" />
          </div>
          <div className="space-y-2 w-full">
            <h3 className="text-lg font-black text-slate-900">4. Contas Financeiras Isoladas e Transferências</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Cada conta cadastrada possui seu próprio <strong>Saldo Atual</strong> e <strong>Saldo Projetado</strong>. Somente movimentações vinculadas àquela conta específica afetam seus saldos.
            </p>
            <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-xs space-y-1">
              <span className="font-bold text-slate-800 block">Exemplo de Isolamento por Conta:</span>
              <p className="text-slate-600">
                Se sua <strong>Conta Corrente tem R$ 1.000,00</strong> e sua <strong>Conta Poupança tem R$ 2.000,00</strong>, e você cadastra uma receita prevista de <strong>R$ 500,00 vinculada à Conta Corrente</strong>:
                a Conta Corrente permanece com Saldo Atual de R$ 1.000,00 e passa a ter <strong>Saldo Projetado de R$ 1.500,00</strong>, enquanto a <strong>Conta Poupança permanece inalterada em R$ 2.000,00</strong>.
              </p>
            </div>
            <p className="text-xs text-slate-600 pt-1">
              <strong>Projeções por Horizonte (7, 30, 90 dias e Personalizado):</strong> na aba <em>Contas Financeiras</em>, você pode alternar entre Fim do Mês, 7 dias, 30 dias, 90 dias ou um período personalizado para visualizar Saldo Atual, Entradas Previstas, Saídas Previstas e Saldo Final.
            </p>
            <p className="text-xs text-slate-600">
              <strong>Transferências entre Contas:</strong> ao usar o botão <em>Transferir entre Contas</em>, o valor reduz o saldo da conta de origem e aumenta o saldo da conta de destino, <strong>sem ser contabilizado como receita ou despesa consolidada</strong> nos gráficos do mês.
            </p>
          </div>
        </div>
      </div>

      {/* 5. Cartões, Faturas e Parcelamentos */}
      <div className="pastel-card rounded-3xl p-5 sm:p-6 space-y-4">
        <div className="flex items-start space-x-4">
          <div className="w-11 h-11 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center shrink-0">
            <CreditCard className="w-6 h-6" />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-black text-slate-900">5. Cartões de Crédito, Faturas e Compras Parceladas</h3>
            <ul className="text-xs text-slate-600 space-y-1.5 list-disc pl-4">
              <li><strong>Validação de Limite Disponível:</strong> o limite disponível do cartão é calculado subtraindo todas as despesas e parcelas ainda não pagas do limite total do cartão. Compras que excedam o limite disponível são bloqueadas com aviso claro.</li>
              <li><strong>Divisão Exata de Parcelamentos:</strong> compras parceladas dividem o valor total igualmente entre as parcelas mensais, ajustando eventual diferença de centavos na última parcela (ex: R$ 100,00 em 3x gera 33,33 + 33,33 + 33,34 = R$ 100,00).</li>
              <li><strong>Impacto no Saldo Bancário:</strong> compras no cartão compõem a fatura e os gráficos de despesas por categoria, mas não reduzem o saldo da conta corrente no ato da compra — apenas o pagamento da fatura debita da conta bancária.</li>
            </ul>
          </div>
        </div>
      </div>

      {/* 6. Orçamentos Mensais */}
      <div className="pastel-card rounded-3xl p-5 sm:p-6 space-y-4 border-l-4 border-l-pink-500">
        <div className="flex items-start space-x-4">
          <div className="w-11 h-11 rounded-2xl bg-pink-50 text-[#D83A6F] flex items-center justify-center shrink-0">
            <PieChart className="w-6 h-6" />
          </div>
          <div className="space-y-2 w-full">
            <h3 className="text-lg font-black text-slate-900">6. Orçamentos & Metas por Categoria</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Na aba <em>Orçamentos</em>, você define o limite mensal para cada categoria de despesa (Alimentação, Moradia, Transporte, Saúde, Lazer, Educação, Assinaturas, Outros). O valor utilizado é calculado automaticamente a partir das despesas elegíveis registradas no período (nunca preenchido manualmente).
            </p>
            <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-xs space-y-1">
              <span className="font-bold text-slate-800 block">Exemplo Numérico de Orçamento:</span>
              <p className="text-slate-600">
                Se você definir um <strong>limite mensal de R$ 800,00</strong> para Alimentação e registrar <strong>despesas elegíveis somando R$ 600,00</strong> no mês:
                o sistema exibirá automaticamente <strong>75% utilizado (R$ 600,00)</strong> e <strong>R$ 200,00 de saldo disponível</strong> dentro da meta.
                Ao atingir 80% o orçamento entra em <em>Atenção</em>, e ao atingir ou superar 100% é sinalizado como <em>Limite Ultrapassado</em>.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 7. Análise Geral */}
      <div className="pastel-card rounded-3xl p-5 sm:p-6 space-y-4">
        <div className="flex items-start space-x-4">
          <div className="w-11 h-11 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
            <BarChart3 className="w-6 h-6" />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-black text-slate-900">7. Análise Geral e Consistência entre Telas</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              A aba <em>Análise Geral</em> consolida os mesmos indicadores exibidos em <em>Início</em>, <em>Contas Financeiras</em>, <em>Transações</em> e <em>Orçamentos</em>:
              evolução dos últimos 6 meses (receitas vs. despesas efetivadas), distribuição percentual de gastos por categoria, status dos compromissos (Pagos, Pendentes e Atrasados) e uso do limite dos cartões.
            </p>
          </div>
        </div>
      </div>

      {/* 8. Assistente de IA */}
      <div className="pastel-card rounded-3xl p-5 sm:p-6 space-y-4 border-l-4 border-l-indigo-500">
        <div className="flex items-start space-x-4">
          <div className="w-11 h-11 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0">
            <Bot className="w-6 h-6" />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-black text-slate-900">8. Assistente Virtual com IA — Origem dos Dados e Limitações</h3>
            <ul className="text-xs text-slate-600 space-y-1.5 list-disc pl-4">
              <li><strong>Origem Determinística dos Dados:</strong> o assistente de IA (integrado ao Google Gemini) não inventa números nem faz estimativas aleatórias. Ele consulta exclusivamente o resumo contábil oficial calculado pelo motor financeiro do Finnk para a sua conta autenticada.</li>
              <li><strong>O que você pode perguntar:</strong> quanto recebeu e gastou no mês, qual sua maior categoria de despesa, comparativo percentual com o mês anterior, compromissos próximos do vencimento, compras parceladas ativas e explicação entre Saldo Atual e Saldo Projetado.</li>
              <li><strong>Limitações e Segurança:</strong> o assistente atua estritamente em modo de leitura e orientação financeira educativa. Ele não cria, não edita e não exclui transações, contas ou cartões, e não realiza recomendações especulativas de investimentos de risco.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
