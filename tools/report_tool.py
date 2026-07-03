from langchain_core.tools import tool
import os
import pandas as pd
from fpdf import FPDF
import database.db as db
from datetime import datetime

REPORTS_DIR = "C:/Users/Admin/.gemini/antigravity-ide/scratch/finance-ai/reports"

class FinancialPDF(FPDF):
    def header(self):
        # Logo or brand header
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(9, 9, 11)  # Zinc-950
        self.cell(0, 10, 'FINANCEMIND AI', border=0, new_x='LMARGIN', new_y='NEXT', align='L')
        self.set_font('Helvetica', '', 10)
        self.set_text_color(113, 113, 122)  # Zinc-500
        self.cell(0, 5, 'Intelligent Personal Finance Assistant - Report', border=0, new_x='LMARGIN', new_y='NEXT', align='L')
        self.ln(5)
        # Horizontal line
        self.set_draw_color(228, 228, 231)  # Zinc-200
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(8)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(161, 161, 170)  # Zinc-400
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

@tool
def generate_csv_report(month_str: str = None) -> str:
    """
    Generates and exports a CSV report of transactions for the specified month (YYYY-MM).
    If month_str is None, it defaults to the current month.
    """
    try:
        db.init_db()
        transactions = db.get_all_transactions()
        
        if not month_str:
            month_str = datetime.now().strftime("%Y-%m")
            
        filtered = [t for t in transactions if t.date.startswith(month_str)]
        
        if not filtered:
            return f"No transactions found for {month_str} to export."
            
        # Convert list of Transaction dataclass to DataFrame
        data = [t.to_dict() for t in filtered]
        df = pd.DataFrame(data)
        
        # Format and order columns
        df = df[['id', 'date', 'type', 'category', 'amount', 'description']]
        
        os.makedirs(REPORTS_DIR, exist_ok=True)
        file_path = os.path.join(REPORTS_DIR, f"transactions_{month_str}.csv")
        df.to_csv(file_path, index=False)
        
        return f"CSV Report successfully generated at: {file_path}"
    except Exception as e:
        return f"Error generating CSV report: {str(e)}"

