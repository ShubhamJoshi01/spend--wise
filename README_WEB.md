# Expense Tracker Web Application

A complete web interface for the Expense Tracker application with separate user and admin interfaces.

## Features

### User Interface
- **Dashboard**: Overview of income, expenses, savings, and alerts
- **Transactions**: Add, view, and filter transactions
- **Budgets**: Create and manage monthly budgets
- **Analytics**: Visual analytics with charts and insights
- **Chatbot**: AI-powered natural language query interface
- **Reports**: Generate weekly, monthly, and category-wise reports
- **Alerts**: View budget warnings and exceeded notifications

### Admin Interface
- **Dashboard**: System overview and statistics
- **User Management**: View and manage users
- **Transaction Management**: View all transactions
- **Category Management**: Add and manage expense categories

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure MySQL database is set up:**
   - Database should be created and configured
   - SQL triggers and procedures should be installed (see `INSTALL_SQL.md`)

3. **Configure database (if needed):**
   - Update `src/config.py` with your database credentials
   - Or set environment variables: `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`

## Running the Application

1. **Start the Flask server:**
   ```bash
   python app.py
   ```

2. **Access the web interface:**
   - Open your browser and go to: `http://localhost:5000`
   - You'll be redirected to the login page

3. **First-time setup:**
   - Register a new user account
   - Or use existing credentials to login
   - For admin access, create a user with role='admin' in the database

## Usage

### User Login
1. Go to the login page
2. Enter your email and password
3. You'll be redirected to your dashboard

### Adding Transactions
1. Navigate to "Transactions" from the menu
2. Click "+ Add Transaction"
3. Fill in the form:
   - Select type (Income/Expense)
   - Choose category
   - Enter amount
   - Select date
   - Choose payment method (optional)
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

### Admin Features
- Login with an admin account
- Access admin dashboard for system management
- Manage users, view all transactions, and manage categories

## Project Structure

```
project_env/
├── app.py                 # Flask application
├── templates/            # HTML templates
│   ├── base.html        # Base template
│   ├── login.html       # Login page
│   ├── register.html    # Registration page
│   ├── user/           # User interface pages
│   │   ├── dashboard.html
│   │   ├── transactions.html
│   │   ├── budgets.html
│   │   ├── analytics.html
│   │   ├── chatbot.html
│   │   ├── reports.html
│   │   └── alerts.html
│   └── admin/          # Admin interface pages
│       ├── dashboard.html
│       ├── users.html
│       ├── transactions.html
│       └── categories.html
├── static/             # Static files
│   ├── css/
│   │   └── style.css  # Main stylesheet
│   └── js/
│       └── main.js    # Common JavaScript
└── src/               # Backend modules
    ├── auth.py       # Authentication
    ├── operations.py # Database operations
    ├── chatbot.py    # Chatbot functionality
    └── analytics.py  # Analytics
```

## Security Notes

- Change the `app.secret_key` in `app.py` for production
- Use environment variables for database credentials
- Implement HTTPS in production
- Add rate limiting for API endpoints
- Consider adding CSRF protection

## Troubleshooting

### Database Connection Issues
- Check database credentials in `src/config.py`
- Ensure MySQL server is running
- Verify database `expense_tracker` exists

### Stored Procedures Not Found
- Run SQL installation scripts (see `INSTALL_SQL.md`)
- Verify procedures are installed: `python Scripts/verify_installation.py`

### Chatbot Not Working
- Ensure Ollama is installed and running
- Check that the `llama3` model is available
- Verify network connectivity

## Development

To run in development mode with auto-reload:
```bash
export FLASK_ENV=development
python app.py
```

## Production Deployment

For production:
1. Set `debug=False` in `app.py`
2. Use a production WSGI server (e.g., Gunicorn)
3. Configure proper database connection pooling
4. Set up HTTPS
5. Use environment variables for sensitive configuration

