import datetime
import random
from backend.database import SessionLocal, Base, engine
from backend.models import (
    User, Customer, Account, Transaction, Category,
    Budget, Goal, LoanSimulated, Product, FraudAlert, HoldingSimulated
)
from backend.security import hash_password
from backend.services.recommendation_service import RecommendationService
from backend.services.knowledge_service import KnowledgeService
from backend.services.fraud_service import FraudService
from backend.services.audit_service import AuditService

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(Customer).count() > 0:
            print("Database already seeded.")
            return

        print("Seeding database with 5 banking personas and 12 months of transactions...")

        # 1. Create Personas requested by user
        personas_data = [
            {
                "username": "indukiran",
                "email": "indukiran@example.com",
                "role": "customer",
                "first_name": "Indukiran",
                "last_name": "Reddy",
                "phone": "+919845012345",
                "dob": "1990-05-12",
                "pan": "ABCPI1234F",
                "income": 180000.0,
                "credit_score": 790,
                "employer": "Cloud Architectures Ltd",
                "risk_profile": "Moderate",
                "acc_num": "409210089101",
                "balance": 345000.0,
                "account_type": "salary"
            },
            {
                "username": "manasa",
                "email": "manasa@example.com",
                "role": "customer",
                "first_name": "Manasa",
                "last_name": "Rao",
                "phone": "+919845023456",
                "dob": "1993-08-22",
                "pan": "BCRPM9876M",
                "income": 135000.0,
                "credit_score": 765,
                "employer": "FinTech Innovations Inc",
                "risk_profile": "Moderate",
                "acc_num": "409210089202",
                "balance": 210000.0,
                "account_type": "salary"
            },
            {
                "username": "kishan",
                "email": "kishan@example.com",
                "role": "customer",
                "first_name": "Kishan",
                "last_name": "Kumar",
                "phone": "+919845034567",
                "dob": "1997-03-15",
                "pan": "CDEPK4567K",
                "income": 95000.0,
                "credit_score": 740,
                "employer": "Freelance Full-Stack Developer",
                "risk_profile": "Aggressive",
                "acc_num": "409210089303",
                "balance": 125000.0,
                "account_type": "current"
            },
            {
                "username": "manjunath",
                "email": "manjunath@example.com",
                "role": "customer",
                "first_name": "Manjunath",
                "last_name": "Hegde",
                "phone": "+919845045678",
                "dob": "1982-11-30",
                "pan": "DEFPM7890H",
                "income": 220000.0,
                "credit_score": 810,
                "employer": "Hegde Global Enterprises",
                "risk_profile": "Conservative",
                "acc_num": "409210089404",
                "balance": 560000.0,
                "account_type": "savings"
            }
        ]

        customers_created = []
        for p in personas_data:
            cust = Customer(
                first_name=p["first_name"],
                last_name=p["last_name"],
                phone=p["phone"],
                email=p["email"],
                date_of_birth=p["dob"],
                pan_card=p["pan"],
                monthly_income=p["income"],
                credit_score=p["credit_score"],
                employer=p["employer"],
                risk_profile=p["risk_profile"]
            )
            db.add(cust)
            db.flush()

            user = User(
                username=p["username"],
                email=p["email"],
                hashed_password=hash_password("password123"),
                role=p["role"],
                customer_id=cust.id
            )
            db.add(user)

            acc = Account(
                customer_id=cust.id,
                account_number=p["acc_num"],
                account_type=p["account_type"],
                balance=p["balance"],
                currency="INR"
            )
            db.add(acc)
            db.flush()

            customers_created.append((cust, acc, p))

        # Admin user (without customer record)
        admin_user = User(
            username="compliance_admin",
            email="admin@securebank.in",
            hashed_password=hash_password("admin123"),
            role="admin",
            customer_id=None
        )
        db.add(admin_user)
        db.commit()

        # 2. Generate 12 Months of Transactions for Personas
        merchants_by_category = {
            "Food & Dining": [
                ("Swiggy Online", 350.0, 1200.0, "UPI"),
                ("Zomato Delivery", 280.0, 950.0, "UPI"),
                ("Starbucks Coffee", 420.0, 750.0, "CARD"),
                ("Barbeque Nation", 1800.0, 4200.0, "POS"),
                ("Blinkit Quick Delivery", 450.0, 1500.0, "UPI"),
                ("Zepto Daily", 300.0, 1100.0, "UPI")
            ],
            "Shopping": [
                ("Amazon India", 800.0, 8500.0, "CARD"),
                ("Flipkart Retail", 650.0, 4500.0, "UPI"),
                ("Myntra Fashion", 1200.0, 3900.0, "UPI"),
                ("Croma Electronics", 3500.0, 18000.0, "CARD"),
                ("Zara Retail Store", 2500.0, 7500.0, "POS")
            ],
            "Housing & Rent": [
                ("Prestige Society Maintenance", 4500.0, 7500.0, "NEFT"),
                ("Landlord Rental Transfer", 25000.0, 45000.0, "NEFT")
            ],
            "Utilities": [
                ("BESCOM Electricity Board", 1800.0, 3400.0, "UPI"),
                ("Airtel Fiber Broadband", 999.0, 1499.0, "UPI"),
                ("Indane LPG Gas", 950.0, 1100.0, "UPI"),
                ("BWSSB Water Supply", 450.0, 850.0, "UPI")
            ],
            "Transportation": [
                ("Uber Rides", 220.0, 650.0, "UPI"),
                ("Ola Cabs", 180.0, 520.0, "UPI"),
                ("HPCL Fuel Station", 2000.0, 4500.0, "CARD"),
                ("NHAI FASTag Toll", 150.0, 400.0, "UPI")
            ],
            "Entertainment": [
                ("Netflix Subscription", 649.0, 649.0, "CARD"),
                ("Amazon Prime Video", 299.0, 299.0, "CARD"),
                ("Spotify Premium", 119.0, 119.0, "CARD"),
                ("PVR Cinemas Movie", 600.0, 1800.0, "POS")
            ],
            "Healthcare": [
                ("Apollo Pharmacy", 350.0, 2200.0, "UPI"),
                ("1mg Healthcare", 650.0, 1800.0, "UPI"),
                ("Dr. Lal PathLabs", 1200.0, 3500.0, "POS")
            ],
            "Investments": [
                ("Zerodha Broking SIP", 10000.0, 25000.0, "NEFT"),
                ("Groww Mutual Funds", 5000.0, 15000.0, "UPI")
            ]
        }

        # Reference anchor date: Nov 21, 2026
        ref_date = datetime.datetime(2026, 11, 21, 14, 0, 0)
        random.seed(42)

        for cust, acc, p_info in customers_created:
            # Monthly salary / client credits for past 12 months
            for month_offset in range(12, -1, -1):
                m_date = ref_date - datetime.timedelta(days=month_offset * 30.5)
                # Salary on the 1st
                salary_date = datetime.datetime(m_date.year, m_date.month, 1, 9, 30)
                db.add(Transaction(
                    account_id=acc.id,
                    customer_id=cust.id,
                    amount=cust.monthly_income,
                    transaction_type="credit",
                    category="Salary / Income",
                    merchant_name=cust.employer or "Monthly Remittance",
                    description="Monthly Salary Credit",
                    timestamp=salary_date,
                    channel="NEFT"
                ))

                # Recurring Rent on the 3rd
                rent_date = datetime.datetime(m_date.year, m_date.month, 3, 11, 0)
                db.add(Transaction(
                    account_id=acc.id,
                    customer_id=cust.id,
                    amount=min(cust.monthly_income * 0.28, 35000.0),
                    transaction_type="debit",
                    category="Housing & Rent",
                    merchant_name="Landlord Rental Transfer",
                    description="Monthly House Rent",
                    timestamp=rent_date,
                    channel="NEFT",
                    is_recurring=True
                ))

                # Recurring Subscriptions on 5th
                db.add(Transaction(
                    account_id=acc.id,
                    customer_id=cust.id,
                    amount=649.0,
                    transaction_type="debit",
                    category="Entertainment",
                    merchant_name="Netflix Subscription",
                    description="Standard Monthly Plan",
                    timestamp=datetime.datetime(m_date.year, m_date.month, 5, 8, 15),
                    channel="CARD",
                    is_recurring=True
                ))

                # Monthly SIP Investment on 10th
                db.add(Transaction(
                    account_id=acc.id,
                    customer_id=cust.id,
                    amount=min(cust.monthly_income * 0.15, 20000.0),
                    transaction_type="debit",
                    category="Investments",
                    merchant_name="Zerodha Broking SIP",
                    description="Nifty 50 Index Fund Direct Growth",
                    timestamp=datetime.datetime(m_date.year, m_date.month, 10, 10, 0),
                    channel="NEFT",
                    is_recurring=True
                ))

                # Discretionary transactions (food, shopping, transit)
                tx_count = random.randint(15, 25)
                for _ in range(tx_count):
                    day = random.randint(1, min(28, 21 if month_offset == 0 else 28))
                    hour = random.randint(8, 22)
                    minute = random.randint(0, 59)
                    tx_time = datetime.datetime(m_date.year, m_date.month, day, hour, minute)
                    
                    cat = random.choice(list(merchants_by_category.keys()))
                    m_tuple = random.choice(merchants_by_category[cat])
                    amt = round(random.uniform(m_tuple[1], m_tuple[2]), 2)

                    db.add(Transaction(
                        account_id=acc.id,
                        customer_id=cust.id,
                        amount=amt,
                        transaction_type="debit",
                        category=cat,
                        merchant_name=m_tuple[0],
                        description=f"{cat} purchase at {m_tuple[0]}",
                        timestamp=tx_time,
                        channel=m_tuple[3],
                        location_city="Mumbai" if cust.id % 2 == 0 else "Bengaluru"
                    ))

            # Add Budgets & Goals
            db.add(Budget(customer_id=cust.id, category="Food & Dining", monthly_limit=cust.monthly_income * 0.20))
            db.add(Budget(customer_id=cust.id, category="Shopping", monthly_limit=cust.monthly_income * 0.15))
            db.add(Goal(
                customer_id=cust.id,
                name="Emergency Reserve & Home Down Payment",
                target_amount=500000.0,
                current_amount=cust.monthly_income * 2.2,
                target_date="2027-12-31"
            ))

            # Add Holdings
            db.add(HoldingSimulated(
                customer_id=cust.id,
                asset_type="Equity",
                asset_name="UTI Nifty 50 Index Fund",
                invested_amount=cust.monthly_income * 1.5,
                current_value=cust.monthly_income * 1.82,
                return_pct=21.3
            ))
            db.add(HoldingSimulated(
                customer_id=cust.id,
                asset_type="Debt",
                asset_name="HDFC Short Term Debt Fund",
                invested_amount=cust.monthly_income * 0.8,
                current_value=cust.monthly_income * 0.86,
                return_pct=7.5
            ))
            db.add(HoldingSimulated(
                customer_id=cust.id,
                asset_type="Gold",
                asset_name="Sovereign Gold Bond 2026",
                invested_amount=50000.0,
                current_value=63500.0,
                return_pct=27.0
            ))

        db.commit()

        # 3. Seed Products Catalogue & Regulatory Corpus
        RecommendationService.get_recommendations(db, 1)
        KnowledgeService.seed_corpus_if_empty(db)

        # 4. Inject a couple of initial fraud alerts for the primary user (Rajesh Sharma)
        # to ensure the Fraud Alert Centre has live data to display right away
        primary_cust = customers_created[0][0]
        FraudService.inject_synthetic_anomaly(db, primary_cust.id, scenario="outlier")
        FraudService.inject_synthetic_anomaly(db, primary_cust.id, scenario="velocity")

        # 5. Genesis Audit Entry
        AuditService.log_event(
            db=db,
            request_id="GENESIS-INIT",
            action_type="SYSTEM_BOOTSTRAP_SEED",
            customer_id=None,
            notes="Initial system initialization and cryptographic hash-chain bootstrap completed."
        )

        print("Seeding completed successfully!")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
