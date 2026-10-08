# FINNK - Organizador Financeiro 💰

O **FINNK** é uma aplicação completa e responsiva (Mobile-First) projetada para descomplicar o controle financeiro pessoal. Ele oferece gestão inteligente de receitas, despesas, cartões de crédito, compromissos recorrentes e metas de economia, combinando uma interface moderna e intuitiva com um backend poderoso.

---

## 🚀 Funcionalidades Principais

*   **📊 Análise Geral (Dashboard):** Visão completa do seu dinheiro. Acompanhe os saldos, projeções para o fim do mês, evolução financeira e faturas de cartão.
*   **💳 Gestão de Cartões de Crédito:** Controle de limites, faturas, dias de vencimento e fechamento, com suporte a parcelamentos detalhados.
*   **🏦 Múltiplas Contas:** Gerencie diferentes contas (Corrente, Poupança, Investimentos) em um só lugar e saiba onde seu dinheiro está.
*   **🔁 Despesas e Receitas Recorrentes:** Automação de contas fixas (ex: aluguel, salários) e assinaturas. O FINNK projeta os lançamentos nos próximos meses para você não ter surpresas.
*   **🛍️ Lançamentos Parcelados:** O FINNK distribui automaticamente as parcelas de suas compras ao longo dos meses e vincula à fatura correta do cartão.
*   **🔔 Alertas e Vencimentos:** Nunca mais pague juros por esquecimento. O aplicativo alerta sobre compromissos que estão vencendo e atrasados.
*   **📱 Interface Mobile-First:** Experiência de uso fluida em celulares, utilizando componentes amigáveis (Cards, Modais, Menus Inferiores).
*   **🏷️ Categorias Fixas e Personalizadas:** Organização com categorias essenciais invioláveis (Lazer, Saúde, Alimentação, Educação etc) e liberdade para criar as suas.

---

## 🛠️ Tecnologias Utilizadas

### Frontend (App / Web)
*   **React + Vite:** Para construção rápida de interface e componentização.
*   **TailwindCSS:** Para estilos e design responsivo, permitindo um layout limpo em tons pasteis.
*   **Lucide React:** Biblioteca de ícones modernos e leves.
*   **Recharts:** Geração de gráficos para evolução e análise de categorias.
*   **Capacitor:** Empacotamento da aplicação web para formato Android nativo (APK).

### Backend (API)
*   **Python + FastAPI:** Framework backend ultra rápido para construção das APIs.
*   **SQLAlchemy:** ORM para comunicação e estruturação de tabelas de banco de dados.
*   **Pydantic:** Para validação de dados e checagem de tipos entre Frontend e Backend.
*   **JWT (JSON Web Tokens):** Autenticação e proteção das rotas de usuário.

### Infraestrutura e Banco de Dados
*   **PostgreSQL (Neon):** Banco de dados relacional robusto e escalável na nuvem.
*   **Render:** Hospedagem da API Backend e banco de dados (Cloud).
*   **Firebase Hosting:** Hospedagem estática do site/PWA frontend.

---

## ⚙️ Como Executar o Projeto Localmente

### Pré-requisitos
*   [Node.js](https://nodejs.org/en/) (v16+)
*   [Python](https://www.python.org/) (3.10+)
*   Gerenciador de pacotes npm/yarn e pip.

### 1. Clonando o repositório
```bash
git clone https://github.com/SEU_USUARIO/Finnk.git
cd Finnk
```

### 2. Rodando o Backend (FastAPI)
```bash
cd backend
# Crie e ative seu ambiente virtual (opcional mas recomendado)
python -m venv venv
source venv/bin/activate # ou venv\Scripts\activate no Windows

# Instale as dependências
pip install -r requirements.txt

# Inicialize o servidor local na porta 8000
python -m uvicorn app.main:app --reload
```

### 3. Rodando o Frontend (React)
Em um novo terminal, abra a pasta `frontend`:
```bash
cd frontend

# Instale as dependências
npm install

# Inicie o ambiente de desenvolvimento local
npm run dev
```
O aplicativo abrirá no seu navegador, conectando-se automaticamente à API local.

---

## 📱 Gerando o APK Android

Para gerar o arquivo APK e instalar no seu aparelho celular:
1. Certifique-se de que tenha o [Android Studio](https://developer.android.com/studio) configurado no seu computador.
2. Na pasta `frontend`, gere a "build" final e sincronize com o Capacitor:
```bash
npm run build
npx cap sync android
```
3. Abra o projeto Android e gere o APK:
```bash
npx cap open android
```
No Android Studio, acesse o menu **Build > Build Bundle(s) / APK(s) > Build APK(s)**. O arquivo final estará em `android/app/build/outputs/apk/debug/app-debug.apk`.

---

## 🛡️ Licença
Este projeto foi idealizado e desenvolvido como uma aplicação de uso pessoal/comercial fechada. Proibida reprodução não autorizada.
