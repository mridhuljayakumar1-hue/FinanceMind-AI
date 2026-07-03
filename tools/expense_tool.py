from langchain_core.tools import tool
import database.db as db
from database.models import Transaction
from datetime import datetime

CURRENCY = "₹"

@tool
def add_transaction_tool(type: str, category: str, amount: float, date_str: str = None, description: str = "") -> str:
    """
    Records a new income or expense transaction.
    
    Parameters:
    - type: 'income' or 'expense' (str).
    - category: e.g. 'Salary', 'Groceries', 'Rent', 'Utilities', 'Entertainment', 'Transport', 'Other' (str).
    - amount: Monetary amount in Rupees (float).
    - date_str: Date in YYYY-MM-DD format (str, optional, defaults to today).
    - description: Short note about the transaction (str, optional).
    """
    try:
        if type not in ['income', 'expense']:
            return "Error: type must be 'income' or 'expense'."
        if amount <= 0:
            return "Error: Amount must be greater than zero."
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        else:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                return "Error: date_str must be YYYY-MM-DD format."
        tx = Transaction(type=type, category=category, amount=amount, date=date_str, description=description)
        tx_id = db.add_transaction(tx)
        return f"Recorded {type} '{category}' of {CURRENCY}{amount:,.2f} on {date_str} (ID: {tx_id})."
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def get_financial_summary(month_str: str = None) -> str:
    """
    Returns total income, expenses, net savings, and savings rate for a given month (YYYY-MM).
    Defaults to the current month if not specified.
    """
    try:
        db.init_db()
        transactions = db.get_all_transactions()
        if not month_str:
            month_str = datetime.now().strftime("%Y-%m")
        filtered = [t for t in transactions if t.date.startswith(month_str)]
        total_income = sum(t.amount for t in filtered if t.type == 'income')
        total_expense = sum(t.amount for t in filtered if t.type == 'expense')
        net_savings = total_income - total_expense
        savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0
        return (
            f"Financial Summary for {month_str}:\n"
            f"- Total Income: {CURRENCY}{total_income:,.2f}\n"
            f"- Total Expenses: {CURRENCY}{total_expense:,.2f}\n"
            f"- Net Savings: {CURRENCY}{net_savings:,.2f}\n"
            f"- Savings Rate: {savings_rate:.1f}%"
        )
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def list_recent_transactions(limit: int = 10) -> str:
    """Returns the most recent transactions (default last 10)."""
    try:
        db.init_db()
        transactions = db.get_all_transactions()
        if not transactions:
            return "No transactions found."
        lines = ["Recent Transactions:"]
        for t in transactions[:limit]:
            symbol = "+" if t.type == 'income' else "-"
            desc = f" ({t.description})" if t.description else ""
            lines.append(f"- [{t.date}] {t.type.upper()} | {t.category} | {symbol}{CURRENCY}{t.amount:,.2f}{desc}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def analyze_category_spending(month_str: str = None) -> str:
    """
    Groups expenses by category and shows percentage breakdown for a given month.
    Defaults to the current month.
    """
    try:
        db.init_db()
        transactions = db.get_all_transactions()
        if not month_str:
            month_str = datetime.now().strftime("%Y-%m")
        expenses = [t for t in transactions if t.type == 'expense' and t.date.startswith(month_str)]
        if not expenses:
            return f"No expenses found for {month_str}."
        total_expense = sum(t.amount for t in expenses)
        category_totals = {}
        for t in expenses:
            category_totals[t.category] = category_totals.get(t.category, 0.0) + t.amount
        sorted_cats = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
        lines = [f"Category Analysis for {month_str} (Total: {CURRENCY}{total_expense:,.2f}):"]
        for cat, amt in sorted_cats:
            pct = (amt / total_expense) * 100
            lines.append(f"- {cat}: {CURRENCY}{amt:,.2f} ({pct:.1f}%)")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {str(e)}"
