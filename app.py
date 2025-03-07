# Top of app.py
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify # type: ignore
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user # type: ignore
from database import db, User
import os
from datetime import datetime
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash # type: ignore

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance_tracker.db'
app.secret_key = 'Danso90-Flames'  # Replace with a secure key
db.init_app(app)

# Ensure all tables are created on startup
with app.app_context():
    db.create_all()  # Creates 'users' table
    # Call init_db() after db.create_all() to ensure SQLite tables are also created
    def init_db():
        conn = sqlite3.connect("finance_tracker.db")
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS balance (
                id INTEGER PRIMARY KEY,
                amount REAL NOT NULL
            )
        ''')
        cursor.execute("SELECT COUNT(*) FROM balance")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO balance (id, amount) VALUES (1, 0)")
        conn.commit()
        conn.close()
    init_db()  # Call this within app context

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def read_balance():
    conn = sqlite3.connect("finance_tracker.db")
    cursor = conn.cursor()
    cursor.execute("SELECT amount FROM balance WHERE id=1")
    balance = cursor.fetchone()[0]
    conn.close()
    return balance

def write_balance(amount):
    conn = sqlite3.connect("finance_tracker.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE balance SET amount = ? WHERE id = 1", (amount,))
    conn.commit()
    conn.close()

def load_transactions():
    conn = sqlite3.connect("finance_tracker.db")
    cursor = conn.cursor()
    cursor.execute("SELECT date, type, amount FROM transactions ORDER BY id DESC")
    transactions = cursor.fetchall()
    conn.close()
    return transactions

def log_transaction(transaction_type, amount):
    conn = sqlite3.connect("finance_tracker.db")
    cursor = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO transactions (date, type, amount) VALUES (?, ?, ?)", 
                   (date, transaction_type, amount))
    conn.commit()
    conn.close()

# Home route (unchanged)
@app.route('/')
def home():
    balance = read_balance()
    transactions = load_transactions()
    return render_template('index.html', balance=balance, transactions=transactions)

# Add Income (unchanged from previous AJAX version)
@app.route("/add_income", methods=["POST"])
@login_required
def add_income():
    data = request.get_json()
    if not data or 'amount' not in data:
        return jsonify({'success': False, 'error': 'No amount provided'}), 400
    
    try:
        amount = float(data["amount"])
        if amount <= 0:
            return jsonify({'success': False, 'error': 'Amount must be positive'}), 400
        
        balance = read_balance()
        new_balance = balance + amount
        write_balance(new_balance)
        log_transaction("Income", amount)
        
        return jsonify({
            'success': True,
            'balance': new_balance,
            'transaction': {
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'type': 'Income',
                'amount': amount
            }
        })
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid amount'}), 400

# Add Expense (unchanged from previous AJAX version)
@app.route("/add_expense", methods=["POST"])
@login_required
def add_expense():
    data = request.get_json()
    if not data or 'amount' not in data:
        return jsonify({'success': False, 'error': 'No amount provided'}), 400
    
    try:
        amount = float(data["amount"])
        if amount <= 0:
            return jsonify({'success': False, 'error': 'Amount must be positive'}), 400
        
        balance = read_balance()
        new_balance = balance - amount
        write_balance(new_balance)
        log_transaction("Expense", amount)
        
        return jsonify({
            'success': True,
            'balance': new_balance,
            'transaction': {
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'type': 'Expense',
                'amount': amount
            }
        })
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid amount'}), 400

# Register route (modified for AJAX)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Check if request is AJAX
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return jsonify({'success': False, 'message': 'Username and password are required'}), 400

            if User.query.filter_by(username=username).first():
                return jsonify({'success': False, 'message': 'Username already exists'}), 400

            new_user = User(username=username)
            new_user.password_hash = generate_password_hash(password)
            db.session.add(new_user)
            db.session.commit()

            return jsonify({'success': True, 'message': 'Registration successful! Please log in.'})
        else:
            # Fallback for non-AJAX (traditional form submission)
            username = request.form['username']
            password = request.form['password']

            if User.query.filter_by(username=username).first():
                flash('Username already exists', 'danger')
                return redirect(url_for('register'))

            new_user = User(username=username)
            new_user.password_hash = generate_password_hash(password)
            db.session.add(new_user)
            db.session.commit()

            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')

# Login route (modified for AJAX)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Check if request is AJAX
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return jsonify({'success': False, 'message': 'Username and password are required'}), 400

            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                return jsonify({'success': True, 'message': 'Login successful!', 'redirect': url_for('dashboard')})
            else:
                return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
        else:
            # Fallback for non-AJAX (traditional form submission)
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()

            if user and user.check_password(password):
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid credentials', 'danger')
                return redirect(url_for('login'))

    return render_template('login.html')

# Logout route (modified for AJAX)
@app.route('/logout', methods=['GET'])  # Changed to GET for simplicity; POST could also work
@login_required
def logout():
    logout_user()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  # Check if AJAX request
        return jsonify({'success': True, 'message': 'Logged out successfully', 'redirect': url_for('login')})
    else:
        # Fallback for non-AJAX
        flash('Logged out successfully', 'success')
        return redirect(url_for('login'))

# Dashboard route (unchanged)
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)