@tool
def generate_pdf_report(month_str: str = None) -> str:
    """
    Generates and exports a comprehensive PDF report for the specified month (YYYY-MM),
    containing financial summary, budget status, category expense analysis, and savings goal progression.
    If month_str is None, it defaults to the current month.
    """
    try:
        db.init_db()
        transactions = db.get_all_transactions()
        budgets = db.get_all_budgets()
        goals = db.get_all_savings_goals()
        
        if not month_str:
            month_str = datetime.now().strftime("%Y-%m")
            
        filtered = [t for t in transactions if t.date.startswith(month_str)]
        
        # Calculate summary values
        total_income = sum(t.amount for t in filtered if t.type == 'income')
        total_expense = sum(t.amount for t in filtered if t.type == 'expense')
        net_savings = total_income - total_expense
        savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0
        
        # Category breakdown
        category_expenses = {}
        for t in filtered:
            if t.type == 'expense':
                category_expenses[t.category] = category_expenses.get(t.category, 0.0) + t.amount
        
        # Create PDF object
        pdf = FinancialPDF()
        pdf.add_page()
        
        # Document title / header info
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 10, f"Monthly Financial Statement - {datetime.strptime(month_str, '%Y-%m').strftime('%B %Y')}", new_x='LMARGIN', new_y='NEXT')
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 6, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", new_x='LMARGIN', new_y='NEXT')
        pdf.ln(5)
        
        # Summary Section Header
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(9, 9, 11)
        pdf.cell(0, 8, "1. Executive Summary", new_x='LMARGIN', new_y='NEXT')
        pdf.ln(2)
        
        # Draw Summary Grid
        pdf.set_font('Helvetica', '', 10)
        # Table headers
        pdf.set_fill_color(244, 244, 245)  # Zinc-100
        pdf.set_text_color(39, 39, 42)    # Zinc-800
        pdf.cell(50, 8, "Metric", border=1, fill=True)
        pdf.cell(50, 8, "Amount ($)", border=1, fill=True)
        pdf.cell(90, 8, "Analysis / Notes", border=1, fill=True, new_x='LMARGIN', new_y='NEXT')
        
        # Table rows
        pdf.cell(50, 8, "Total Income", border=1)
        pdf.cell(50, 8, f"${total_income:,.2f}", border=1)
        pdf.cell(90, 8, "All inflows this month.", border=1, new_x='LMARGIN', new_y='NEXT')
        
        pdf.cell(50, 8, "Total Expenses", border=1)
        pdf.cell(50, 8, f"${total_expense:,.2f}", border=1)
        pdf.cell(90, 8, f"Incurred monthly outlays.", border=1, new_x='LMARGIN', new_y='NEXT')
        
        pdf.cell(50, 8, "Net Savings", border=1)
        if net_savings >= 0:
            pdf.set_text_color(22, 163, 74) # Green
            pdf.cell(50, 8, f"${net_savings:,.2f}", border=1)
            pdf.set_text_color(39, 39, 42)
            pdf.cell(90, 8, "Positive net savings.", border=1, new_x='LMARGIN', new_y='NEXT')
        else:
            pdf.set_text_color(220, 38, 38) # Red
            pdf.cell(50, 8, f"${net_savings:,.2f}", border=1)
            pdf.set_text_color(39, 39, 42)
            pdf.cell(90, 8, "WARNING: Net negative savings this month!", border=1, new_x='LMARGIN', new_y='NEXT')
            
        pdf.cell(50, 8, "Savings Rate", border=1)
        pdf.cell(50, 8, f"{savings_rate:.1f}%", border=1)
        pdf.cell(90, 8, "Target savings rate is > 20.0%.", border=1, new_x='LMARGIN', new_y='NEXT')
        pdf.ln(8)
        
        # Category spending breakdown
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, "2. Category Expense Breakdown", new_x='LMARGIN', new_y='NEXT')
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_fill_color(244, 244, 245)
        pdf.cell(60, 8, "Category", border=1, fill=True)
        pdf.cell(40, 8, "Spent ($)", border=1, fill=True)
        pdf.cell(40, 8, "Budget ($)", border=1, fill=True)
        pdf.cell(50, 8, "Usage (%)", border=1, fill=True, new_x='LMARGIN', new_y='NEXT')
        
        # Map budgets
        budget_map = {b.category: b.amount for b in budgets}
        
        if not category_expenses:
            pdf.cell(190, 8, "No expenses recorded this month.", border=1, align='C', new_x='LMARGIN', new_y='NEXT')
        else:
            for cat, amt in sorted(category_expenses.items(), key=lambda x: x[1], reverse=True):
                bg_limit = budget_map.get(cat, 0.0)
                usage_pct = (amt / bg_limit * 100) if bg_limit > 0 else 0
                
                pdf.cell(60, 8, cat, border=1)
                pdf.cell(40, 8, f"${amt:,.2f}", border=1)
                pdf.cell(40, 8, f"${bg_limit:,.2f}" if bg_limit > 0 else "N/A", border=1)
                
                # Check status colour
                if bg_limit > 0 and amt > bg_limit:
                    pdf.set_text_color(220, 38, 38)
                    status_text = f"{usage_pct:.1f}% [OVER]"
                elif bg_limit > 0 and usage_pct >= 80:
                    pdf.set_text_color(217, 119, 6)
                    status_text = f"{usage_pct:.1f}% [NEAR]"
                else:
                    pdf.set_text_color(39, 39, 42)
                    status_text = f"{usage_pct:.1f}%" if bg_limit > 0 else "N/A"
                    
                pdf.cell(50, 8, status_text, border=1, new_x='LMARGIN', new_y='NEXT')
                pdf.set_text_color(39, 39, 42)
        pdf.ln(8)
        
        # Savings Goals Section
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, "3. Savings Goals Progression", new_x='LMARGIN', new_y='NEXT')
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_fill_color(244, 244, 245)
        pdf.cell(60, 8, "Goal Name", border=1, fill=True)
        pdf.cell(40, 8, "Target ($)", border=1, fill=True)
        pdf.cell(40, 8, "Current ($)", border=1, fill=True)
        pdf.cell(50, 8, "Progress (%)", border=1, fill=True, new_x='LMARGIN', new_y='NEXT')
        
        if not goals:
            pdf.cell(190, 8, "No active savings goals defined.", border=1, align='C', new_x='LMARGIN', new_y='NEXT')
        else:
            for g in goals:
                pct = (g.current_amount / g.target_amount * 100) if g.target_amount > 0 else 0
                pdf.cell(60, 8, g.name, border=1)
                pdf.cell(40, 8, f"${g.target_amount:,.2f}", border=1)
                pdf.cell(40, 8, f"${g.current_amount:,.2f}", border=1)
                pdf.cell(50, 8, f"{pct:.1f}%", border=1, new_x='LMARGIN', new_y='NEXT')
        
        # Output PDF to file
        os.makedirs(REPORTS_DIR, exist_ok=True)
        file_path = os.path.join(REPORTS_DIR, f"report_{month_str}.pdf")
        pdf.output(file_path)
        
        return f"PDF Report successfully generated at: {file_path}"
    except Exception as e:
        return f"Error generating PDF report: {str(e)}"
