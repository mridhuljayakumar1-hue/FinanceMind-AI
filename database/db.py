import sqlite3
import os
from datetime import datetime
from database.models import Transaction, Budget, SavingsGoal, ChatMessage

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "finance.db")

def get_connection(db_path=DEFAULT_DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=DEFAULT_DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Create transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                description TEXT
            )
        """)
        
        # Create budgets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT UNIQUE NOT NULL,
                amount REAL NOT NULL
            )
        """)
        
        # Create savings_goals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS savings_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                target_amount REAL NOT NULL,
                current_amount REAL NOT NULL,
                target_date TEXT NOT NULL
            )
        """)
        
        # Create chat_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        
        # Seed default budgets if they don't exist
        cursor.execute("SELECT COUNT(*) FROM budgets")
        if cursor.fetchone()[0] == 0:
            default_budgets = [
                ("Groceries", 8000.0),
                ("Rent", 15000.0),
                ("Utilities", 3000.0),
                ("Entertainment", 3000.0),
                ("Dining Out", 3000.0),
                ("Transport", 2000.0),
                ("Medical", 2000.0),
                ("Shopping", 3000.0),
                ("Other", 2000.0)
            ]
            cursor.executemany("INSERT INTO budgets (category, amount) VALUES (?, ?)", default_budgets)

        # Seed default transactions
        cursor.execute("SELECT COUNT(*) FROM transactions")
        if cursor.fetchone()[0] == 0:
            current_month = datetime.now().strftime("%Y-%m")
            default_txs = [
                ("income", "Salary", 50000.0, f"{current_month}-01", "Monthly salary credit"),
                ("income", "Freelance", 8000.0, f"{current_month}-15", "Freelance web project"),
                ("expense", "Rent", 15000.0, f"{current_month}-01", "Monthly apartment rent"),
                ("expense", "Groceries", 3500.0, f"{current_month}-03", "Weekly grocery shopping"),
                ("expense", "Groceries", 2800.0, f"{current_month}-10", "Mid-month groceries"),
                ("expense", "Utilities", 2200.0, f"{current_month}-04", "Electricity + Internet bill"),
                ("expense", "Entertainment", 1200.0, f"{current_month}-08", "OTT subscriptions + movie"),
                ("expense", "Dining Out", 1800.0, f"{current_month}-12", "Dinner with friends"),
                ("expense", "Transport", 1500.0, f"{current_month}-05", "Cab + monthly bus pass"),
                ("expense", "Other", 800.0, f"{current_month}-20", "Stationery and misc")
            ]
            cursor.executemany("INSERT INTO transactions (type, category, amount, date, description) VALUES (?, ?, ?, ?, ?)", default_txs)

            
        # Seed default savings goal
        cursor.execute("SELECT COUNT(*) FROM savings_goals")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO savings_goals (name, target_amount, current_amount, target_date) VALUES (?, ?, ?, ?)",
                ("Emergency Fund", 100000.0, 35000.0, f"{int(datetime.now().strftime('%Y'))+1}-12-31")
            )

            
        conn.commit()

# --- Transactions Functions ---

def add_transaction(tx: Transaction, db_path=DEFAULT_DB_PATH) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO transactions (type, category, amount, date, description) VALUES (?, ?, ?, ?, ?)",
            (tx.type, tx.category, tx.amount, tx.date, tx.description)
        )
        conn.commit()
        return cursor.lastrowid

def get_all_transactions(db_path=DEFAULT_DB_PATH):
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions ORDER BY date DESC, id DESC")
        rows = cursor.fetchall()
        return [Transaction(id=r['id'], type=r['type'], category=r['category'], amount=r['amount'], date=r['date'], description=r['description']) for r in rows]

def delete_transaction(tx_id: int, db_path=DEFAULT_DB_PATH) -> bool:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
        conn.commit()
        return cursor.rowcount > 0

# --- Budgets Functions ---

def set_budget(category: str, amount: float, db_path=DEFAULT_DB_PATH):
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO budgets (category, amount) VALUES (?, ?)
            ON CONFLICT(category) DO UPDATE SET amount = excluded.amount
        """, (category, amount))
        conn.commit()

def get_all_budgets(db_path=DEFAULT_DB_PATH):
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM budgets")
        rows = cursor.fetchall()
        return [Budget(id=r['id'], category=r['category'], amount=r['amount']) for r in rows]

def get_budget_for_category(category: str, db_path=DEFAULT_DB_PATH):
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM budgets WHERE category = ?", (category,))
        row = cursor.fetchone()
        if row:
            return Budget(id=row['id'], category=row['category'], amount=row['amount'])
        return None

def delete_budget(category: str, db_path=DEFAULT_DB_PATH) -> bool:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM budgets WHERE category = ?", (category,))
        conn.commit()
        return cursor.rowcount > 0

# --- Savings Goals Functions ---

def add_savings_goal(goal: SavingsGoal, db_path=DEFAULT_DB_PATH) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO savings_goals (name, target_amount, current_amount, target_date) VALUES (?, ?, ?, ?)",
            (goal.name, goal.target_amount, goal.current_amount, goal.target_date)
        )
        conn.commit()
        return cursor.lastrowid

def get_all_savings_goals(db_path=DEFAULT_DB_PATH):
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM savings_goals ORDER BY target_date ASC")
        rows = cursor.fetchall()
        return [SavingsGoal(id=r['id'], name=r['name'], target_amount=r['target_amount'], current_amount=r['current_amount'], target_date=r['target_date']) for r in rows]

def update_savings_goal_progress(goal_id: int, current_amount: float, db_path=DEFAULT_DB_PATH) -> bool:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE savings_goals SET current_amount = ? WHERE id = ?", (current_amount, goal_id))
        conn.commit()
        return cursor.rowcount > 0

def delete_savings_goal(goal_id: int, db_path=DEFAULT_DB_PATH) -> bool:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM savings_goals WHERE id = ?", (goal_id,))
        conn.commit()
        return cursor.rowcount > 0

# --- Chat History Functions ---

def add_chat_message(msg: ChatMessage, db_path=DEFAULT_DB_PATH) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_history (role, content, timestamp) VALUES (?, ?, ?)",
            (msg.role, msg.content, msg.timestamp)
        )
        conn.commit()
        return cursor.lastrowid

def get_chat_history(limit=50, db_path=DEFAULT_DB_PATH):
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chat_history ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        messages = [ChatMessage(id=r['id'], role=r['role'], content=r['content'], timestamp=r['timestamp']) for r in rows]
        # Return in chronological order
        messages.reverse()
        return messages

def clear_chat_history(db_path=DEFAULT_DB_PATH):
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_history")
        conn.commit()
