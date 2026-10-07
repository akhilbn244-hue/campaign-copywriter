"""
segmenter.py  -  SORTS CUSTOMERS INTO GROUPS
============================================

No AI here at all - just plain rules, like you'd use in Excel.

Why segment?  One email for everyone is boring. A VIP who spent 5,000 AED
should hear something different from someone who bought once last week.
So we sort customers into groups (segments), then write one email per group.

The rules (easy to change - see SEGMENT RULES below):
- New      -> has ordered only once
- VIP      -> has spent 1,000 or more in total
- Regular  -> everyone else
"""

import pandas as pd   # pandas = Excel inside Python

# The columns the uploaded CSV must have. If one is missing we explain which.
REQUIRED_COLUMNS = ["name", "email", "age", "city", "total_spend", "orders", "last_purchase"]

# ---- SEGMENT RULES (change these numbers to change who lands where) ----
VIP_MIN_SPEND = 1000
NEW_MAX_ORDERS = 1


def load_customers(file):
    """
    Read a CSV file into a table (a pandas "DataFrame") and check it looks right.
    `file` can be a file path or a file uploaded through the app.
    """
    table = pd.read_csv(file)

    # Make column names forgiving: " Total_Spend " becomes "total_spend".
    table.columns = [c.strip().lower() for c in table.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in table.columns]
    if missing:
        raise ValueError(
            "Your CSV is missing these columns: " + ", ".join(missing)
            + ". It needs: " + ", ".join(REQUIRED_COLUMNS)
        )

    # Turn text like "1,250" into the number 1250, so we can do maths on it.
    table["total_spend"] = pd.to_numeric(
        table["total_spend"].astype(str).str.replace(",", ""), errors="coerce"
    ).fillna(0)
    table["orders"] = pd.to_numeric(table["orders"], errors="coerce").fillna(0).astype(int)
    table["age"] = pd.to_numeric(table["age"], errors="coerce")
    table["last_purchase"] = pd.to_datetime(table["last_purchase"], errors="coerce")

    return table


def pick_segment(customer):
    """
    Decide the segment for ONE customer (one row of the table).
    The order matters: we check "New" first, so a first-time big spender
    is treated as New, not VIP.
    """
    if customer["orders"] <= NEW_MAX_ORDERS:
        return "New"
    if customer["total_spend"] >= VIP_MIN_SPEND:
        return "VIP"
    return "Regular"


def add_segments(table):
    """Add a 'segment' column by running pick_segment on every row."""
    table = table.copy()                         # don't change the original
    table["segment"] = table.apply(pick_segment, axis=1)   # axis=1 means "row by row"
    return table


def summarise_segments(table):
    """
    Build a small summary per segment - this is what we describe to the AI,
    so it knows WHO it is writing for (without sending everyone's personal data).
    """
    summary = (
        table.groupby("segment")
        .agg(
            customers=("name", "count"),
            avg_spend=("total_spend", "mean"),
            avg_age=("age", "mean"),
            avg_orders=("orders", "mean"),
            top_city=("city", lambda cities: cities.mode().iat[0] if not cities.mode().empty else "-"),
        )
        .round(0)
        .reset_index()
    )
    return summary
