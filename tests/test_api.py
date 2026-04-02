import pytest
import sqlite3
import os
from fastapi.testclient import TestClient

from backend.main import app
from backend.db.database import get_db, init_db, DB_URL
from backend.helpers.hashing import hash_password
from backend.auth.auth import get_current_user

def override_get_current_user():
    return {
        "id": 1,
        "name": "Admin",
        "email": "admin@test.com",
        "role": "admin",
        "is_active": 1
    }

app.dependency_overrides[get_current_user] = override_get_current_user

TEST_DB_URL = "test_finance.db"

def override_get_db():
    conn = sqlite3.connect(TEST_DB_URL)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    import backend.db.database as db_app
    db_app.DB_URL = TEST_DB_URL 
    init_db()
    
    conn = sqlite3.connect(TEST_DB_URL)
    conn.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)", 
                ("Admin", "admin@test.com", hash_password("admin123"), "admin"))
    conn.commit()
    conn.close()
    
    yield
    
    if os.path.exists(TEST_DB_URL):
        os.remove(TEST_DB_URL)

client = TestClient(app)

def test_login_success():
    response = client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "admin123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_create_record_and_audit():
    login_response = client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "admin123"
    })
    token = login_response.json()["access_token"]
    
    res = client.post("/api/records", json={
        "amount": 500,
        "type": "income",
        "category": "freelance",
        "date": "2026-04-02",
        "notes": "Test Record"
    }, headers={"Authorization": f"Bearer {token}"})
    
    assert res.status_code == 200, res.text
    assert res.json()["amount"] == 500
    
    conn = sqlite3.connect(TEST_DB_URL)
    audit = conn.execute("SELECT * FROM audit_logs").fetchone()
    conn.close()
    
    assert audit is not None
    assert audit[2] == "CREATE" 
    
def test_dashboard_unauthorized():
    app.dependency_overrides.pop(get_current_user, None) 
    response = client.get("/api/dashboard")
    assert response.status_code == 401
