from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional, Tuple
from backend.schemas import LoanResultObject, CalculationNotes
from backend.config import format_inr

class LoanService:
    """
    Loan & Mortgage Navigator.
    Uses exact Decimal arithmetic to ensure calculations are accurate to the paisa.
    """

    @classmethod
    def calculate_emi(
        cls,
        principal: float | int | Decimal,
        annual_rate_pct: float | int | Decimal,
        tenure_months: int
    ) -> Decimal:
        """
        Standard Equated Monthly Instalment (EMI) Formula:
        EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)
        where:
        P = Principal loan amount
        r = Monthly interest rate = Annual rate / (12 * 100)
        n = Tenure in months
        """
        P = Decimal(str(principal))
        R = Decimal(str(annual_rate_pct))
        n = tenure_months

        if R == 0:
            return (P / Decimal(str(n))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        monthly_rate = R / (Decimal("12") * Decimal("100"))
        numerator = P * monthly_rate * ((Decimal("1") + monthly_rate) ** n)
        denominator = ((Decimal("1") + monthly_rate) ** n) - Decimal("1")
        
        emi = numerator / denominator
        return emi.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @classmethod
    def generate_amortisation_schedule(
        cls,
        principal: float | int | Decimal,
        annual_rate_pct: float | int | Decimal,
        tenure_months: int,
        limit_months: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Generate monthly amortisation schedule."""
        P = Decimal(str(principal))
        R = Decimal(str(annual_rate_pct))
        n = tenure_months
        monthly_rate = R / (Decimal("12") * Decimal("100"))
        emi = cls.calculate_emi(P, R, n)

        balance = P
        schedule: List[Dict[str, Any]] = []
        max_rows = limit_months if limit_months is not None else n

        for month in range(1, min(n + 1, max_rows + 1)):
            interest = (balance * monthly_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            principal_paid = emi - interest
            if month == n:
                principal_paid = balance
                emi = principal_paid + interest
                balance = Decimal("0.00")
            else:
                balance = balance - principal_paid
                if balance < Decimal("0.00"):
                    balance = Decimal("0.00")

            schedule.append({
                "month": month,
                "emi": float(emi),
                "principal_paid": float(principal_paid),
                "interest_paid": float(interest),
                "remaining_balance": float(balance.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                "formatted_balance": format_inr(float(balance))
            })

        return schedule

    @classmethod
    def calculate_prepayment_impact(
        cls,
        principal: float | int | Decimal,
        annual_rate_pct: float | int | Decimal,
        tenure_months: int,
        prepayment_amount: float | int | Decimal,
        prepayment_month: int = 12
    ) -> Dict[str, Any]:
        """
        Compute prepayment savings:
        Option A: Keep tenure same, reduce EMI
        Option B: Keep EMI same, reduce tenure
        """
        P = Decimal(str(principal))
        R = Decimal(str(annual_rate_pct))
        n = tenure_months
        L = Decimal(str(prepayment_amount))
        monthly_rate = R / (Decimal("12") * Decimal("100"))

        orig_emi = cls.calculate_emi(P, R, n)
        orig_total_pay = orig_emi * Decimal(str(n))
        orig_total_interest = orig_total_pay - P

        # Amortise up to prepayment_month
        balance = P
        for _ in range(1, prepayment_month + 1):
            interest = (balance * monthly_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            balance = balance - (orig_emi - interest)

        new_balance = max(Decimal("0.00"), balance - L)
        remaining_months = n - prepayment_month

        # Option A: Reduced EMI, same tenure
        new_reduced_emi = cls.calculate_emi(new_balance, R, remaining_months)
        total_pay_reduced_emi = (orig_emi * prepayment_month) + L + (new_reduced_emi * remaining_months)
        savings_reduced_emi = orig_total_pay - total_pay_reduced_emi

        # Option B: Same EMI, reduced tenure
        # Solve for new tenure: n = log(EMI / (EMI - P*r)) / log(1 + r)
        cur_bal = new_balance
        months_needed = 0
        total_interest_b = Decimal("0.00")
        while cur_bal > Decimal("0.00") and months_needed < remaining_months:
            months_needed += 1
            intr = (cur_bal * monthly_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            total_interest_b += intr
            prin = orig_emi - intr
            cur_bal -= prin

        total_pay_reduced_tenure = (orig_emi * prepayment_month) + L + (orig_emi * months_needed)
        savings_reduced_tenure = orig_total_pay - total_pay_reduced_tenure
        tenure_months_saved = remaining_months - months_needed

        return {
            "prepayment_amount": float(L),
            "formatted_prepayment": format_inr(float(L)),
            "prepayment_at_month": prepayment_month,
            "reduced_emi_option": {
                "new_emi": float(new_reduced_emi),
                "formatted_new_emi": format_inr(float(new_reduced_emi)),
                "total_interest_saved": float(savings_reduced_emi),
                "formatted_interest_saved": format_inr(float(savings_reduced_emi))
            },
            "reduced_tenure_option": {
                "months_saved": max(0, tenure_months_saved),
                "years_saved": round(max(0, tenure_months_saved) / 12, 1),
                "total_interest_saved": float(savings_reduced_tenure),
                "formatted_interest_saved": format_inr(float(savings_reduced_tenure))
            }
        }

    @classmethod
    def calculate_balance_transfer(
        cls,
        outstanding_principal: float | int | Decimal,
        current_rate_pct: float | int | Decimal,
        new_rate_pct: float | int | Decimal,
        remaining_tenure_months: int,
        processing_fee_pct: float | int | Decimal = 0.5
    ) -> Dict[str, Any]:
        """Evaluate refinancing/balance transfer profitability and break-even point."""
        P = Decimal(str(outstanding_principal))
        cur_r = Decimal(str(current_rate_pct))
        new_r = Decimal(str(new_rate_pct))
        n = remaining_tenure_months
        fee_rate = Decimal(str(processing_fee_pct)) / Decimal("100")

        cur_emi = cls.calculate_emi(P, cur_r, n)
        cur_total_pay = cur_emi * Decimal(str(n))

        new_emi = cls.calculate_emi(P, new_r, n)
        processing_fee = (P * fee_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        new_total_pay = (new_emi * Decimal(str(n))) + processing_fee

        net_savings = cur_total_pay - new_total_pay
        monthly_saving = cur_emi - new_emi
        break_even_months = int((processing_fee / monthly_saving).quantize(Decimal("1"), rounding=ROUND_HALF_UP)) if monthly_saving > 0 else 999

        return {
            "outstanding_principal": float(P),
            "current_rate": float(cur_r),
            "new_rate": float(new_r),
            "current_emi": float(cur_emi),
            "formatted_current_emi": format_inr(float(cur_emi)),
            "new_emi": float(new_emi),
            "formatted_new_emi": format_inr(float(new_emi)),
            "monthly_cash_savings": float(monthly_saving),
            "formatted_monthly_savings": format_inr(float(monthly_saving)),
            "processing_fee": float(processing_fee),
            "formatted_processing_fee": format_inr(float(processing_fee)),
            "net_total_savings": float(net_savings),
            "formatted_net_total_savings": format_inr(float(net_savings)),
            "break_even_months": break_even_months,
            "is_recommended": net_savings > 0 and break_even_months <= 18
        }

    @classmethod
    def evaluate_affordability(
        cls,
        monthly_income: float | int | Decimal,
        existing_emis: float | int | Decimal,
        proposed_emi: float | int | Decimal,
        max_foir_pct: float = 50.0
    ) -> Tuple[float, bool, str]:
        """
        Assess customer loan affordability using Fixed Obligation to Income Ratio (FOIR).
        Standard banking prudence dictates FOIR <= 50%.
        """
        inc = Decimal(str(monthly_income))
        exist = Decimal(str(existing_emis))
        prop = Decimal(str(proposed_emi))

        if inc <= Decimal("0.00"):
            return 100.0, False, "Monthly income cannot be zero."

        total_obligations = exist + prop
        foir = (total_obligations / inc) * Decimal("100")
        foir_float = round(float(foir), 1)

        is_affordable = foir_float <= max_foir_pct
        if is_affordable:
            notes = f"Affordable: Total obligations ({format_inr(float(total_obligations))}) take {foir_float}% of monthly income (limit: {max_foir_pct}%)."
        else:
            notes = f"High obligation warning: Proposed EMI pushes debt ratio to {foir_float}%, exceeding the prudent {max_foir_pct}% banking ceiling."

        return foir_float, is_affordable, notes

    @classmethod
    def calculate_loan_package(
        cls,
        principal: float,
        annual_rate_pct: float = 8.5,
        tenure_months: int = 240,
        monthly_income: float = 125000.0,
        existing_emis: float = 12000.0
    ) -> LoanResultObject:
        """Complete loan navigation package."""
        emi = cls.calculate_emi(principal, annual_rate_pct, tenure_months)
        total_payment = emi * Decimal(str(tenure_months))
        total_interest = total_payment - Decimal(str(principal))

        foir, is_afford, afford_notes = cls.evaluate_affordability(monthly_income, existing_emis, emi)
        
        # Prepayment impact simulation (e.g. ₹2 Lakh at month 12)
        prep_sim = cls.calculate_prepayment_impact(
            principal=principal,
            annual_rate_pct=annual_rate_pct,
            tenure_months=tenure_months,
            prepayment_amount=min(200000.0, principal * 0.1),
            prepayment_month=12
        )

        # Balance transfer what-if (if refinanced at 0.5% lower)
        bt_sim = cls.calculate_balance_transfer(
            outstanding_principal=principal,
            current_rate_pct=annual_rate_pct,
            new_rate_pct=max(6.5, annual_rate_pct - 0.5),
            remaining_tenure_months=tenure_months
        )

        calc_notes = CalculationNotes(
            formula="EMI = P * r * (1+r)^n / ((1+r)^n - 1) using python decimal.Decimal (ROUND_HALF_UP)",
            data_window=f"Tenure: {tenure_months} months ({tenure_months//12} yrs)",
            transaction_count=1,
            filters_applied={"principal": principal, "rate": annual_rate_pct, "tenure_months": tenure_months},
            breakdown={
                "principal": principal,
                "annual_rate": annual_rate_pct,
                "tenure_months": tenure_months,
                "monthly_emi": float(emi),
                "total_interest": float(total_interest),
                "total_payment": float(total_payment),
                "foir_pct": foir
            },
            source_transaction_ids=[],
            calculation_summary=f"Exact EMI calculated: {format_inr(float(emi))} | Total Interest: {format_inr(float(total_interest))}"
        )

        return LoanResultObject(
            principal=float(principal),
            formatted_principal=format_inr(principal),
            annual_interest_rate=float(annual_rate_pct),
            tenure_months=tenure_months,
            emi=float(emi),
            formatted_emi=format_inr(float(emi)),
            total_interest=float(total_interest),
            formatted_total_interest=format_inr(float(total_interest)),
            total_payment=float(total_payment),
            formatted_total_payment=format_inr(float(total_payment)),
            foir_pct=foir,
            is_affordable=is_afford,
            affordability_notes=afford_notes,
            prepayment_options=prep_sim,
            balance_transfer=bt_sim,
            calculation_notes=calc_notes
        )
