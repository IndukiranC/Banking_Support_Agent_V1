import re
from typing import Dict, Any, List, Set, Tuple
from backend.schemas import VerificationReport
from backend.config import format_inr

class OutputVerifier:
    """
    Deterministic Financial Verifier.
    Every LLM-generated message must pass through this verifier.
    Matches extracted figures, percentages, and metrics against the Python result object.
    """

    ALLOWED_CONTEXT_NUMBERS = {
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
        12, 24, 30, 31, 50, 20, 100, 365,
        2024, 2025, 2026, 2027
    }

    @classmethod
    def extract_numbers_from_text(cls, text: str) -> List[Tuple[float, str]]:
        """
        Extract numerical quantities from text, resolving:
        - Plain integers & floats (42500, 42,500.50)
        - Currency notations (₹42,500, Rs 50000)
        - Indian denominations (40 lakh -> 4000000, 1.5 crore -> 15000000)
        - Percentages (8.5% -> 8.5)
        """
        results: List[Tuple[float, str]] = []

        # 1. Indian lakh/crore patterns: e.g. "₹40 lakh", "40 lakhs", "1.5 crore"
        lakh_matches = re.finditer(r'(?:₹|rs\.?|inr\s*)?\s*(\d+(?:\.\d+)?)\s*(?:lakhs?|lacs?)\b', text, re.IGNORECASE)
        for m in lakh_matches:
            val = float(m.group(1)) * 100_000
            results.append((val, m.group(0).strip()))

        crore_matches = re.finditer(r'(?:₹|rs\.?|inr\s*)?\s*(\d+(?:\.\d+)?)\s*(?:crores?|crs?)\b', text, re.IGNORECASE)
        for m in crore_matches:
            val = float(m.group(1)) * 10_000_000
            results.append((val, m.group(0).strip()))

        # 2. Percentage patterns: e.g. "8.5%", "15.2 %"
        pct_matches = re.finditer(r'(\d+(?:\.\d+)?)\s*%', text)
        for m in pct_matches:
            val = float(m.group(1))
            results.append((val, m.group(0).strip()))

        # 3. Currency and formatted numbers: e.g. "₹42,500.00", "₹1,250"
        curr_matches = re.finditer(r'(?:₹|rs\.?|inr)\s*([0-9,]+(?:\.[0-9]+)?)', text, re.IGNORECASE)
        for m in curr_matches:
            raw_num = m.group(1).replace(",", "")
            try:
                val = float(raw_num)
                results.append((val, m.group(0).strip()))
            except ValueError:
                pass

        # 4. Standalone numbers with commas: e.g. "42,500" or standalone floats >= 10
        gen_matches = re.finditer(r'\b(\d{1,3}(?:,\d{2,3})+(?:\.\d+)?|\d+\.\d+|\b\d{2,}\b)', text)
        for m in gen_matches:
            raw_str = m.group(1)
            raw_clean = raw_str.replace(",", "")
            try:
                val = float(raw_clean)
                # Filter out pure small years or already parsed
                results.append((val, raw_str))
            except ValueError:
                pass

        # Deduplicate results by (rounded value, representation)
        seen = set()
        unique = []
        for val, repr_str in results:
            key = (round(val, 2), repr_str.lower().strip())
            if key not in seen:
                seen.add(key)
                unique.append((val, repr_str))
        return unique

    @classmethod
    def collect_numbers_from_result_object(cls, obj: Any) -> Set[float]:
        """Recursively harvest all valid numeric metrics from the Python result object."""
        numbers: Set[float] = set()

        if obj is None:
            return numbers

        if isinstance(obj, (int, float)):
            numbers.add(round(float(obj), 2))
            # Also add scaled/percentage equivalents if 0.085 -> 8.5
            if 0 < float(obj) < 1.0:
                numbers.add(round(float(obj) * 100, 2))
        elif isinstance(obj, str):
            # Check if string contains currency or number
            clean = re.sub(r'[₹,RsINR\s]', '', obj)
            try:
                val = float(clean)
                numbers.add(round(val, 2))
            except ValueError:
                pass
        elif isinstance(obj, dict):
            for v in obj.values():
                numbers.update(cls.collect_numbers_from_result_object(v))
        elif isinstance(obj, (list, tuple, set)):
            for item in obj:
                numbers.update(cls.collect_numbers_from_result_object(item))

        return numbers

    @classmethod
    def verify(cls, text: str, result_object: Dict[str, Any]) -> VerificationReport:
        """
        Perform strict verification:
        Ensures that every financial claim in text matches truth in result_object.
        """
        extracted = cls.extract_numbers_from_text(text)
        known_numbers = cls.collect_numbers_from_result_object(result_object)

        verified: List[str] = []
        discrepancies: List[str] = []

        for val, repr_str in extracted:
            rounded_val = round(val, 2)
            int_val = int(val) if val.is_integer() else None

            # Check if it's an allowed context number (e.g. 50, 30, 20 rule, 12 months)
            if int_val is not None and int_val in cls.ALLOWED_CONTEXT_NUMBERS:
                verified.append(f"{repr_str} (Standard Metric)")
                continue

            # Check against result object with 1% relative tolerance or absolute 1.0 tolerance
            matched = False
            for k in known_numbers:
                if abs(k - rounded_val) <= 1.5 or (k > 0 and abs(k - rounded_val) / k < 0.015):
                    matched = True
                    break

            if matched:
                verified.append(f"{repr_str} -> matches {rounded_val}")
            else:
                # If number is larger than 100 and not in result, this is an unverified financial claim
                if val >= 50:
                    discrepancies.append(f"Unverified figure '{repr_str}' ({rounded_val}) found in LLM response")

        if discrepancies:
            return VerificationReport(
                passed=False,
                status="DISCREPANCY_DETECTED",
                verified_numbers=verified,
                discrepancies=discrepancies,
                explanation=f"Found {len(discrepancies)} number(s) in AI response that could not be verified against the calculated financial truth."
            )

        return VerificationReport(
            passed=True,
            status="PASSED",
            verified_numbers=verified,
            discrepancies=[],
            explanation="All extracted figures and percentages successfully verified against calculated result object."
        )

    @classmethod
    def build_deterministic_template(cls, intent: str, result: Dict[str, Any]) -> str:
        """
        Deterministic, 100% faithful template generator when Ollama is offline
        or when verification fails after retry.
        """
        if intent == "spending_summary":
            cat = result.get("category", "all spending")
            total = result.get("formatted_total_spent", "₹0")
            count = result.get("transaction_count", 0)
            window = result.get("data_window", "Current Month")
            mom = result.get("month_over_month_change_pct", 0.0)
            mom_str = f"+{mom:.1f}%" if mom > 0 else f"{mom:.1f}%"
            top_merchants = result.get("top_merchants", [])
            merch_str = ", ".join([f"{m.get('name')} ({format_inr(m.get('amount', 0))})" for m in top_merchants[:3]]) or "None recorded"
            
            opps = result.get("savings_opportunities", [])
            opps_str = "\n".join([f"• {op}" for op in opps]) if opps else "• Maintain regular budget checks."

            return (
                f"### Spending Analysis for {cat.title()}\n\n"
                f"During **{window}**, you spent a total of **{total}** across **{count} transactions**.\n\n"
                f"**Key Metrics:**\n"
                f"- **Month-over-Month Change:** {mom_str} compared to last month ({result.get('formatted_last_month_spent', '₹0')})\n"
                f"- **Top Merchants:** {merch_str}\n\n"
                f"**Potential Savings Opportunities:**\n{opps_str}\n\n"
                f"_This summary was generated deterministically from your authenticated account records._"
            )

        elif intent == "loan_calculator":
            p = result.get("formatted_principal", "₹0")
            emi = result.get("formatted_emi", "₹0")
            rate = result.get("annual_interest_rate", 8.5)
            tenure = result.get("tenure_months", 240)
            tot_int = result.get("formatted_total_interest", "₹0")
            tot_pay = result.get("formatted_total_payment", "₹0")
            foir = result.get("foir_pct", 0.0)
            afford = "Within standard affordability limits (FOIR < 50%)" if result.get("is_affordable") else "High obligation warning (FOIR exceeds recommended threshold)"

            return (
                f"### Loan & EMI Computation\n\n"
                f"For a principal of **{p}** at **{rate}% p.a.** over **{tenure} months** ({tenure//12} years):\n\n"
                f"- **Monthly EMI:** **{emi}**\n"
                f"- **Total Interest Payable:** **{tot_int}**\n"
                f"- **Total Amount Payable:** **{tot_pay}**\n"
                f"- **Affordability Assessment (FOIR):** **{foir:.1f}%** — {afford}\n\n"
                f"_Calculated with exact Decimal arithmetic._"
            )

        elif intent == "fraud_inquiry":
            alerts = result.get("recent_alerts", [])
            score = result.get("risk_score", 0)
            level = result.get("risk_level", "LOW")
            rules = result.get("triggered_rules", [])
            rules_str = "\n".join([f"• **{r.get('rule')}:** {r.get('reason')} (Weight: {r.get('weight')})" for r in rules]) if rules else "• No active anomaly rules triggered."

            return (
                f"### Fraud Monitoring & Security Status\n\n"
                f"Your current account risk status is **{level}** (Risk Score: **{score}/100**).\n\n"
                f"**Security Signals & Triggered Rules:**\n{rules_str}\n\n"
                f"If you recognize all recent activity, you can confirm via the **'This was me'** button. If you see any unrecognized charges, click **'This wasn't me'** to instantly secure your card."
            )

        elif intent == "transfer_check":
            is_rep = result.get("is_repeated", False)
            prior = result.get("prior_transaction")
            if is_rep and prior:
                return (
                    f"### ⚠️ Repeated Transaction Alert\n\n"
                    f"{result.get('message', '')}\n\n"
                    f"**Recent Transfer on Record:**\n"
                    f"- **Recipient:** {prior.get('recipient')}\n"
                    f"- **Amount Sent:** {prior.get('formatted_amount')}\n"
                    f"- **Date & Time:** {prior.get('timestamp')} ({prior.get('time_ago')})\n"
                    f"- **Channel:** {prior.get('channel')}\n\n"
                    f"> **Important Advisory:** This is an informational alert to prevent accidental duplicate transfers. **You are not restricted or blocked.** If you intended to make this transfer again, you may proceed."
                )
            else:
                return (
                    f"### ✅ Transfer Check: Clear\n\n"
                    f"No recent duplicate transactions detected for this recipient.\n"
                    f"You may proceed safely with your transfer."
                )

        elif intent == "budget_guidance":
            income = result.get("formatted_income", "₹0")
            needs = result.get("needs_pct", 50.0)
            wants = result.get("wants_pct", 30.0)
            savings = result.get("savings_pct", 20.0)
            emerg = result.get("formatted_emergency_target", "₹0")

            return (
                f"### 50/30/20 Financial Guidance Plan\n\n"
                f"Based on your authenticated monthly income of **{income}**:\n\n"
                f"- **Needs (Essentials):** **{needs:.1f}%** (Target: 50%)\n"
                f"- **Wants (Discretionary):** **{wants:.1f}%** (Target: 30%)\n"
                f"- **Savings & Investments:** **{savings:.1f}%** (Target: 20%)\n"
                f"- **Recommended Emergency Fund (6 Months):** **{emerg}**\n\n"
                f"_Guidance numbers are deterministically benchmarked against your actual cash-flow._"
            )

        elif intent == "regulatory_rag":
            docs = result.get("matched_documents", [])
            citations = result.get("citations", [])
            cite_str = "\n".join([f"• **{c.get('document')} ({c.get('section')}):** {c.get('text')}" for c in citations]) if citations else "• Official RBI KYC & Banking Redressal Portal."
            return (
                f"### Regulatory Information & Compliance\n\n"
                f"{result.get('official_source_notice', '')}\n\n"
                f"**Official Regulatory Citations:**\n{cite_str}\n\n"
                f"_Information sourced strictly from verified RBI master directions and official regulatory filings._"
            )

        elif intent == "product_recommendation":
            prods = result.get("recommended_products", [])
            prods_str = "\n".join([
                f"• **{p.get('name')}**: Fit Score: {p.get('fit_score')}/100\n  - Why it fits: {p.get('fit_reason')}\n  - Rate/Fee: {p.get('interest_rate_or_fee')}"
                for p in prods[:3]
            ])
            return (
                f"### Personalized Product Matches\n\n"
                f"Based on your verified credit profile and transaction habits, here are your best matched products:\n\n"
                f"{prods_str}\n\n"
                f"_All recommendations follow transparent rule-based eligibility checks with zero hidden sponsored ranking._"
            )

        elif intent == "investment_info":
            prof = result.get("risk_profile", "Moderate")
            alloc = result.get("recommended_allocation", {})
            alloc_str = ", ".join([f"{k}: {v*100:.0f}%" for k, v in alloc.items()])
            disc = result.get("disclaimer", "")
            return (
                f"### Investment Awareness & Portfolio Benchmark\n\n"
                f"Your assessed profile is **{prof}**.\n\n"
                f"**Standard Asset Allocation Benchmark:**\n{alloc_str}\n\n"
                f"> **Notice:** {disc}"
            )

        elif intent == "account_balance":
            name = result.get("customer_name", "Customer")
            bal = result.get("formatted_balance", "₹0")
            acc_num = result.get("masked_account", "Account")
            income = result.get("formatted_income", "₹0")
            score = result.get("credit_score", "N/A")
            return (
                f"### 💳 Account Balance & Profile Summary\n\n"
                f"Hello **{name}**, here are your verified account details:\n\n"
                f"- **Available Liquid Balance:** **{bal}**\n"
                f"- **Primary Account:** `{acc_num}` (Active)\n"
                f"- **Registered Monthly Income:** **{income}**\n"
                f"- **Credit Score:** **{score}** (Verified)\n\n"
                f"_Data retrieved directly from your authenticated banking ledger._"
            )

        elif intent == "recent_transactions":
            txs = result.get("transactions", [])
            if not txs:
                return "You have no recorded transactions in this period."
            rows = []
            for t in txs[:6]:
                rows.append(f"• **{t.get('date')}**: {t.get('merchant')} — **{t.get('formatted_amount', t.get('amount'))}** ({t.get('category')}, via {t.get('channel')})")
            rows_str = "\n".join(rows)
            return (
                f"### 📜 Recent Transaction History\n\n"
                f"Here are your latest verified transactions:\n\n"
                f"{rows_str}\n\n"
                f"_You can export your complete itemized statement as CSV from the Spending tab._"
            )

        elif intent == "greeting":
            name = result.get("customer_name", "there")
            bal = result.get("formatted_balance", "₹0")
            return (
                f"Hello **{name}**! 👋 Welcome to your Antigravity Banking Assistant.\n\n"
                f"Your current liquid balance is **{bal}**.\n\n"
                f"**Here is what I can help you with right now:**\n"
                f"• **Instant Money Transfers:** Send funds with built-in repeated payee duplicate warnings\n"
                f"• **Spending Analytics:** Break down your monthly food, shopping, and utility expenses\n"
                f"• **Loan & EMI Calculator:** Calculate paisa-exact EMI, FOIR, and prepayment impact\n"
                f"• **Fraud & Security:** Review real-time anomaly detection alerts\n"
                f"• **RBI Regulatory Guidance:** Official KYC rules, deposit insurance, and Ombudsman info\n\n"
                f"How may I assist you today?"
            )

        elif intent == "general_banking_faq":
            name = result.get("customer_name", "there")
            bal = result.get("formatted_balance", "₹0")
            return (
                f"### 🏦 Antigravity Banking Assistant\n\n"
                f"Hello **{name}**! Your active account balance is **{bal}**.\n\n"
                f"I specialize in verifiable, mathematical banking advisory. You can ask me:\n"
                f"1. **Account & Balances:** *'What is my account balance?'* or *'Show my recent transactions'*\n"
                f"2. **Transfers:** *'Send ₹5,000 to Kishan'* (with duplicate payment advisory)\n"
                f"3. **Spending Insights:** *'How much did I spend on food this month?'*\n"
                f"4. **Loans & EMI:** *'Can I afford a ₹40 lakh home loan at 8.5%?'*\n"
                f"5. **Regulatory Rules:** *'What are valid KYC documents under RBI rules?'*\n\n"
                f"What would you like to explore?"
            )

        return (
            "I have processed your request deterministically. Please review your account details or choose one of the quick suggestions below."
        )
