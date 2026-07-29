"""
FinTrack AI
app.py

Personal Finance Dashboard built with Streamlit.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from utils import (
    ensure_storage,
    load_transactions,
)

# -------------------------------------------------------
# Page Configuration
# -------------------------------------------------------

st.set_page_config(
    page_title="FinTrack AI",
    page_icon="💰",
    layout="wide",
)

# -------------------------------------------------------
# Simple Styling
# -------------------------------------------------------

st.markdown(
    """
    <style>
    .main{
        padding-top:1rem;
    }
    div[data-testid="stMetric"]{
        border:1px solid #dddddd;
        border-radius:12px;
        padding:10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------
# Title
# -------------------------------------------------------

st.title("💰 FinTrack AI")
st.caption("Track income, expenses and financial health.")

# -------------------------------------------------------
# Sidebar
# -------------------------------------------------------

with st.sidebar:
    st.header("Navigation")
    st.success("FinTrack AI Ready")

# -------------------------------------------------------
# Initialize Storage
# -------------------------------------------------------

try:
    ensure_storage()
except Exception as exc:
    st.error(f"Unable to initialize storage.\n\n{exc}")
    st.stop()

# -------------------------------------------------------
# Load Data
# -------------------------------------------------------

try:
    df = load_transactions()

except Exception as exc:
    st.error(f"Unable to load transaction data.\n\n{exc}")
    st.stop()

# -------------------------------------------------------
# Safety Checks
# -------------------------------------------------------

if df is None:
    df = pd.DataFrame()

if not isinstance(df, pd.DataFrame):
    st.error("Invalid data returned by utils.py")
    st.stop()

# -------------------------------------------------------
# Session State
# -------------------------------------------------------

if "selected_index" not in st.session_state:
    st.session_state.selected_index = None

if "refresh_counter" not in st.session_state:
    st.session_state.refresh_counter = 0

# -------------------------------------------------------
# Empty Dataset
# -------------------------------------------------------

if df.empty:
    st.info(
        "No transactions available yet.\n\n"
        "Use the Add Transaction section to create your first record."
    )

st.divider()
# -------------------------------------------------------
# Additional Imports
# -------------------------------------------------------

from utils import (
    dashboard_summary,
    format_currency,
)

# -------------------------------------------------------
# Dashboard Summary
# -------------------------------------------------------

try:
    summary = dashboard_summary(df)
except Exception as exc:
    st.error(f"Unable to calculate dashboard summary.\n\n{exc}")
    st.stop()

st.subheader("📊 Dashboard")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Income",
        format_currency(float(summary.get("income", 0))),
    )

with col2:
    st.metric(
        "Total Expense",
        format_currency(float(summary.get("expense", 0))),
    )

with col3:
    st.metric(
        "Net Balance",
        format_currency(float(summary.get("balance", 0))),
    )

with col4:
    st.metric(
        "Transactions",
        int(summary.get("transactions", 0)),
    )

col5, col6 = st.columns(2)

with col5:
    st.metric(
        "Savings Rate",
        f"{float(summary.get('savings_rate', 0)):.2f}%",
    )

with col6:
    avg_income = float(summary.get("average_income", 0))
    avg_expense = float(summary.get("average_expense", 0))

    st.metric(
        "Average Income / Expense",
        f"{format_currency(avg_income)} / {format_currency(avg_expense)}",
    )

st.divider()
# ==========================================================
# PART 3 — SEARCH, FILTERS & TRANSACTION TABLE
# ==========================================================

from utils import (
    filter_transactions,
    recent_transactions,
    get_categories,
)

st.subheader("🔍 Search & Filters")

col1, col2, col3 = st.columns(3)

with col1:
    transaction_type = st.selectbox(
        "Transaction Type",
        ["All", "Income", "Expense"],
    )

with col2:
    categories = ["All"] + list(get_categories(df))
    category = st.selectbox(
        "Category",
        categories,
    )

with col3:
    keyword = st.text_input(
        "Search Description",
        placeholder="Search transactions...",
    )

try:
    filtered_df = filter_transactions(
        df=df,
        transaction_type=None if transaction_type == "All" else transaction_type,
        category=None if category == "All" else category,
        keyword=keyword.strip() if keyword.strip() else None,
    )
except Exception as exc:
    st.error(f"Filtering failed: {exc}")
    filtered_df = df.copy()

st.divider()

st.subheader("📋 Transactions")

if filtered_df.empty:
    st.info("No matching transactions found.")
else:
    display_df = (
        filtered_df.sort_values("Date", ascending=False)
        .reset_index(drop=True)
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        label="⬇ Download Filtered CSV",
        data=display_df.to_csv(index=False),
        file_name="transactions.csv",
        mime="text/csv",
    )

st.divider()

st.subheader("🕒 Recent Transactions")

try:
    recent_df = recent_transactions(df=df, limit=10)

    if recent_df.empty:
        st.info("No recent transactions available.")
    else:
        st.dataframe(
            recent_df.reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )

except Exception as exc:
    st.warning(f"Unable to load recent transactions: {exc}")

st.divider()
# ==========================================================
# PART 4 — CHARTS & ANALYTICS
# ==========================================================

import plotly.express as px

