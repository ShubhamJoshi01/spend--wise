"""Flask web application for expense tracker."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

# Add project root to path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src import analytics, auth, chatbot, operations
from src.auth import AuthenticationError, AuthorizationError, UserSession

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")  # Use environment variable in production!


def get_current_user() -> UserSession | None:
    """Get current user from session."""
    if "user" in session:
        return UserSession(**session["user"])
    return None


def require_login(f):
    """Decorator to require login."""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not get_current_user():
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def require_role(required_role: str):
    """Decorator to require specific role."""

    def decorator(f):
        from functools import wraps

        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                return redirect(url_for("login"))
            if user.role != required_role:
                return jsonify({"error": "Access denied"}), 403
            return f(*args, **kwargs)

        return decorated_function

    return decorator


# ==================== Routes ====================


@app.route("/")
def index():
    """Home page - redirect to login or dashboard."""
    user = get_current_user()
    if user:
        if user.role == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("user_dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page."""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            return render_template("login.html", error="Email and password are required")

        user_session = auth.authenticate_user(email, password)
        if user_session:
            session["user"] = {
                "userid": user_session.userid,
                "email": user_session.email,
                "name": user_session.name,
                "role": user_session.role,
            }
            if user_session.role == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("user_dashboard"))
        else:
            return render_template("login.html", error="Invalid email or password")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Logout and clear session."""
    session.clear()
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    """User registration page."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        contact = request.form.get("contact", "").strip() or None

        if not all([name, email, password]):
            return render_template("register.html", error="Name, email, and password are required")

        try:
            userid = auth.register_user(name, email, password, contact, role="user")
            return render_template("login.html", success="Registration successful! Please login.")
        except AuthenticationError as e:
            return render_template("register.html", error=str(e))

    return render_template("register.html")


# ==================== User Routes ====================


@app.route("/user/dashboard")
@require_login
def user_dashboard():
    """User dashboard."""
    user = get_current_user()
    return render_template("user/dashboard.html", user=user)


@app.route("/user/transactions")
@require_login
def user_transactions():
    """User transactions page."""
    user = get_current_user()
    return render_template("user/transactions.html", user=user)


@app.route("/user/budgets")
@require_login
def user_budgets():
    """User budgets page."""
    user = get_current_user()
    return render_template("user/budgets.html", user=user)


@app.route("/user/analytics")
@require_login
def user_analytics():
    """User analytics page."""
    user = get_current_user()
    return render_template("user/analytics.html", user=user)


@app.route("/user/chatbot")
@require_login
def user_chatbot():
    """User chatbot page."""
    user = get_current_user()
    return render_template("user/chatbot.html", user=user)


@app.route("/user/reports")
@require_login
def user_reports():
    """User reports page."""
    user = get_current_user()
    return render_template("user/reports.html", user=user)


@app.route("/user/alerts")
@require_login
def user_alerts():
    """User alerts page."""
    user = get_current_user()
    return render_template("user/alerts.html", user=user)


# ==================== Admin Routes ====================


@app.route("/admin/dashboard")
@require_login
@require_role("admin")
def admin_dashboard():
    """Admin dashboard."""
    user = get_current_user()
    return render_template("admin/dashboard.html", user=user)


@app.route("/admin/users")
@require_login
@require_role("admin")
def admin_users():
    """Admin user management page."""
    user = get_current_user()
    return render_template("admin/users.html", user=user)


@app.route("/admin/transactions")
@require_login
@require_role("admin")
def admin_transactions():
    """Admin transactions management page."""
    user = get_current_user()
    return render_template("admin/transactions.html", user=user)


@app.route("/admin/categories")
@require_login
@require_role("admin")
def admin_categories():
    """Admin categories management page."""
    user = get_current_user()
    return render_template("admin/categories.html", user=user)


# ==================== API Routes ====================


