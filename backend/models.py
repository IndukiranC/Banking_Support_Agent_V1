import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from backend.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="customer")  # customer, analyst, admin
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    totp_secret = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    customer = relationship("Customer", back_populates="user", uselist=False)

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(100), nullable=False)
    date_of_birth = Column(String(20), nullable=True)
    pan_card = Column(String(10), nullable=True)
    credit_score = Column(Integer, default=750)
    monthly_income = Column(Float, default=75000.0)
    employer = Column(String(100), nullable=True)
    risk_profile = Column(String(20), default="Moderate")  # Conservative, Moderate, Aggressive
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="customer", uselist=False)
    accounts = relationship("Account", back_populates="customer", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="customer", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="customer", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="customer", cascade="all, delete-orphan")
    loans = relationship("LoanSimulated", back_populates="customer", cascade="all, delete-orphan")
    holdings = relationship("HoldingSimulated", back_populates="customer", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="customer", cascade="all, delete-orphan")

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    account_number = Column(String(30), unique=True, index=True, nullable=False)
    account_type = Column(String(20), default="savings")  # savings, salary, current
    balance = Column(Float, default=0.0)
    currency = Column(String(5), default="INR")
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    customer = relationship("Customer", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(10), nullable=False)  # debit, credit
    category = Column(String(50), nullable=False, index=True)
    merchant_name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    channel = Column(String(20), default="UPI")  # UPI, NEFT, IMPS, POS, CARD
    device_id = Column(String(50), default="dev-main-phone")
    location_city = Column(String(50), default="Mumbai")
    location_country = Column(String(10), default="IN")
    ip_address = Column(String(45), default="127.0.0.1")
    is_flagged_fraud = Column(Boolean, default=False)
    is_recurring = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    
    account = relationship("Account", back_populates="transactions")
    customer = relationship("Customer", back_populates="transactions")
    fraud_alert = relationship("FraudAlert", back_populates="transaction", uselist=False)

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    icon = Column(String(50), default="tag")
    is_essential = Column(Boolean, default=False)  # For 50/30/20 budget analysis

class Budget(Base):
    __tablename__ = "budgets"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    category = Column(String(50), nullable=False)
    monthly_limit = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    customer = relationship("Customer", back_populates="budgets")

class Goal(Base):
    __tablename__ = "goals"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    name = Column(String(100), nullable=False)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    target_date = Column(String(20), nullable=False)
    status = Column(String(20), default="IN_PROGRESS")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    customer = relationship("Customer", back_populates="goals")

class LoanSimulated(Base):
    __tablename__ = "loans_simulated"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    loan_type = Column(String(50), default="Home Loan")  # Home, Personal, Auto, Education
    principal = Column(Float, nullable=False)
    annual_interest_rate = Column(Float, nullable=False)
    tenure_months = Column(Integer, nullable=False)
    emi = Column(Float, nullable=False)
    total_interest = Column(Float, nullable=False)
    status = Column(String(20), default="SIMULATED")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    customer = relationship("Customer", back_populates="loans")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String(30), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # credit_card, loan, savings, fd
    interest_rate_or_fee = Column(String(50), nullable=False)
    reward_rate = Column(String(100), nullable=True)
    min_income = Column(Float, default=0.0)
    min_credit_score = Column(Integer, default=650)
    min_balance = Column(Float, default=0.0)
    description = Column(Text, nullable=False)
    caveats = Column(Text, nullable=True)
    rules_json = Column(JSON, default=dict)

class FraudAlert(Base):
    __tablename__ = "fraud_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    risk_score = Column(Integer, nullable=False)  # 0 to 100
    risk_level = Column(String(10), nullable=False)  # LOW, MEDIUM, HIGH
    triggered_rules = Column(JSON, default=list)  # [{name, reason, weight, score}]
    status = Column(String(30), default="PENDING")  # PENDING, CONFIRMED_FRAUD, DISMISSED_USER, REVIEWED_ANALYST
    user_feedback = Column(String(50), nullable=True)  # "THIS_WAS_ME", "THIS_WAS_NOT_ME"
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    transaction = relationship("Transaction", back_populates="fraud_alert")

class HoldingSimulated(Base):
    __tablename__ = "holdings_simulated"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    asset_type = Column(String(30), nullable=False)  # Equity, Debt, Gold, Liquid
    asset_name = Column(String(100), nullable=False)
    invested_amount = Column(Float, nullable=False)
    current_value = Column(Float, nullable=False)
    return_pct = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    customer = relationship("Customer", back_populates="holdings")

class KBDocument(Base):
    __tablename__ = "kb_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    document_type = Column(String(50), nullable=False)
    version = Column(String(20), default="1.0")
    effective_date = Column(String(20), nullable=False)
    source_url = Column(String(255), nullable=True)
    
    chunks = relationship("KBChunk", back_populates="document", cascade="all, delete-orphan")

class KBChunk(Base):
    __tablename__ = "kb_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("kb_documents.id"), nullable=False)
    section_title = Column(String(200), nullable=False)
    section_number = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    keywords = Column(String(255), nullable=True)
    embedding = Column(JSON, nullable=True)  # list of floats
    
    document = relationship("KBDocument", back_populates="chunks")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    title = Column(String(100), default="New Chat")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    customer = relationship("Customer", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    intent = Column(String(50), nullable=True)
    result_object = Column(JSON, nullable=True)
    verification_status = Column(String(30), default="PASSED")  # PASSED, REGENERATED, TEMPLATE_FALLBACK
    calculation_details = Column(JSON, nullable=True)
    latency_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="messages")

class AuditLogEntry(Base):
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(64), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    customer_id = Column(Integer, nullable=True)
    user_id = Column(Integer, nullable=True)
    action_type = Column(String(50), nullable=False)
    intent = Column(String(50), nullable=True)
    services_invoked = Column(JSON, default=list)
    verification_status = Column(String(30), nullable=True)
    prev_hash = Column(String(64), nullable=False)
    curr_hash = Column(String(64), nullable=False)
    client_ip = Column(String(45), default="127.0.0.1")
    notes = Column(Text, nullable=True)
