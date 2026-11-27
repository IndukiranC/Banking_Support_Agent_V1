from backend.database import SessionLocal
from backend.services.spending_service import SpendingService
from backend.models import Customer, Account, Transaction

def test_repeated_transfer_alert_without_restriction():
    """
    Test feature requirement:
    Repeated transactions to the same person must alert the user,
    but structurally MUST NOT restrict or block them.
    """
    db = SessionLocal()
    try:
        # User 1: Indukiran Reddy
        customer_id = 1
        account = db.query(Account).filter(Account.customer_id == customer_id).first()
        initial_balance = account.balance
        recipient = "Kishan Kumar"
        amount = 1500.0

        # 1. First transfer check
        first_check = SpendingService.check_repeated_transfer(
            db=db,
            customer_id=customer_id,
            recipient_name=recipient,
            amount=amount
        )
        assert first_check["is_restricted"] is False

        # 2. Execute first transfer
        exec_1 = SpendingService.execute_transfer(
            db=db,
            customer_id=customer_id,
            recipient_name=recipient,
            amount=amount,
            channel="UPI"
        )
        assert exec_1["success"] is True
        assert exec_1["new_balance"] == initial_balance - amount

        # 3. Second transfer check to the SAME recipient
        second_check = SpendingService.check_repeated_transfer(
            db=db,
            customer_id=customer_id,
            recipient_name=recipient,
            amount=amount
        )
        assert second_check["is_repeated"] is True
        assert second_check["is_restricted"] is False  # MUST NOT RESTRICT
        assert second_check["alert_level"] == "WARNING"
        assert "⚠️ Repeated Transaction Alert" in second_check["message"]
        assert second_check["prior_transaction"]["recipient"] == recipient
        assert second_check["prior_transaction"]["amount"] == amount

        # 4. Execute second transfer anyway (proceeding despite the warning)
        exec_2 = SpendingService.execute_transfer(
            db=db,
            customer_id=customer_id,
            recipient_name=recipient,
            amount=amount,
            channel="UPI"
        )
        assert exec_2["success"] is True  # Verifies user is NOT blocked
        assert exec_2["new_balance"] == initial_balance - (2 * amount)

    finally:
        # Roll back test debit to preserve balance
        db.query(Transaction).filter(
            Transaction.customer_id == customer_id,
            Transaction.merchant_name == recipient,
            Transaction.amount == amount
        ).delete()
        account.balance = initial_balance
        db.commit()
        db.close()
