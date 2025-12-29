from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/customs", tags=["Customs"])


@router.post("/", response_model=schemas.CustomsLog, status_code=status.HTTP_201_CREATED)
def create_customs_log(log: schemas.CustomsLogCreate, db: Session = Depends(get_db)):
    """Create a new customs log entry"""
    # Verify company exists
    company = db.query(models.Company).filter(models.Company.id == log.company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Check if pedimento number already exists
    existing = db.query(models.CustomsLog).filter(
        models.CustomsLog.pedimento_number == log.pedimento_number
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pedimento number already exists"
        )
    
    # Verify expense exists if provided
    if log.expense_id:
        expense = db.query(models.Expense).filter(models.Expense.id == log.expense_id).first()
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found"
            )
    
    db_log = models.CustomsLog(**log.dict())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


@router.get("/", response_model=List[schemas.CustomsLog])
def list_customs_logs(
    company_id: int = None,
    status_filter: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List customs logs with optional filters"""
    query = db.query(models.CustomsLog)
    
    if company_id:
        query = query.filter(models.CustomsLog.company_id == company_id)
    
    if status_filter:
        query = query.filter(models.CustomsLog.status == status_filter)
    
    logs = query.order_by(models.CustomsLog.import_date.desc()).offset(skip).limit(limit).all()
    return logs


@router.get("/{log_id}", response_model=schemas.CustomsLog)
def get_customs_log(log_id: int, db: Session = Depends(get_db)):
    """Get customs log by ID"""
    log = db.query(models.CustomsLog).filter(models.CustomsLog.id == log_id).first()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customs log not found"
        )
    return log


@router.put("/{log_id}", response_model=schemas.CustomsLog)
def update_customs_log(
    log_id: int,
    log_update: schemas.CustomsLogUpdate,
    db: Session = Depends(get_db)
):
    """Update customs log"""
    log = db.query(models.CustomsLog).filter(models.CustomsLog.id == log_id).first()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customs log not found"
        )
    
    # Update fields
    for key, value in log_update.dict(exclude_unset=True).items():
        setattr(log, key, value)
    
    db.commit()
    db.refresh(log)
    return log


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customs_log(log_id: int, db: Session = Depends(get_db)):
    """Delete customs log"""
    log = db.query(models.CustomsLog).filter(models.CustomsLog.id == log_id).first()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customs log not found"
        )
    
    db.delete(log)
    db.commit()
    return None
