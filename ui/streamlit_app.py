import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys
from datetime import datetime

# Add parent directory to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database.db as db
from database.models import Transaction, Budget, SavingsGoal, ChatMessage
from agents.finance_agent import run_finance_agent
from memory.memory_helper import clear_chat_history

# Initialize Database
db.init_db()

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinanceMind AI",
    page_icon="₹",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Session State ───────────────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
if "chat_messages" not in st.session_state:
    # Load from DB on first run
    st.session_state.chat_messages = []

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

IS_DARK = st.session_state.theme == "dark"

# ─── Color Tokens ────────────────────────────────────────────────────────────
bg          = "#09090b" if IS_DARK else "#f8fafc"
bg_subtle   = "#0c0c0f" if IS_DARK else "#f1f5f9"
card        = "#111113" if IS_DARK else "#ffffff"
card_hover  = "#1a1a1f" if IS_DARK else "#f8fafc"
border      = "#1e1e28" if IS_DARK else "#e2e8f0"
border_sub  = "#141418" if IS_DARK else "#f1f5f9"
text        = "#f8fafc" if IS_DARK else "#0f172a"
text_muted  = "#94a3b8"
text_dim    = "#475569" if IS_DARK else "#94a3b8"
green       = "#4ade80" if IS_DARK else "#16a34a"
green_bg    = "rgba(74,222,128,0.10)" if IS_DARK else "rgba(22,163,74,0.08)"
red         = "#f87171" if IS_DARK else "#dc2626"
red_bg      = "rgba(248,113,113,0.10)" if IS_DARK else "rgba(220,38,38,0.08)"
amber       = "#fbbf24" if IS_DARK else "#d97706"
amber_bg    = "rgba(251,191,36,0.10)" if IS_DARK else "rgba(217,119,6,0.08)"
blue        = "#60a5fa" if IS_DARK else "#2563eb"
blue_bg     = "rgba(96,165,250,0.12)" if IS_DARK else "rgba(37,99,235,0.08)"
shadow      = "none" if IS_DARK else "0 1px 4px rgba(0,0,0,0.06)"
accent      = "#6366f1"

css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono&display=swap');

/* ── Reset Streamlit chrome ── */
header[data-testid="stHeader"], footer, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"],
.stDeployButton, div[data-testid="stSidebarCollapsedControl"] {{
    display: none !important;
}}
[data-testid="stMainBlockContainer"] > div > div > div > div > section > div {{
    padding-top: 0 !important;
}}

/* ── Global ── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"],
.main, .block-container, section[data-testid="stMain"] {{
    background-color: {bg} !important;
    color: {text} !important;
    font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}}
.block-container {{
    padding: 1.5rem 2rem 3rem !important;
    max-width: 1380px !important;
}}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
    background-color: {bg_subtle} !important;
    border-right: 1px solid {border} !important;
}}
[data-testid="stSidebar"] .block-container {{
    padding: 1.5rem 1rem !important;
}}

/* ── KPI Cards ── */
.kpi-card {{
    background: {card};
    border: 1px solid {border};
    border-radius: 14px;
    padding: 1.3rem 1.5rem;
    box-shadow: {shadow};
    transition: transform 0.18s ease, box-shadow 0.18s ease;
    position: relative;
    overflow: hidden;
}}
.kpi-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, {accent}, {blue});
    opacity: 0.6;
}}
.kpi-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.18);
}}
.kpi-icon {{
    font-size: 1.3rem;
    margin-bottom: 0.5rem;
    display: block;
}}
.kpi-label {{
    font-size: 0.73rem;
    color: {text_muted};
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.3rem;
}}
.kpi-value {{
    font-size: 1.9rem;
    font-weight: 800;
    color: {text};
    letter-spacing: -0.04em;
    line-height: 1.1;
    font-family: 'JetBrains Mono', monospace;
}}
.kpi-delta {{
    display: inline-flex;
    align-items: center;
    gap: 3px;
    font-size: 0.74rem;
    font-weight: 600;
    margin-top: 0.5rem;
    padding: 3px 8px;
    border-radius: 20px;
}}
.delta-up   {{ color: {green}; background: {green_bg}; }}
.delta-down {{ color: {red};   background: {red_bg};   }}
.delta-warn {{ color: {amber}; background: {amber_bg}; }}
.delta-blue {{ color: {blue};  background: {blue_bg};  }}

