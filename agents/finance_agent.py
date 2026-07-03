import os
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

# Import all tools
from tools.calculator_tool import (
    calculate_emi,
    calculate_simple_interest,
    calculate_compound_interest,
    calculate_investment_returns,
    calculate_savings_goal_requirements
)
from tools.budget_tool import (
    get_budget_status,
    recommend_budget,
    suggest_savings_opportunities
)
from tools.expense_tool import (
    add_transaction_tool,
    get_financial_summary,
    list_recent_transactions,
    analyze_category_spending
)
from tools.report_tool import (
    generate_csv_report,
    generate_pdf_report
)
from agents.planner import create_financial_plan
from memory.memory_helper import load_chat_history_for_agent, save_chat_message

# Load environment variables
load_dotenv()

# List of tools available to the agent
FINANCE_TOOLS = [
    create_financial_plan,
    calculate_emi,
    calculate_simple_interest,
    calculate_compound_interest,
    calculate_investment_returns,
    calculate_savings_goal_requirements,
    get_budget_status,
    recommend_budget,
    suggest_savings_opportunities,
    add_transaction_tool,
    get_financial_summary,
    list_recent_transactions,
    analyze_category_spending,
    generate_csv_report,
    generate_pdf_report
]

# System instruction for the agent
SYSTEM_PROMPT = (
    "You are FinanceMind AI, a highly intelligent, analytical, and professional Personal Finance Assistant for Indian users.\n"
    "Your mission is to help users manage their personal finances: track income/expenses, analyze spending, "
    "provide budgeting advice, calculate financial metrics (like EMIs, loan details, compound interest), "
    "and generate financial reports. All amounts are in Indian Rupees (₹).\n\n"
    "CRITICAL RULES:\n"
    "1. REASONING & PLANNING: Before answering, plan which tool is best. For complex multi-step requests, "
    "use the `create_financial_plan` tool first to decompose the work.\n"
    "2. DATA STORAGE: If a user asks to record income or expense, use `add_transaction_tool`. "
    "For lists or spending analysis, use the matching tools.\n"
    "3. EXPORTS: If the user asks for a report, PDF, or CSV, use `generate_csv_report` or `generate_pdf_report` tools.\n"
    "4. DISCLAIMER: When discussing loans, investments, or savings returns, include at the bottom:\n"
    "   *Disclaimer: All calculations are for educational purposes only. "
    "Please consult a SEBI-registered financial advisor before making major financial decisions.*\n"
    "5. SCOPE: Focus exclusively on personal finance, budgeting, savings, and calculators. Politely refuse off-topic requests.\n"
    "6. RESPONSE STYLE: Professional, clear, formatted in Markdown. Always use ₹ (Rupee symbol) for currency. "
    "Format large amounts using Indian numbering: e.g. ₹1,00,000 (1 Lakh), ₹10,00,000 (10 Lakh)."
)


def _get_llm():
    """Initialises and returns the configured Gemini LLM."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable is not set. "
            "Please set it in your environment or a .env file."
        )
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=api_key,
        temperature=0.2,
    )


def run_finance_agent(user_query: str) -> str:
    """
    Executes the Finance Agent for a given user query using LangGraph
    create_react_agent, loading conversation memory and persisting the response.
    """
    try:
        # Load recent chat history as LangChain message objects
        chat_history = load_chat_history_for_agent(limit=10)

        # Save the incoming user message
        save_chat_message("user", user_query)

        # Build the LLM
        llm = _get_llm()

        # Build the LangGraph react agent.
        # `prompt` accepts a SystemMessage directly – this is the ONE place the
        # system instruction is injected; do NOT also add it to `messages` below
        # or the model will receive a duplicate system turn which causes empty output.
        agent = create_react_agent(
            model=llm,
            tools=FINANCE_TOOLS,
            prompt=SystemMessage(content=SYSTEM_PROMPT),
        )

        # Build the message list: only history + current user message (no SystemMessage here)
        messages = chat_history + [HumanMessage(content=user_query)]

        # Invoke the agent
        result = agent.invoke({"messages": messages})

        # Extract the last AI message as the response
        ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
        if ai_messages:
            response = ai_messages[-1].content
        else:
            response = "I encountered an issue generating a response. Please try again."

        # Persist assistant response
        save_chat_message("assistant", response)

        return response

    except ValueError as ve:
        error_msg = (
            f"**Configuration Error:** {str(ve)}\n\n"
            "Please provide a valid Gemini API Key in the sidebar."
        )
        save_chat_message("assistant", error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"**Agent Error:** {str(e)}"
        save_chat_message("assistant", error_msg)
        return error_msg
