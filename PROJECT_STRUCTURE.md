# Project Structure

This document describes the structure of the Expense Tracker project.

## Core Application Files

- `app.py` - Main Flask web application (entry point for web interface)
- `main.py` - CLI entry point for testing features (chatbot, analytics, database operations)
- `requirements.txt` - Python dependencies

## Source Code (`src/`)

- `analytics.py` - Data analysis and visualization functions
- `auth.py` - Authentication and authorization (password hashing, login, registration)
- `chatbot.py` - AI chatbot for natural language to SQL conversion
- `config.py` - Database configuration
- `db.py` - Database connection utilities
- `logger.py` - Logging configuration
- `operations.py` - High-level database operations (transactions, budgets, summaries)

## Database (`database/`)

- `schema_dump.sql` - Database schema (tables, relationships)
- `triggers.sql` - SQL triggers for budget monitoring and alerts
- `procedures.sql` - Stored procedures for budget status and alerts
- `data_dump.sql` - Sample data (optional, for testing)

## Web Interface

### Templates (`templates/`)

- `base.html` - Base template with navigation
- `login.html` - User login page
- `register.html` - User registration page

#### User Templates (`templates/user/`)
- `dashboard.html` - User dashboard
- `transactions.html` - Transaction management
- `budgets.html` - Budget management
- `analytics.html` - Analytics and insights
- `chatbot.html` - AI chatbot interface
- `reports.html` - Reports
- `alerts.html` - Budget alerts

#### Admin Templates (`templates/admin/`)
- `dashboard.html` - Admin dashboard
- `users.html` - User management
- `transactions.html` - Transaction management
- `categories.html` - Category management

### Static Files (`static/`)

- `css/style.css` - Application styles
- `js/main.js` - JavaScript utilities

## Scripts (`Scripts/`)

**Note:** The `Scripts/` folder contains both virtual environment scripts (necessary for Python venv) and project utility scripts.

### Project Utility Scripts:
- `install_triggers_procedures.py` - Install SQL triggers and procedures
- `verify_installation.py` - Verify database setup
- `show_users.py` - Display existing users
- `reset_user_password.py` - Reset user password
- `ensure_demo_data.py` - Create demo data
- `export_data.py` - Export database data
- `export_schema.py` - Export database schema

### Virtual Environment Scripts (DO NOT DELETE):
- `activate`, `activate.bat`, `Activate.ps1` - Virtual environment activation
- `python.exe`, `pip.exe` - Python executables
- Other venv executables

## Installation Files

- `INSTALL_SQL.bat` - Batch script to install SQL triggers/procedures
- `INSTALL_SQL.md` - Installation guide for SQL components
- `QUICK_START.md` - Quick start guide
- `README_WEB.md` - Web interface documentation

## Tests (`tests/`)

- `test_chatbot.py` - Chatbot functionality tests

## Running the Application

### Web Interface:
```bash
python app.py
```
Then open http://localhost:5000 in your browser.

### CLI Interface:
```bash
python main.py
```

## Database Setup

1. Create MySQL database: `expense_tracker`
2. Run `database/schema_dump.sql` to create tables
3. Run `INSTALL_SQL.bat` or follow `INSTALL_SQL.md` to install triggers and procedures
4. (Optional) Run `database/data_dump.sql` for sample data

