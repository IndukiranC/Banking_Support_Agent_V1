from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class LoginRequest(BaseModel):
    username: str
    password: str

class PersonaInfo(BaseModel):
    id: int
    name: str
    username: str
    role: str
    persona_type: str
    monthly_income: float
    credit_score: int
    account_number: str
    balance: float

# Structured Intent Schema (used for Ollama Structured Output)
class ParsedIntent(BaseModel):
    intent: str = Field(
        ..., 
        description="One of: spending_summary, loan_calculator, fraud_inquiry, budget_guidance, product_recommendation, investment_info, regulatory_rag, transfer_check, account_balance, greeting, recent_transactions, human_handoff, general_banking_faq, out_of_scope"
    )
    category: Optional[str] = Field(None, description="Spending or product category (e.g. food, shopping, utilities, travel)")
    period: Optional[str] = Field("current_month", description="Time period: current_month, last_month, last_30_days, year_to_date, custom")
    amount: Optional[float] = Field(None, description="Numeric amount mentioned in query, e.g. 500000 or 4000000")
    tenure_months: Optional[int] = Field(None, description="Tenure in months, e.g. 240 for 20 years or 60 for 5 years")
    interest_rate: Optional[float] = Field(None, description="Interest rate percentage, e.g. 8.5")
    wants_advice: bool = Field(False, description="Whether user explicitly asked for advice or ways to reduce spending/save money")
    confidence: float = Field(1.0, description="Confidence score from 0.0 to 1.0")
    missing_slots: List[str] = Field(default_factory=list, description="List of required slots that were not found in user query")
    clarifying_question: Optional[str] = Field(None, description="Question to ask user if critical slots are missing")

# Calculation Notes Schema ("Show Your Work")
class CalculationNotes(BaseModel):
    formula: str
    data_window: str
    transaction_count: int
    filters_applied: Dict[str, Any]
    breakdown: Optional[Dict[str, Any]] = None
    source_transaction_ids: List[int] = []
    calculation_summary: str

# Result Objects (Deterministic Truth from Python Services)
class SpendingResultObject(BaseModel):
    customer_id: int
    category: str
    period: str
    data_window: str
    total_spent: float
    formatted_total_spent: str
    transaction_count: int
    last_month_spent: float
    formatted_last_month_spent: str
    month_over_month_change_pct: float
    top_merchants: List[Dict[str, Any]]
    category_breakdown: List[Dict[str, Any]]
    recurring_items: List[Dict[str, Any]]
    savings_opportunities: List[str]
    calculation_notes: CalculationNotes

class LoanResultObject(BaseModel):
    principal: float
    formatted_principal: str
    annual_interest_rate: float
    tenure_months: int
    emi: float
    formatted_emi: str
    total_interest: float
    formatted_total_interest: str
    total_payment: float
    formatted_total_payment: str
    foir_pct: float
    is_affordable: bool
    affordability_notes: str
    prepayment_options: Optional[Dict[str, Any]] = None
    balance_transfer: Optional[Dict[str, Any]] = None
    calculation_notes: CalculationNotes

class FraudResultObject(BaseModel):
    customer_id: int
    total_alerts: int
    high_risk_alerts: int
    recent_alerts: List[Dict[str, Any]]
    active_inquiry: Optional[Dict[str, Any]] = None
    risk_score: int
    risk_level: str
    triggered_rules: List[Dict[str, Any]]
    recommended_action: str
    calculation_notes: CalculationNotes

class GuidanceResultObject(BaseModel):
    customer_id: int
    monthly_income: float
    formatted_income: str
    needs_spent: float
    wants_spent: float
    savings_amount: float
    needs_pct: float
    wants_pct: float
    savings_pct: float
    target_split: Dict[str, float]
    emergency_fund_target: float
    formatted_emergency_target: str
    current_savings: float
    savings_rate_trend: List[Dict[str, Any]]
    goals: List[Dict[str, Any]]
    what_if_scenario: Optional[Dict[str, Any]] = None
    calculation_notes: CalculationNotes

class ProductResultObject(BaseModel):
    recommended_products: List[Dict[str, Any]]
    excluded_products: List[Dict[str, Any]]
    customer_profile: Dict[str, Any]
    calculation_notes: CalculationNotes

class InvestmentResultObject(BaseModel):
    risk_profile: str
    recommended_allocation: Dict[str, float]
    current_holdings: List[Dict[str, Any]]
    sip_simulation: Optional[Dict[str, Any]] = None
    disclaimer: str
    calculation_notes: CalculationNotes

class RegulatoryResultObject(BaseModel):
    query: str
    matched_documents: List[Dict[str, Any]]
    citations: List[Dict[str, str]]
    confidence: float
    is_grounded: bool
    official_source_notice: str
    calculation_notes: CalculationNotes

# Chat Message & Flow
class CheckTransferRequest(BaseModel):
    recipient_name: str
    amount: float
    window_hours: Optional[int] = 72

class ExecuteTransferRequest(BaseModel):
    recipient_name: str
    amount: float
    channel: Optional[str] = "UPI"
    category: Optional[str] = "Transfers"

class ChatMessageRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    context_slots: Optional[Dict[str, Any]] = None

class VerificationReport(BaseModel):
    passed: bool
    status: str  # PASSED, REGENERATED, TEMPLATE_FALLBACK
    verified_numbers: List[str] = []
    discrepancies: List[str] = []
    explanation: str

class ChatMessageResponse(BaseModel):
    conversation_id: int
    reply: str
    intent: str
    result_object: Optional[Dict[str, Any]] = None
    calculation_notes: Optional[CalculationNotes] = None
    verification: VerificationReport
    suggested_chips: List[str] = []
    latency_ms: int
    ai_status: str  # "OLLAMA_LLAMA3_1" or "OFFLINE_RULE_FALLBACK"