@app.route("/api/transactions", methods=["GET", "POST"])
@require_login
def api_transactions():
    """API for transactions."""
    user = get_current_user()
    if request.method == "POST":
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        # Validate required fields
        required_fields = ["categoryid", "amount", "type", "date"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"success": False, "error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
        
        try:
            from datetime import date
            from decimal import Decimal

            # Convert paymentmethod to int or None
            paymentmethod = None
            if data.get("paymentmethod"):
                try:
                    paymentmethod = int(data["paymentmethod"])
                except (ValueError, TypeError):
                    paymentmethod = None

            trans_id = operations.record_transaction(
                userid=user.userid if user.role == "user" else data.get("userid", user.userid),
                categoryid=int(data["categoryid"]),
                amount=Decimal(str(data["amount"])),
                trans_type=data["type"],
                transaction_date=date.fromisoformat(data["date"]),
                paymentmethod=paymentmethod,
            )
            return jsonify({"success": True, "trans_id": trans_id})
        except ValueError as e:
            return jsonify({"success": False, "error": f"Invalid data format: {str(e)}"}), 400
        except KeyError as e:
            return jsonify({"success": False, "error": f"Missing field: {str(e)}"}), 400
        except Exception as e:
            error_msg = str(e)
            # Note: Budget overrun errors should no longer occur since we removed the blocking trigger
            # Transactions will always be inserted, and alerts will be generated automatically
            # But we keep this check in case there are other constraints
            # Check for other database constraint errors
            if "foreign key" in error_msg.lower() or "constraint" in error_msg.lower():
                return jsonify({
                    "success": False,
                    "error": "Invalid category or payment method selected. Please check your selections."
                }), 400
            # Generic error
            import traceback
            error_details = traceback.format_exc()
            print(f"Transaction API Error: {error_details}")  # Log to console for debugging
            return jsonify({"success": False, "error": f"Error adding transaction: {error_msg}"}), 500

    # GET - return user's transactions
    try:
        from src.db import db_cursor

        query = "SELECT t.*, c.name as category_name FROM transaction t JOIN category c ON t.categoryid = c.categoryid WHERE t.userid = %s ORDER BY t.date DESC LIMIT 100"
        with db_cursor() as (_, cursor):
            cursor.execute(query, (user.userid,))
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            transactions = [dict(zip(columns, row)) for row in rows]
        return jsonify({"success": True, "transactions": transactions})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/budgets", methods=["GET", "POST"])
@require_login
def api_budgets():
    """API for budgets."""
    user = get_current_user()
    if request.method == "POST":
        data = request.get_json()
        try:
            from decimal import Decimal
            from src.db import db_cursor

            query = """
                INSERT INTO budget (userid, categoryid, limitamount, month, status)
                VALUES (%s, %s, %s, %s, %s)
            """
            with db_cursor(commit=True) as (_, cursor):
                cursor.execute(
                    query,
                    (
                        user.userid if user.role == "user" else data.get("userid", user.userid),
                        int(data["categoryid"]),
                        Decimal(str(data["limitamount"])),
                        int(data["month"]),
                        data.get("status", "active"),
                    ),
                )
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400

    # GET
    try:
        from src.db import db_cursor

        query = """
            SELECT b.*, c.name as category_name 
            FROM budget b 
            JOIN category c ON b.categoryid = c.categoryid 
            WHERE b.userid = %s 
            ORDER BY b.month DESC, b.budgetid DESC
        """
        with db_cursor() as (_, cursor):
            cursor.execute(query, (user.userid,))
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            budgets = [dict(zip(columns, row)) for row in rows]
        return jsonify({"success": True, "budgets": budgets})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/categories", methods=["GET"])
@require_login
def api_categories():
    """API for categories."""
    try:
        from src.db import db_cursor

        query = "SELECT * FROM category ORDER BY name"
        with db_cursor() as (_, cursor):
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            categories = [dict(zip(columns, row)) for row in rows]
        return jsonify({"success": True, "categories": categories})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/payment-methods", methods=["GET"])
@require_login
def api_payment_methods():
    """API for payment methods."""
    try:
        from src.db import db_cursor

        query = "SELECT * FROM paymentmethod ORDER BY type"
        with db_cursor() as (_, cursor):
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            methods = [dict(zip(columns, row)) for row in rows]
        return jsonify({"success": True, "payment_methods": methods})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/alerts", methods=["GET"])
@require_login
def api_alerts():
    """API for user alerts."""
    user = get_current_user()
    try:
        alerts = operations.get_user_alerts(user.userid, unread_only=False)
        return jsonify({"success": True, "alerts": alerts})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/chatbot/query", methods=["POST"])
@require_login
def api_chatbot_query():
    """API for chatbot queries with user context."""
    data = request.get_json()
    user_message = data.get("message", "").strip()
    user = get_current_user()

    if not user_message:
        return jsonify({"success": False, "error": "Message is required"}), 400

    try:
        # Build prompt with user context to filter queries
        prompt = chatbot.build_prompt(user_message, userid=user.userid)
        raw_response = chatbot.ask_agent(prompt)
        parsed = chatbot.parse_agent_response(raw_response)

        if not parsed:
            # Try to extract SQL even if format is slightly off
            import re
            sql_match = re.search(r'SELECT.*?;', raw_response, re.IGNORECASE | re.DOTALL)
            if sql_match:
                parsed_sql = sql_match.group(0).strip()
                # Ensure userid filter is added
                if "WHERE" in parsed_sql.upper() and "userid" not in parsed_sql.lower():
                    parsed_sql = parsed_sql.replace("WHERE", f"WHERE userid = {user.userid} AND", 1)
                elif "WHERE" not in parsed_sql.upper():
                    parsed_sql = parsed_sql.rstrip(";") + f" WHERE userid = {user.userid};"
                
                parsed = chatbot.ParsedAgentResponse(
                    sql=parsed_sql,
                    explanation="Query executed successfully"
                )
            else:
                return jsonify({
                    "success": False, 
                    "error": "Could not parse response. Please try rephrasing your question.",
                    "raw": raw_response[:200] if len(raw_response) > 200 else raw_response
                }), 400

        # Ensure userid is in the query for security
        sql_lower = parsed.sql.lower()
        if "userid" not in sql_lower and "transaction" in sql_lower:
            # Try to add userid filter
            if "where" in sql_lower:
                parsed.sql = parsed.sql.replace("WHERE", f"WHERE userid = {user.userid} AND", 1)
            else:
                parsed.sql = parsed.sql.rstrip(";") + f" WHERE userid = {user.userid};"

        rows, columns = chatbot.execute_sql(parsed.sql)
        
        # Format results better
        formatted_rows = []
        if rows:
            for row in rows:
                formatted_row = []
                for item in row:
                    if isinstance(item, (int, float)):
                        if isinstance(item, float):
                            formatted_row.append(f"{item:.2f}")
                        else:
                            formatted_row.append(str(item))
                    elif hasattr(item, 'isoformat'):  # datetime/date
                        formatted_row.append(item.isoformat())
                    else:
                        formatted_row.append(str(item) if item is not None else "")
                formatted_rows.append(formatted_row)

        return jsonify(
            {
                "success": True,
                "sql": parsed.sql,
                "explanation": parsed.explanation,
                "rows": formatted_rows,
                "columns": columns if columns else [],
                "row_count": len(formatted_rows) if formatted_rows else 0,
            }
        )
    except ValueError as e:
        # Security error
        return jsonify({"success": False, "error": str(e)}), 403
    except Exception as e:
        import traceback
        from src.logger import get_logger
        logger = get_logger("chatbot")
        logger.error(f"Chatbot error: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": f"Error processing query: {str(e)}"}), 500