/* ── Chart Cards ── */
.chart-card {{
    background: {card};
    border: 1px solid {border};
    border-radius: 14px;
    padding: 1.4rem 1.4rem 0.8rem;
    box-shadow: {shadow};
    margin-bottom: 1.2rem;
}}
.chart-card-title {{
    font-size: 0.9rem;
    font-weight: 700;
    color: {text};
    margin-bottom: 0.15rem;
}}
.chart-card-sub {{
    font-size: 0.73rem;
    color: {text_muted};
    margin-bottom: 0.8rem;
}}

/* ── Data Tables ── */
.fin-table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 0.83rem;
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid {border};
}}
.fin-table th {{
    text-align: left;
    padding: 0.65rem 1rem;
    background: {bg_subtle};
    color: {text_muted};
    font-weight: 600;
    font-size: 0.71rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-bottom: 1px solid {border};
}}
.fin-table td {{
    padding: 0.7rem 1rem;
    color: {text};
    border-bottom: 1px solid {border_sub};
    vertical-align: middle;
}}
.fin-table tr:last-child td {{ border-bottom: none; }}
.fin-table tr:hover td {{ background: {card_hover}; }}

/* ── Badges ── */
.badge {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.71rem;
    font-weight: 600;
    text-align: center;
    white-space: nowrap;
}}
.badge-income  {{ color: {green}; background: {green_bg}; }}
.badge-expense {{ color: {red};   background: {red_bg};   }}
.badge-warn    {{ color: {amber}; background: {amber_bg}; }}
.badge-blue    {{ color: {blue};  background: {blue_bg};  }}

/* ── Page Header ── */
.page-header {{
    border-bottom: 1px solid {border};
    padding-bottom: 1rem;
    margin-bottom: 1.5rem;
}}
.page-title {{
    font-size: 1.9rem;
    font-weight: 800;
    letter-spacing: -0.05em;
    background: linear-gradient(135deg, {blue} 0%, {accent} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
}}
.page-subtitle {{
    font-size: 0.8rem;
    color: {text_muted};
    margin-top: 0.2rem;
}}

/* ── Tabs ── */
button[data-baseweb="tab"] {{
    background: transparent !important;
    color: {text_muted} !important;
    font-size: 0.84rem !important;
    font-weight: 500 !important;
    padding: 0.55rem 1.1rem !important;
    border: 1px solid transparent !important;
    border-radius: 8px !important;
    transition: all 0.15s !important;
}}
button[data-baseweb="tab"]:hover {{
    color: {text} !important;
    background: {card_hover} !important;
}}
button[data-baseweb="tab"][aria-selected="true"] {{
    color: {text} !important;
    background: {card} !important;
    border-color: {border} !important;
    font-weight: 600 !important;
}}
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {{ display: none !important; }}
[data-baseweb="tab-list"] {{
    gap: 4px !important;
    background: {bg_subtle} !important;
    border: 1px solid {border} !important;
    border-radius: 12px !important;
    padding: 4px !important;
    margin-bottom: 1.5rem !important;
}}

/* ── Streamlit widgets ── */
[data-testid="stHorizontalBlock"] {{ gap: 1rem !important; }}
div.stButton > button {{
    background: {card} !important;
    color: {text} !important;
    border: 1px solid {border} !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 0.15s !important;
    font-family: 'DM Sans', sans-serif !important;
}}
div.stButton > button:hover {{
    background: {card_hover} !important;
    border-color: {text_muted} !important;
}}
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div input,
[data-testid="stNumberInputContainer"] input,
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {{
    background: {bg_subtle} !important;
    border-color: {border} !important;
    color: {text} !important;
    border-radius: 8px !important;
}}
label[data-testid="stWidgetLabel"] p {{
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    color: {text_muted} !important;
}}
div.stAlert {{
    border-radius: 10px !important;
}}

/* ── Section Divider ── */
.section-title {{
    font-size: 1.05rem;
    font-weight: 700;
    color: {text};
    margin: 0.5rem 0 1rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}
.section-title::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: {border};
}}

/* ── Calculator Result Box ── */
.calc-result {{
    background: {bg_subtle};
    border: 1px solid {border};
    border-left: 3px solid {accent};
    border-radius: 8px;
    padding: 1rem 1.2rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.83rem;
    line-height: 1.7;
    color: {text};
    white-space: pre-line;
}}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# ─── Helpers ─────────────────────────────────────────────────────────────────
CURRENCY = "₹"

