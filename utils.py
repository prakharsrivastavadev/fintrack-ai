"""
FinTrack AI
utils.py

Shared utility functions for data validation and storage.

Author: Prakhar Srivastava
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

# --------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CSV_FILE = DATA_DIR / "transactions.csv"

# --------------------------------------------------------------------
# Schema
# --------------------------------------------------------------------

REQUIRED_COLUMNS = [
    "Date",
    "Type",
    "Category",
    "Description",
    "Amount",
]

VALID_TRANSACTION_TYPES = {"Income", "Expense"}

DEFAULT_CATEGORY = "General"
DEFAULT_DESCRIPTION = "No description"

# --------------------------------------------------------------------
# Storage
# --------------------------------------------------------------------


def ensure_storage() -> None:
    """Create the data folder and CSV file if missing."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not CSV_FILE.exists():
        pd.DataFrame(columns=REQUIRED_COLUMNS).to_csv(
            CSV_FILE,
            index=False,
        )


# --------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------


def clean_text(value: Any) -> str:
    """Return trimmed string."""

    if value is None:
        return ""

    return str(value).strip()


def validate_date(date: str) -> str:
    """Validate YYYY-MM-DD date."""

    date = clean_text(date)

    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(
            "Date must use YYYY-MM-DD format."
        ) from exc

    return date


def validate_amount(amount: Any) -> float:
    """Validate positive numeric amount."""

    try:
        value = float(amount)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Please enter a valid amount."
        ) from exc

    if value <= 0:
        raise ValueError(
            "Amount must be greater than zero."
        )

    return round(value, 2)


def validate_transaction_type(value: str) -> str:
    """Validate transaction type."""

    value = clean_text(value).title()

    if value not in VALID_TRANSACTION_TYPES:
        raise ValueError(
            "Transaction type must be Income or Expense."
        )

    return value


def validate_category(category: str) -> str:
    """Validate category."""

    category = clean_text(category)

    if not category:
        return DEFAULT_CATEGORY

    return category.title()


def validate_description(description: str) -> str:
    """Validate description."""

    description = clean_text(description)

    if not description:
        return DEFAULT_DESCRIPTION

    return description


def validate_transaction(
    date: str,
    transaction_type: str,
    category: str,
    description: str,
    amount: Any,
) -> dict[str, Any]:
    """Return a validated transaction dictionary."""

    return {
        "Date": validate_date(date),
        "Type": validate_transaction_type(transaction_type),
        "Category": validate_category(category),
        "Description": validate_description(description),
        "Amount": validate_amount(amount),
    }
# --------------------------------------------------------------------
# DataFrame Helpers
# --------------------------------------------------------------------


def create_empty_dataframe() -> pd.DataFrame:
    """Return an empty transaction DataFrame."""

    return pd.DataFrame(columns=REQUIRED_COLUMNS)


