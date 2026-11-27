export interface Persona {
  id: number;
  name: string;
  username: string;
  role: string;
  persona_type: string;
  monthly_income: number;
  credit_score: number;
  account_number: string;
  balance: number;
}

export interface CalculationNotes {
  formula: string;
  data_window: string;
  transaction_count: number;
  filters_applied: Record<string, any>;
  breakdown?: Record<string, any>;
  source_transaction_ids?: number[];
  calculation_summary: string;
}

export interface VerificationReport {
  passed: boolean;
  status: 'PASSED' | 'REGENERATED' | 'TEMPLATE_FALLBACK';
  verified_numbers?: string[];
  discrepancies?: string[];
  explanation: string;
}

export interface ChatMessage {
  id?: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  intent?: string;
  result_object?: any;
  calculation_notes?: CalculationNotes;
  verification?: VerificationReport;
  suggested_chips?: string[];
  latency_ms?: number;
  ai_status?: string;
  created_at?: string;
}

export interface SpendingSummary {
  customer_id: number;
  category: string;
  period: string;
  data_window: string;
  total_spent: number;
  formatted_total_spent: string;
  transaction_count: number;
  last_month_spent: number;
  formatted_last_month_spent: string;
  month_over_month_change_pct: number;
  top_merchants: Array<{ name: string; amount: number; formatted_amount: string }>;
  category_breakdown: Array<{ category: string; amount: number; formatted_amount: string; percentage: number }>;
  recurring_items: Array<{ merchant: string; category: string; amount: number; formatted_amount: string }>;
  savings_opportunities: string[];
  calculation_notes: CalculationNotes;
}

export interface CashFlowForecast {
  days_passed: number;
  days_remaining: number;
  spent_so_far: number;
  formatted_spent_so_far: string;
  daily_burn_rate: number;
  formatted_daily_burn_rate: string;
  projected_month_end_spend: number;
  formatted_projected_total: string;
  monthly_income: number;
  formatted_monthly_income: string;
  projected_savings: number;
  formatted_projected_savings: string;
}

export interface FraudRuleTriggered {
  rule: string;
  name: string;
  weight: number;
  reason: string;
}

export interface FraudAlertItem {
  alert_id: number;
  transaction_id: number;
  merchant: string;
  amount: number;
  formatted_amount: string;
  risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  status: string;
  user_feedback?: string;
  triggered_rules: FraudRuleTriggered[];
  created_at: string;
}

export interface FraudSummary {
  customer_id: number;
  total_alerts: number;
  high_risk_alerts: number;
  recent_alerts: FraudAlertItem[];
  risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  triggered_rules: FraudRuleTriggered[];
  recommended_action: string;
  calculation_notes: CalculationNotes;
}

export interface LoanPackage {
  principal: number;
  formatted_principal: string;
  annual_interest_rate: number;
  tenure_months: number;
  emi: number;
  formatted_emi: string;
  total_interest: number;
  formatted_total_interest: string;
  total_payment: number;
  formatted_total_payment: string;
  foir_pct: number;
  is_affordable: boolean;
  affordability_notes: string;
  prepayment_options?: any;
  balance_transfer?: any;
  calculation_notes: CalculationNotes;
}

export interface GuidancePlan {
  customer_id: number;
  monthly_income: number;
  formatted_income: string;
  needs_spent: number;
  wants_spent: number;
  savings_amount: number;
  needs_pct: number;
  wants_pct: number;
  savings_pct: number;
  target_split: { needs: number; wants: number; savings: number };
  emergency_fund_target: number;
  formatted_emergency_target: string;
  current_savings: number;
  savings_rate_trend: Array<{ month: string; savings_rate_pct: number; amount_saved: number }>;
  goals: Array<any>;
  what_if_scenario?: any;
  calculation_notes: CalculationNotes;
}

export interface ProductMatches {
  recommended_products: Array<{
    product_code: string;
    name: string;
    category: string;
    interest_rate_or_fee: string;
    reward_rate: string;
    fit_score: number;
    fit_reason: string;
    description: string;
    caveats?: string;
  }>;
  excluded_products: Array<{
    product_code: string;
    name: string;
    category: string;
    exclusion_reasons: string[];
    caveats?: string;
  }>;
  customer_profile: any;
  calculation_notes: CalculationNotes;
}

export interface RegulatoryCitation {
  document: string;
  section: string;
  text: string;
}

export interface RegulatoryResult {
  query: string;
  matched_documents: Array<{
    document_title: string;
    section: string;
    section_title: string;
    snippet: string;
    confidence: number;
    source_url?: string;
  }>;
  citations: RegulatoryCitation[];
  confidence: number;
  is_grounded: boolean;
  official_source_notice: string;
  calculation_notes: CalculationNotes;
}

export interface InvestmentPortfolio {
  risk_profile: string;
  recommended_allocation: Record<string, number>;
  current_holdings: Array<{
    id: number;
    asset_type: string;
    asset_name: string;
    invested_amount: number;
    formatted_invested: string;
    current_value: number;
    formatted_current: string;
    return_pct: number;
  }>;
  sip_simulation?: any;
  disclaimer: string;
  calculation_notes: CalculationNotes;
}

export interface AuditLogItem {
  id: number;
  request_id: string;
  timestamp: string;
  action_type: string;
  customer_id?: number;
  intent?: string;
  services_invoked?: string[];
  verification_status?: string;
  prev_hash: string;
  curr_hash: string;
  client_ip: string;
  notes?: string;
}
