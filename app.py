from flask import Flask, render_template, request, redirect, url_for # type: ignore
import os
from datetime import datetime
import sqlite3

app = Flask(__name__)

# Files for storing data
BALANCE_FILE = "data.txt"
TRANSACTIONS_FILE = "transactions.txt"

# Function to initialize the database
def init_db():
    conn = sqlite3.connect("finance_tracker.db")  # Database file
    cursor = conn.cursor()

    # Create transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL
        )
    ''')

    # Create balance table (optional)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS balance (
            id INTEGER PRIMARY KEY,
            amount REAL NOT NULL
        )
    ''')

    # Ensure balance table has one entry
    cursor.execute("SELECT COUNT(*) FROM balance")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO balance (id, amount) VALUES (1, 0)")

    conn.commit()
    conn.close()

# Call this function when the app starts
init_db()

# Read balance from file
def read_balance():
    conn = sqlite3.connect("finance_tracker.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT amount FROM balance WHERE id=1")
    balance = cursor.fetchone()[0]
    
    conn.close()
    return balance


# Write balance to file
def write_balance(amount):
    conn = sqlite3.connect("finance_tracker.db")
    cursor = conn.cursor()

    cursor.execute("UPDATE balance SET amount = ? WHERE id = 1", (amount,))
    
    conn.commit()
    conn.close()


# Load transactions from file
def load_transactions():
    conn = sqlite3.connect("finance_tracker.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT date, type, amount FROM transactions ORDER BY id DESC")
    transactions = cursor.fetchall()
    
    conn.close()
    return transactions


# Add transaction to file
def log_transaction(transaction_type, amount):
    conn = sqlite3.connect("finance_tracker.db")
    cursor = conn.cursor()
    
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO transactions (date, type, amount) VALUES (?, ?, ?)", 
                   (date, transaction_type, amount))
    
    conn.commit()
    conn.close()


# Home route
@app.route('/')
def home():
    balance = read_balance()
    transactions = load_transactions()
    return render_template('index.html', balance=balance, transactions=transactions)


# Add Income
@app.route("/add_income", methods=["POST"])
def add_income():
    amount = float(request.form["amount"])
    
    # Update balance
    balance = read_balance()
    new_balance = balance + amount
    write_balance(new_balance)

    # Log transaction
    log_transaction("Income", amount)
    
    return redirect(url_for("index"))


# Add Expense
@app.route("/add_expense", methods=["POST"])
def add_expense():
    amount = float(request.form["amount"])
    
    # Update balance
    balance = read_balance()
    new_balance = balance - amount
    write_balance(new_balance)

    # Log transaction
    log_transaction("Expense", amount)
    
    return redirect(url_for("index"))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)

