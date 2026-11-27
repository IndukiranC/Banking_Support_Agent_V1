import re
import json
import logging
import datetime
from typing import Dict, Any, List, Optional, Tuple, Iterator
from sqlalchemy.orm import Session
from backend.models import Customer, Conversation, Message
from backend.schemas import (
    ParsedIntent, CalculationNotes, VerificationReport,
    ChatMessageResponse
)
from backend.ollama_client import OllamaClient, OllamaUnavailableError
from backend.verifier import OutputVerifier
from backend.services.spending_service import SpendingService
from backend.services.loan_service import LoanService
from backend.services.fraud_service import FraudService
from backend.services.guidance_service import GuidanceService
from backend.services.recommendation_service import RecommendationService
from backend.services.investment_service import InvestmentService
from backend.services.knowledge_service import KnowledgeService
from backend.services.audit_service import AuditService
from backend.config import format_inr

logger = logging.getLogger(__name__)

class InputGuard:
    """
    Multi-layer prompt injection defense and input sanitization.
    """
    INJECTION_PATTERNS = [
        r'ignore\s+(?:all\s+)?(?:previous|prior)?\s*(?:instructions|prompts|directions|guidelines|constraints|rules|safety\s+protocols|restrictions)',
        r'disregard\s+(?:all\s+)?(?:previous|prior|earlier)?\s*(?:instructions|prompts|directions|commands|limits|guidance|directives|safety\s+filters)',
        r'system\s*:\s*',
        r'<\|im_start\|>',
        r'<\|im_end\|>',
        r'show\s+(?:me\s+)?all\s+(?:customers|users|passwords|secrets|tokens)',
        r'show\s+(?:me\s+)?confidential\s+employee',
        r'show\s+(?:me\s+)?(?:user|customer)\s+\d+[\'s]*\s+(?:transactions|bank balance|account|pan|credit score)',
        r'select\s+\*\s+from',
        r'drop\s+table',
        r'delete\s+from\s+(?:users|transactions|audit_log)',
        r'bypass\s+(?:auth|verification|security)',
        r'you\s+are\s+now\s+(?:in\s+developer\s+mode|dan|an\s+unrestricted)',
        r'jailbreak',
        r'print\s+(?:your\s+)?(?:exact\s+)?system\s+prompt',
        r'tell\s+me\s+how\s+to\s+(?:hack|clone|forge|evade)',
        r'show\s+(?:me\s+)?secret\s+tokens',
        r'secret\s+encryption\s+key',
        r'private\s+keys?\s+used',
        r'argon2\s+password\s+hashes',
        r'pwned',
        r'rm\s+-rf',
        r'database\s+(?:password|dump)',
        r'override\s+security',
        r'grant\s+(?:root|customer\s+1\s+admin)',
        r'unauthorized\s+withdrawal',
        r'switch\s+customer_id\s+in\s+session',
        r'no\s+longer\s+bound\s+by\s+banking',
        r'tell\s+me\s+the\s+pan\s+card\s+and\s+phone\s+number\s+of\s+customer',
        r'simulate\s+an\s+authorized\s+transfer.*without\s+confirmation',
        r'output\s+raw\s+sql',
        r'disable\s+the\s+output\s+verifier',
        r'security_bypassed'
    ]

    @classmethod
    def screen_input(cls, user_text: str) -> Tuple[bool, str, Optional[str]]:
        """
        Screen untrusted user input.
        Returns: (is_safe, sanitized_text, refusal_reason)
        """
        text = user_text.strip()
        if len(text) == 0:
            return False, "", "Empty input received."
        if len(text) > 1000:
            return False, text[:1000], "Input exceeded maximum permitted length (1,000 characters)."

        lower = text.lower()
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                logger.warning(f"Prompt injection screened: matched pattern '{pattern}'")
                return False, text, "Security policy violation: Suspicious directive or prompt injection attempt detected."

        return True, text, None

    @classmethod
    def wrap_user_content(cls, text: str) -> str:
        """Wrap untrusted text in strict XML tags to prevent jailbreak leakage."""
        clean = text.replace("<user_input>", "").replace("</user_input>", "")
        return f"<user_input>\n{clean}\n</user_input>"


