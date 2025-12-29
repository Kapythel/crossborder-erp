from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app import models, schemas
from app.services.ocr_processor import OCRProcessor
from app.services.file_handler import FileHandler
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/expenses", tags=["Expenses"])
ocr_processor = OCRProcessor()
file_handler = FileHandler()


@router.post("/upload", response_model=schemas.OCRResult)
async def upload_receipt(
    file: UploadFile = File(...),
    company_id: int = Form(...)
):
    """
    Upload receipt image/PDF and extract data via OCR
    This endpoint processes the file and returns extracted data
    The user can then review/edit before creating the expense
    """
    # Verify company exists
    # Note: We can't use db dependency here because it's async
    # In production, consider using async SQLAlchemy
    
    try:
        # Save file and get bytes
        file_path, file_bytes = await file_handler.save_file(file)
        
        # Process with OCR
        raw_text, currency, extracted_fields = ocr_processor.process(
            file_bytes,
            file.content_type
        )
        
        # Determine confidence based on fields extracted
        extracted_count = len([v for v in extracted_fields.values() if v is not None])
        if extracted_count >= 4:
            confidence = "high"
        elif extracted_count >= 2:
            confidence = "medium"
        else:
            confidence = "low"
        
        return schemas.OCRResult(
            raw_text=raw_text,
            detected_currency=currency,
            extracted_fields=extracted_fields,
            confidence=confidence
        )
    
    except Exception as e:
        logger.error(f"Error processing receipt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing receipt: {str(e)}"
        )


@router.post("/", response_model=schemas.Expense, status_code=status.HTTP_201_CREATED)
def create_expense(expense: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    """Create a new expense (after OCR review)"""
    # Verify company exists
    company = db.query(models.Company).filter(models.Company.id == expense.company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    db_expense = models.Expense(**expense.dict())
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


@router.get("/", response_model=List[schemas.Expense])
def list_expenses(
    company_id: int = None,
    category: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List expenses with optional filters"""
    query = db.query(models.Expense)
    
    if company_id:
        query = query.filter(models.Expense.company_id == company_id)
    
    if category:
        query = query.filter(models.Expense.category == category)
    
    expenses = query.order_by(models.Expense.date.desc()).offset(skip).limit(limit).all()
    return expenses


@router.get("/{expense_id}", response_model=schemas.Expense)
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    """Get expense by ID"""
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    return expense


@router.put("/{expense_id}", response_model=schemas.Expense)
def update_expense(
    expense_id: int,
    expense_update: schemas.ExpenseUpdate,
    db: Session = Depends(get_db)
):
    """Update expense (for manual corrections after OCR)"""
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    # Update fields
    for key, value in expense_update.dict(exclude_unset=True).items():
        setattr(expense, key, value)
    
    db.commit()
    db.refresh(expense)
    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    """Delete expense"""
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    # Delete associated file if exists
    if expense.receipt_url:
        # Extract file path from URL (for local storage)
        # In production with Cloudinary, skip this
        pass
    
    db.delete(expense)
    db.commit()
    return None
