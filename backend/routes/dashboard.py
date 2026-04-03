from fastapi import APIRouter, Depends
from backend.auth.auth import get_current_user
from backend.db.database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("")
def dashboard(user: dict = Depends(get_current_user), db=Depends(get_db)):
    income = db.execute("SELECT COALESCE(SUM(amount), 0) FROM records WHERE type='income' AND deleted_at IS NULL").fetchone()[0]
    expense = db.execute("SELECT COALESCE(SUM(amount), 0) FROM records WHERE type='expense' AND deleted_at IS NULL").fetchone()[0]
    
    categories = db.execute(
        "SELECT category, SUM(amount) FROM records WHERE deleted_at IS NULL GROUP BY category"
    ).fetchall()
    
    recent = db.execute(
        "SELECT * FROM records WHERE deleted_at IS NULL ORDER BY date DESC, id DESC LIMIT 5"
    ).fetchall()
    
    months = db.execute(
        """
        SELECT 
            strftime('%Y-%m', date) as month,
            SUM(CASE WHEN type='income' THEN amount ELSE 0 END) as income,
            SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) as expense
        FROM records
        WHERE deleted_at IS NULL
        GROUP BY month
        ORDER BY month
        """
    ).fetchall()

    return {
        "total_income": income,
        "total_expenses": expense,
        "net_balance": income - expense,
        "category_breakdown": {row[0] or "uncategorized": row[1] for row in categories},
        "recent_transactions": [dict(r) for r in recent],
        "monthly_trend": [{"month": r[0], "income": r[1], "expense": r[2]} for r in months]
    }
