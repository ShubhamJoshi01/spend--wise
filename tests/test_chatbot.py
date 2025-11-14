from __future__ import annotations

import sys
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src import chatbot  


class ParseAgentResponseTests(unittest.TestCase):
    def test_valid_response(self):
        response = (
            "SQL: SELECT SUM(amount) FROM transaction WHERE type = 'expense';\n"
            "Output: Totals expenses."
        )
        parsed = chatbot.parse_agent_response(response)
        self.assertIsNotNone(parsed)
        self.assertEqual(
            parsed.sql, "SELECT SUM(amount) FROM transaction WHERE type = 'expense';"
        )
        self.assertEqual(parsed.explanation, "Totals expenses.")

    def test_missing_markers_returns_none(self):
        response = "SELECT * FROM transaction;"
        parsed = chatbot.parse_agent_response(response)
        self.assertIsNone(parsed)

    def test_multiple_sql_markers(self):
        response = (
            "SQL: SELECT * FROM transaction;\n"
            "SQL: SELECT * FROM category;\n"
            "Output: ..."
        )
        parsed = chatbot.parse_agent_response(response)
        self.assertIsNone(parsed)


class ExecuteSqlGuardsTests(unittest.TestCase):
    def test_drop_statement_rejected(self):
        with self.assertRaises(ValueError):
            chatbot.execute_sql("DROP TABLE user;")


if __name__ == "__main__":
    unittest.main()





