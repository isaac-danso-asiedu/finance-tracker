from flask import Flask, render_template, request, redirect, url_for
import os
from datetime import datetime

app = Flask(__name__)

# Files for storing data
BALANCE_FILE = "data.txt"
TRANSACTIONS_FILE = "transactions.txt"

# Read balance from file
def read_balance():
    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, "r") as file:
            return float(file.read().strip() or 0.0)
    return 0.0

# Write balance to file
def write_balance(balance):
    with open(BALANCE_FILE, "w") as file:
        file.write(str(balance))

# Load transactions from file
def load_transactions():
    transactions = []
    if os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, "r") as file:
            for line in file:
                parts = line.strip().split(" | ")
                if len(parts) > 1:
                    timestamp, details = parts
                    transaction_type = details.split(": GHS ")[0]
                    amount = details.split(": GHS ")[1]
                    transactions.append((timestamp, transaction_type, amount))
    return transactions

# Add transaction to file
def log_transaction(transaction_type, amount):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(TRANSACTIONS_FILE, "a") as file:
        file.write(f"{timestamp} | {transaction_type}: GHS {amount}\n")

# Home route
@app.route('/')
def index():
    balance = read_balance()
    transactions = load_transactions()
    return render_template("index.html", balance=balance, transactions=transactions)

# Add Income
@app.route('/add_income', methods=['POST'])
def add_income():
    amount = float(request.form.get("amount"))
    balance = read_balance() + amount
    write_balance(balance)
    log_transaction("Income", amount)
    return redirect(url_for("index"))

# Add Expense
@app.route('/add_expense', methods=['POST'])
def add_expense():
    amount = float(request.form.get("amount"))
    balance = read_balance()
    
    if amount > balance:
        return "Insufficient balance!", 400
    
    balance -= amount
    write_balance(balance)
    log_transaction("Expense", amount)
    return redirect(url_for("index"))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)

