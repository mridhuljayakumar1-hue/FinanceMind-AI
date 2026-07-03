from langchain_core.tools import tool

@tool
def create_financial_plan(query: str) -> str:
    """
    Decomposes a complex financial request into a step-by-step plan of action.
    Use this tool when a user request has multiple steps, such as setting up a savings goal 
    AND calculating returns AND comparing with current budget.
    
    Parameters:
    - query: The user's complex financial query (str).
    """
    plan = (
        f"Decomposed Financial Plan for: '{query}'\n\n"
        f"Step 1: Check Current Database State\n"
        f"  - Query recent transactions and current budget settings to establish a baseline.\n\n"
        f"Step 2: Execute Mathematical Calculations\n"
        f"  - Run relevant loan, EMI, interest, or investment calculators based on query parameters.\n\n"
        f"Step 3: Analyze Budget & Saving Implications\n"
        f"  - Compare calculations against current category budgets and savings goals.\n\n"
        f"Step 4: Generate Actionable Recommendations\n"
        f"  - Provide savings suggestions, warnings, or adjustments to help achieve the user's objective."
    )
    return plan