from utils import (
    expense_chart_data,
    income_chart_data,
    balance_chart_data,
    category_summary,
    monthly_summary,
)

st.subheader("📈 Financial Analytics")

col1, col2 = st.columns(2)

# ----------------------------------------------------------
# Expense by Category
# ----------------------------------------------------------

with col1:
    try:
        expense_df = expense_chart_data(df)

        if not expense_df.empty:
            fig = px.pie(
                expense_df,
                names="Category",
                values="Amount",
                title="Expense Distribution",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expense data available.")

    except Exception as exc:
        st.warning(f"Expense chart unavailable: {exc}")

# ----------------------------------------------------------
# Income by Category
# ----------------------------------------------------------

with col2:
    try:
        income_df = income_chart_data(df)

        if not income_df.empty:
            fig = px.pie(
                income_df,
                names="Category",
                values="Amount",
                title="Income Distribution",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No income data available.")

    except Exception as exc:
        st.warning(f"Income chart unavailable: {exc}")

st.divider()

# ----------------------------------------------------------
# Monthly Balance Trend
# ----------------------------------------------------------

try:
    balance_df = balance_chart_data(df)

    if not balance_df.empty:
        fig = px.line(
            balance_df,
            x="Month",
            y="Balance",
            markers=True,
            title="Monthly Balance Trend",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No balance trend available.")

except Exception as exc:
    st.warning(f"Balance chart unavailable: {exc}")

st.divider()

# ----------------------------------------------------------
# Category Summary
# ----------------------------------------------------------

st.subheader("📂 Category Summary")

try:
    cat_df = category_summary(df)

    if not cat_df.empty:
        st.dataframe(
            cat_df.reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No category summary available.")

except Exception as exc:
    st.warning(f"Category summary unavailable: {exc}")

st.divider()

# ----------------------------------------------------------
# Monthly Summary
# ----------------------------------------------------------

st.subheader("📅 Monthly Summary")

try:
    month_df = monthly_summary(df)

    if not month_df.empty:
        st.dataframe(
            month_df.reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No monthly summary available.")

except Exception as exc:
    st.warning(f"Monthly summary unavailable: {exc}")

st.divider()
# ==========================================================
# PART 5 — INSIGHTS, EXPORT & DATA OVERVIEW
# ==========================================================

from utils import (
    health_report,
    export_transactions,
)

st.subheader("🧠 Financial Health")

try:
    report = health_report(df)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("Status", report.get("status", "N/A"))

    with c2:
        st.metric(
            "Savings Rate",
            f"{report.get('savings_rate',0):.2f}%"
        )

    with c3:
        st.metric(
            "Net Balance",
            format_currency(report.get("balance",0))
        )

    warnings = report.get("warnings", [])

    if warnings:
        st.warning("Recommendations")

        for warning in warnings:
            st.write(f"• {warning}")
    else:
        st.success("Financial health looks good.")

except Exception as exc:
    st.error(f"Health report failed: {exc}")

st.divider()

# ----------------------------------------------------------

st.subheader("📄 Dataset Preview")

preview_rows = min(len(df), 15)

if preview_rows:
    st.dataframe(
        df.head(preview_rows),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No transactions available.")

st.divider()

# ----------------------------------------------------------

st.subheader("📤 Export")

try:
    csv_data = export_transactions(df=df)

    st.download_button(
        "⬇ Download Transactions",
        csv_data,
        file_name="fintrack_transactions.csv",
        mime="text/csv",
    )

except Exception as exc:
    st.error(f"Export failed: {exc}")

st.divider()

# ----------------------------------------------------------

st.subheader("📊 Dataset Statistics")

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Transactions", len(df))

with c2:
    st.metric(
        "Categories",
        df["Category"].nunique() if not df.empty else 0,
    )

with c3:
    st.metric(
        "Missing Values",
        int(df.isna().sum().sum()),
    )

st.divider()
# ==========================================================
# PART 6 — FINAL SECTION
# ==========================================================

st.subheader("📌 Application Information")

left_col, right_col = st.columns(2)

with left_col:
    st.info(
        """
### Features
- Dashboard Overview
- Transaction Search
- Smart Filters
- Financial Analytics
- Category Summary
- Monthly Summary
- Data Export
- Health Report
        """
    )

with right_col:
    st.success(
        """
### Current Status
✅ Storage Initialized

✅ Transactions Loaded

✅ Dashboard Ready

✅ Analytics Available

✅ Export Enabled
        """
    )

st.divider()

# ----------------------------------------------------------
# Data Validation
# ----------------------------------------------------------

st.subheader("🛡 Data Validation")

if df.empty:
    st.warning("Dataset is empty.")
else:
    st.success(f"Loaded **{len(df)}** transaction(s).")

    missing = df.isna().sum().sum()

    if missing == 0:
        st.success("No missing values detected.")
    else:
        st.warning(f"Missing values detected: **{missing}**")

st.divider()

# ----------------------------------------------------------
# Footer
# ----------------------------------------------------------

st.markdown("---")

st.caption(
    "© 2026 FinTrack AI • Personal Finance Dashboard"
)

st.caption(
    "Built with Streamlit, Pandas and Plotly"
)







