from fastapi import APIRouter, Depends
from backend.auth.auth import get_current_user
from backend.db.database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("")
def dashboard(user: dict = Depends(get_current_user), db=Depends(get_db)):
    income = db.execute("SELECT COALESCE(SUM(amount), 0) FROM records WHERE type='income' AND deleted_at IS NULL").fetchone()[0]
    expense = db.execute("SELECT COALESCE(SUM(amount), 0) FROM records WHERE type='expense' AND deleted_at IS NULL").fetchone()[0]

    # print("income and expense:", income, expense)

    cat_data = db.execute(
        "SELECT category, SUM(amount) FROM records WHERE deleted_at IS NULL GROUP BY category"
    ).fetchall()
    
    recent_tx = db.execute(
        "SELECT * FROM records WHERE deleted_at IS NULL ORDER BY date DESC, id DESC LIMIT 5"
    ).fetchall()
    
    # print(recent_tx)
    
    monthly_data = db.execute(
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

    cat_dict = {}
    for row in cat_data:
        k = row[0]
        if not k:
            k = "uncategorized"
        cat_dict[k] = row[1]

    recent_list = []
    for r in recent_tx:
        recent_list.append(dict(r))

    trend_list = []
    for m in monthly_data:
        trend_list.append({
            "month": m[0],
            "income": m[1],
            "expense": m[2]
        })

    return {
        "total_income": income,
        "total_expenses": expense,
        "net_balance": income - expense,
        "category_breakdown": cat_dict,
        "recent_transactions": recent_list,
        "monthly_trend": trend_list
    }