def fmt(amount: float) -> str:
    """Format amount in Indian Rupee style: ₹1,50,000.00"""
    return f"{CURRENCY}{amount:,.0f}"

def kpi_card(icon, label, value, delta=None, delta_type="up"):
    cls = f"delta-{delta_type}"
    arrow = "↑" if delta_type == "up" else ("↓" if delta_type == "down" else ("!" if delta_type == "warn" else "•"))
    delta_html = f'<div class="kpi-delta {cls}">{arrow} {delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="kpi-card">
        <span class="kpi-icon">{icon}</span>
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color=text_muted, size=11),
    margin=dict(l=10, r=10, t=20, b=10),
    xaxis=dict(
        gridcolor="rgba(148,163,184,0.08)",
        zerolinecolor="rgba(148,163,184,0.08)",
        tickfont=dict(size=10),
    ),
    yaxis=dict(
        gridcolor="rgba(148,163,184,0.08)",
        zerolinecolor="rgba(148,163,184,0.08)",
        tickfont=dict(size=10),
    ),
    legend=dict(font=dict(size=11)),
)

COLORS = ["#6366f1", "#60a5fa", "#4ade80", "#fbbf24", "#f87171", "#a78bfa", "#34d399", "#fb923c"]

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='display:flex;align-items:center;gap:10px;margin-bottom:1.5rem;'>
        <span style='font-size:1.8rem;'>₹</span>
        <span style='font-weight:800;font-size:1.2rem;letter-spacing:-0.03em;
            background:linear-gradient(135deg,{blue},{accent});
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;'>
            FinanceMind AI
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"<p style='font-size:0.75rem;color:{text_muted};margin-bottom:1rem;'>Intelligent Personal Finance Assistant</p>", unsafe_allow_html=True)

    st.markdown("**🔑 Gemini API Key**")
    api_input = st.text_input(
        "API Key",
        value=st.session_state.gemini_api_key,
        type="password",
        placeholder="Paste your Gemini API Key here",
        label_visibility="collapsed"
    )
    if api_input != st.session_state.gemini_api_key:
        st.session_state.gemini_api_key = api_input
        os.environ["GEMINI_API_KEY"] = api_input
        st.success("API Key saved!")

    st.markdown("---")

    try:
        txs    = db.get_all_transactions()
        budgets = db.get_all_budgets()
        goals  = db.get_all_savings_goals()
        st.markdown(f"""
        <div style='background:{card};border:1px solid {border};border-radius:10px;padding:0.9rem;font-size:0.82rem;'>
            <div style='color:{text_muted};font-size:0.72rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.6rem;'>Database</div>
            <div style='display:flex;flex-direction:column;gap:0.4rem;'>
                <div>📋 <b>{len(txs)}</b> Transactions</div>
                <div>🏷️ <b>{len(budgets)}</b> Budget Categories</div>
                <div>🎯 <b>{len(goals)}</b> Savings Goals</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    except Exception:
        pass

    st.markdown("---")
    theme_label = "☀️ Switch to Light" if IS_DARK else "🌙 Switch to Dark"
    st.button(theme_label, on_click=toggle_theme, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        clear_chat_history()
        st.session_state.chat_messages = []
        st.success("Chat history cleared!")
        st.rerun()

    if st.button("🔄 Reset Demo Data", use_container_width=True):
        if os.path.exists(db.DEFAULT_DB_PATH):
            os.remove(db.DEFAULT_DB_PATH)
        db.init_db()
        st.session_state.chat_messages = []
        st.success("Database reset!")
        st.rerun()

# ─── Page Header ─────────────────────────────────────────────────────────────
h1, h2 = st.columns([9, 1.5])
with h1:
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">FinanceMind AI</h1>
        <p class="page-subtitle">Intelligent Personal Finance · Powered by LangChain Agents & Gemini</p>
    </div>
    """, unsafe_allow_html=True)

# ─── Navigation Tabs ─────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Dashboard",
    "💬 AI Assistant",
    "➕ Add Transaction",
    "🏷️ Budgets & Goals",
    "📁 Reports",
    "🧮 Calculators",
])

current_month = datetime.now().strftime("%Y-%m")

