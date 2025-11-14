"""High-level database operations for transactions, budgets, and summaries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional, Tuple

from mysql.connector import Error

from .db import db_cursor, get_connection


class DatabaseOperationError(RuntimeError):
    """Raised when an operation fails."""

    def __init__(self, message: str, original_error: Error | None = None) -> None:
        super().__init__(message)
        self.original_error = original_error


@dataclass(frozen=True)
class TransactionSummary:
    category: str
    total_amount: Decimal


def record_transaction(
    userid: int,
    categoryid: int,
    amount: Decimal | float,
    trans_type: str,
    transaction_date: date,
    paymentmethod: int | None = None,
) -> int:
    """Insert a transaction record and return the generated ID."""
    query = """
        INSERT INTO transaction (userid, categoryid, amount, type, date, paymentmethod)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    params = (
        userid,
        categoryid,
        str(amount),  # ensure Decimal compatibility
        trans_type,
        transaction_date,
        paymentmethod,
    )

    try:
        with db_cursor(commit=True) as (conn, cursor):
            cursor.execute(query, params)
            return cursor.lastrowid
    except Error as exc:
        raise DatabaseOperationError("Failed to record transaction.", exc) from exc


def update_budget(budgetid: int, new_limitamount: Decimal | float, new_status: str) -> None:
    """Update the limit and status for a budget entry."""
    query = """
        UPDATE budget
        SET limitamount = %s,
            status = %s
        WHERE budgetid = %s
    """

    try:
        with db_cursor(commit=True) as (_, cursor):
            cursor.execute(query, (str(new_limitamount), new_status, budgetid))
    except Error as exc:
        raise DatabaseOperationError("Failed to update budget.", exc) from exc


def view_user_summary(userid: int) -> List[TransactionSummary]:
    """Return total spend per category for a user."""
    query = """
        SELECT c.name AS category, SUM(t.amount) AS total
        FROM transaction t
        JOIN category c ON t.categoryid = c.categoryid
        WHERE t.userid = %s
        GROUP BY c.categoryid, c.name
        ORDER BY total DESC
    """

    try:
        with db_cursor() as (_, cursor):
            cursor.execute(query, (userid,))
            rows: Iterable[Tuple[str, Decimal]] = cursor.fetchall()
    except Error as exc:
        raise DatabaseOperationError("Failed to fetch user summary.", exc) from exc

    return [TransactionSummary(category=row[0], total_amount=row[1]) for row in rows]


def fetch_first_id(table: str, id_column: str) -> Optional[int]:
    """Return the first ID from the specified table or None if empty."""
    query = f"SELECT {id_column} FROM {table} ORDER BY {id_column} LIMIT 1"
    with db_cursor() as (_, cursor):
        cursor.execute(query)
        result = cursor.fetchone()
    return int(result[0]) if result else None


def check_budget_status(userid: int, categoryid: int, month: int) -> Dict[str, Any]:
    """Check budget status using stored procedure.
    
    Args:
        userid: User ID.
        categoryid: Category ID.
        month: Month number (1-12).
    
    Returns:
        Dictionary with budget status information.
    
    Raises:
        DatabaseOperationError: If the operation fails.
    """
    query = "CALL check_budget_status(%s, %s, %s)"
    try:
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Use multi=True for stored procedures
            for result in cursor.execute(query, (userid, categoryid, month), multi=True):
                if result.with_rows:
                    row = result.fetchone()
                    if row:
                        columns = [desc[0] for desc in result.description]
                        return dict(zip(columns, row))
            return {}
        finally:
            cursor.close()
            conn.close()
    except Error as exc:
        error_msg = str(exc)
        if "does not exist" in error_msg.lower():
            raise DatabaseOperationError(
                "Stored procedures are not installed. Please run:\n"
                "  mysql -u root -p expense_tracker < database/triggers.sql\n"
                "  mysql -u root -p expense_tracker < database/procedures.sql\n"
                "Or use: INSTALL_SQL.bat",
                exc
            ) from exc
        raise DatabaseOperationError("Failed to check budget status.", exc) from exc


def get_user_alerts(userid: int, unread_only: bool = True) -> List[Dict[str, Any]]:
    """Get budget alerts for a user using stored procedure.
    
    Args:
        userid: User ID.
        unread_only: If True, return only unread alerts.
    
    Returns:
        List of alert dictionaries.
    
    Raises:
        DatabaseOperationError: If the operation fails.
    """
    query = "CALL get_user_alerts(%s, %s)"
    try:
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Use multi=True for stored procedures
            for result in cursor.execute(query, (userid, unread_only), multi=True):
                if result.with_rows:
                    rows = result.fetchall()
                    if rows:
                        columns = [desc[0] for desc in result.description]
                        return [dict(zip(columns, row)) for row in rows]
            return []
        finally:
            cursor.close()
            conn.close()
    except Error as exc:
        error_msg = str(exc)
        if "does not exist" in error_msg.lower():
            raise DatabaseOperationError(
                "Stored procedures are not installed. Please run:\n"
                "  mysql -u root -p expense_tracker < database/triggers.sql\n"
                "  mysql -u root -p expense_tracker < database/procedures.sql\n"
                "Or use: INSTALL_SQL.bat",
                exc
            ) from exc
        raise DatabaseOperationError("Failed to fetch alerts.", exc) from exc


def mark_alert_read(alertid: int) -> None:
    """Mark an alert as read using stored procedure.
    
    Args:
        alertid: Alert ID to mark as read.
    
    Raises:
        DatabaseOperationError: If the operation fails.
    """
    query = "CALL mark_alert_read(%s)"
    try:
        with db_cursor(commit=True) as (_, cursor):
            cursor.execute(query, (alertid,))
    except Error as exc:
        error_msg = str(exc)
        if "does not exist" in error_msg.lower():
            raise DatabaseOperationError(
                "Stored procedures are not installed. Please run:\n"
                "  mysql -u root -p expense_tracker < database/triggers.sql\n"
                "  mysql -u root -p expense_tracker < database/procedures.sql\n"
                "Or use: INSTALL_SQL.bat",
                exc
            ) from exc
        raise DatabaseOperationError("Failed to mark alert as read.", exc) from exc


