from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app import models, schemas
from app.config import settings

router = APIRouter(prefix="/api/invoices", tags=["Invoices"])


@router.post("/", response_model=schemas.Invoice, status_code=status.HTTP_201_CREATED)
def create_invoice(invoice: schemas.InvoiceCreate, db: Session = Depends(get_db)):
    """Create a new invoice with automatic tax calculation"""
    # Verify company exists
    company = db.query(models.Company).filter(models.Company.id == invoice.company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Check if invoice number already exists
    existing = db.query(models.Invoice).filter(
        models.Invoice.invoice_number == invoice.invoice_number
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice number already exists"
        )
    
    # Calculate tax (Texas Sales Tax: 8.25%)
    tax_amount = invoice.subtotal * settings.texas_sales_tax_rate
    total = invoice.subtotal + tax_amount
    
    # Create invoice
    db_invoice = models.Invoice(
        **invoice.dict(),
        tax_amount=round(tax_amount, 2),
        total=round(total, 2)
    )
    
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    return db_invoice


@router.get("/", response_model=List[schemas.Invoice])
def list_invoices(
    company_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List invoices with optional company filter"""
    query = db.query(models.Invoice)
    
    if company_id:
        query = query.filter(models.Invoice.company_id == company_id)
    
    invoices = query.offset(skip).limit(limit).all()
    return invoices


@router.get("/{invoice_id}", response_model=schemas.Invoice)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Get invoice by ID"""
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    return invoice


@router.put("/{invoice_id}", response_model=schemas.Invoice)
def update_invoice(
    invoice_id: int,
    invoice_update: schemas.InvoiceUpdate,
    db: Session = Depends(get_db)
):
    """Update invoice and recalculate tax if subtotal changed"""
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    update_data = invoice_update.dict(exclude_unset=True)
    
    # Recalculate tax if subtotal changed
    if 'subtotal' in update_data:
        new_subtotal = update_data['subtotal']
        tax_amount = new_subtotal * settings.texas_sales_tax_rate
        update_data['tax_amount'] = round(tax_amount, 2)
        update_data['total'] = round(new_subtotal + tax_amount, 2)
    
    # Update fields
    for key, value in update_data.items():
        setattr(invoice, key, value)
    
    db.commit()
    db.refresh(invoice)
    return invoice


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Delete invoice"""
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    db.delete(invoice)
    db.commit()
    return None
