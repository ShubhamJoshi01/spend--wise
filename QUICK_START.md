# Quick Start Guide

## 🚀 Start the Web Application

1. **Open terminal in project directory:**
   ```powershell
   cd C:\pbl_dbms_project\project_env
   ```

2. **Start the Flask server:**
   ```powershell
   python app.py
   ```

3. **Open your browser:**
   - Go to: `http://localhost:5000`
   - You'll see the login page

## 👤 First Time Setup

### Option 1: Register New User
1. Click "Register here" on login page
2. Fill in your details
3. Click "Register"
4. Login with your new credentials

### Option 2: Use Existing User
- Use existing email/password from database
- Or create admin user directly in database:
  ```sql
  INSERT INTO user (name, email, contact) VALUES ('Admin', 'admin@example.com', '1234567890');
  INSERT INTO login (userid, password, role) VALUES (LAST_INSERT_ID(), 'your_hashed_password', 'admin');
  ```

## 📋 Available Features

### User Features (After Login)
- **Dashboard**: Overview of finances
- **Transactions**: Add/view transactions
- **Budgets**: Set monthly budgets
- **Analytics**: View spending insights
- **Chatbot**: Ask questions in natural language
- **Reports**: Generate financial reports
- **Alerts**: View budget warnings

### Admin Features (Admin Role)
- **Dashboard**: System overview
- **Users**: Manage all users
- **Transactions**: View all transactions
- **Categories**: Manage expense categories

## 🎯 Quick Test

1. Login to the application
2. Go to "Transactions" → Click "+ Add Transaction"
3. Add a test transaction
4. Go to "Dashboard" to see it reflected
5. Go to "Chatbot" and ask: "Show my total expenses this month"

## ⚠️ Troubleshooting

**Port already in use?**
- Change port in `app.py`: `app.run(port=5001)`

**Database connection error?**
- Check `src/config.py` for correct credentials
- Ensure MySQL is running

**Chatbot not working?**
- Ensure Ollama is installed and running
- Model `llama3` should be available

## 📝 Next Steps

- Add more transactions to see analytics
- Create budgets to test alert system
- Try different chatbot queries
- Explore all features in the menu