@app.route("/api/analytics/summary", methods=["GET"])
@require_login
def api_analytics_summary():
    """API for analytics summary with time period support."""
    user = get_current_user()
    try:
        from src.db import db_cursor
        from datetime import datetime

        # Get time period from query parameter
        period = request.args.get("period", "last_6_months")
        
        # Build date filter based on period
        date_filters = {
            "current_month": "MONTH(date) = MONTH(CURDATE()) AND YEAR(date) = YEAR(CURDATE())",
            "last_3_months": "date >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)",
            "last_6_months": "date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)",
            "last_year": "date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)",
            "all_time": "1=1"  # No date filter
        }
        date_filter = date_filters.get(period, date_filters["last_6_months"])

        # Get totals for the selected period
        query = f"""
            SELECT 
                type,
                SUM(amount) as total
            FROM transaction
            WHERE userid = %s
              AND {date_filter}
            GROUP BY type
        """
        with db_cursor() as (_, cursor):
            cursor.execute(query, (user.userid,))
            totals = {row[0]: float(row[1]) for row in cursor.fetchall()}

        income = totals.get("income", 0.0)
        expenses = totals.get("expense", 0.0)
        savings = income - expenses

        # Top categories for the selected period
        query = f"""
            SELECT c.name, SUM(t.amount) as total
            FROM transaction t
            JOIN category c ON t.categoryid = c.categoryid
            WHERE t.userid = %s
              AND t.type = 'expense'
              AND {date_filter}
            GROUP BY c.categoryid, c.name
            ORDER BY total DESC
            LIMIT 3
        """
        with db_cursor() as (_, cursor):
            cursor.execute(query, (user.userid,))
            top_categories = [{"category": row[0], "amount": float(row[1])} for row in cursor.fetchall()]

        # Monthly trend data - adjust based on period
        if period == "current_month":
            # For current month, show daily breakdown
            query = f"""
                SELECT 
                    DATE_FORMAT(date, '%Y-%m-%d') as day,
                    type,
                    SUM(amount) as total
                FROM transaction
                WHERE userid = %s
                  AND {date_filter}
                GROUP BY day, type
                ORDER BY day ASC
            """
            trend_key = "days"
        else:
            # For other periods, show monthly breakdown
            interval_map = {
                "last_3_months": 3,
                "last_6_months": 6,
                "last_year": 12,
                "all_time": None
            }
            interval = interval_map.get(period, 6)
            
            if interval:
                query = f"""
                    SELECT 
                        DATE_FORMAT(date, '%Y-%m') as month,
                        type,
                        SUM(amount) as total
                    FROM transaction
                    WHERE userid = %s
                      AND date >= DATE_SUB(CURDATE(), INTERVAL {interval} MONTH)
                    GROUP BY month, type
                    ORDER BY month ASC
                """
            else:
                # All time - show all months
                query = """
                    SELECT 
                        DATE_FORMAT(date, '%Y-%m') as month,
                        type,
                        SUM(amount) as total
                    FROM transaction
                    WHERE userid = %s
                    GROUP BY month, type
                    ORDER BY month ASC
                """
            trend_key = "months"
        
        monthly_trends = {"income": [], "expense": [], trend_key: []}
        with db_cursor() as (_, cursor):
            cursor.execute(query, (user.userid,))
            rows = cursor.fetchall()
            period_data = {}
            for period_val, trans_type, total in rows:
                if period_val not in period_data:
                    period_data[period_val] = {"income": 0.0, "expense": 0.0}
                period_data[period_val][trans_type] = float(total)
            
            for period_val in sorted(period_data.keys()):
                monthly_trends[trend_key].append(period_val)
                monthly_trends["income"].append(period_data[period_val]["income"])
                monthly_trends["expense"].append(period_data[period_val]["expense"])

        # Category-wise spending for the selected period
        query = f"""
            SELECT c.name, SUM(t.amount) as total
            FROM transaction t
            JOIN category c ON t.categoryid = c.categoryid
            WHERE t.userid = %s
              AND t.type = 'expense'
              AND {date_filter}
            GROUP BY c.categoryid, c.name
            ORDER BY total DESC
        """
        with db_cursor() as (_, cursor):
            cursor.execute(query, (user.userid,))
            all_categories = [{"category": row[0], "amount": float(row[1])} for row in cursor.fetchall()]

        return jsonify(
            {
                "success": True,
                "income": income,
                "expenses": expenses,
                "savings": savings,
                "top_categories": top_categories,
                "monthly_trends": monthly_trends,
                "all_categories": all_categories,
                "period": period,
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

