"""Command-line entry point for the expense tracker project."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Callable

from src import analytics, auth, chatbot, operations


def run_chatbot() -> None:
    chatbot.chatbot_loop()


def run_analytics() -> None:
    rows = analytics.fetch_historic_data()
    data, months, categories = analytics.process_data(rows)
    fig1 = analytics.plot_monthly_spendings(data, months, categories)
    fig1.show()
    fig2 = analytics.plot_category_spendings_overall(data)
    fig2.show()

    df = analytics.fetch_dataframe()
    prepared = analytics.prepare_data(df)
    predictions = analytics.train_predict(prepared.pivot)
    fig3 = analytics.plot_spendings(prepared.pivot, predictions)
    fig3.show()
    recommendations = analytics.recommend_savings(predictions, prepared.original_df)
    for rec in recommendations:
        print(rec)


def run_database_examples() -> None:
    user_id = operations.fetch_first_id("user", "userid")
    category_id = operations.fetch_first_id("category", "categoryid")
    payment_method_id = operations.fetch_first_id("paymentmethod", "methodid")

    if user_id is None or category_id is None:
        print("Missing prerequisite data: ensure at least one user and category exist.")
        return

    new_trans_id = operations.record_transaction(
        userid=user_id,
        categoryid=category_id,
        amount=Decimal("120.50"),
        trans_type="income",
        transaction_date=date.today(),
        paymentmethod=payment_method_id,
    )
    print(f"Inserted transaction with ID: {new_trans_id}")

    operations.update_budget(budgetid=1, new_limitamount=Decimal("5000"), new_status="active")
    print("Budget updated.")

    summary = operations.view_user_summary(userid=user_id)
    print("User Summary:")
    for item in summary:
        print(f"- {item.category}: {item.total_amount}")


def run_auth_examples() -> None:
    """Demonstrate authentication and alert functionality."""
    print("\n=== Authentication Demo ===\n")
    
    # Try to authenticate with existing user
    print("1. Attempting to authenticate...")
    email = input("Enter email (or press Enter to skip): ").strip()
    if not email:
        print("Skipping authentication demo.")
        return
    
    password = input("Enter password: ").strip()
    session = auth.authenticate_user(email, password)
    
    if session:
        print(f"✓ Authenticated as: {session.name} (ID: {session.userid}, Role: {session.role})")
        
        # Show alerts
        print("\n2. Checking budget alerts...")
        alerts = operations.get_user_alerts(session.userid, unread_only=True)
        if alerts:
            print(f"Found {len(alerts)} unread alert(s):")
            for alert in alerts:
                print(f"  - [{alert['alert_type'].upper()}] {alert['message']}")
        else:
            print("No unread alerts.")
        
        # Check budget status
        print("\n3. Checking budget status...")
        category_id = operations.fetch_first_id("category", "categoryid")
        if category_id:
            try:
                budget_status = operations.check_budget_status(
                    userid=session.userid,
                    categoryid=category_id,
                    month=date.today().month
                )
                if budget_status:
                    print(f"Budget Status:")
                    print(f"  Limit: {budget_status.get('limit_amount', 'N/A')}")
                    print(f"  Spent: {budget_status.get('spent_amount', 'N/A')}")
                    print(f"  Remaining: {budget_status.get('remaining_amount', 'N/A')}")
                    print(f"  Alert Level: {budget_status.get('alert_level', 'N/A')}")
            except Exception as e:
                print(f"Error checking budget: {e}")
    else:
        print("✗ Authentication failed. Invalid email or password.")
        print("\nNote: You can register a new user using the auth module directly.")


def main() -> None:
    actions: dict[str, Callable[[], None]] = {
        "1": run_chatbot,
        "2": run_analytics,
        "3": run_database_examples,
        "4": run_auth_examples,
    }

    print("Select an option:")
    print("1. Chatbot")
    print("2. Analytics")
    print("3. Database operations demo")
    print("4. Authentication & Alerts demo")

    choice = input("Enter choice (1/2/3/4): ").strip()
    action = actions.get(choice)
    if not action:
        print("Invalid choice.")
        return
    action()


if __name__ == "__main__":
    main()







