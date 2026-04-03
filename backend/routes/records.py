from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.db.database import get_db
from backend.schemas.record import RecordCreate, RecordUpdate, RecordResponse
from backend.auth.auth import get_current_user
from backend.auth.roles import require_role

router = APIRouter(prefix="/api/records", tags=["records"])

def _get_record(db, record_id: int):
    # safely fetch record
    record = db.execute(
        "SELECT * FROM records WHERE id = ? AND deleted_at IS NULL",
        (record_id,)
    ).fetchone()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return dict(record)

@router.post("", response_model=RecordResponse, dependencies=[require_role("admin", "analyst")])
def create_record(payload: RecordCreate, user: dict = Depends(get_current_user), db=Depends(get_db)):
    # create new record
    cur = db.execute(
        "INSERT INTO records (user_id, amount, type, category, date, notes) VALUES (?, ?, ?, ?, ?, ?)",
        (user["id"], payload.amount, payload.type, payload.category, payload.date, payload.notes)
    )
    record_id = cur.lastrowid
    # audit log
    db.execute(
        "INSERT INTO audit_logs (record_id, action, user_id, details) VALUES (?, ?, ?, ?)",
        (record_id, "CREATE", user["id"], f"Created record with amount {payload.amount}")
    )
    db.commit()
    return _get_record(db, record_id)

@router.get("", response_model=list[RecordResponse], dependencies=[require_role("admin", "analyst")])
def get_records(
    type: str = Query(None, pattern="^(income|expense)$"),
    category: str = None,
    from_date: str = None,
    to_date: str = None,
    search: str = Query(None, description="Search across notes and category"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    query = "SELECT * FROM records WHERE deleted_at IS NULL"
    params = []
    if type:
        query += " AND type = ?"
        params.append(type)
    if category:
        query += " AND category = ?"
        params.append(category)
    if from_date:
        query += " AND date >= ?"
        params.append(from_date)
    if to_date:
        query += " AND date <= ?"
        params.append(to_date)
        
    if search:
        query += " AND (notes LIKE ? OR category LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
        
    # apply pagination & ordering
    query += " ORDER BY date DESC LIMIT ? OFFSET ?"
    params.extend([limit, (page - 1) * limit])
    
    # print("debug query:", query)
    
    results = db.execute(query, params).fetchall()
    
    data_list = []
    for r in results:
        data_list.append(dict(r))
        
    return data_list

@router.patch("/{id}", response_model=RecordResponse, dependencies=[require_role("admin", "analyst")])
def update_record(id: int, payload: RecordUpdate, user: dict = Depends(get_current_user), db=Depends(get_db)):
    _get_record(db, id)
    
    updates, params = [], []
    for key, value in payload.dict(exclude_unset=True).items():
        updates.append(f"{key} = ?")
        params.append(value)
        
    if not updates:
        return _get_record(db, id)
        
    params.append(id)
    db.execute(f"UPDATE records SET {', '.join(updates)} WHERE id = ?", params)
    
    # audit log
    db.execute(
        "INSERT INTO audit_logs (record_id, action, user_id, details) VALUES (?, ?, ?, ?)",
        (id, "UPDATE", user["id"], f"Updated fields: {', '.join([k for k, v in payload.dict(exclude_unset=True).items()])}")
    )
    db.commit()
    return _get_record(db, id)

@router.delete("/{id}", status_code=204, dependencies=[require_role("admin")])
def delete_record(id: int, user: dict = Depends(get_current_user), db=Depends(get_db)):
    # admin only
    _get_record(db, id)
    
    # soft delete
    db.execute(
        "UPDATE records SET deleted_at = ? WHERE id = ?",
        (datetime.utcnow().isoformat(), id)
    )
    # audit log
    db.execute(
        "INSERT INTO audit_logs (record_id, action, user_id, details) VALUES (?, ?, ?, ?)",
        (id, "DELETE", user["id"], "Soft deleted record")
    )
    db.commit()