# ════════════════════════════════════════════════════════════════
# TAB 1 — DASHBOARD
# ════════════════════════════════════════════════════════════════
with tab1:
    tx_list = db.get_all_transactions()
    this_month = [t for t in tx_list if t.date.startswith(current_month)]

    total_income  = sum(t.amount for t in this_month if t.type == "income")
    total_expense = sum(t.amount for t in this_month if t.type == "expense")
    net_savings   = total_income - total_expense
    savings_rate  = (net_savings / total_income * 100) if total_income > 0 else 0.0

    # ── KPI Row ──
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_card("💰", "Total Income", fmt(total_income), f"{datetime.now().strftime('%b %Y')}", "blue")
    with k2:
        kpi_card("💸", "Total Expenses", fmt(total_expense), f"{len([t for t in this_month if t.type=='expense'])} transactions", "down")
    with k3:
        kpi_card("🏦", "Net Savings", fmt(net_savings), "Available balance", "up" if net_savings >= 0 else "down")
    with k4:
        kpi_card("📈", "Savings Rate", f"{savings_rate:.1f}%", "Target: >20%", "up" if savings_rate >= 20 else "warn")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts Row ──
    c1, c2 = st.columns(2)

    with c1:
        st.markdown(f"""
        <div class="chart-card">
            <div class="chart-card-title">Expense Distribution</div>
            <div class="chart-card-sub">Category breakdown for {datetime.now().strftime('%B %Y')}</div>
        """, unsafe_allow_html=True)

        cat_spend = {}
        for t in this_month:
            if t.type == "expense":
                cat_spend[t.category] = cat_spend.get(t.category, 0.0) + t.amount

        if cat_spend:
            df_pie = pd.DataFrame(list(cat_spend.items()), columns=["Category", "Amount"])
            fig = px.pie(df_pie, values="Amount", names="Category",
                         color_discrete_sequence=COLORS, hole=0.45)
            fig.update_layout(**PLOT_LAYOUT)
            fig.update_traces(textposition="inside", textinfo="percent+label",
                              textfont_size=11)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No expenses this month yet.")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="chart-card">
            <div class="chart-card-title">Income vs Expenses</div>
            <div class="chart-card-sub">Monthly comparison (last 6 months)</div>
        """, unsafe_allow_html=True)

        history = {}
        for t in tx_list:
            m = t.date[:7]
            if m not in history:
                history[m] = {"income": 0.0, "expense": 0.0}
            history[m][t.type] += t.amount

        if history:
            sorted_m = sorted(history.keys())[-6:]
            rows = []
            for m in sorted_m:
                label = datetime.strptime(m, "%Y-%m").strftime("%b '%y")
                rows.append({"Month": label, "Type": "Income",  "Amount": history[m]["income"]})
                rows.append({"Month": label, "Type": "Expense", "Amount": history[m]["expense"]})
            df_bar = pd.DataFrame(rows)
            fig2 = px.bar(df_bar, x="Month", y="Amount", color="Type", barmode="group",
                          color_discrete_map={"Income": "#4ade80", "Expense": "#f87171"})
            fig2.update_layout(**PLOT_LAYOUT)
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No history available.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Savings trend ──
    st.markdown('<div class="section-title">💹 Savings Trend</div>', unsafe_allow_html=True)
    if history:
        sorted_m2 = sorted(history.keys())
        trend_data = []
        for m in sorted_m2:
            savings_v = history[m]["income"] - history[m]["expense"]
            trend_data.append({"Month": datetime.strptime(m, "%Y-%m").strftime("%b '%y"), "Savings": savings_v})
        df_trend = pd.DataFrame(trend_data)
        fig3 = px.area(df_trend, x="Month", y="Savings",
                       color_discrete_sequence=["#6366f1"],
                       line_shape="spline")
        fig3.update_traces(fill="tozeroy", fillcolor="rgba(99,102,241,0.12)")
        fig3.update_layout(**PLOT_LAYOUT, height=220)
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    # ── Recent Transactions ──
    st.markdown('<div class="section-title">🕐 Recent Transactions</div>', unsafe_allow_html=True)

    if tx_list:
        rows_html = ""
        for t in tx_list[:8]:
            badge_cls = "badge-income" if t.type == "income" else "badge-expense"
            sign = "+" if t.type == "income" else "−"
            color = green if t.type == "income" else red
            rows_html += f"""
            <tr>
                <td>{datetime.strptime(t.date, "%Y-%m-%d").strftime("%d %b %Y")}</td>
                <td><span class="badge {badge_cls}">{t.type.upper()}</span></td>
                <td>{t.category}</td>
                <td style="font-family:'JetBrains Mono',monospace;font-weight:700;color:{color};">
                    {sign}{CURRENCY}{t.amount:,.0f}
                </td>
                <td style="color:{text_muted};">{t.description or "—"}</td>
            </tr>"""

        st.markdown(f"""
        <table class="fin-table">
            <thead><tr>
                <th>Date</th><th>Type</th><th>Category</th><th>Amount</th><th>Notes</th>
            </tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
        """, unsafe_allow_html=True)
    else:
        st.info("No transactions yet. Add one in the 'Add Transaction' tab.")

# ════════════════════════════════════════════════════════════════
# TAB 2 — AI ASSISTANT CHAT
# ════════════════════════════════════════════════════════════════
with tab2:
    st.markdown(f"""
    <div style='display:flex;align-items:center;gap:0.6rem;margin-bottom:1rem;'>
        <span style='font-size:1.5rem;'>🤖</span>
        <div>
            <div style='font-weight:700;font-size:1rem;'>FinanceMind AI Agent</div>
            <div style='font-size:0.75rem;color:{text_muted};'>Ask anything about your finances — it reasons, plans, and uses tools automatically</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Load messages from DB if session is fresh
    if not st.session_state.chat_messages:
        db_msgs = db.get_chat_history(limit=40)
        st.session_state.chat_messages = [{"role": m.role, "content": m.content} for m in db_msgs]

    # Render existing messages using st.chat_message (clean, built-in bubbles)
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])

    # Chat input
    user_input = st.chat_input("Ask FinanceMind AI... (e.g. 'How much did I spend this month?')")

    if user_input:
        # Check API key
        active_key = st.session_state.gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        if not active_key:
            st.error("⚠️ Please enter your **Gemini API Key** in the sidebar to activate the AI agent.")
        else:
            os.environ["GEMINI_API_KEY"] = active_key

            # Show user message immediately
            st.session_state.chat_messages.append({"role": "user", "content": user_input})
            with st.chat_message("user", avatar="🧑"):
                st.markdown(user_input)

            # Get agent response
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Thinking and selecting tools…"):
                    response = run_finance_agent(user_input)
                st.markdown(response)

            st.session_state.chat_messages.append({"role": "assistant", "content": response})

