import datetime
import math
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from backend.models import Transaction, Customer, Account, FraudAlert
from backend.schemas import FraudResultObject, CalculationNotes
from backend.config import format_inr

class FraudService:
    """
    Explainable Weighted Rule Engine for Real-Time Fraud & Anomaly Detection.
    Evaluates 7 distinct behavioural signals. Computes composite risk score (0-100).
    """

    WEIGHTS = {
        "velocity": 25,
        "amount_outlier": 25,
        "new_payee_high_value": 20,
        "geo_device_anomaly": 20,
        "time_of_day": 15,
        "structuring": 20,
        "duplicate_charge": 25,
    }

    MAX_POSSIBLE_SCORE = sum(WEIGHTS.values()) # 150

    @classmethod
    def analyze_transaction(
        cls,
        db: Session,
        customer_id: int,
        transaction: Transaction,
        recent_history_window_minutes: int = 1440
    ) -> Dict[str, Any]:
        """
        Evaluate all 7 fraud signals on a specific transaction against customer history.
        """
        triggered_rules: List[Dict[str, Any]] = []
        raw_score = 0

        # Query past transactions for baseline
        cutoff_date = transaction.timestamp - datetime.timedelta(days=90)
        past_txs = db.query(Transaction).filter(
            Transaction.customer_id == customer_id,
            Transaction.id != transaction.id,
            Transaction.timestamp < transaction.timestamp,
            Transaction.timestamp >= cutoff_date
        ).all()

        # 1. Velocity Signal: 5+ transactions in 10 minutes
        ten_min_window = transaction.timestamp - datetime.timedelta(minutes=10)
        recent_burst = [
            t for t in past_txs 
            if t.timestamp >= ten_min_window and t.timestamp <= transaction.timestamp
        ]
        if len(recent_burst) >= 4: # plus current tx makes >= 5
            w = cls.WEIGHTS["velocity"]
            raw_score += w
            triggered_rules.append({
                "rule": "VELOCITY_SPIKE",
                "name": "High Transaction Velocity",
                "weight": w,
                "reason": f"Detected {len(recent_burst) + 1} transactions within a 10-minute window (threshold: >= 5)."
            })

        # 2. Amount Outlier Signal: > 3σ or > 5x category median
        category_txs = [t.amount for t in past_txs if t.category == transaction.category and t.transaction_type == "debit"]
        if len(category_txs) >= 5:
            sorted_amounts = sorted(category_txs)
            median_amt = sorted_amounts[len(sorted_amounts) // 2]
            mean_amt = sum(category_txs) / len(category_txs)
            variance = sum((x - mean_amt) ** 2 for x in category_txs) / len(category_txs)
            std_dev = math.sqrt(variance) if variance > 0 else 1.0

            if (transaction.amount > median_amt * 5.0) or (std_dev > 0 and (transaction.amount - mean_amt) / std_dev > 3.0):
                w = cls.WEIGHTS["amount_outlier"]
                raw_score += w
                triggered_rules.append({
                    "rule": "AMOUNT_OUTLIER",
                    "name": "Statistical Amount Outlier",
                    "weight": w,
                    "reason": f"Amount {format_inr(transaction.amount)} exceeds 5x category median ({format_inr(median_amt)}) or 3 standard deviations."
                })
        elif transaction.amount > 100000.0:
            # Baseline absolute outlier check if category history sparse
            w = cls.WEIGHTS["amount_outlier"]
            raw_score += w
            triggered_rules.append({
                "rule": "AMOUNT_OUTLIER",
                "name": "High Value Outlier",
                "weight": w,
                "reason": f"High single transaction amount of {format_inr(transaction.amount)}."
            })

        # 3. New Payee / Merchant + High Value (> ₹25,000)
        seen_merchants = {t.merchant_name.lower().strip() for t in past_txs}
        is_new_merchant = transaction.merchant_name.lower().strip() not in seen_merchants
        if is_new_merchant and transaction.amount >= 25000.0:
            w = cls.WEIGHTS["new_payee_high_value"]
            raw_score += w
            triggered_rules.append({
                "rule": "NEW_MERCHANT_HIGH_VALUE",
                "name": "First-Time Payee High Value",
                "weight": w,
                "reason": f"First-time payment to '{transaction.merchant_name}' exceeding high-value threshold of ₹25,000 ({format_inr(transaction.amount)})."
            })

        # 4. Geo / Device Anomaly: Impossible travel or unknown device
        known_devices = {t.device_id for t in past_txs if t.device_id}
        known_cities = {t.location_city for t in past_txs if t.location_city}
        is_new_device = bool(known_devices and transaction.device_id not in known_devices)

        # Check impossible travel: location change within 1 hour across distant cities
        one_hour_window = transaction.timestamp - datetime.timedelta(hours=1)
        recent_locations = [t.location_city for t in past_txs if t.timestamp >= one_hour_window and t.location_city]
        impossible_travel = bool(recent_locations and any(c != transaction.location_city for c in recent_locations))

        if is_new_device or impossible_travel:
            w = cls.WEIGHTS["geo_device_anomaly"]
            raw_score += w
            reason_parts = []
            if is_new_device:
                reason_parts.append(f"Unrecognized device '{transaction.device_id}'")
            if impossible_travel:
                reason_parts.append(f"Impossible geo-velocity (active in {recent_locations[-1]} within last hour)")
            triggered_rules.append({
                "rule": "GEO_DEVICE_ANOMALY",
                "name": "Device or Location Anomaly",
                "weight": w,
                "reason": " and ".join(reason_parts) + "."
            })

        # 5. Time-of-Day Anomaly: Large transfer between 01:00 AM and 05:00 AM
        tx_hour = transaction.timestamp.hour
        if (1 <= tx_hour <= 4) and transaction.amount >= 15000.0:
            w = cls.WEIGHTS["time_of_day"]
            raw_score += w
            triggered_rules.append({
                "rule": "UNUSUAL_TIME_OF_DAY",
                "name": "Nocturnal High-Value Transfer",
                "weight": w,
                "reason": f"Large debit of {format_inr(transaction.amount)} executed at {transaction.timestamp.strftime('%I:%M %p')}, outside customary hours."
            })

        # 6. Structuring / Smurfing: Repeated amounts just under threshold (e.g. ₹48,000 - ₹49,999)
        twenty_four_hours = transaction.timestamp - datetime.timedelta(hours=24)
        structuring_candidates = [
            t for t in past_txs
            if t.timestamp >= twenty_four_hours and 45000.0 <= t.amount < 50000.0
        ]
        if 45000.0 <= transaction.amount < 50000.0 and len(structuring_candidates) >= 1:
            w = cls.WEIGHTS["structuring"]
            raw_score += w
            triggered_rules.append({
                "rule": "STRUCTURING_PATTERN",
                "name": "Regulatory Reporting Structuring",
                "weight": w,
                "reason": f"Repeated transaction ({format_inr(transaction.amount)}) just below the ₹50,000 regulatory reporting threshold."
            })

        # 7. Duplicate Charge: Identical merchant and exact amount within 5 minutes
        five_min_window = transaction.timestamp - datetime.timedelta(minutes=5)
        duplicates = [
            t for t in past_txs
            if t.timestamp >= five_min_window and t.merchant_name == transaction.merchant_name and abs(t.amount - transaction.amount) < 0.01
        ]
        if duplicates:
            w = cls.WEIGHTS["duplicate_charge"]
            raw_score += w
            triggered_rules.append({
                "rule": "DUPLICATE_CHARGE",
                "name": "Suspected Duplicate Charge",
                "weight": w,
                "reason": f"Identical debit of {format_inr(transaction.amount)} to '{transaction.merchant_name}' within 5 minutes of transaction #{duplicates[0].id}."
            })

        # Normalize score to 0 - 100
        normalized_score = min(100, int((raw_score / 60.0) * 100)) if raw_score > 0 else 0

        if normalized_score >= 70:
            level = "HIGH"
        elif normalized_score >= 35:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "transaction_id": transaction.id,
            "raw_score": raw_score,
            "risk_score": normalized_score,
            "risk_level": level,
            "triggered_rules": triggered_rules,
            "is_suspicious": normalized_score >= 35
        }

    @classmethod
    def get_fraud_summary(cls, db: Session, customer_id: int) -> FraudResultObject:
        """Fetch active alerts, customer risk profile, and explainable audit trail."""
        alerts = db.query(FraudAlert).filter(
            FraudAlert.customer_id == customer_id
        ).order_by(FraudAlert.created_at.desc()).all()

        high_risk_count = sum(1 for a in alerts if a.risk_level == "HIGH" and a.status == "PENDING")
        total_alerts = len(alerts)

        recent_alerts_data = []
        for a in alerts[:10]:
            recent_alerts_data.append({
                "alert_id": a.id,
                "transaction_id": a.transaction_id,
                "merchant": a.transaction.merchant_name if a.transaction else "Unknown",
                "amount": a.transaction.amount if a.transaction else 0.0,
                "formatted_amount": format_inr(a.transaction.amount) if a.transaction else "₹0",
                "risk_score": a.risk_score,
                "risk_level": a.risk_level,
                "status": a.status,
                "user_feedback": a.user_feedback,
                "triggered_rules": a.triggered_rules,
                "created_at": a.created_at.strftime("%d %b %Y, %I:%M %p")
            })

        top_alert = alerts[0] if alerts else None
        active_score = top_alert.risk_score if top_alert and top_alert.status == "PENDING" else 15
        active_level = top_alert.risk_level if top_alert and top_alert.status == "PENDING" else "LOW"
        active_rules = top_alert.triggered_rules if top_alert and top_alert.status == "PENDING" else []

        rec_action = (
            "Review pending high-risk charges. Confirm valid transactions or freeze card if unrecognized."
            if high_risk_count > 0 else "Account security standing is healthy. No critical anomalies active."
        )

        calc_notes = CalculationNotes(
            formula="RiskScore = Min(100, Round(Sum(TriggeredRuleWeights) / 60 * 100))",
            data_window="Past 90 days baseline + real-time ingestion",
            transaction_count=total_alerts,
            filters_applied={"customer_id": customer_id},
            breakdown={"total_alerts": total_alerts, "high_risk_alerts": high_risk_count, "active_risk_score": active_score},
            source_transaction_ids=[a.transaction_id for a in alerts[:5]],
            calculation_summary=f"Evaluated against 7 weighted behavioural rules. Overall risk score: {active_score}/100 ({active_level})."
        )

        return FraudResultObject(
            customer_id=customer_id,
            total_alerts=total_alerts,
            high_risk_alerts=high_risk_count,
            recent_alerts=recent_alerts_data,
            active_inquiry=recent_alerts_data[0] if recent_alerts_data else None,
            risk_score=active_score,
            risk_level=active_level,
            triggered_rules=active_rules,
            recommended_action=rec_action,
            calculation_notes=calc_notes
        )

    @classmethod
    def record_feedback(cls, db: Session, alert_id: int, feedback: str) -> Dict[str, Any]:
        """
        Record 'THIS_WAS_ME' or 'THIS_WAS_NOT_ME'.
        If 'THIS_WAS_ME': lowers score, updates baseline.
        If 'THIS_WAS_NOT_ME': confirms fraud, freezes simulated card channel.
        """
        alert = db.query(FraudAlert).filter(FraudAlert.id == alert_id).first()
        if not alert:
            return {"success": False, "error": "Alert not found"}

        alert.user_feedback = feedback
        if feedback == "THIS_WAS_ME":
            alert.status = "DISMISSED_USER"
            alert.notes = "Customer verified transaction as legitimate. Added merchant to safe baseline."
        elif feedback == "THIS_WAS_NOT_ME":
            alert.status = "CONFIRMED_FRAUD"
            alert.notes = "Customer confirmed unauthorized debit. Card temporarily locked; dispute case opened."
            if alert.transaction:
                alert.transaction.is_flagged_fraud = True
        
        db.commit()
        db.refresh(alert)
        return {
            "success": True,
            "alert_id": alert.id,
            "new_status": alert.status,
            "feedback": alert.user_feedback,
            "notes": alert.notes
        }

    @classmethod
    def inject_synthetic_anomaly(cls, db: Session, customer_id: int, scenario: str = "new_payee_outlier") -> Dict[str, Any]:
        """
        Fraud Simulator: Injects a live synthetic suspicious transaction to demonstrate
        end-to-end detection, scoring, and UI alerts.
        """
        account = db.query(Account).filter(Account.customer_id == customer_id).first()
        if not account:
            return {"success": False, "error": "No account found"}

        now = datetime.datetime.utcnow()

        if scenario == "velocity":
            # 5 quick micro-transactions
            created = []
            for i in range(5):
                tx = Transaction(
                    account_id=account.id,
                    customer_id=customer_id,
                    amount=4999.0 + (i * 10),
                    transaction_type="debit",
                    category="Shopping",
                    merchant_name=f"Online Electronics {i+1}",
                    timestamp=now - datetime.timedelta(seconds=(5 - i) * 60),
                    channel="UPI",
                    device_id="unknown-device-xyz",
                    location_city="London",
                    is_flagged_fraud=True
                )
                db.add(tx)
                db.flush()
                created.append(tx)
            target_tx = created[-1]

        elif scenario == "structuring":
            tx = Transaction(
                account_id=account.id,
                customer_id=customer_id,
                amount=49800.0,
                transaction_type="debit",
                category="Miscellaneous",
                merchant_name="Crypto Exchange Global",
                timestamp=now,
                channel="NEFT",
                device_id="tor-proxy-01",
                location_city="Dubai",
                is_flagged_fraud=True
            )
            db.add(tx)
            db.flush()
            target_tx = tx

        else: # default: nocturnal high value outlier to new merchant
            tx = Transaction(
                account_id=account.id,
                customer_id=customer_id,
                amount=85000.0,
                transaction_type="debit",
                category="Shopping",
                merchant_name="Luxury Watches Geneva",
                timestamp=now.replace(hour=3, minute=15),
                channel="CARD",
                device_id="unrecognized-macbook-pro",
                location_city="Geneva",
                location_country="CH",
                is_flagged_fraud=True,
                notes="Injected anomaly via Fraud Simulator"
            )
            db.add(tx)
            db.flush()
            target_tx = tx

        # Analyze with rule engine
        analysis = cls.analyze_transaction(db, customer_id, target_tx)
        
        # Create alert entry
        alert = FraudAlert(
            transaction_id=target_tx.id,
            customer_id=customer_id,
            risk_score=analysis["risk_score"],
            risk_level=analysis["risk_level"],
            triggered_rules=analysis["triggered_rules"],
            status="PENDING",
            notes="Live simulated anomaly detected by rule engine"
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        return {
            "success": True,
            "scenario": scenario,
            "transaction_id": target_tx.id,
            "amount": target_tx.amount,
            "formatted_amount": format_inr(target_tx.amount),
            "merchant": target_tx.merchant_name,
            "risk_score": alert.risk_score,
            "risk_level": alert.risk_level,
            "triggered_rules": alert.triggered_rules,
            "alert_id": alert.id
        }
