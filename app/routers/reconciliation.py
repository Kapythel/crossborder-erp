from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from random import uniform, choice
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/reconciliation", tags=["Reconciliation"])


def generate_mock_bank_transactions(expenses: List[models.Expense]) -> List[schemas.BankTransaction]:
    """Generate mock bank transactions for demonstration"""
    transactions = []
    
    # Create matching transactions for some expenses
    for expense in expenses:
        # 70% chance of having a matching transaction
        if uniform(0, 1) < 0.7:
            # Add some variance to date (±2 days)
            days_offset = choice([-2, -1, 0, 1, 2])
            transaction_date = expense.date + timedelta(days=days_offset)
            
            # Add some variance to amount (for testing matching logic)
            amount_variance = uniform(-0.5, 0.5) if uniform(0, 1) < 0.3 else 0
            
            transaction = schemas.BankTransaction(
                transaction_id=f"TXN-{expense.id}-{abs(hash(str(expense.date)))}",
                date=transaction_date,
                description=expense.description[:50] if expense.description else "Purchase",
                amount=round(expense.amount + amount_variance, 2),
                currency=expense.currency
            )
            transactions.append(transaction)
    
    # Add some unmatched transactions
    for i in range(3):
        transaction = schemas.BankTransaction(
            transaction_id=f"TXN-UNMATCHED-{i}",
            date=datetime.utcnow() - timedelta(days=i),
            description=f"Unmatched Transaction {i+1}",
            amount=round(uniform(10, 200), 2),
            currency=choice(["USD", "MXN"])
        )
        transactions.append(transaction)
    
    return sorted(transactions, key=lambda x: x.date, reverse=True)


def match_expense_to_transaction(
    expense: models.Expense,
    transactions: List[schemas.BankTransaction]
) -> tuple:
    """
    Match an expense to a bank transaction
    Returns: (matching_transaction, confidence)
    """
    best_match = None
    best_confidence = "no_match"
    
    for transaction in transactions:
        # Check if already matched
        if hasattr(transaction, '_matched'):
            continue
        
        # Exact amount match within 2 days
        if (abs((transaction.date - expense.date).days) <= 2 and
            abs(transaction.amount - expense.amount) < 0.01 and
            transaction.currency == expense.currency):
            best_match = transaction
            best_confidence = "exact"
            transaction._matched = True
            break
        
        # Likely match: close amount and date
        if (abs((transaction.date - expense.date).days) <= 3 and
            abs(transaction.amount - expense.amount) < 1.0 and
            transaction.currency == expense.currency):
            if best_confidence != "exact":
                best_match = transaction
                best_confidence = "likely"
    
    return best_match, best_confidence


@router.get("/", response_model=List[schemas.ReconciliationItem])
def get_reconciliation(
    company_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get reconciliation view matching expenses with bank transactions
    This is a mockup using simulated bank data
    """
    # Get expenses for company
    expenses = db.query(models.Expense).filter(
        models.Expense.company_id == company_id
    ).order_by(
        models.Expense.date.desc()
    ).offset(skip).limit(limit).all()
    
    if not expenses:
        return []
    
    # Generate mock bank transactions
    transactions = generate_mock_bank_transactions(expenses)
    
    # Match expenses to transactions
    reconciliation_items = []
    for expense in expenses:
        matching_transaction, confidence = match_expense_to_transaction(expense, transactions)
        
        item = schemas.ReconciliationItem(
            expense=expense,
            matching_transaction=matching_transaction,
            match_confidence=confidence
        )
        reconciliation_items.append(item)
    
    return reconciliation_items
