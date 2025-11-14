"""Interactive SQL chatbot powered by Ollama."""

from __future__ import annotations

import json
import subprocess
import textwrap
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from mysql.connector import Error

from .db import db_cursor
from .logger import get_logger

logger = get_logger("chatbot")


def ask_agent(prompt: str, model: str = "llama3") -> str:
    """Invoke the Ollama model with the provided prompt."""
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt.encode("utf-8"),
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"Ollama invocation failed with exit code {exc.returncode}: {exc.stderr.decode('utf-8', 'ignore')}"
        ) from exc
    return result.stdout.decode("utf-8").strip()


def fetch_schema(table_name: str) -> List[Dict[str, str | None]]:
    """Return schema metadata for the given table."""
    with db_cursor() as (_, cursor):
        cursor.execute(f"DESCRIBE {table_name}")
        rows = cursor.fetchall()
    schema = [
        {
            "field": row[0],
            "type": row[1],
            "null": row[2],
            "key": row[3],
            "default": row[4],
            "extra": row[5],
        }
        for row in rows
    ]
    return schema


def format_schema_for_prompt(table_name: str) -> str:
    """Serialize schema as JSON for prompt injection."""
    schema = fetch_schema(table_name)
    return json.dumps({table_name: schema}, indent=4)


def build_prompt(user_message: str, userid: int | None = None) -> str:
    """Build the LLM prompt including schemas and instructions.
    
    Args:
        user_message: The user's natural language query.
        userid: Optional user ID to filter queries by user.
    """
    transaction_schema = format_schema_for_prompt("transaction")
    category_schema = format_schema_for_prompt("category")
    
    user_filter_note = ""
    if userid is not None:
        user_filter_note = f"""
        IMPORTANT: All queries must filter by userid = {userid} to show only the current user's data.
        Always include "WHERE userid = {userid}" (or add it to existing WHERE clauses with AND).
        """
    
    return textwrap.dedent(
        f"""
        You are a SQL assistant connected to a MySQL database for an expense tracking application.

        Database schema:
        1. Transaction Table: {transaction_schema}
        2. Category Table: {category_schema}

        {user_filter_note}

        You have complete knowledge of the schema above. The user is not allowed to provide additional schema details.
        You must use only the tables and columns listed. Assume expenses are stored in the `transaction` table and categories in `category`.

        RESPONSE FORMAT (mandatory):
        SQL: <one fully-formed SQL statement using the schema above>
        Output: <brief natural-language summary of what the query returns>

        RULES (enforced, do not violate):
        - Never ask the user for schema information or clarifications—always produce the best possible SQL with the given schema.
        - Always use the exact table and column names from the schema.
        - Prefer joins between `transaction` and `category` tables when category names are involved.
        - Use aggregate functions (SUM, MAX, MIN, AVG, COUNT) when requested.
        - For filters like dates or categories, include appropriate WHERE clauses.
        - For date filters, use functions like MONTH(date), YEAR(date), DATE_FORMAT(date, '%Y-%m'), etc.
        - Ensure every SELECT list column is either aggregated or appears in the GROUP BY clause (MySQL ONLY_FULL_GROUP_BY).
        - Never use SELECT * in queries that include GROUP BY; explicitly list required columns.
        - When the user greets without a request, reply with a short greeting and stop (no SQL).
        - Otherwise ALWAYS return both the SQL and Output lines exactly once.
        - Do not wrap the SQL in markdown code fences.
        - Use proper SQL syntax with semicolons at the end.

        EXAMPLES:
        User: "Show my total expenses this month"
        SQL: SELECT SUM(amount) AS total_expense FROM transaction WHERE type = 'expense' AND userid = {userid if userid else 'X'} AND MONTH(date) = MONTH(CURDATE()) AND YEAR(date) = YEAR(CURDATE());
        Output: Shows the total amount of all expense transactions for the current month.

        User: "What did I spend on food?"
        SQL: SELECT SUM(t.amount) AS total_spent FROM transaction t JOIN category c ON t.categoryid = c.categoryid WHERE t.userid = {userid if userid else 'X'} AND t.type = 'expense' AND c.name LIKE '%Food%';
        Output: Shows the total amount spent on food-related categories.

        User request:
        {user_message}
        """
    ).strip()


@dataclass
class ParsedAgentResponse:
    sql: str
    explanation: str


