from langchain_core.tools import tool
import database.db as db
from datetime import datetime

CURRENCY = "₹"

@tool
def get_budget_status() -> str:
    """Checks current month's budget status per category vs spending. Warns of overages."""
    try:
        db.init_db()
        budgets = db.get_all_budgets()
        transactions = db.get_all_transactions()
        current_month = datetime.now().strftime("%Y-%m")
        category_expenses = {}
        for tx in transactions:
            if tx.type == 'expense' and tx.date.startswith(current_month):
                category_expenses[tx.category] = category_expenses.get(tx.category, 0.0) + tx.amount
        if not budgets:
            return "No budgets set yet. Please set category budgets first."
        report_lines = [f"Budget Status for {datetime.now().strftime('%B %Y')}:\n"]
        warnings = []
        for b in budgets:
            spent = category_expenses.get(b.category, 0.0)
            pct = (spent / b.amount) * 100 if b.amount > 0 else 0
            report_lines.append(f"- {b.category}: {CURRENCY}{spent:,.2f} / {CURRENCY}{b.amount:,.2f} ({pct:.1f}%)")
            if pct >= 100:
                warnings.append(f"OVER BUDGET: '{b.category}' exceeded by {CURRENCY}{spent - b.amount:,.2f}!")
            elif pct >= 80:
                warnings.append(f"NEAR LIMIT: '{b.category}' at {pct:.1f}% ({CURRENCY}{b.amount - spent:,.2f} remaining).")
        if warnings:
            report_lines.append("\nAlerts:")
            report_lines.extend(warnings)
        else:
            report_lines.append("\nAll categories are within budget limits!")
        return "\n".join(report_lines)
    except Exception as e:
        return f"Error checking budget: {str(e)}"

@tool
def recommend_budget(monthly_income: float) -> str:
    """
    Recommends a monthly budget using the 50/30/20 rule.
    - 50% Needs, 30% Wants, 20% Savings.
    Parameters:
    - monthly_income: Net monthly income in Rupees (float).
    """
    try:
        needs = monthly_income * 0.50
        wants = monthly_income * 0.30
        savings = monthly_income * 0.20
        needs_breakdown = {"Rent / Housing": needs * 0.60, "Groceries": needs * 0.20, "Utilities": needs * 0.12, "Transport": needs * 0.08}
        wants_breakdown = {"Dining Out": wants * 0.40, "Entertainment": wants * 0.30, "Shopping / Other": wants * 0.30}
        lines = [
            f"Recommended Budget for income {CURRENCY}{monthly_income:,.2f}/month (50/30/20 Rule):",
            f"\n1. Needs (50%) — {CURRENCY}{needs:,.2f}:"
        ]
        for cat, amt in needs_breakdown.items():
            lines.append(f"   - {cat}: {CURRENCY}{amt:,.2f}")
        lines.append(f"\n2. Wants (30%) — {CURRENCY}{wants:,.2f}:")
        for cat, amt in wants_breakdown.items():
            lines.append(f"   - {cat}: {CURRENCY}{amt:,.2f}")
        lines.append(f"\n3. Savings & Debt (20%) — {CURRENCY}{savings:,.2f}:")
        lines.append("   Put towards Emergency Fund, Investments, or Loan repayment.")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def suggest_savings_opportunities() -> str:
    """Analyzes current month's transactions and suggests personalized cost-saving opportunities."""
    try:
        db.init_db()
        transactions = db.get_all_transactions()
        current_month = datetime.now().strftime("%Y-%m")
        expenses = [t for t in transactions if t.type == 'expense' and t.date.startswith(current_month)]
        if not expenses:
            return "No expenses this month yet. Add transactions to get savings recommendations."
        total_exp = sum(t.amount for t in expenses)
        category_totals = {}
        for t in expenses:
            category_totals[t.category] = category_totals.get(t.category, 0.0) + t.amount
        sorted_cats = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
        lines = [f"Savings Opportunities (Total Expenses: {CURRENCY}{total_exp:,.2f}):\n", "Top Spending Categories:"]
        for cat, amt in sorted_cats[:3]:
            pct = (amt / total_exp) * 100
            lines.append(f"- {cat}: {CURRENCY}{amt:,.2f} ({pct:.1f}%)")
        lines.append("\nRecommendations:")
        has_rec = False
        for cat, amt in sorted_cats[:3]:
            if cat == 'Rent' and amt > total_exp * 0.4:
                lines.append("- Housing cost is high (>40%). Explore flat-sharing, negotiating rent, or reducing utility usage.")
                has_rec = True
            elif cat == 'Dining Out' and amt > 1000:
                lines.append(f"- Dining Out is {CURRENCY}{amt:,.2f}. Cooking at home can save 50-60% of this (~{CURRENCY}{amt*0.5:,.2f}/month).")
                has_rec = True
            elif cat == 'Entertainment' and amt > 1000:
                lines.append(f"- Entertainment is {CURRENCY}{amt:,.2f}. Audit unused OTT subscriptions and apps.")
                has_rec = True
            elif cat == 'Groceries' and amt > 5000:
                lines.append(f"- Groceries is {CURRENCY}{amt:,.2f}. Meal planning and buying staples in bulk can reduce this by 20-30%.")
                has_rec = True
        if not has_rec:
            lines.append("- Review 'Entertainment', 'Dining Out', and 'Other' for subscription creep.")
            lines.append("- Apply the 24-hour rule before any non-essential purchase.")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {str(e)}"
