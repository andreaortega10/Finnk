const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://finnk.onrender.com/api';

export async function request(endpoint, options = {}) {
  const token = localStorage.getItem('finnk_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const config = {
    ...options,
    headers,
  };

  if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
    config.body = JSON.stringify(options.body);
  }

  // Timeout preventivo de 25s para conexões lentas/mobile
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), options.timeout || 25000);
  config.signal = controller.signal;

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    clearTimeout(timeoutId);
    
    if (response.status === 401) {
      // Se não for rota de login/registro, limpa sessão expirada
      if (!endpoint.includes('/auth/login') && !endpoint.includes('/auth/register')) {
        localStorage.removeItem('finnk_token');
        localStorage.removeItem('finnk_user');
        window.dispatchEvent(new Event('auth:unauthorized'));
      }
    }

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      const errorMsg = (data && data.detail) || (data && data.message) || 'Ocorreu um erro ao processar sua solicitação.';
      throw new Error(errorMsg);
    }

    return data;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('Tempo limite esgotado. Verifique sua conexão ou tente novamente.');
    }
    throw error;
  }
}

export const api = {
  // Auth
  auth: {
    ping: () => {
      try {
        const rootUrl = new URL(API_BASE_URL).origin;
        return fetch(rootUrl, { method: 'GET', keepalive: true }).catch(() => null);
      } catch {
        return fetch(`${API_BASE_URL}/health`, { method: 'GET', keepalive: true }).catch(() => null);
      }
    },
    register: (body) => request('/auth/register', { method: 'POST', body }),
    login: (body) => request('/auth/login', { method: 'POST', body }),
    googleLogin: (body) => request('/auth/google', { method: 'POST', body }),
    forgotPassword: (body) => request('/auth/forgot-password', { method: 'POST', body }),
    resetPassword: (body) => request('/auth/reset-password', { method: 'POST', body }),
    getProfile: () => request('/auth/me'),
    updateProfile: (body) => request('/auth/me', { method: 'PUT', body }),
    changePassword: (body) => request('/auth/change-password', { method: 'POST', body }),
    seedDemo: () => request('/auth/seed-demo', { method: 'POST' }),
  },


  // Dashboard
  dashboard: {
    getHomeSummary: (month, year) => {
      const params = new URLSearchParams();
      if (month) params.append('month', month);
      if (year) params.append('year', year);
      const q = params.toString() ? `?${params.toString()}` : '';
      return request(`/dashboard/home-summary${q}`);
    },
    getAnalytics: (month, year) => {
      const params = new URLSearchParams();
      if (month) params.append('month', month);
      if (year) params.append('year', year);
      const q = params.toString() ? `?${params.toString()}` : '';
      return request(`/dashboard/analytics${q}`);
    },
  },

  // Contas
  accounts: {
    list: () => request('/accounts'),
    create: (body) => request('/accounts', { method: 'POST', body }),
    update: (id, body) => request(`/accounts/${id}`, { method: 'PUT', body }),
    delete: (id) => request(`/accounts/${id}`, { method: 'DELETE' }),
  },

  // Cartões
  cards: {
    list: () => request('/cards'),
    create: (body) => request('/cards', { method: 'POST', body }),
    update: (id, body) => request(`/cards/${id}`, { method: 'PUT', body }),
    delete: (id) => request(`/cards/${id}`, { method: 'DELETE' }),
    getInvoices: (id, month, year) => {
      const params = new URLSearchParams();
      if (month) params.append('month', month);
      if (year) params.append('year', year);
      const q = params.toString() ? `?${params.toString()}` : '';
      return request(`/cards/${id}/invoices${q}`);
    },
  },

  // Categorias
  categories: {
    list: (type, includeHidden = false) => {
      const params = new URLSearchParams();
      if (type) params.append('type', type);
      if (includeHidden) params.append('include_hidden', 'true');
      const q = params.toString() ? `?${params.toString()}` : '';
      return request(`/categories${q}`);
    },
    create: (body) => request('/categories', { method: 'POST', body }),
    update: (id, body) => request(`/categories/${id}`, { method: 'PUT', body }),
    delete: (id) => request(`/categories/${id}`, { method: 'DELETE' }),
  },

  // Transações & Compromissos
  transactions: {
    list: (filters = {}) => {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '') {
          params.append(k, v);
        }
      });
      const q = params.toString() ? `?${params.toString()}` : '';
      return request(`/transactions${q}`);
    },
    get: (id) => request(`/transactions/${id}`),
    create: (body) => request('/transactions', { method: 'POST', body }),
    update: (id, body) => request(`/transactions/${id}`, { method: 'PUT', body }),
    updateStatus: (id, status) => request(`/transactions/${id}/status`, { method: 'PATCH', body: { status } }),
    delete: (id) => request(`/transactions/${id}`, { method: 'DELETE' }),
  },

  // Compras Parceladas
  installments: {
    list: () => request('/installments'),
    get: (id) => request(`/installments/${id}`),
    create: (body) => request('/installments', { method: 'POST', body }),
    delete: (id, deleteMode = 'FUTURE_ONLY', forcePaid = false) => {
      const params = new URLSearchParams({
        delete_mode: deleteMode,
        force_paid: forcePaid ? 'true' : 'false',
      });
      return request(`/installments/${id}?${params.toString()}`, { method: 'DELETE' });
    },
  },

  // Recorrências
  recurring: {
    list: () => request('/recurring'),
    create: (body) => request('/recurring', { method: 'POST', body }),
    update: (id, body) => request(`/recurring/${id}`, { method: 'PUT', body }),
    toggle: (id) => request(`/recurring/${id}/toggle`, { method: 'PATCH' }),
    delete: (id) => request(`/recurring/${id}`, { method: 'DELETE' }),
  },

  // Orçamentos
  budgets: {
    list: (month, year) => {
      const params = new URLSearchParams();
      if (month) params.append('month', month);
      if (year) params.append('year', year);
      const q = params.toString() ? `?${params.toString()}` : '';
      return request(`/budgets${q}`);
    },
    set: (body) => request('/budgets', { method: 'POST', body }),
    delete: (id) => request(`/budgets/${id}`, { method: 'DELETE' }),
  },

  // Alertas
  alerts: {
    list: () => request('/alerts'),
    markRead: (id) => request(`/alerts/${id}/read`, { method: 'PATCH' }),
    markAllRead: () => request('/alerts/mark-all-read', { method: 'POST' }),
    delete: (id) => request(`/alerts/${id}`, { method: 'DELETE' }),
  },

  // Auditoria & LGPD
  user: {
    getAuditLogs: () => request('/user/audit-logs'),
    exportData: () => request('/user/export-data'),
    deleteAccount: () => request('/user/account', { method: 'DELETE' }),
    resetData: () => request('/user/reset-data', { method: 'POST' }),
    removeDemoData: () => request('/user/remove-demo-data', { method: 'POST' }),
  },
};


