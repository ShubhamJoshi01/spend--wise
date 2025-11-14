# Expense Tracker - DBMS Project

A comprehensive expense tracking web application built with Flask and MySQL, featuring user authentication, budget management, analytics, and an AI-powered chatbot for natural language queries.

## Features

### User Interface
- **Dashboard**: Overview of income, expenses, savings, and alerts
- **Transactions**: Add, view, and filter transactions
- **Budgets**: Create and manage monthly budgets with automatic alerts
- **Analytics**: Visual analytics with charts and spending insights
- **Chatbot**: AI-powered natural language query interface (using Ollama)
- **Reports**: Generate weekly, monthly, and category-wise reports
- **Alerts**: View budget warnings and exceeded notifications

### Admin Interface
- **Dashboard**: System overview and statistics
- **User Management**: View and manage all users
- **Transaction Management**: View all transactions across users
- **Category Management**: Add and manage expense categories

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: MySQL
- **Frontend**: HTML, CSS, JavaScript
- **AI Chatbot**: Ollama (LLM for natural language to SQL conversion)
- **Analytics**: Pandas, NumPy, Matplotlib, Scikit-learn

## Prerequisites

- Python 3.8+
- MySQL Server
- Ollama (for chatbot functionality)
  - Install from [ollama.ai](https://ollama.ai)
  - Pull the model: `ollama pull llama3`

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd pbl_dbms_project
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv project_env
   ```

3. **Activate the virtual environment:**
   - Windows:
     ```powershell
     project_env\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source project_env/bin/activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up the database:**
   - Create MySQL database: `expense_tracker`
   - Run `database/schema_dump.sql` to create tables
   - Run `database/triggers.sql` and `database/procedures.sql` to install triggers and stored procedures
   - (Optional) Run `database/data_dump.sql` for sample data

6. **Configure environment variables:**
   Create a `.env` file in the project root:
   ```env
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your_database_password
   DB_NAME=expense_tracker
   FLASK_SECRET_KEY=your-secret-key-here
   ```
   
   **Note**: The `.env` file is gitignored. Never commit sensitive credentials.

## Running the Application

1. **Start the Flask server:**
   ```bash
   python app.py
   ```

2. **Access the web interface:**
   - Open your browser and go to: `http://localhost:5000`
   - You'll be redirected to the login page

3. **First-time setup:**
   - Register a new user account from the login page
   - Or use existing credentials to login
   - For admin access, create a user with `role='admin'` in the database

## Usage

### User Login
1. Go to the login page
2. Enter your email and password
3. You'll be redirected to your dashboard

### Adding Transactions
1. Navigate to "Transactions" from the menu
2. Click "+ Add Transaction"
3. Fill in the form (type, category, amount, date, payment method)
4. Click "Add Transaction"

### Managing Budgets
1. Navigate to "Budgets"
2. Click "+ Add Budget"
3. Select category, month, and set limit amount
4. Budget alerts will automatically trigger when limits are approached or exceeded

### Using the Chatbot
1. Navigate to "Chatbot"
2. Type questions in natural language, such as:
   - "Show my total expenses this month"
   - "What did I spend on food?"
   - "Show my income for January"
3. The chatbot will convert your question to SQL and display results

### Viewing Analytics
1. Navigate to "Analytics"
2. View monthly summary, top spending categories, and trends
3. Charts are automatically generated from your transaction data

## Project Structure

```
pbl_dbms_project/
├── app.py                 # Flask web application entry point
├── main.py                # CLI entry point for testing
├── requirements.txt       # Python dependencies
├── src/                   # Source code modules
│   ├── analytics.py      # Data analysis and visualization
│   ├── auth.py           # Authentication and authorization
│   ├── chatbot.py        # AI chatbot for NL to SQL
│   ├── config.py         # Database configuration
│   ├── db.py             # Database connection utilities
│   ├── logger.py         # Logging configuration
│   └── operations.py     # High-level database operations
├── database/              # Database files
│   ├── schema_dump.sql   # Database schema
│   ├── triggers.sql      # SQL triggers
│   ├── procedures.sql    # Stored procedures
│   └── data_dump.sql     # Sample data (optional)
├── templates/             # HTML templates
│   ├── base.html         # Base template
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   ├── user/             # User interface pages
│   └── admin/            # Admin interface pages
├── static/                # Static files
│   ├── css/              # Stylesheets
│   └── js/               # JavaScript files
└── tests/                 # Test files
    └── test_chatbot.py   # Chatbot tests
```

## Database Setup

The application uses MySQL with the following key components:

- **Tables**: Users, transactions, budgets, categories, login credentials
- **Triggers**: Automatic budget monitoring and alert generation
- **Stored Procedures**: Budget status checks and alert management

See `PROJECT_STRUCTURE.md` for detailed database schema information.

## Security Notes

- **Never commit sensitive data**: The `.env` file is gitignored
- **Change the secret key**: Use a strong `FLASK_SECRET_KEY` in production
- **Use environment variables**: All sensitive configuration should use environment variables
- **HTTPS in production**: Always use HTTPS in production deployments
- **Database credentials**: Never hardcode database passwords

## Development

### Running in Development Mode
```bash
export FLASK_ENV=development
python app.py
```

### Running Tests
```bash
python -m pytest tests/
```

## Troubleshooting

### Database Connection Issues
- Check database credentials in environment variables
- Ensure MySQL server is running
- Verify database `expense_tracker` exists
- Check that all SQL scripts have been executed

### Stored Procedures Not Found
- Run `database/triggers.sql` and `database/procedures.sql`
- Verify procedures are installed: `python Scripts/verify_installation.py`

### Chatbot Not Working
- Ensure Ollama is installed and running
- Check that the `llama3` model is available: `ollama list`
- Verify network connectivity

### Port Already in Use
- Change port in `app.py`: `app.run(port=5001)`

## Production Deployment

For production deployment:

1. Set `debug=False` in `app.py`
2. Use a production WSGI server (e.g., Gunicorn)
3. Configure proper database connection pooling
4. Set up HTTPS
5. Use environment variables for all sensitive configuration
6. Set a strong `FLASK_SECRET_KEY`
7. Implement rate limiting for API endpoints
8. Consider adding CSRF protection

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is part of a DBMS course project.

## Additional Documentation

- `PROJECT_STRUCTURE.md` - Detailed project structure
- `QUICK_START.md` - Quick start guide
- `README_WEB.md` - Web interface documentation

