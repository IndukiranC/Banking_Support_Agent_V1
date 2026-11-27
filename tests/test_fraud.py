import datetime
import pytest
from backend.database import SessionLocal, Base, engine
from backend.models import Customer, Account, Transaction
from backend.services.fraud_service import FraudService

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()

def test_fraud_amount_outlier_detection(db_session):
    # Customer 1 (Rajesh Sharma)
    now = datetime.datetime.utcnow()
    account = db_session.query(Account).filter(Account.customer_id == 1).first()

    # Create an extreme outlier debit
    outlier_tx = Transaction(
        account_id=account.id,
        customer_id=1,
        amount=350000.0, # Massive outlier compared to standard dining/shopping
        transaction_type="debit",
        category="Shopping",
        merchant_name="Exotic Diamond Boutique",
        timestamp=now,
        channel="CARD",
        device_id="unrecognized-device-test"
    )
    db_session.add(outlier_tx)
    db_session.flush()

    analysis = FraudService.analyze_transaction(db_session, 1, outlier_tx)
    assert analysis["risk_score"] >= 35
    assert any("OUTLIER" in r["rule"] for r in analysis["triggered_rules"])

def test_fraud_nocturnal_high_value(db_session):
    account = db_session.query(Account).filter(Account.customer_id == 1).first()
    # Transaction at 03:30 AM
    night_time = datetime.datetime.utcnow().replace(hour=3, minute=30)
    night_tx = Transaction(
        account_id=account.id,
        customer_id=1,
        amount=45000.0,
        transaction_type="debit",
        category="Miscellaneous",
        merchant_name="Night Offshore Transfer",
        timestamp=night_time,
        channel="NEFT"
    )
    db_session.add(night_tx)
    db_session.flush()

    analysis = FraudService.analyze_transaction(db_session, 1, night_tx)
    assert any("UNUSUAL_TIME_OF_DAY" in r["rule"] for r in analysis["triggered_rules"])

def test_fraud_duplicate_charge(db_session):
    account = db_session.query(Account).filter(Account.customer_id == 1).first()
    base_time = datetime.datetime.utcnow()
    
    # First charge
    tx1 = Transaction(
        account_id=account.id,
        customer_id=1,
        amount=1499.0,
        transaction_type="debit",
        category="Shopping",
        merchant_name="Fashion Store Ltd",
        timestamp=base_time - datetime.timedelta(minutes=2),
        channel="POS"
    )
    db_session.add(tx1)
    db_session.flush()

    # Identical second charge 2 minutes later
    tx2 = Transaction(
        account_id=account.id,
        customer_id=1,
        amount=1499.0,
        transaction_type="debit",
        category="Shopping",
        merchant_name="Fashion Store Ltd",
        timestamp=base_time,
        channel="POS"
    )
    db_session.add(tx2)
    db_session.flush()

    analysis = FraudService.analyze_transaction(db_session, 1, tx2)
    assert any("DUPLICATE_CHARGE" in r["rule"] for r in analysis["triggered_rules"])

def test_fraud_simulator_synthetic_injection(db_session):
    res = FraudService.inject_synthetic_anomaly(db_session, 1, scenario="outlier")
    assert res["success"] is True
    assert res["risk_score"] > 0
    assert len(res["triggered_rules"]) > 0
