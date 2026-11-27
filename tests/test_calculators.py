import pytest
from decimal import Decimal
from backend.services.loan_service import LoanService

def test_golden_vector_home_loan_40_lakh():
    """
    Standard Banking Golden Test Vector 1:
    Principal: ₹40,00,000
    Interest Rate: 8.5% p.a.
    Tenure: 240 months (20 years)
    Expected EMI: ₹34,713.06
    """
    principal = 4000000
    rate = 8.5
    tenure = 240

    emi = LoanService.calculate_emi(principal, rate, tenure)
    assert float(emi) == 34712.93

    package = LoanService.calculate_loan_package(principal, rate, tenure, monthly_income=100000)
    assert package.emi == 34712.93
    assert package.total_payment == round(34712.93 * 240, 2)
    assert package.total_interest == round((34712.93 * 240) - 4000000, 2)

def test_golden_vector_personal_loan_10_lakh():
    """
    Standard Banking Golden Test Vector 2:
    Principal: ₹10,00,000
    Interest Rate: 10.0% p.a.
    Tenure: 60 months (5 years)
    Expected EMI: ₹21,247.04
    """
    principal = 1000000
    rate = 10.0
    tenure = 60

    emi = LoanService.calculate_emi(principal, rate, tenure)
    assert float(emi) == 21247.04

def test_zero_interest_loan():
    """Zero interest financing should split principal evenly across months."""
    principal = 120000
    rate = 0.0
    tenure = 12

    emi = LoanService.calculate_emi(principal, rate, tenure)
    assert float(emi) == 10000.00

def test_amortisation_schedule_completion():
    """Final remaining balance after tenure must be exactly 0.00."""
    schedule = LoanService.generate_amortisation_schedule(500000, 9.0, 36)
    assert len(schedule) == 36
    assert schedule[-1]["remaining_balance"] == 0.00
    # Sum of principal paid must equal initial principal
    total_principal_paid = sum(row["principal_paid"] for row in schedule)
    assert round(total_principal_paid, 2) == 500000.00

def test_prepayment_reduces_interest_or_tenure():
    """A lump sum prepayment at month 12 must yield positive interest savings."""
    res = LoanService.calculate_prepayment_impact(
        principal=2000000,
        annual_rate_pct=8.5,
        tenure_months=180,
        prepayment_amount=200000,
        prepayment_month=12
    )
    assert res["reduced_emi_option"]["total_interest_saved"] > 100000.0
    assert res["reduced_tenure_option"]["months_saved"] > 12

def test_foir_affordability_rules():
    """FOIR <= 50% must be approved; FOIR > 50% must flag warning."""
    foir_good, afford_good, _ = LoanService.evaluate_affordability(
        monthly_income=100000,
        existing_emis=15000,
        proposed_emi=25000
    )
    assert foir_good == 40.0
    assert afford_good is True

    foir_bad, afford_bad, _ = LoanService.evaluate_affordability(
        monthly_income=100000,
        existing_emis=35000,
        proposed_emi=25000
    )
    assert foir_bad == 60.0
    assert afford_bad is False
