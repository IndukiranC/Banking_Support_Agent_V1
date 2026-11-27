import pytest
from backend.verifier import OutputVerifier

def test_extract_numbers_variations():
    text = "You spent ₹42,500.50 on shopping, took a 40 lakh loan at 8.5% interest, and have 15 transactions."
    extracted = OutputVerifier.extract_numbers_from_text(text)
    values = [val for val, _ in extracted]

    # Check 42500.50
    assert any(abs(v - 42500.50) < 0.01 for v in values)
    # Check 40 lakh (40,00,000)
    assert any(abs(v - 4000000.0) < 0.01 for v in values)
    # Check 8.5%
    assert any(abs(v - 8.5) < 0.01 for v in values)
    # Check 15
    assert any(abs(v - 15.0) < 0.01 for v in values)

def test_verifier_passes_on_faithful_response():
    result_object = {
        "formatted_total_spent": "₹12,450",
        "total_spent": 12450.0,
        "transaction_count": 8,
        "month_over_month_change_pct": 14.5
    }
    llm_text = (
        "During this period, your total outlay was ₹12,450 across 8 recorded transactions, "
        "which is a 14.5% increase compared to last month."
    )
    report = OutputVerifier.verify(llm_text, result_object)
    assert report.passed is True
    assert len(report.discrepancies) == 0

def test_verifier_rejects_hallucinated_figures():
    result_object = {
        "formatted_total_spent": "₹12,450",
        "total_spent": 12450.0,
        "transaction_count": 8
    }
    # LLM hallucinates a ₹55,000 figure
    llm_text = "You spent ₹55,000 on luxury goods across 8 orders."
    report = OutputVerifier.verify(llm_text, result_object)
    assert report.passed is False
    assert len(report.discrepancies) > 0
    assert any("55000" in d or "55,000" in d for d in report.discrepancies)

def test_deterministic_template_coverage():
    spending_res = {
        "category": "Food & Dining",
        "formatted_total_spent": "₹15,200",
        "transaction_count": 22,
        "data_window": "1–21 Nov 2026",
        "month_over_month_change_pct": -5.2,
        "top_merchants": [{"name": "Swiggy", "amount": 6500}],
        "savings_opportunities": ["Reduce midnight deliveries"]
    }
    template = OutputVerifier.build_deterministic_template("spending_summary", spending_res)
    assert "₹15,200" in template
    assert "22 transactions" in template
    assert "Food & Dining" in template
