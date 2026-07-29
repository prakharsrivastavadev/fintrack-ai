"""
FinTrack AI
app.py

Personal Finance Dashboard

Author: Prakhar Srivastava
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from utils import (
    app_information,
    balance_chart_data,
    category_summary,
    current_month_summary,
    dashboard_summary,
    ensure_storage,
    expense_chart_data,
    export_transactions,
    filter_transactions,
    format_currency,
    get_categories,
    health_report,
    income_chart_data,
    last_updated,
    load_transactions,
    monthly_summary,
    recent_transactions,
)

# ==========================================================
# PAGE CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="FinTrack AI",
    page_icon="💰",
    layout="wide",
)

# ==========================================================
# CUSTOM CSS
# ==========================================================

st.markdown(
    """
<style>

.block-container{
    padding-top:1.2rem;
}

div[data-testid="stMetric"]{
    border:1px solid #dcdcdc;
    border-radius:12px;
    padding:12px;
}

</style>
""",
    unsafe_allow_html=True,
)

# ==========================================================
# INITIALIZE STORAGE
# ==========================================================

try:
    ensure_storage()

except Exception as exc:
    st.error(f"Storage initialization failed.\n\n{exc}")
    st.stop()

# ==========================================================
# LOAD DATA
# ==========================================================

try:
    df = load_transactions()

except Exception as exc:
    st.error(f"Unable to load transaction data.\n\n{exc}")
    st.stop()

if df is None:
    df = pd.DataFrame()

if not isinstance(df, pd.DataFrame):
    st.error("Invalid data returned from utils.py")
    st.stop()

# ==========================================================
# SESSION STATE
# ==========================================================

if "selected_index" not in st.session_state:
    st.session_state.selected_index = None

if "refresh_counter" not in st.session_state:
    st.session_state.refresh_counter = 0

# ==========================================================
# APPLICATION HEADER
# ==========================================================

info = app_information()

st.title(f"💰 {info['app_name']}")

st.caption(
    f"Version {info['version']} • {info['author']}"
)

st.divider()

# ==========================================================
# EMPTY DATASET MESSAGE
# ==========================================================

if df.empty:
    st.info(
        "No transactions found.\n\n"
        "Add your first transaction to begin tracking your finances."
)
# ==========================================================
# DASHBOARD SUMMARY
# ==========================================================

summary = dashboard_summary(df)

st.subheader("📊 Dashboard")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "💰 Total Income",
        format_currency(summary["income"]),
    )

with col2:
    st.metric(
        "💸 Total Expense",
        format_currency(summary["expense"]),
    )

with col3:
    st.metric(
        "🏦 Net Balance",
        format_currency(summary["balance"]),
    )

with col4:
    st.metric(
        "📝 Transactions",
        summary["transactions"],
    )

st.divider()

# ==========================================================
# AVERAGE STATISTICS
# ==========================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Average Income",
        format_currency(summary["average_income"]),
    )

with col2:
    st.metric(
        "Average Expense",
        format_currency(summary["average_expense"]),
    )

with col3:
    st.metric(
        "Savings Rate",
        f"{summary['savings_rate']:.2f}%",
    )

st.divider()

# ==========================================================
# CURRENT MONTH SUMMARY
# ==========================================================

month = current_month_summary(df)

st.subheader("📅 Current Month")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Income",
        format_currency(month["income"]),
    )

with col2:
    st.metric(
        "Expense",
        format_currency(month["expense"]),
    )

with col3:
    st.metric(
        "Balance",
        format_currency(month["balance"]),
    )

st.divider()
# ==========================================================
# SEARCH & FILTERS
# ==========================================================

st.subheader("🔍 Search Transactions")

col1, col2, col3 = st.columns(3)

with col1:
    transaction_type = st.selectbox(
        "Transaction Type",
        ["All", "Income", "Expense"],
    )

with col2:
    category_list = ["All"] + get_categories(df)

    category = st.selectbox(
        "Category",
        category_list,
    )

with col3:
    keyword = st.text_input(
        "Description",
        placeholder="Search description...",
    )

try:

    filtered_df = filter_transactions(
        df=df,
        transaction_type=None if transaction_type == "All" else transaction_type,
        category=None if category == "All" else category,
        keyword=keyword if keyword.strip() else None,
    )

except Exception as exc:

    st.error(f"Unable to filter transactions.\n\n{exc}")

    filtered_df = df.copy()

st.divider()

# ==========================================================
# TRANSACTION TABLE
# ==========================================================

st.subheader("📋 Transactions")

if filtered_df.empty:

    st.info("No matching transactions found.")

else:

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
    )

st.divider()

# ==========================================================
# RECENT TRANSACTIONS
# ==========================================================

st.subheader("🕒 Recent Transactions")

try:

    recent_df = recent_transactions(
        limit=10,
        df=df,
    )

    if recent_df.empty:

        st.info("No recent transactions available.")

    else:

        st.dataframe(
            recent_df,
            use_container_width=True,
            hide_index=True,
        )

except Exception as exc:

    st.warning(f"Unable to load recent transactions.\n\n{exc}")

st.divider()
# ==========================================================
# CHARTS & ANALYTICS
# ==========================================================

st.subheader("📈 Financial Analytics")

col1, col2 = st.columns(2)

# ----------------------------------------------------------
# Expense Distribution
# ----------------------------------------------------------

with col1:

    expense_df = expense_chart_data(df)

    if expense_df.empty:

        st.info("No expense data available.")

    else:

        fig = px.pie(
            expense_df,
            names="Category",
            values="Amount",
            title="Expense Distribution",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

# ----------------------------------------------------------
# Income Distribution
# ----------------------------------------------------------

with col2:

    income_df = income_chart_data(df)

    if income_df.empty:

        st.info("No income data available.")

    else:

        fig = px.pie(
            income_df,
            names="Category",
            values="Amount",
            title="Income Distribution",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

st.divider()

# ==========================================================
# MONTHLY BALANCE TREND
# ==========================================================

st.subheader("📊 Monthly Balance")

balance_df = balance_chart_data(df)

if balance_df.empty:

    st.info("No monthly balance available.")

else:

    fig = px.line(
        balance_df,
        x="Month",
        y="Balance",
        markers=True,
        title="Monthly Balance Trend",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

st.divider()

# ==========================================================
# CATEGORY SUMMARY
# ==========================================================

st.subheader("📂 Category Summary")

category_df = category_summary(df=df)

if category_df.empty:

    st.info("No category summary available.")

else:

    st.dataframe(
        category_df,
        use_container_width=True,
        hide_index=True,
    )

st.divider()

# ==========================================================
# MONTHLY SUMMARY
# ==========================================================

st.subheader("📅 Monthly Summary")

monthly_df = monthly_summary(df)

if monthly_df.empty:

    st.info("No monthly summary available.")

else:

    st.dataframe(
        monthly_df,
        use_container_width=True,
        hide_index=True,
    )

st.divider()
# ==========================================================
# FINANCIAL HEALTH
# ==========================================================

st.subheader("🩺 Financial Health")

try:

    report = health_report(df)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Status",
            report["status"],
        )

    with col2:
        st.metric(
            "Savings Rate",
            f"{report['savings_rate']:.2f}%",
        )

    with col3:
        st.metric(
            "Net Balance",
            format_currency(report["balance"]),
        )

except Exception as exc:

    st.error(f"Unable to generate health report.\n\n{exc}")

st.divider()

# ==========================================================
# DATASET PREVIEW
# ==========================================================

st.subheader("📄 Dataset Preview")

preview_rows = st.slider(
    "Rows to Preview",
    min_value=5,
    max_value=50,
    value=10,
)

if df.empty:

    st.info("No transactions available.")

else:

    st.dataframe(
        df.head(preview_rows),
        use_container_width=True,
        hide_index=True,
    )

st.divider()

# ==========================================================
# EXPORT
# ==========================================================

st.subheader("📤 Export Transactions")

csv_data = df.to_csv(index=False)

st.download_button(
    label="⬇ Download CSV",
    data=csv_data,
    file_name="fintrack_transactions.csv",
    mime="text/csv",
)

st.divider()

# ==========================================================
# APPLICATION DETAILS
# ==========================================================

st.subheader("ℹ️ Application Details")

info = app_information()

left, right = st.columns(2)

with left:

    st.write(f"**Application:** {info['app_name']}")
    st.write(f"**Version:** {info['version']}")

with right:

    st.write(f"**Author:** {info['author']}")
    st.write(f"**Last Updated:** {last_updated()}")

st.divider()
# ==========================================================
# DATA QUALITY
# ==========================================================

st.subheader("🛡️ Data Quality")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Transactions",
        len(df),
    )

with col2:
    st.metric(
        "Categories",
        df["Category"].nunique() if not df.empty else 0,
    )

with col3:
    st.metric(
        "Missing Values",
        int(df.isna().sum().sum()),
    )

if df.empty:
    st.warning("No transaction data available.")
else:
    if df.isna().sum().sum() == 0:
        st.success("Dataset looks healthy.")
    else:
        st.warning("Dataset contains missing values.")

st.divider()

# ==========================================================
# RAW DATA
# ==========================================================

with st.expander("📋 View Complete Dataset"):

    if df.empty:
        st.info("No transactions to display.")
    else:
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

st.divider()

# ==========================================================
# FOOTER
# ==========================================================

st.markdown("---")

st.caption(
    "💰 FinTrack AI • Personal Finance Dashboard"
)

st.caption(
    f"Version {info['version']} | Last Updated: {last_updated()}"
    )