class IntentRouter:
    """
    Dual-engine Intent Router:
    1. Primary: Local LLM structured JSON extraction via Ollama
    2. Fallback: High-precision Rule & Keyword Pattern Engine
    """

    INTENT_KEYWORDS = {
        "spending_summary": [
            "spend", "spent", "spending", "expense", "expenses", "transactions",
            "purchases", "cost", "how much did i spend", "debits", "outlay", "kharcha"
        ],
        "loan_calculator": [
            "loan", "emi", "mortgage", "home loan", "interest rate", "tenure",
            "amortisation", "amortization", "prepayment", "afford", "borrow"
        ],
        "fraud_inquiry": [
            "fraud", "suspicious", "alert", "stolen", "unauthorized", "unrecognised",
            "flagged", "anomaly", "compromised", "scam", "blocked", "freeze"
        ],
        "budget_guidance": [
            "budget", "50/30/20", "saving", "savings", "guidance", "emergency fund",
            "goal", "financial plan", "reduce spending", "cut down"
        ],
        "product_recommendation": [
            "recommend", "card", "credit card", "offer", "upgrade", "best product",
            "fixed deposit", "fd", "savings account", "rewards"
        ],
        "investment_info": [
            "invest", "investment", "portfolio", "sip", "mutual fund", "stocks",
            "shares", "equity", "gold", "asset allocation", "returns"
        ],
        "regulatory_rag": [
            "kyc", "rbi", "regulation", "pmla", "dicgc", "ombudsman", "rule",
            "guideline", "documents", "aadhaar", "ovd", "dormant", "inoperative", "limit"
        ],
        "human_handoff": [
            "human", "agent", "representative", "officer", "manager", "support desk",
            "talk to person", "complaint"
        ]
    }

    @classmethod
    def route_with_rules(cls, text: str, context_slots: Optional[Dict[str, Any]] = None) -> ParsedIntent:
        """Deterministic rule-based intent router."""
        lower = text.lower()
        slots = context_slots or {}

        # 0. Extract numeric amounts early (e.g. 40 lakh, 50000, 1500)
        amount = None
        lakh_m = re.search(r'(\d+(?:\.\d+)?)\s*(?:lakhs?|lacs?)', lower)
        if lakh_m:
            amount = float(lakh_m.group(1)) * 100_000
        else:
            crore_m = re.search(r'(\d+(?:\.\d+)?)\s*(?:crores?|crs?)', lower)
            if crore_m:
                amount = float(crore_m.group(1)) * 10_000_000
            else:
                amt_m = re.search(r'(?:₹|rs\.?)?\s*(\d{3,})', lower)
                if amt_m:
                    amount = float(amt_m.group(1))

        # 1. Check for human handoff
        if any(kw in lower for kw in cls.INTENT_KEYWORDS["human_handoff"]):
            return ParsedIntent(intent="human_handoff", confidence=1.0)

        # 2. Check for greetings & self-introduction
        greeting_words = ["hi", "hello", "hey", "namaste", "hola", "greetings", "good morning", "good evening", "good afternoon"]
        if any(re.search(rf'\b{re.escape(w)}\b', lower) for w in greeting_words) or any(phrase in lower for phrase in ["who are you", "what can you do", "help me", "can you help"]):
            return ParsedIntent(intent="greeting", confidence=1.0)

        # 3. Check for account balance inquiries
        balance_keywords = ["balance", "how much money", "account balance", "liquid balance", "my funds", "check balance", "how much do i have", "how much in my account", "available balance", "what is my balance"]
        if any(kw in lower for kw in balance_keywords):
            return ParsedIntent(intent="account_balance", confidence=0.98)

        # 4. Check for recent transaction history / statements
        recent_tx_keywords = ["recent transactions", "transaction history", "last transactions", "past payments", "recent debits", "passbook", "show transactions", "show my transactions"]
        recent_tx_keywords = [
            "recent transactions", "transaction history", "last transactions", "last transaction",
            "latest transaction", "most recent transaction", "previous payment", "past payments",
            "recent debits", "passbook", "show transactions", "show my transactions"
        ]
        if any(kw in lower for kw in recent_tx_keywords):
            return ParsedIntent(intent="recent_transactions", confidence=0.98)

        # 5. Check transfer or repeated transaction inquiry
        transfer_keywords = ["transfer", "send money", "repeat transaction", "duplicate transaction", "repeated transaction", "pay to", "send to", "send rs", "send ₹"]
        is_transfer = any(kw in lower for kw in transfer_keywords) or (re.search(r'\b(send|transfer|pay|remit)\b', lower) and (re.search(r'\bto\b', lower) or re.search(r'\d+', lower)))
        if is_transfer:
            recipient = None
            for name in ["Kishan", "Manasa", "Indukiran", "Manjunath"]:
                if name.lower() in lower:
                    recipient = name
                    break
            if not recipient:
                to_m = re.search(r'(?:to|payee)\s+([a-zA-Z]+)', text, re.IGNORECASE)
                if to_m:
                    recipient = to_m.group(1).title()
            return ParsedIntent(
                intent="transfer_check",
                category=recipient or "Kishan",
                amount=amount or 5000.0,
                confidence=0.95
            )

        # 6. Extract potential category
        category = slots.get("category")
        for cat in SpendingService.CATEGORIES:
            cat_words = cat.lower().replace("&", "").split()
            if any(w in lower for w in cat_words if len(w) > 3):
                category = cat
                break
        if not category and ("food" in lower or "dining" in lower or "swiggy" in lower or "zomato" in lower):
            category = "Food & Dining"
        elif not category and ("shop" in lower or "amazon" in lower or "flipkart" in lower):
            category = "Shopping"

        # 7. Check time period
        period = "current_month"
        if "last month" in lower or "previous month" in lower:
            period = "last_month"
        elif "year" in lower:
            period = "year_to_date"

        # 5. Check loan indicators
        if any(kw in lower for kw in cls.INTENT_KEYWORDS["loan_calculator"]):
            tenure = 240 # default 20 years
            tenure_m = re.search(r'(\d+)\s*(?:years?|yrs?)', lower)
            if tenure_m:
                tenure = int(tenure_m.group(1)) * 12
            else:
                month_m = re.search(r'(\d+)\s*(?:months?|mths?)', lower)
                if month_m:
                    tenure = int(month_m.group(1))

            rate = 8.5 # standard floating rate
            rate_m = re.search(r'(\d+(?:\.\d+)?)\s*%', lower)
            if rate_m:
                rate = float(rate_m.group(1))

            return ParsedIntent(
                intent="loan_calculator",
                amount=amount or 4000000.0, # default 40 Lakhs if unstated
                tenure_months=tenure,
                interest_rate=rate,
                confidence=0.95
            )

        # 6. Check fraud indicators
        if any(kw in lower for kw in cls.INTENT_KEYWORDS["fraud_inquiry"]):
            return ParsedIntent(intent="fraud_inquiry", confidence=0.95)

        # 7. Check regulatory RAG
        if any(kw in lower for kw in cls.INTENT_KEYWORDS["regulatory_rag"]):
            return ParsedIntent(intent="regulatory_rag", confidence=0.95)

        # 8. Check budget guidance
        if any(kw in lower for kw in cls.INTENT_KEYWORDS["budget_guidance"]):
            wants_advice = "how can i" in lower or "reduce" in lower or "cut" in lower or "save" in lower
            return ParsedIntent(
                intent="budget_guidance",
                category=category,
                wants_advice=wants_advice,
                confidence=0.90
            )

        # 9. Check products
        if any(kw in lower for kw in cls.INTENT_KEYWORDS["product_recommendation"]):
            return ParsedIntent(intent="product_recommendation", category=category, confidence=0.90)

        # 10. Check investment
        if any(kw in lower for kw in cls.INTENT_KEYWORDS["investment_info"]):
            return ParsedIntent(intent="investment_info", amount=amount, confidence=0.90)

        # 12. Check spending summary
        if any(kw in lower for kw in cls.INTENT_KEYWORDS["spending_summary"]) or category:
            wants_advice = "reduce" in lower or "cut" in lower or "save" in lower or "advice" in lower
            return ParsedIntent(
                intent="spending_summary",
                category=category,
                period=period,
                wants_advice=wants_advice,
                confidence=0.92
            )

        # Default fallback
        return ParsedIntent(intent="general_banking_faq", confidence=0.70)

    @classmethod
    def route_with_llm(cls, text: str, context_slots: Optional[Dict[str, Any]] = None) -> ParsedIntent:
        """Fast-path deterministic router with LLM fallback."""
        rule_res = cls.route_with_rules(text, context_slots)
        if rule_res.confidence >= 0.85 and rule_res.intent != "general_banking_faq":
            return rule_res

        ollama = OllamaClient.get_instance()
        if not ollama.is_available():
            return rule_res

        system_prompt = (
            "You are a strict financial intent extraction engine. "
            "Analyze the user message and extract intent, category, period, amount, tenure_months, interest_rate, and wants_advice. "
            "Output ONLY valid JSON matching this schema:\n"
            "{\n"
            '  "intent": "spending_summary" | "loan_calculator" | "fraud_inquiry" | "budget_guidance" | "product_recommendation" | "investment_info" | "regulatory_rag" | "transfer_check" | "account_balance" | "greeting" | "recent_transactions" | "human_handoff" | "general_banking_faq" | "out_of_scope",\n'
            '  "category": string or null,\n'
            '  "period": "current_month" | "last_month" | "year_to_date",\n'
            '  "amount": number or null,\n'
            '  "tenure_months": integer or null,\n'
            '  "interest_rate": number or null,\n'
            '  "wants_advice": boolean\n'
            "}"
        )

        user_content = f"User message: {text}\nActive context slots: {json.dumps(context_slots or {})}"

        try:
            resp = ollama.generate(prompt=user_content, system=system_prompt, format_json=True, temperature=0.0)
            data = json.loads(resp)
            parsed = ParsedIntent(**data)
            return parsed
        except Exception as e:
            logger.info(f"Ollama structured intent parsing failed ({e}), using rule-based router.")
            return rule_res
            return cls.route_with_rules(text, context_slots)