def parse_agent_response(response: str) -> Optional[ParsedAgentResponse]:
    """Extract SQL and explanation from the LLM response."""
    sql_marker = "SQL:"
    output_marker = "Output:"
    if sql_marker not in response:
        return None
    sql_start = response.find(sql_marker) + len(sql_marker)
    output_start = response.find(output_marker, sql_start)
    if output_start == -1:
        return None
    sql = response[sql_start:output_start].strip().strip("`")
    explanation = response[output_start + len(output_marker) :].strip()
    if "\nSQL:" in sql:
        return None
    if not sql:
        return None
    return ParsedAgentResponse(sql=sql, explanation=explanation)


def execute_sql(sql: str) -> Tuple[Optional[List[Tuple]], Optional[List[str]]]:
    """Execute SQL and return rows plus column names when available."""
    dangerous_keywords = {"DROP", "TRUNCATE"}
    upper_sql = sql.upper()
    if any(keyword in upper_sql for keyword in dangerous_keywords):
        raise ValueError("Destructive SQL statements are not permitted.")

    with db_cursor(commit=True) as (conn, cursor):
        logger.debug("Executing SQL: %s", sql)
        cursor.execute(sql)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            return rows, columns
        # no resultset, commit already handled via context
        return None, None


def chatbot_loop(input_func=input, print_func=print) -> None:
    """Run the interactive chatbot session."""
    print_func("Bot: Hello! SQL assistant ready. Type 'exit' to quit.")
    while True:
        user_message = input_func("You: ").strip()
        if user_message.lower() in {"exit", "quit"}:
            print_func("Bot: Goodbye!")
            break
        if not user_message:
            continue

        prompt = build_prompt(user_message)
        attempts = 0
        parsed: Optional[ParsedAgentResponse] = None

        while attempts < 2:
            logger.debug("Prompt to model (attempt %s):\n%s", attempts + 1, prompt)
            try:
                raw_response = ask_agent(prompt)
            except RuntimeError as err:
                print_func(f"Bot: Model error → {err}")
                logger.error("Model invocation failed: %s", err)
                break

            logger.debug("Raw model response:\n%s", raw_response)
            print_func(f"Bot (raw): {raw_response}")
            parsed = parse_agent_response(raw_response)
            if not parsed:
                logger.warning("Failed to parse response on attempt %s: %s", attempts + 1, raw_response)
                if attempts == 0:
                    prompt += (
                        "\n\nReminder: Respond strictly with the `SQL:` and `Output:` format. "
                        "If the request needs aggregation, follow the rules provided."
                    )
                    attempts += 1
                    continue
                print_func("Bot: Unable to parse agent response.")
                break

            sql_upper = parsed.sql.upper()
            if "GROUP BY" in sql_upper and "SELECT *" in sql_upper:
                logger.warning("Detected SELECT * with GROUP BY. Requesting rewrite.")
                if attempts == 0:
                    prompt += (
                        "\n\nReminder: Do NOT use SELECT * when GROUP BY is present. "
                        "List only aggregated columns and group keys."
                    )
                    attempts += 1
                    continue
                print_func("Bot: Generated SQL is invalid (SELECT * used with GROUP BY). Please rephrase your request.")
                parsed = None
                break

            break  # parsed successfully

        if not parsed:
            continue

        print_func(f"Bot SQL:\n{parsed.sql}")
        if parsed.explanation:
            print_func(f"Bot Explanation:\n{parsed.explanation}")
        else:
            print_func("Bot: (No explanation provided by model.)")
            logger.warning("Missing explanation for response.")

        try:
            rows, columns = execute_sql(parsed.sql)
        except (ValueError, Error) as err:
            print_func(f"Bot: SQL execution error → {err}")
            logger.error("SQL execution error: %s", err)
            continue

        if rows is None:
            print_func("Bot: Statement executed successfully.")
        elif rows:
            print_func(f"Bot: Actual Output ({len(rows)} rows)")
            print_rows(rows, columns or [])
        else:
            print_func("Bot: Query returned no rows.")


def print_rows(rows: List[Tuple], columns: List[str]) -> None:
    """Print rows in a simple tabular format."""
    if columns:
        header = " | ".join(columns)
        print(header)
        print("-" * len(header))
    for row in rows:
        print(" | ".join(str(item) for item in row))