# ════════════════════════════════════════════════════════════════
# TAB 3 — ADD TRANSACTION
# ════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-title">➕ Record a New Transaction</div>', unsafe_allow_html=True)

    with st.form("add_tx_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            tx_type = st.selectbox("Transaction Type", ["expense", "income"])
        with col2:
            income_cats  = ["Salary", "Freelance", "Business", "Investment Returns", "Rental Income", "Gift", "Other"]
            expense_cats = ["Groceries", "Rent", "Utilities", "Entertainment", "Dining Out",
                            "Transport", "Shopping", "Medical", "Education", "EMI / Loan", "Other"]
            tx_cat = st.selectbox("Category", income_cats if tx_type == "income" else expense_cats)
        with col3:
            tx_amount = st.number_input(f"Amount ({CURRENCY})", min_value=0.01, step=100.0, format="%.2f")

        col4, col5 = st.columns([1, 2])
        with col4:
            tx_date = st.date_input("Date", value=datetime.today())
        with col5:
            tx_desc = st.text_input("Notes / Description", placeholder="e.g. Monthly rent payment to landlord")

        if st.form_submit_button("✅ Record Transaction", use_container_width=True):
            if tx_amount <= 0:
                st.error("Amount must be greater than zero.")
            else:
                new_tx = Transaction(
                    type=tx_type,
                    category=tx_cat,
                    amount=tx_amount,
                    date=tx_date.strftime("%Y-%m-%d"),
                    description=tx_desc
                )
                tx_id = db.add_transaction(new_tx)
                st.success(f"✅ Recorded {tx_type}: **{tx_cat}** — {CURRENCY}{tx_amount:,.2f} (ID #{tx_id})")

    # Recent quick-view
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">🕐 All Transactions</div>', unsafe_allow_html=True)
    all_tx = db.get_all_transactions()
    if all_tx:
        rows = ""
        for t in all_tx[:20]:
            badge_cls = "badge-income" if t.type == "income" else "badge-expense"
            sign = "+" if t.type == "income" else "−"
            color = green if t.type == "income" else red
            rows += f"""<tr>
                <td>{t.id}</td>
                <td>{datetime.strptime(t.date, "%Y-%m-%d").strftime("%d %b %Y")}</td>
                <td><span class="badge {badge_cls}">{t.type.upper()}</span></td>
                <td>{t.category}</td>
                <td style="font-family:'JetBrains Mono',monospace;font-weight:700;color:{color};">{sign}{CURRENCY}{t.amount:,.0f}</td>
                <td style="color:{text_muted};">{t.description or "—"}</td>
            </tr>"""
        st.markdown(f"""
        <table class="fin-table">
            <thead><tr><th>#</th><th>Date</th><th>Type</th><th>Category</th><th>Amount</th><th>Notes</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# TAB 4 — BUDGETS & GOALS
# ════════════════════════════════════════════════════════════════
with tab4:
    col_b1, col_b2 = st.columns(2)

    with col_b1:
        st.markdown('<div class="section-title">🏷️ Category Budgets</div>', unsafe_allow_html=True)

        budgets_list = db.get_all_budgets()
        tx_list_b    = db.get_all_transactions()
        cat_spent    = {}
        for t in tx_list_b:
            if t.type == "expense" and t.date.startswith(current_month):
                cat_spent[t.category] = cat_spent.get(t.category, 0.0) + t.amount

        if budgets_list:
            rows = ""
            for b in budgets_list:
                spent = cat_spent.get(b.category, 0.0)
                pct   = (spent / b.amount * 100) if b.amount > 0 else 0
                if pct >= 100:
                    badge = f'<span class="badge badge-expense">OVER</span>'
                    style = f"color:{red};font-weight:700;"
                elif pct >= 80:
                    badge = f'<span class="badge badge-warn">NEAR</span>'
                    style = f"color:{amber};font-weight:600;"
                else:
                    badge = f'<span class="badge badge-blue">OK</span>'
                    style = f"color:{text};"
                rows += f"""<tr>
                    <td>{b.category}</td>
                    <td style="font-family:'JetBrains Mono',monospace;">{CURRENCY}{b.amount:,.0f}</td>
                    <td style="font-family:'JetBrains Mono',monospace;">{CURRENCY}{spent:,.0f}</td>
                    <td style="{style}">{pct:.1f}% {badge}</td>
                </tr>"""
            st.markdown(f"""
            <table class="fin-table">
                <thead><tr><th>Category</th><th>Budget</th><th>Spent</th><th>Usage</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("budget_form"):
            c1, c2 = st.columns(2)
            with c1:
                b_cat = st.selectbox("Category", ["Groceries", "Rent", "Utilities", "Entertainment",
                                                   "Dining Out", "Transport", "Shopping", "Medical",
                                                   "Education", "EMI / Loan", "Other"])
            with c2:
                b_lim = st.number_input(f"Monthly Limit ({CURRENCY})", min_value=0.0, step=500.0, format="%.0f")
            if st.form_submit_button("💾 Save Budget", use_container_width=True):
                db.set_budget(b_cat, b_lim)
                st.success(f"Budget for **{b_cat}** set to {CURRENCY}{b_lim:,.0f}/month")
                st.rerun()

    with col_b2:
        st.markdown('<div class="section-title">🎯 Savings Goals</div>', unsafe_allow_html=True)
        goals_list = db.get_all_savings_goals()

        if goals_list:
            for g in goals_list:
                pct = (g.current_amount / g.target_amount) if g.target_amount > 0 else 0
                remaining = g.target_amount - g.current_amount
                st.markdown(f"""
                <div class="chart-card" style="margin-bottom:0.8rem;padding:1rem 1.2rem;">
                    <div style="display:flex;justify-content:space-between;align-items:baseline;">
                        <div style="font-weight:700;font-size:0.92rem;">🎯 {g.name}</div>
                        <div style="font-family:'JetBrains Mono',monospace;font-size:0.8rem;color:{text_muted};">
                            {pct*100:.1f}%
                        </div>
                    </div>
                    <div style="font-family:'JetBrains Mono',monospace;font-size:0.8rem;color:{text_muted};margin:0.3rem 0;">
                        {CURRENCY}{g.current_amount:,.0f} of {CURRENCY}{g.target_amount:,.0f} · 
                        {CURRENCY}{remaining:,.0f} remaining · Target: {g.target_date}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.progress(min(max(pct, 0.0), 1.0))

                with st.expander(f"Update / Delete — {g.name}"):
                    nc = st.number_input("Current saved amount (₹)", min_value=0.0, value=g.current_amount, key=f"ga_{g.id}")
                    cu, cd = st.columns(2)
                    with cu:
                        if st.button("Update", key=f"gu_{g.id}", use_container_width=True):
                            db.update_savings_goal_progress(g.id, nc)
                            st.success("Updated!")
                            st.rerun()
                    with cd:
                        if st.button("Delete", key=f"gd_{g.id}", use_container_width=True):
                            db.delete_savings_goal(g.id)
                            st.rerun()
        else:
            st.info("No savings goals. Create one below.")

        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("goal_form"):
            g_name   = st.text_input("Goal Name", placeholder="e.g. Emergency Fund, New Car, Home Loan")
            c1, c2   = st.columns(2)
            with c1:
                g_target = st.number_input(f"Target Amount ({CURRENCY})", min_value=1.0, step=1000.0, format="%.0f")
                g_curr   = st.number_input(f"Already Saved ({CURRENCY})", min_value=0.0, step=500.0, format="%.0f")
            with c2:
                g_date = st.date_input("Target Date", value=datetime.today())
            if st.form_submit_button("🎯 Create Goal", use_container_width=True) and g_name:
                db.add_savings_goal(SavingsGoal(
                    name=g_name,
                    target_amount=g_target,
                    current_amount=g_curr,
                    target_date=g_date.strftime("%Y-%m-%d")
                ))
                st.success(f"Goal '{g_name}' created! Target: {CURRENCY}{g_target:,.0f}")
                st.rerun()

# ════════════════════════════════════════════════════════════════
# TAB 5 — REPORTS & EXPORTS
# ════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-title">📁 Generate & Download Reports</div>', unsafe_allow_html=True)

    col_r1, col_r2 = st.columns(2)

    with col_r1:
        st.markdown(f"""
        <div class="chart-card">
            <div class="chart-card-title">📄 PDF Monthly Statement</div>
            <div class="chart-card-sub">Full summary with budget analysis and savings goals</div>
        </div>""", unsafe_allow_html=True)

        pdf_month = st.selectbox("Month (PDF)", [current_month], key="pdf_sel")
        if st.button("Build PDF Report", use_container_width=True, key="pdf_btn"):
            from tools.report_tool import generate_pdf_report
            res = generate_pdf_report.invoke(pdf_month)
            if "generated at:" in res:
                path = res.split("generated at:")[-1].strip()
                if os.path.exists(path):
                    with open(path, "rb") as f:
                        st.download_button("⬇️ Download PDF", f.read(),
                                           file_name=f"FinanceMind_{pdf_month}.pdf",
                                           mime="application/pdf", use_container_width=True)
                st.success(res)
            else:
                st.error(res)

    with col_r2:
        st.markdown(f"""
        <div class="chart-card">
            <div class="chart-card-title">📊 CSV Transaction Export</div>
            <div class="chart-card-sub">Raw data for Excel / Google Sheets import</div>
        </div>""", unsafe_allow_html=True)

        csv_month = st.selectbox("Month (CSV)", [current_month], key="csv_sel")
        if st.button("Build CSV Export", use_container_width=True, key="csv_btn"):
            from tools.report_tool import generate_csv_report
            res = generate_csv_report.invoke(csv_month)
            if "generated at:" in res:
                path = res.split("generated at:")[-1].strip()
                if os.path.exists(path):
                    with open(path, "rb") as f:
                        st.download_button("⬇️ Download CSV", f.read(),
                                           file_name=f"transactions_{csv_month}.csv",
                                           mime="text/csv", use_container_width=True)
                st.success(res)
            else:
                st.error(res)

# ════════════════════════════════════════════════════════════════
# TAB 6 — CALCULATORS
# ════════════════════════════════════════════════════════════════
with tab6:
    st.markdown('<div class="section-title">🧮 Financial Calculators</div>', unsafe_allow_html=True)

    sub1, sub2, sub3, sub4 = st.tabs(["🏠 EMI / Loan", "📈 SIP Returns", "💰 Compound Interest", "🎯 Savings Goal"])

    with sub1:
        st.markdown(f"<p style='color:{text_muted};font-size:0.83rem;'>Calculate your monthly EMI and total interest payable on any loan.</p>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: emi_p = st.number_input(f"Loan Amount ({CURRENCY})", min_value=1000.0, value=500000.0, step=10000.0, key="ep")
        with c2: emi_r = st.number_input("Interest Rate (% p.a.)", min_value=0.1, value=8.5, step=0.1, key="er")
        with c3: emi_t = st.number_input("Tenure (Months)", min_value=6, value=60, step=6, key="et")
        if st.button("Calculate EMI →", use_container_width=True, key="emi_btn"):
            from tools.calculator_tool import calculate_emi
            res = calculate_emi.invoke({"principal": emi_p, "annual_rate": emi_r, "tenure_months": emi_t})
            st.markdown(f'<div class="calc-result">{res}</div>', unsafe_allow_html=True)
            st.caption("*Educational only. Consult a SEBI-registered advisor before taking loans.*")

    with sub2:
        st.markdown(f"<p style='color:{text_muted};font-size:0.83rem;'>Plan your SIP investments and estimate future corpus.</p>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: sip_m = st.number_input(f"Monthly SIP ({CURRENCY})", min_value=100.0, value=5000.0, step=500.0, key="sm")
        with c2: sip_r = st.number_input("Expected Return (% p.a.)", min_value=1.0, value=12.0, step=0.5, key="sr")
        with c3: sip_y = st.number_input("Duration (Years)", min_value=1, value=10, step=1, key="sy")
        if st.button("Calculate Returns →", use_container_width=True, key="sip_btn"):
            from tools.calculator_tool import calculate_investment_returns
            res = calculate_investment_returns.invoke({"monthly_investment": sip_m, "expected_annual_return": sip_r, "years": sip_y})
            st.markdown(f'<div class="calc-result">{res}</div>', unsafe_allow_html=True)
            st.caption("*Educational only. Mutual fund returns are subject to market risk.*")

    with sub3:
        st.markdown(f"<p style='color:{text_muted};font-size:0.83rem;'>Calculate how your deposit grows with compounding.</p>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1: ci_p = st.number_input(f"Principal ({CURRENCY})", min_value=100.0, value=50000.0, step=1000.0, key="cp")
        with c2: ci_r = st.number_input("Rate (% p.a.)", min_value=0.1, value=7.0, step=0.1, key="cr")
        with c3: ci_y = st.number_input("Years", min_value=1, value=5, step=1, key="cy")
        with c4: ci_f = st.selectbox("Frequency", [1, 2, 4, 12], index=3, key="cf",
                                      format_func=lambda x: {1:"Annual",2:"Half-Yearly",4:"Quarterly",12:"Monthly"}[x])
        if st.button("Calculate Maturity →", use_container_width=True, key="ci_btn"):
            from tools.calculator_tool import calculate_compound_interest
            res = calculate_compound_interest.invoke({"principal": ci_p, "annual_rate": ci_r, "time_years": ci_y, "compounding_frequency": ci_f})
            st.markdown(f'<div class="calc-result">{res}</div>', unsafe_allow_html=True)
            st.caption("*Educational only. FD/RD rates may vary by bank.*")

    with sub4:
        st.markdown(f"<p style='color:{text_muted};font-size:0.83rem;'>Find out how much you need to save monthly to hit your financial goal.</p>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            sg_target = st.number_input(f"Goal Amount ({CURRENCY})", min_value=100.0, value=100000.0, step=5000.0, key="gt")
            sg_curr   = st.number_input(f"Current Savings ({CURRENCY})", min_value=0.0, value=10000.0, step=1000.0, key="gc")
        with c2:
            sg_months = st.number_input("Time Frame (Months)", min_value=1, value=24, step=3, key="gm")
            sg_rate   = st.number_input("Savings Account Rate (% p.a.)", min_value=0.0, value=4.0, step=0.5, key="gr")
        if st.button("Calculate Monthly Target →", use_container_width=True, key="sg_btn"):
            from tools.calculator_tool import calculate_savings_goal_requirements
            res = calculate_savings_goal_requirements.invoke({
                "target_amount": sg_target,
                "current_savings": sg_curr,
                "time_months": sg_months,
                "annual_interest_rate": sg_rate
            })
            st.markdown(f'<div class="calc-result">{res}</div>', unsafe_allow_html=True)
