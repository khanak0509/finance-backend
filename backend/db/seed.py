from backend.db.database import get_connection, init_db
from backend.utils.hashing import hash_password

def seed():
    init_db()
    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        
        users = [
            ("Admin", "admin@finance.dev", hash_password("admin123"), "admin"),
            ("Analyst", "analyst@finance.dev", hash_password("analyst123"), "analyst"),
            ("Viewer", "viewer@finance.dev", hash_password("viewer123"), "viewer"),
        ]
        
        for u in users:
            conn.execute(
                "INSERT OR IGNORE INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                u
            )
            
        count = conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        if count >= 15:
            return

        users_dict = {row["email"]: row["id"] for row in conn.execute("SELECT id, email FROM users")}
        admin_id = users_dict.get("admin@finance.dev", 1)
        analyst_id = users_dict.get("analyst@finance.dev", 2)
        
        records = [
            (admin_id, 5000, "income", "salary", "2024-01-05", "January salary"),
            (admin_id, -1200, "expense", "rent", "2024-01-01", "Rent"),
            (analyst_id, -300, "expense", "groceries", "2024-01-10", "Groceries"),
            (analyst_id, 800, "income", "freelance", "2024-02-15", "Side project"),
            (admin_id, -100, "expense", "utilities", "2024-02-20", "Electricity"),
            (admin_id, -50, "expense", "transport", "2024-02-28", "Metro"),
            (analyst_id, -200, "expense", "entertainment", "2024-03-05", "Concert"),
            (analyst_id, 5200, "income", "salary", "2024-03-10", "March salary"),
            (admin_id, -150, "expense", "groceries", "2024-03-15", "Food"),
            (admin_id, 1000, "income", "bonus", "2024-04-01", "Q1 Bonus"),
            (analyst_id, -400, "expense", "travel", "2024-04-12", "Trip"),
            (analyst_id, -80, "expense", "utilities", "2024-04-20", "Water bill"),
            (admin_id, -600, "expense", "healthcare", "2024-05-02", "Dentist"),
            (admin_id, 4800, "income", "salary", "2024-05-05", "May salary"),
            (analyst_id, -250, "expense", "groceries", "2024-05-18", "Groceries"),
        ]

        conn.executemany(
            "INSERT INTO records (user_id, amount, type, category, date, notes) VALUES (?, ?, ?, ?, ?, ?)",
            records
        )

if __name__ == "__main__":
    seed()
