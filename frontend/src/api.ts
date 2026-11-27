import {
  Persona, ChatMessage, SpendingSummary, CashFlowForecast,
  FraudSummary, LoanPackage, GuidancePlan, ProductMatches,
  RegulatoryResult, InvestmentPortfolio, AuditLogItem
} from './types';

const API_BASE = '/api/v1';

let authToken: string | null = localStorage.getItem('banking_auth_token');

export const setAuthToken = (token: string | null) => {
  authToken = token;
  if (token) {
    localStorage.setItem('banking_auth_token', token);
  } else {
    localStorage.removeItem('banking_auth_token');
  }
};

const getHeaders = () => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  };
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }
  return headers;
};

export const api = {
  // Auth
  async getPersonas(): Promise<Persona[]> {
    const res = await fetch(`${API_BASE}/auth/personas`);
    return res.json();
  },

  async switchPersona(userId: number): Promise<{ access_token: string; user: any }> {
    const res = await fetch(`${API_BASE}/auth/switch-persona/${userId}`, { method: 'POST' });
    const data = await res.json();
    setAuthToken(data.access_token);
    return data;
  },

  async getMe(): Promise<any> {
    const res = await fetch(`${API_BASE}/auth/me`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Not authenticated');
    return res.json();
  },

  async getHealth(): Promise<any> {
    const res = await fetch(`${API_BASE}/health`);
    return res.json();
  },

  // Chat
  async sendMessage(message: string, conversationId?: number, contextSlots?: any): Promise<ChatMessage> {
    const res = await fetch(`${API_BASE}/chat/message`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ message, conversation_id: conversationId, context_slots: contextSlots })
    });
    return res.json();
  },

  async getChatHistory(conversationId?: number): Promise<ChatMessage[]> {
    const res = await fetch(`${API_BASE}/chat/history${conversationId ? `?conversation_id=${conversationId}` : ''}`, {
      headers: getHeaders()
    });
    return res.json();
  },

  // Spending
  async getSpendingSummary(category?: string, period: string = 'current_month'): Promise<SpendingSummary> {
    const params = new URLSearchParams({ period });
    if (category) params.append('category', category);
    const res = await fetch(`${API_BASE}/spending/summary?${params.toString()}`, { headers: getHeaders() });
    return res.json();
  },

  async getCashflowForecast(): Promise<CashFlowForecast> {
    const res = await fetch(`${API_BASE}/spending/forecast`, { headers: getHeaders() });
    return res.json();
  },

  async checkTransfer(recipientName: string, amount: number, windowHours = 72): Promise<any> {
    const res = await fetch(`${API_BASE}/spending/check-transfer`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ recipient_name: recipientName, amount, window_hours: windowHours })
    });
    return res.json();
  },

  async executeTransfer(recipientName: string, amount: number, channel = 'UPI', category = 'Transfers'): Promise<any> {
    const res = await fetch(`${API_BASE}/spending/execute-transfer`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ recipient_name: recipientName, amount, channel, category })
    });
    return res.json();
  },

  // Loans
  async calculateLoan(principal: number, rate: number, tenureMonths: number): Promise<LoanPackage> {
    const res = await fetch(`${API_BASE}/loans/calculate?principal=${principal}&rate=${rate}&tenure_months=${tenureMonths}`, {
      headers: getHeaders()
    });
    return res.json();
  },

  async getAmortisationSchedule(principal: number, rate: number, tenureMonths: number, limit = 24): Promise<any[]> {
    const res = await fetch(`${API_BASE}/loans/amortisation-schedule?principal=${principal}&rate=${rate}&tenure_months=${tenureMonths}&limit=${limit}`, {
      headers: getHeaders()
    });
    return res.json();
  },

  async getPrepaymentImpact(principal: number, rate: number, tenureMonths: number, prepaymentAmount: number, prepaymentMonth = 12): Promise<any> {
    const res = await fetch(`${API_BASE}/loans/prepayment-whatif?principal=${principal}&rate=${rate}&tenure_months=${tenureMonths}&prepayment_amount=${prepaymentAmount}&prepayment_month=${prepaymentMonth}`, {
      headers: getHeaders()
    });
    return res.json();
  },

  // Fraud
  async getFraudSummary(): Promise<FraudSummary> {
    const res = await fetch(`${API_BASE}/fraud/summary`, { headers: getHeaders() });
    return res.json();
  },

  async reviewFraudAlert(alertId: number, feedback: 'THIS_WAS_ME' | 'THIS_WAS_NOT_ME'): Promise<any> {
    const res = await fetch(`${API_BASE}/fraud/review/${alertId}`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ feedback })
    });
    return res.json();
  },

  async simulateFraud(scenario = 'outlier'): Promise<any> {
    const res = await fetch(`${API_BASE}/fraud/simulate?scenario=${scenario}`, {
      method: 'POST',
      headers: getHeaders()
    });
    return res.json();
  },

  // Guidance
  async getGuidancePlan(diningCut = 0, shoppingCut = 0): Promise<GuidancePlan> {
    const res = await fetch(`${API_BASE}/guidance/plan?dining_cut=${diningCut}&shopping_cut=${shoppingCut}`, {
      headers: getHeaders()
    });
    return res.json();
  },

  // Products
  async getProductRecommendations(category?: string): Promise<ProductMatches> {
    const res = await fetch(`${API_BASE}/products/recommendations${category ? `?category=${category}` : ''}`, {
      headers: getHeaders()
    });
    return res.json();
  },

  // Investments
  async getInvestmentPortfolio(sipMonthly?: number): Promise<InvestmentPortfolio> {
    const res = await fetch(`${API_BASE}/investments/portfolio${sipMonthly ? `?sip_monthly=${sipMonthly}` : ''}`, {
      headers: getHeaders()
    });
    return res.json();
  },

  async calculateSip(monthly: number, returnPct: number, years: number): Promise<any> {
    const res = await fetch(`${API_BASE}/investments/sip-calculator?monthly_investment=${monthly}&expected_return_pct=${returnPct}&tenure_years=${years}`, {
      headers: getHeaders()
    });
    return res.json();
  },

  // Regulatory RAG
  async searchKnowledge(query: string): Promise<RegulatoryResult> {
    const res = await fetch(`${API_BASE}/knowledge/search?q=${encodeURIComponent(query)}`, {
      headers: getHeaders()
    });
    return res.json();
  },

  async getKnowledgeDocuments(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/knowledge/documents`, { headers: getHeaders() });
    return res.json();
  },

  // Audit
  async getAuditLogs(limit = 50): Promise<AuditLogItem[]> {
    const res = await fetch(`${API_BASE}/audit/logs?limit=${limit}`, { headers: getHeaders() });
    return res.json();
  },

  async verifyAuditChain(): Promise<any> {
    const res = await fetch(`${API_BASE}/audit/verify-chain`, { headers: getHeaders() });
    return res.json();
  },

  // Quality & Eval Harness
  async getQualityMetrics(): Promise<any> {
    const res = await fetch(`${API_BASE}/quality/metrics`, { headers: getHeaders() });
    return res.json();
  },

  async runBenchmark(): Promise<any> {
    const res = await fetch(`${API_BASE}/quality/run-benchmark`, {
      method: 'POST',
      headers: getHeaders()
    });
    return res.json();
  }
};
