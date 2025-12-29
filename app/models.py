from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Company(Base):
    """Multi-tenant company model"""
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    ein = Column(String(50), unique=True, nullable=False, index=True)  # US Tax ID
    texas_sales_tax_id = Column(String(50), nullable=True)
    rfc = Column(String(50), nullable=True, index=True)  # Mexico Tax ID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    invoices = relationship("Invoice", back_populates="company", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="company", cascade="all, delete-orphan")
    customs_logs = relationship("CustomsLog", back_populates="company", cascade="all, delete-orphan")


class Invoice(Base):
    """Invoice model with automatic tax calculation"""
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    invoice_number = Column(String(100), nullable=False, unique=True, index=True)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    subtotal = Column(Float, nullable=False)
    tax_amount = Column(Float, nullable=False)  # Calculated based on Texas rate (8.25%)
    total = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")  # USD or MXN
    status = Column(String(50), default="pending")  # pending, paid, cancelled
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="invoices")


class Expense(Base):
    """Expense model with OCR integration"""
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    description = Column(String(500), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")  # USD or MXN
    receipt_url = Column(String(500), nullable=True)  # Local path or Cloudinary URL
    ocr_data = Column(JSON, nullable=True)  # Extracted OCR fields
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    category = Column(String(100), nullable=True)  # e.g., "Meals", "Transportation"
    vendor = Column(String(255), nullable=True)
    tax_amount = Column(Float, nullable=True)
    tip_amount = Column(Float, nullable=True)
    status = Column(String(50), default="pending")  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="expenses")
    customs_logs = relationship("CustomsLog", back_populates="expense")


class CustomsLog(Base):
    """Customs log for cross-border tracking"""
    __tablename__ = "customs_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=True, index=True)
    pedimento_number = Column(String(100), nullable=False, unique=True, index=True)
    bill_of_lading = Column(String(100), nullable=True)
    import_date = Column(DateTime, nullable=False)
    customs_value = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(String(50), default="in_process")  # in_process, cleared, held
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="customs_logs")
    expense = relationship("Expense", back_populates="customs_logs")
