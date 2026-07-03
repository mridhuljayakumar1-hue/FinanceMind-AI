from langchain_core.tools import tool

CURRENCY = "₹"

@tool
def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> str:
    """
    Calculates the Equated Monthly Installment (EMI) for a loan.
    
    Parameters:
    - principal: The loan amount in Rupees (float).
    - annual_rate: The annual interest rate in percentage (float, e.g., 8.5 for 8.5%).
    - tenure_months: The loan tenure in months (int).
    """
    try:
        r = (annual_rate / 100) / 12
        p = principal
        n = tenure_months
        if r == 0:
            emi = p / n
        else:
            emi = p * r * ((1 + r) ** n) / (((1 + r) ** n) - 1)
        total_payment = emi * n
        total_interest = total_payment - p
        return (
            f"EMI Calculation Results:\n"
            f"- Monthly EMI: {CURRENCY}{emi:,.2f}\n"
            f"- Principal Amount: {CURRENCY}{p:,.2f}\n"
            f"- Total Interest Payable: {CURRENCY}{total_interest:,.2f}\n"
            f"- Total Amount (Principal + Interest): {CURRENCY}{total_payment:,.2f}"
        )
    except Exception as e:
        return f"Error calculating EMI: {str(e)}"

@tool
def calculate_simple_interest(principal: float, rate: float, time_years: float) -> str:
    """
    Calculates Simple Interest and the total amount.
    
    Parameters:
    - principal: The principal amount in Rupees (float).
    - rate: The annual interest rate in percentage (float).
    - time_years: The time period in years (float).
    """
    try:
        interest = (principal * rate * time_years) / 100
        total = principal + interest
        return (
            f"Simple Interest Results:\n"
            f"- Principal: {CURRENCY}{principal:,.2f}\n"
            f"- Rate: {rate}% per year\n"
            f"- Time: {time_years} years\n"
            f"- Interest Earned: {CURRENCY}{interest:,.2f}\n"
            f"- Total Value: {CURRENCY}{total:,.2f}"
        )
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def calculate_compound_interest(principal: float, annual_rate: float, time_years: float, compounding_frequency: int = 12) -> str:
    """
    Calculates Compound Interest and the final accumulated amount.
    
    Parameters:
    - principal: The principal amount in Rupees (float).
    - annual_rate: The annual interest rate in percentage (float).
    - time_years: The time period in years (float).
    - compounding_frequency: Number of times compounded per year (int, default 12).
    """
    try:
        p, r, t, n = principal, annual_rate / 100, time_years, compounding_frequency
        amount = p * ((1 + r/n) ** (n * t))
        interest = amount - p
        return (
            f"Compound Interest Results:\n"
            f"- Principal: {CURRENCY}{p:,.2f}\n"
            f"- Annual Rate: {annual_rate}%\n"
            f"- Time: {t} years | Compounded: {n}x/year\n"
            f"- Interest Earned: {CURRENCY}{interest:,.2f}\n"
            f"- Total Accumulated Value: {CURRENCY}{amount:,.2f}"
        )
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def calculate_investment_returns(monthly_investment: float, expected_annual_return: float, years: int) -> str:
    """
    Calculates SIP (Systematic Investment Plan) returns for monthly investments.
    
    Parameters:
    - monthly_investment: Monthly investment amount in Rupees (float).
    - expected_annual_return: Expected annual return rate in percentage (float).
    - years: Investment duration in years (int).
    """
    try:
        p = monthly_investment
        r = (expected_annual_return / 100) / 12
        n = years * 12
        if r == 0:
            future_value = p * n
        else:
            future_value = p * (((1 + r) ** n - 1) / r) * (1 + r)
        total_invested = p * n
        returns = future_value - total_invested
        return (
            f"SIP Investment Results:\n"
            f"- Monthly SIP: {CURRENCY}{p:,.2f}\n"
            f"- Duration: {years} years ({n} months)\n"
            f"- Expected Annual Return: {expected_annual_return}%\n"
            f"- Total Invested: {CURRENCY}{total_invested:,.2f}\n"
            f"- Estimated Returns: {CURRENCY}{returns:,.2f}\n"
            f"- Total Future Value: {CURRENCY}{future_value:,.2f}"
        )
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def calculate_savings_goal_requirements(target_amount: float, current_savings: float, time_months: int, annual_interest_rate: float = 0.0) -> str:
    """
    Calculates the required monthly savings to achieve a financial goal in Rupees.
    
    Parameters:
    - target_amount: Target savings goal amount in Rupees (float).
    - current_savings: Amount already saved in Rupees (float).
    - time_months: Time frame in months (int).
    - annual_interest_rate: Annual interest rate of savings account (float, optional).
    """
    try:
        needed = target_amount - current_savings
        if needed <= 0:
            return f"Goal achieved! Current savings ({CURRENCY}{current_savings:,.2f}) already exceed target ({CURRENCY}{target_amount:,.2f})."
        r = (annual_interest_rate / 100) / 12
        n = time_months
        if r == 0:
            monthly_required = needed / n
        else:
            fv_current = current_savings * ((1 + r) ** n)
            remaining_needed = target_amount - fv_current
            if remaining_needed <= 0:
                return (
                    f"Goal will be achieved by your current savings alone!\n"
                    f"- Future Value of Current Savings: {CURRENCY}{fv_current:,.2f}"
                )
            monthly_required = remaining_needed / (((1 + r) ** n - 1) / r)
        return (
            f"Savings Goal Plan:\n"
            f"- Target: {CURRENCY}{target_amount:,.2f}\n"
            f"- Current Savings: {CURRENCY}{current_savings:,.2f}\n"
            f"- Gap to Fill: {CURRENCY}{needed:,.2f}\n"
            f"- Time Frame: {n} months\n"
            f"- Interest Rate: {annual_interest_rate}% p.a.\n"
            f"- Required Monthly Savings: {CURRENCY}{monthly_required:,.2f}"
        )
    except Exception as e:
        return f"Error: {str(e)}"
