"""Analytics helpers for expense trends and forecasting."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

import matplotlib.pyplot as plt
import mysql.connector
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from sklearn.linear_model import LinearRegression

from .db import db_cursor, get_connection


def fetch_historic_data() -> List[Tuple[str, str, float]]:
    """Return total monthly spendings by category."""
    query = """
        SELECT DATE_FORMAT(t.date, '%Y-%m') AS month,
               c.name AS category,
               SUM(t.amount) AS total_spent
        FROM transaction t
        JOIN category c ON t.categoryid = c.categoryid
        WHERE t.type = 'expense'
        GROUP BY month, category
        ORDER BY month ASC, category ASC
    """

    with db_cursor() as (_, cursor):
        cursor.execute(query)
        rows = cursor.fetchall()
    return [(month, category, float(total)) for month, category, total in rows]


def process_data(rows: Iterable[Tuple[str, str, float]]):
    """Transform rows into nested dict plus sorted labels."""
    data = defaultdict(dict)
    months_set = set()
    categories_set = set()
    for month, category, total_spent in rows:
        data[month][category] = total_spent
        months_set.add(month)
        categories_set.add(category)
    months = sorted(months_set)
    categories = sorted(categories_set)
    return data, months, categories


def plot_monthly_spendings(data, months: Sequence[str], categories: Sequence[str]) -> Figure:
    """Plot monthly spendings per category and return the figure."""
    fig, ax = plt.subplots(figsize=(10, 5))
    for category in categories:
        spendings = [data.get(month, {}).get(category, 0) for month in months]
        ax.plot(months, spendings, label=category)
    ax.set_title("Monthly Spendings by Category")
    ax.set_xlabel("Month")
    ax.set_ylabel("Amount Spent")
    ax.tick_params(axis="x", rotation=45)
    ax.legend()
    fig.tight_layout()
    return fig


def plot_category_spendings_overall(data) -> Figure:
    """Plot overall spendings distribution."""
    overall_spendings = defaultdict(float)
    for month in data:
        for category in data[month]:
            overall_spendings[category] += float(data[month][category])
    labels = list(overall_spendings.keys())
    amounts = list(overall_spendings.values())

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(amounts, labels=labels, autopct="%1.1f%%")
    ax.set_title("Overall Spendings Distribution by Category")
    return fig


def fetch_dataframe() -> pd.DataFrame:
    """Fetch expense data aggregated monthly/category into a DataFrame."""
    query = """
        SELECT DATE_FORMAT(t.date, '%Y-%m') AS month,
               t.categoryid,
               c.name AS category_name,
               SUM(t.amount) AS total_spent
        FROM transaction t
        JOIN category c ON t.categoryid = c.categoryid
        WHERE t.type = 'expense'
        GROUP BY month, t.categoryid, category_name
        ORDER BY month, category_name
    """

    conn = get_connection()
    try:
        df = pd.read_sql(query, conn)
    finally:
        conn.close()

    category_necessity = {
        "Food": "necessary",
        "Rent": "necessary",
        "Utilities": "necessary",
        "Entertainment": "discretionary",
        "Travel": "discretionary",
        "Shopping": "discretionary",
        "Health": "necessary",
        "Miscellaneous": "discretionary",
    }
    df["necessity"] = df["category_name"].map(category_necessity).fillna("discretionary")
    return df


@dataclass
class PreparedData:
    pivot: pd.DataFrame
    original_df: pd.DataFrame


def prepare_data(df: pd.DataFrame) -> PreparedData:
    """Pivot the dataframe to months vs categories and add index column."""
    pivot = df.pivot(index="month", columns="category_name", values="total_spent").fillna(0)
    pivot["month_idx"] = np.arange(len(pivot))
    return PreparedData(pivot=pivot, original_df=df)


def train_predict(pivot: pd.DataFrame) -> Dict[str, float]:
    """Train linear regression per category and predict next month."""
    model = LinearRegression()
    predictions: Dict[str, float] = {}
    feature = pivot[["month_idx"]]
    for category in pivot.columns[:-1]:  # skip month_idx
        y = pivot[category]
        model.fit(feature, y)
        next_month_idx = np.array([[pivot["month_idx"].max() + 1]])
        predictions[category] = float(model.predict(next_month_idx)[0])
    return predictions


def plot_spendings(pivot: pd.DataFrame, predictions: Dict[str, float]) -> Figure:
    """Generate a combined historic and predicted spendings plot."""
    months = pivot.index.tolist()
    categories = list(pivot.columns[:-1])

    fig, ax = plt.subplots(figsize=(12, 6))
    for category in categories:
        ax.plot(months, pivot[category], label=f"{category} (Historical)")
        ax.plot(
            months[-1] + " (predicted)",
            predictions[category],
            marker="*",
            color="red",
        )

    ax.set_xlabel("Month")
    ax.set_ylabel("Spendings (Rupees)")
    ax.set_title("Historic and Predicted Monthly Spendings by Category")
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    return fig


def recommend_savings(
    predictions: Dict[str, float],
    df_with_necessity: pd.DataFrame,
    threshold: float = 100.0,
) -> List[str]:
    """Return textual recommendations based on predicted spendings."""
    results: List[str] = []
    for category, amount in predictions.items():
        necessity = (
            df_with_necessity[df_with_necessity["category_name"] == category]["necessity"]
            .iloc[0]
            if not df_with_necessity[df_with_necessity["category_name"] == category].empty
            else "discretionary"
        )
        if necessity == "discretionary" and amount > threshold:
            results.append(
                f"Consider reducing spending in discretionary category '{category}': "
                f"Predicted {amount:.2f} rupees next month."
            )
        else:
            results.append(
                f"Spending in necessary or low predicted category '{category}': "
                f"{amount:.2f} rupees. No major cuts recommended."
            )
    return results