def verify_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure every required column exists.
    Missing columns are created automatically.
    """

    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            df[column] = None

    return df[REQUIRED_COLUMNS]


# --------------------------------------------------------------------
# Load / Save
# --------------------------------------------------------------------


def load_transactions() -> pd.DataFrame:
    """
    Load transaction data safely.
    """

    ensure_storage()

    try:
        df = pd.read_csv(CSV_FILE)

    except (
        FileNotFoundError,
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
    ):
        return create_empty_dataframe()

    df = verify_schema(df)

    if df.empty:
        return df

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce",
    )

    df = df.dropna(subset=["Date"])

    df["Amount"] = (
        pd.to_numeric(
            df["Amount"],
            errors="coerce",
        )
        .fillna(0)
        .round(2)
    )

    df["Type"] = (
        df["Type"]
        .astype(str)
        .str.title()
    )

    df["Category"] = (
        df["Category"]
        .astype(str)
        .str.strip()
    )

    df["Description"] = (
        df["Description"]
        .astype(str)
        .str.strip()
    )

    df = df.sort_values(
        "Date",
        ascending=False,
    ).reset_index(drop=True)

    return df


def save_transactions(df: pd.DataFrame) -> None:
    """
    Save transaction data.
    """

    ensure_storage()

    df = verify_schema(df.copy())

    if not df.empty:

        df["Date"] = (
            pd.to_datetime(
                df["Date"],
                errors="coerce",
            )
            .dt.strftime("%Y-%m-%d")
        )

        df["Amount"] = (
            pd.to_numeric(
                df["Amount"],
                errors="coerce",
            )
            .fillna(0)
            .round(2)
        )

    temp_file = CSV_FILE.with_suffix(".tmp")

    df.to_csv(
        temp_file,
        index=False,
    )

    temp_file.replace(CSV_FILE)


# --------------------------------------------------------------------
# Utility Helpers
# --------------------------------------------------------------------


def reload_transactions() -> pd.DataFrame:
    """Reload latest transaction data."""

    return load_transactions()


def transaction_count(
    df: pd.DataFrame | None = None,
) -> int:
    """Return total transaction count."""

    if df is None:
        df = load_transactions()

    return len(df)


def is_empty(
    df: pd.DataFrame,
) -> bool:
    """Return True if dataframe has no rows."""

    return df.empty


def get_categories(
    df: pd.DataFrame | None = None,
) -> list[str]:
    """Return sorted category list."""

    if df is None:
        df = load_transactions()

    if df.empty:
        return []

    return sorted(
        df["Category"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )
# --------------------------------------------------------------------
# Transaction CRUD Operations
# --------------------------------------------------------------------


def transaction_exists(
    date: str,
    transaction_type: str,
    category: str,
    description: str,
    amount: Any,
    df: pd.DataFrame | None = None,
) -> bool:
    """
    Return True if an identical transaction already exists.
    """

    if df is None:
        df = load_transactions()

    if df.empty:
        return False

    transaction = validate_transaction(
        date,
        transaction_type,
        category,
        description,
        amount,
    )

    comparison = df.copy()

    comparison["Date"] = (
        pd.to_datetime(comparison["Date"])
        .dt.strftime("%Y-%m-%d")
    )

    comparison["Category"] = (
        comparison["Category"]
        .astype(str)
        .str.title()
        .str.strip()
    )

    comparison["Description"] = (
        comparison["Description"]
        .astype(str)
        .str.strip()
    )

    comparison["Type"] = (
        comparison["Type"]
        .astype(str)
        .str.title()
    )

    comparison["Amount"] = (
        pd.to_numeric(
            comparison["Amount"],
            errors="coerce",
        )
        .fillna(0)
        .round(2)
    )

    duplicate = comparison[
        (comparison["Date"] == transaction["Date"])
        & (comparison["Type"] == transaction["Type"])
        & (comparison["Category"] == transaction["Category"])
        & (comparison["Description"] == transaction["Description"])
        & (comparison["Amount"] == transaction["Amount"])
    ]

    return not duplicate.empty


def add_transaction(
    date: str,
    transaction_type: str,
    category: str,
    description: str,
    amount: Any,
) -> bool:
    """
    Add a transaction.

    Returns True if inserted.
    Returns False if duplicate exists.
    """

    df = load_transactions()

    if transaction_exists(
        date,
        transaction_type,
        category,
        description,
        amount,
        df,
    ):
        return False

    transaction = validate_transaction(
        date,
        transaction_type,
        category,
        description,
        amount,
    )

    df = pd.concat(
        [
            df,
            pd.DataFrame([transaction]),
        ],
        ignore_index=True,
    )

    save_transactions(df)

    return True


def update_transaction(
    index: int,
    date: str,
    transaction_type: str,
    category: str,
    description: str,
    amount: Any,
) -> None:
    """
    Update an existing transaction.
    """

    df = load_transactions()

    if not 0 <= index < len(df):
        raise IndexError("Invalid transaction index.")

    transaction = validate_transaction(
        date,
        transaction_type,
        category,
        description,
        amount,
    )

    for key, value in transaction.items():
        df.at[index, key] = value

    save_transactions(df)


def delete_transaction(
    index: int,
) -> None:
    """
    Delete a transaction.
    """

    df = load_transactions()

    if not 0 <= index < len(df):
        raise IndexError("Invalid transaction index.")

    df = (
        df.drop(index=index)
        .reset_index(drop=True)
    )

    save_transactions(df)


def clear_transactions() -> None:
    """
    Remove every transaction.
    """

    save_transactions(
        create_empty_dataframe()
    )


def get_transaction(
    index: int,
) -> dict[str, Any]:
    """
    Return one transaction as a dictionary.
    """

    df = load_transactions()

    if not 0 <= index < len(df):
        raise IndexError("Invalid transaction index.")

    record = (
        df.iloc[index]
        .to_dict()
    )

    if isinstance(record["Date"], pd.Timestamp):
        record["Date"] = (
            record["Date"]
            .strftime("%Y-%m-%d")
        )

    return record
# --------------------------------------------------------------------
# Financial Analytics
# --------------------------------------------------------------------


def total_income(
    df: pd.DataFrame | None = None,
) -> float:
    """
    Return total income.
    """

    if df is None:
        df = load_transactions()

    if df.empty:
        return 0.0

    income = df[df["Type"] == "Income"]

    return round(float(income["Amount"].sum()), 2)


def total_expense(
    df: pd.DataFrame | None = None,
) -> float:
    """
    Return total expenses.
    """

    if df is None:
        df = load_transactions()

    if df.empty:
        return 0.0

    expense = df[df["Type"] == "Expense"]

    return round(float(expense["Amount"].sum()), 2)


def net_balance(
    df: pd.DataFrame | None = None,
) -> float:
    """
    Return current balance.
    """

    if df is None:
        df = load_transactions()

    return round(
        total_income(df) - total_expense(df),
        2,
    )


def savings_rate(
    df: pd.DataFrame | None = None,
) -> float:
    """
    Return savings percentage.
    """

    if df is None:
        df = load_transactions()

    income = total_income(df)

    if income <= 0:
        return 0.0

    return round(
        (net_balance(df) / income) * 100,
        2,
    )


# --------------------------------------------------------------------
# Dashboard Summary
# --------------------------------------------------------------------


def dashboard_summary(
    df: pd.DataFrame | None = None,
) -> dict[str, float | int]:
    """
    Dashboard statistics.
    """

    if df is None:
        df = load_transactions()

    return {
        "income": total_income(df),
        "expense": total_expense(df),
        "balance": net_balance(df),
        "transactions": len(df),
        "savings_rate": savings_rate(df),
        "average_income": average_income(df),
        "average_expense": average_expense(df),
    }


# --------------------------------------------------------------------
# Averages
# --------------------------------------------------------------------


def average_income(
    df: pd.DataFrame | None = None,
) -> float:

    if df is None:
        df = load_transactions()

    income = df[df["Type"] == "Income"]

    if income.empty:
        return 0.0

    return round(
        float(income["Amount"].mean()),
        2,
    )


def average_expense(
    df: pd.DataFrame | None = None,
) -> float:

    if df is None:
        df = load_transactions()

    expense = df[df["Type"] == "Expense"]

    if expense.empty:
        return 0.0

    return round(
        float(expense["Amount"].mean()),
        2,
    )


# --------------------------------------------------------------------
# Largest Transactions
# --------------------------------------------------------------------


def largest_income(
    df: pd.DataFrame | None = None,
) -> float:

    if df is None:
        df = load_transactions()

    income = df[df["Type"] == "Income"]

    if income.empty:
        return 0.0

    return round(
        float(income["Amount"].max()),
        2,
    )


def largest_expense(
    df: pd.DataFrame | None = None,
) -> float:

    if df is None:
        df = load_transactions()

    expense = df[df["Type"] == "Expense"]

    if expense.empty:
        return 0.0

    return round(
        float(expense["Amount"].max()),
        2,
    )


# --------------------------------------------------------------------
# Category Analytics
# --------------------------------------------------------------------


def category_summary(
    transaction_type: str | None = None,
    df: pd.DataFrame | None = None,
) -> pd.DataFrame:

    if df is None:
        df = load_transactions()

    if df.empty:
        return pd.DataFrame(
            columns=["Category", "Amount"]
        )

    result = df.copy()

    if transaction_type:
        result = result[
            result["Type"] == transaction_type.title()
        ]

    summary = (
        result
        .groupby(
            "Category",
            as_index=False,
        )["Amount"]
        .sum()
        .sort_values(
            "Amount",
            ascending=False,
        )
    )

    summary["Amount"] = (
        summary["Amount"]
        .round(2)
    )

    return summary.reset_index(drop=True)


def top_expense_categories(
    limit: int = 5,
    df: pd.DataFrame | None = None,
) -> pd.DataFrame:

    return category_summary(
        "Expense",
        df,
    ).head(limit)


def top_income_categories(
    limit: int = 5,
    df: pd.DataFrame | None = None,
) -> pd.DataFrame:

    return category_summary(
        "Income",
        df,
    ).head(limit)
# --------------------------------------------------------------------
# Monthly Analytics
# --------------------------------------------------------------------

def monthly_summary(
    df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Return monthly income, expense and balance.
    """

    if df is None:
        df = load_transactions()

    if df.empty:
        return pd.DataFrame(
            columns=[
                "Month",
                "Income",
                "Expense",
                "Balance",
            ]
        )

    monthly = df.copy()

    monthly["Month"] = (
        pd.to_datetime(monthly["Date"])
        .dt.to_period("M")
        .astype(str)
    )

    summary = (
        monthly.pivot_table(
            index="Month",
            columns="Type",
            values="Amount",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
    )

    if "Income" not in summary.columns:
        summary["Income"] = 0.0

    if "Expense" not in summary.columns:
        summary["Expense"] = 0.0

    summary["Balance"] = (
        summary["Income"] -
        summary["Expense"]
    ).round(2)

    return summary.sort_values("Month")


# --------------------------------------------------------------------
# Filtering
# --------------------------------------------------------------------

def filter_transactions(
    df: pd.DataFrame | None = None,
    transaction_type: str | None = None,
    category: str | None = None,
    keyword: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    Filter transactions.
    """

    if df is None:
        df = load_transactions()

    result = df.copy()

    if transaction_type:
        result = result[
            result["Type"] ==
            transaction_type.title()
        ]

    if category:
        result = result[
            result["Category"] ==
            category
        ]

    if keyword:
        keyword = keyword.lower().strip()

        result = result[
            result["Description"]
            .astype(str)
            .str.lower()
            .str.contains(
                keyword,
                na=False,
            )
        ]

    if start_date:
        result = result[
            pd.to_datetime(result["Date"])
            >= pd.to_datetime(start_date)
        ]

    if end_date:
        result = result[
            pd.to_datetime(result["Date"])
            <= pd.to_datetime(end_date)
        ]

    return result.reset_index(drop=True)


# --------------------------------------------------------------------
# Recent Transactions
# --------------------------------------------------------------------

def recent_transactions(
    limit: int = 10,
    df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Return most recent transactions.
    """

    if df is None:
        df = load_transactions()

    return (
        df.sort_values(
            "Date",
            ascending=False,
        )
        .head(limit)
        .reset_index(drop=True)
    )


# --------------------------------------------------------------------
# Chart Helpers
# --------------------------------------------------------------------

def expense_chart_data(
    df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Expense chart dataset.
    """

    return category_summary(
        "Expense",
        df,
    )


def income_chart_data(
    df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Income chart dataset.
    """

    return category_summary(
        "Income",
        df,
    )


def balance_chart_data(
    df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Monthly balance chart.
    """

    return monthly_summary(df)


# --------------------------------------------------------------------
# Export
# --------------------------------------------------------------------

def export_transactions(
    filename: str,
    df: pd.DataFrame | None = None,
) -> None:
    """
    Export transactions.
    """

    if df is None:
        df = load_transactions()

    df.to_csv(
        filename,
        index=False,
    )


# --------------------------------------------------------------------
# Formatting
# --------------------------------------------------------------------

def format_currency(
    value: float,
) -> str:
    """
    Format Indian Rupee.
    """

    return f"₹{value:,.2f}"


def safe_float(
    value: Any,
) -> float:
    """
    Safe numeric conversion.
    """

    try:
        return round(
            float(value),
            2,
        )

    except (
        TypeError,
        ValueError,
    ):
        return 0.0
# --------------------------------------------------------------------
# Insights & Utility Functions
# --------------------------------------------------------------------

def current_month_summary(
    df: pd.DataFrame | None = None,
) -> dict[str, float]:
    """
    Return current month's income, expense and balance.
    """

    if df is None:
        df = load_transactions()

    if df.empty:
        return {
            "income": 0.0,
            "expense": 0.0,
            "balance": 0.0,
        }

    today = pd.Timestamp.today()

    current = df[
        (pd.to_datetime(df["Date"]).dt.month == today.month)
        &
        (pd.to_datetime(df["Date"]).dt.year == today.year)
    ]

    income = total_income(current)
    expense = total_expense(current)

    return {
        "income": income,
        "expense": expense,
        "balance": round(income - expense, 2),
    }


def spending_trend(
    df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Monthly spending trend.
    """

    monthly = monthly_summary(df)

    if monthly.empty:
        return monthly

    return monthly[[
        "Month",
        "Expense",
    ]]


def income_trend(
    df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Monthly income trend.
    """

    monthly = monthly_summary(df)

    if monthly.empty:
        return monthly

    return monthly[[
        "Month",
        "Income",
    ]]


def health_report(
    df: pd.DataFrame | None = None,
) -> dict[str, float | str]:
    """
    Overall financial health indicators.
    """

    if df is None:
        df = load_transactions()

    income = total_income(df)
    expense = total_expense(df)
    balance = income - expense

    if income == 0:
        score = "No Income Data"
    elif balance >= income * 0.30:
        score = "Excellent"
    elif balance >= income * 0.15:
        score = "Good"
    elif balance >= 0:
        score = "Average"
    else:
        score = "Needs Attention"

    return {
        "income": income,
        "expense": expense,
        "balance": round(balance, 2),
        "savings_rate": savings_rate(df),
        "status": score,
    }


# --------------------------------------------------------------------
# Miscellaneous
# --------------------------------------------------------------------

def last_updated() -> str:
    """
    Current timestamp.
    """

    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def app_information() -> dict[str, str]:
    """
    Metadata used by the Streamlit UI.
    """

    return {
        "app_name": "FinTrack AI",
        "version": "1.0.0",
        "author": "Prakhar Srivastava",
    }


# --------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------

__all__ = [
    "load_transactions",
    "save_transactions",
    "reload_transactions",
    "add_transaction",
    "update_transaction",
    "delete_transaction",
    "clear_transactions",
    "get_transaction",
    "transaction_exists",
    "transaction_count",
    "total_income",
    "total_expense",
    "net_balance",
    "savings_rate",
    "average_income",
    "average_expense",
    "largest_income",
    "largest_expense",
    "dashboard_summary",
    "monthly_summary",
    "category_summary",
    "top_income_categories",
    "top_expense_categories",
    "recent_transactions",
    "filter_transactions",
    "expense_chart_data",
    "income_chart_data",
    "balance_chart_data",
    "current_month_summary",
    "spending_trend",
    "income_trend",
    "health_report",
    "export_transactions",
    "format_currency",
    "safe_float",
    "get_categories",
    "last_updated",
    "app_information",
]