class ConversationOrchestrator:
    """
    Core Conversation Orchestrator:
    - Enforces Customer ID from authenticated session only (Zero-Trust LLM)
    - Coordinates InputGuard -> IntentRouter -> Services -> ResponseComposer -> OutputVerifier -> AuditService
    """

    @classmethod
    def process_turn(
        cls,
        db: Session,
        customer_id: int,
        user_text: str,
        conversation_id: Optional[int] = None,
        context_slots: Optional[Dict[str, Any]] = None,
        client_ip: str = "127.0.0.1"
    ) -> ChatMessageResponse:
        start_time = datetime.datetime.utcnow()
        request_id = f"REQ-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{customer_id}"

        # 1. Screen input with InputGuard
        is_safe, sanitized_text, refusal = InputGuard.screen_input(user_text)
        if not is_safe:
            AuditService.log_event(
                db=db,
                request_id=request_id,
                action_type="INPUT_SCREENING_REJECTION",
                customer_id=customer_id,
                client_ip=client_ip,
                notes=refusal
            )
            return ChatMessageResponse(
                conversation_id=conversation_id or 1,
                reply=f"⚠️ Request Rejected: {refusal}",
                intent="security_violation",
                result_object=None,
                calculation_notes=None,
                verification=VerificationReport(
                    passed=True,
                    status="PASSED",
                    explanation="Input blocked by security filter."
                ),
                suggested_chips=["Check my balance", "How much did I spend this month?", "View fraud alerts"],
                latency_ms=10,
                ai_status="OFFLINE_RULE_FALLBACK"
            )

        # 2. Extract Intent
        parsed_intent = IntentRouter.route_with_llm(sanitized_text, context_slots)
        intent = parsed_intent.intent

        # 3. Dispatch to deterministic service based on intent
        services_invoked = []
        result_object: Dict[str, Any] = {}
        calc_notes: Optional[CalculationNotes] = None

        if intent == "spending_summary":
            services_invoked.append("SpendingService")
            res = SpendingService.get_spending_summary(
                db=db,
                customer_id=customer_id,
                category=parsed_intent.category,
                period=parsed_intent.period or "current_month"
            )
            result_object = res.model_dump()
            calc_notes = res.calculation_notes

        elif intent == "loan_calculator":
            services_invoked.append("LoanService")
            cust = db.query(Customer).filter(Customer.id == customer_id).first()
            income = cust.monthly_income if cust else 100000.0
            res = LoanService.calculate_loan_package(
                principal=parsed_intent.amount or 4000000.0,
                annual_rate_pct=parsed_intent.interest_rate or 8.5,
                tenure_months=parsed_intent.tenure_months or 240,
                monthly_income=income
            )
            result_object = res.model_dump()
            calc_notes = res.calculation_notes

        elif intent == "fraud_inquiry":
            services_invoked.append("FraudService")
            res = FraudService.get_fraud_summary(db=db, customer_id=customer_id)
            result_object = res.model_dump()
            calc_notes = res.calculation_notes

        elif intent == "budget_guidance":
            services_invoked.append("GuidanceService")
            dining_cut = 20.0 if parsed_intent.wants_advice else 0.0
            res = GuidanceService.calculate_budget_guidance(
                db=db,
                customer_id=customer_id,
                dining_reduction_pct=dining_cut
            )
            result_object = res.model_dump()
            calc_notes = res.calculation_notes

        elif intent == "product_recommendation":
            services_invoked.append("RecommendationService")
            res = RecommendationService.get_recommendations(
                db=db,
                customer_id=customer_id,
                category=parsed_intent.category
            )
            result_object = res.model_dump()
            calc_notes = res.calculation_notes

        elif intent == "investment_info":
            services_invoked.append("InvestmentService")
            res = InvestmentService.get_investment_portfolio(
                db=db,
                customer_id=customer_id,
                sip_monthly=parsed_intent.amount or 10000.0
            )
            result_object = res.model_dump()
            calc_notes = res.calculation_notes

        elif intent == "regulatory_rag":
            services_invoked.append("KnowledgeService")
            res = KnowledgeService.query_regulatory_corpus(db=db, query_text=sanitized_text)
            result_object = res.model_dump()
            calc_notes = res.calculation_notes

        elif intent == "transfer_check":
            services_invoked.append("SpendingService.check_repeated_transfer")
            recipient = parsed_intent.category or "Kishan"
            transfer_amount = parsed_intent.amount or 5000.0
            check_res = SpendingService.check_repeated_transfer(
                db=db,
                customer_id=customer_id,
                recipient_name=recipient,
                amount=transfer_amount
            )
            result_object = check_res
            calc_notes = CalculationNotes(
                formula="72-Hour Payee Duplicate Window Check",
                data_window="Past 72 hours",
                transaction_count=1 if check_res.get("is_repeated") else 0,
                filters_applied={"recipient": recipient, "amount": transfer_amount, "window_hours": 72},
                calculation_summary=check_res.get("message", "")
            )

        elif intent == "account_balance":
            services_invoked.append("AccountBalanceService")
            cust = db.query(Customer).filter(Customer.id == customer_id).first()
            acc = cust.accounts[0] if cust and cust.accounts else None
            bal = acc.balance if acc else 0.0
            acc_num = acc.account_number if acc else "0000000000"
            result_object = {
                "customer_name": f"{cust.first_name} {cust.last_name}" if cust else "Valued Customer",
                "balance": bal,
                "formatted_balance": format_inr(bal),
                "masked_account": f"****{acc_num[-4:]}",
                "formatted_income": format_inr(cust.monthly_income if cust else 0),
                "credit_score": cust.credit_score if cust else 750
            }
            calc_notes = CalculationNotes(
                formula="Live Ledger Balance Verification",
                data_window="Real-time",
                transaction_count=0,
                filters_applied={"account_id": acc.id if acc else None},
                calculation_summary=f"Balance verified at {format_inr(bal)} for account ****{acc_num[-4:]}"
            )

        elif intent == "recent_transactions":
            services_invoked.append("RecentTransactionsService")
            cust = db.query(Customer).filter(Customer.id == customer_id).first()
            from backend.models import Transaction
            txs = db.query(Transaction).filter(
                Transaction.customer_id == customer_id
            ).order_by(Transaction.timestamp.desc()).limit(6).all()
            result_object = {
                "customer_name": f"{cust.first_name} {cust.last_name}" if cust else "Valued Customer",
                "transactions": [
                    {
                        "date": t.timestamp.strftime("%d %b %Y"),
                        "merchant": t.merchant_name,
                        "amount": t.amount,
                        "formatted_amount": format_inr(t.amount),
                        "category": t.category,
                        "channel": t.channel
                    } for t in txs
                ]
            }
            calc_notes = CalculationNotes(
                formula="Top 6 Recent Journal Entries",
                data_window="Latest",
                transaction_count=len(txs),
                filters_applied={"limit": 6},
                calculation_summary=f"Retrieved {len(txs)} verified transactions from database."
            )

        elif intent == "greeting":
            services_invoked.append("GreetingService")
            cust = db.query(Customer).filter(Customer.id == customer_id).first()
            acc = cust.accounts[0] if cust and cust.accounts else None
            bal = acc.balance if acc else 0.0
            result_object = {
                "customer_name": f"{cust.first_name} {cust.last_name}" if cust else "there",
                "balance": bal,
                "formatted_balance": format_inr(bal)
            }
            calc_notes = CalculationNotes(
                formula="Deterministic Session Welcome Protocol",
                data_window="Current Session",
                transaction_count=0,
                filters_applied={},
                calculation_summary="Session greeting composed with live account context."
            )

        elif intent == "human_handoff":
            services_invoked.append("HumanHandoffStub")
            result_object = {
                "support_channel": "Priority Relationship Desk",
                "phone": "1800-202-BANK",
                "hours": "24/7 Priority Support",
                "ticket_created": f"TKT-{datetime.datetime.utcnow().strftime('%H%M%S')}"
            }
            calc_notes = CalculationNotes(
                formula="Direct Human Banker Routing Protocol",
                data_window="Live",
                transaction_count=0,
                filters_applied={},
                calculation_summary="Request routed to specialized customer support agent."
            )

        else: # general or out of scope
            services_invoked.append("GeneralBankingService")
            cust = db.query(Customer).filter(Customer.id == customer_id).first()
            acc = cust.accounts[0] if cust and cust.accounts else None
            bal = acc.balance if acc else 0.0
            result_object = {
                "customer_name": f"{cust.first_name} {cust.last_name}" if cust else "there",
                "balance": bal,
                "formatted_balance": format_inr(bal),
                "message": "Welcome to Antigravity Banking Assistant. I specialize in spending insights, loans & EMI, fraud alerts, budgeting, and RBI regulatory guidance."
            }
            calc_notes = CalculationNotes(
                formula="General Domain Policy Filter",
                data_window="N/A",
                transaction_count=0,
                filters_applied={},
                calculation_summary="General banking capabilities overview with live context."
            )

        # 4. Compose Narrative with LLM (or Fallback Template)
        ollama = OllamaClient.get_instance()
        ai_online = ollama.is_available()
        final_reply = ""
        verification_status = "PASSED"
        verification_rep = VerificationReport(passed=True, status="PASSED", explanation="Deterministic template used.")

        if ai_online and intent in [
            "spending_summary", "loan_calculator", "fraud_inquiry", "budget_guidance",
            "product_recommendation", "investment_info", "regulatory_rag"
        ]:
            system_prompt = (
                "You are Antigravity Banking Assistant: a friendly, highly professional, precise banking advisor.\n"
                "CRITICAL RULES:\n"
                "1. You must ONLY use the exact figures, percentages, dates, and names provided in the RESULT_OBJECT JSON below.\n"
                "2. DO NOT invent, hallucinate, or alter any number or monetary amount.\n"
                "3. If advice was requested, provide 2 actionable bullet points based strictly on the savings_opportunities in the JSON.\n"
                "4. Format currency figures with the Rupee symbol (₹) and Indian comma grouping (e.g. ₹42,500).\n"
                "5. Keep the response concise, structured, and easy to read."
            )

            prompt_text = (
                f"User Question:\n{sanitized_text}\n\n"
                f"Computed RESULT_OBJECT (Deterministic Truth):\n{json.dumps(result_object, indent=2)}\n\n"
                "Write the helpful response to the customer:"
            )

            try:
                # First generation attempt
                candidate_text = ollama.generate(prompt=prompt_text, system=system_prompt, temperature=0.1)
                
                # Verify candidate text
                verification_rep = OutputVerifier.verify(candidate_text, result_object)
                
                if verification_rep.passed:
                    final_reply = candidate_text
                    verification_status = "PASSED"
                else:
                    logger.info(f"Numeric verification discrepancy detected: {verification_rep.discrepancies}. Retrying with correction.")
                    # One retry attempt with correction prompt
                    correction_prompt = (
                        f"{prompt_text}\n\n"
                        f"CORRECTION NOTICE: Your previous answer contained unverified numbers: {verification_rep.discrepancies}. "
                        "Regenerate using ONLY the exact figures from RESULT_OBJECT."
                    )
                    retry_text = ollama.generate(prompt=correction_prompt, system=system_prompt, temperature=0.0)
                    retry_ver = OutputVerifier.verify(retry_text, result_object)
                    
                    if retry_ver.passed:
                        final_reply = retry_text
                        verification_status = "REGENERATED"
                        verification_rep = retry_ver
                    else:
                        logger.warning("Retry also failed numeric verification. Falling back to deterministic template.")
                        final_reply = OutputVerifier.build_deterministic_template(intent, result_object)
                        verification_status = "TEMPLATE_FALLBACK"
                        verification_rep = VerificationReport(
                            passed=True,
                            status="TEMPLATE_FALLBACK",
                            explanation="Deterministic template engaged following verification discrepancy."
                        )
            except Exception as e:
                logger.warning(f"Ollama generation failed ({e}), using deterministic template.")
                final_reply = OutputVerifier.build_deterministic_template(intent, result_object)
                verification_status = "TEMPLATE_FALLBACK"
                verification_rep = VerificationReport(
                    passed=True,
                    status="TEMPLATE_FALLBACK",
                    explanation="AI service unavailable. Answer produced by deterministic template."
                )
        else:
            final_reply = OutputVerifier.build_deterministic_template(intent, result_object)
            verification_status = "TEMPLATE_FALLBACK" if not ai_online else "PASSED"

        # 5. Suggested follow-up chips
        suggested_chips = cls._generate_chips(intent, parsed_intent)

        # 6. Latency & Audit Logging
        latency_ms = int((datetime.datetime.utcnow() - start_time).total_seconds() * 1000)

        AuditService.log_event(
            db=db,
            request_id=request_id,
            action_type="CHAT_QUERY",
            customer_id=customer_id,
            intent=intent,
            services_invoked=services_invoked,
            verification_status=verification_status,
            client_ip=client_ip,
            notes=f"Processed query with intent {intent} in {latency_ms}ms"
        )

        return ChatMessageResponse(
            conversation_id=conversation_id or 1,
            reply=final_reply,
            intent=intent,
            result_object=result_object,
            calculation_notes=calc_notes,
            verification=verification_rep,
            suggested_chips=suggested_chips,
            latency_ms=latency_ms,
            ai_status="OLLAMA_LLAMA3_1" if ai_online else "OFFLINE_RULE_FALLBACK"
        )

    @classmethod
    def _generate_chips(cls, intent: str, parsed: ParsedIntent) -> List[str]:
        if intent == "spending_summary":
            return [
                "How does this compare to last month?",
                "Show recurring subscriptions",
                "Can I afford a ₹40 lakh home loan?"
            ]
        elif intent == "loan_calculator":
            return [
                "What if I prepay ₹2 lakh in year 1?",
                "Can I get a better balance transfer rate?",
                "Check my 50/30/20 budget"
            ]
        elif intent == "fraud_inquiry":
            return [
                "Explain the high-value rule",
                "Simulate a test anomaly",
                "How to file an RBI complaint?"
            ]
        elif intent == "budget_guidance":
            return [
                "What if I reduce dining by 20%?",
                "Recommend best cashback credit cards",
                "Calculate SIP for ₹10,000 monthly"
            ]
        elif intent == "regulatory_rag":
            return [
                "What documents are valid for KYC?",
                "What is DICGC deposit insurance limit?",
                "How does RBI Ombudsman work?"
            ]
        elif intent == "transfer_check":
            return [
                "Send money to Kishan",
                "Check recent transactions",
                "View my available balance"
            ]
        elif intent == "account_balance":
            return [
                "Show my recent transactions",
                "How much did I spend this month?",
                "Send ₹5,000 to Kishan"
            ]
        elif intent == "recent_transactions":
            return [
                "What is my account balance?",
                "How much did I spend on food?",
                "Check for fraud alerts"
            ]
        elif intent == "greeting":
            return [
                "What is my account balance?",
                "How much did I spend this month?",
                "Send ₹5,000 to Kishan",
                "Can I afford a ₹40 lakh home loan?"
            ]
        else:
            return [
                "How much did I spend on food this month?",
                "Can I afford a ₹40 lakh home loan?",
                "Check for suspicious transactions"
            ]
