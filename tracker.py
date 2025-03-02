import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime

# Files for storing data
BALANCE_FILE = "data.txt"
TRANSACTIONS_FILE = "transactions.txt"

# List of expense categories
expense_categories = ["Food", "Transport", "Bills", "Entertainment", "Others"]

# Function to read balance from file
def read_balance():
    try:
        if os.path.exists(BALANCE_FILE):
            with open(BALANCE_FILE, "r") as file:
                return float(file.read().strip() or 0.0)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read balance: {e}")
    return 0.0

# Function to write balance to file
def write_balance(balance):
    try:
        with open(BALANCE_FILE, "w") as file:
            file.write(str(balance))
    except Exception as e:
        messagebox.showerror("Error", f"Failed to write balance: {e}")

# Function to log transactions
def log_transaction(transaction_type, amount, category=None):
    try:
        with open(TRANSACTIONS_FILE, "a") as file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if category:
                file.write(f"{timestamp} | {transaction_type} ({category}): GHS {amount}\n")
            else:
                file.write(f"{timestamp} | {transaction_type}: GHS {amount}\n")
        load_transactions()
        update_summary()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to log transaction: {e}")

# Function to load transactions
def load_transactions():
    try:
        for row in transaction_table.get_children():
            transaction_table.delete(row)
        
        if os.path.exists(TRANSACTIONS_FILE):
            with open(TRANSACTIONS_FILE, "r") as file:
                for line in file:
                    parts = line.strip().split(" | ")
                    if len(parts) > 1:
                        timestamp, details = parts
                        transaction_type = details.split(": GHS ")[0]
                        amount = details.split(": GHS ")[1]
                        transaction_table.insert("", tk.END, values=(timestamp, transaction_type, amount))
        update_summary()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load transactions: {e}")

# Function to delete selected transaction
def delete_transaction():
    selected_item = transaction_table.selection()
    if not selected_item:
        messagebox.showerror("Error", "Please select a transaction to delete!")
        return
    
    transaction_values = transaction_table.item(selected_item, "values")
    timestamp, transaction_type, amount = transaction_values
    
    try:
        with open(TRANSACTIONS_FILE, "r") as file:
            lines = file.readlines()
        
        with open(TRANSACTIONS_FILE, "w") as file:
            for line in lines:
                if not line.startswith(timestamp):
                    file.write(line)
        
        transaction_table.delete(selected_item)
        update_summary()
        messagebox.showinfo("Success", "Transaction deleted successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete transaction: {e}")

# Function to update financial summary
def update_summary():
    total_income = 0
    total_expense = 0
    
    try:
        if os.path.exists(TRANSACTIONS_FILE):
            with open(TRANSACTIONS_FILE, "r") as file:
                for line in file:
                    parts = line.strip().split(" | ")
                    if len(parts) > 1:
                        details = parts[1]
                        amount = float(details.split(": GHS ")[1])
                        if "Income" in details:
                            total_income += amount
                        elif "Expense" in details:
                            total_expense += amount
        
        net_savings = total_income - total_expense
        label_summary.config(text=f"Total Income: GHS {total_income}\nTotal Expenses: GHS {total_expense}\nNet Savings: GHS {net_savings}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to update summary: {e}")

# Initialize balance from file
balance = read_balance()

# Initialize main window
root = tk.Tk()
root.title("Personal Finance Tracker")
root.geometry("700x600")
root.configure(bg="#f0f0f0")

# Balance Label
label_balance = tk.Label(root, text=f"Current Balance: GHS {balance}", font=("Arial", 14, "bold"), bg="#f0f0f0")
label_balance.pack(pady=10)

# Financial Summary Label
label_summary = tk.Label(root, text="", font=("Arial", 12, "bold"), bg="#f0f0f0", justify=tk.LEFT)
label_summary.pack(pady=10)

# Transactions Table with Scrollbar
frame_table = tk.Frame(root, bg="#f0f0f0")
frame_table.pack(pady=20)

scrollbar = ttk.Scrollbar(frame_table, orient=tk.VERTICAL)
transaction_table = ttk.Treeview(frame_table, columns=("Date", "Type", "Amount"), show="headings", yscrollcommand=scrollbar.set)
scrollbar.config(command=transaction_table.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

for col in ("Date", "Type", "Amount"):
    transaction_table.heading(col, text=col)
    transaction_table.column(col, width=200)
transaction_table.pack()

# Buttons
btn_frame = tk.Frame(root, bg="#f0f0f0")
btn_frame.pack(pady=10)
tk.Button(btn_frame, text="Add Income", command=add_income, font=("Arial", 12), bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame, text="Add Expense", command=add_expense, font=("Arial", 12), bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=5)

load_transactions()
root.mainloop()
