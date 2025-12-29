from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ============ Company Schemas ============
class CompanyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    ein: str = Field(..., min_length=9, max_length=50)
    texas_sales_tax_id: Optional[str] = Field(None, max_length=50)
    rfc: Optional[str] = Field(None, max_length=50)


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    texas_sales_tax_id: Optional[str] = Field(None, max_length=50)
    rfc: Optional[str] = Field(None, max_length=50)


class Company(CompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============ Invoice Schemas ============
class InvoiceBase(BaseModel):
    invoice_number: str = Field(..., max_length=100)
    date: datetime
    subtotal: float = Field(..., gt=0)
    currency: str = Field(default="USD", pattern="^(USD|MXN)$")
    status: str = Field(default="pending")
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    company_id: int


class InvoiceUpdate(BaseModel):
    subtotal: Optional[float] = Field(None, gt=0)
    status: Optional[str] = None
    notes: Optional[str] = None


class Invoice(InvoiceBase):
    id: int
    company_id: int
    tax_amount: float
    total: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============ Expense Schemas ============
class ExpenseBase(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", pattern="^(USD|MXN)$")
    date: datetime
    category: Optional[str] = Field(None, max_length=100)
    vendor: Optional[str] = Field(None, max_length=255)
    tax_amount: Optional[float] = None
    tip_amount: Optional[float] = None


class ExpenseCreate(ExpenseBase):
    company_id: int
    receipt_url: Optional[str] = None
    ocr_data: Optional[dict] = None


class ExpenseUpdate(BaseModel):
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    amount: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = Field(None, pattern="^(USD|MXN)$")
    category: Optional[str] = None
    vendor: Optional[str] = None
    tax_amount: Optional[float] = None
    tip_amount: Optional[float] = None
    status: Optional[str] = None


class Expense(ExpenseBase):
    id: int
    company_id: int
    receipt_url: Optional[str]
    ocr_data: Optional[dict]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============ OCR Response Schema ============
class OCRResult(BaseModel):
    raw_text: str
    detected_currency: str
    extracted_fields: dict
    confidence: str  # high, medium, low


# ============ Customs Log Schemas ============
class CustomsLogBase(BaseModel):
    pedimento_number: str = Field(..., max_length=100)
    bill_of_lading: Optional[str] = Field(None, max_length=100)
    import_date: datetime
    customs_value: float = Field(..., gt=0)
    currency: str = Field(default="USD", pattern="^(USD|MXN)$")
    status: str = Field(default="in_process")
    notes: Optional[str] = None


class CustomsLogCreate(CustomsLogBase):
    company_id: int
    expense_id: Optional[int] = None


class CustomsLogUpdate(BaseModel):
    bill_of_lading: Optional[str] = None
    customs_value: Optional[float] = Field(None, gt=0)
    status: Optional[str] = None
    notes: Optional[str] = None


class CustomsLog(CustomsLogBase):
    id: int
    company_id: int
    expense_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============ Reconciliation Schema ============
class BankTransaction(BaseModel):
    """Mock bank transaction for reconciliation"""
    transaction_id: str
    date: datetime
    description: str
    amount: float
    currency: str


class ReconciliationItem(BaseModel):
    expense: Expense
    matching_transaction: Optional[BankTransaction]
    match_confidence: str  # exact, likely, no_match
