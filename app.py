# Top of app.py
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify # type: ignore
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user # type: ignore
from database import Balance, Transaction, db, User
import os
from datetime import datetime
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash # type: ignore

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Avoid warnings
app.secret_key = 'Danso90-flames'  # Replace with a secure key
db.init_app(app)

# Ensure all tables are created on startup
with app.app_context():
    db.create_all()  # Creates 'users' table
    # Call init_db() after db.create_all() to ensure SQLite tables are also created

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define the user_loader callback
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home route
@app.route('/')
@login_required
def home():
    # Get or create user's balance
    user_balance = Balance.query.filter_by(user_id=current_user.id).first()
    if not user_balance:
        user_balance = Balance(amount=0.0, user_id=current_user.id)
        db.session.add(user_balance)
        db.session.commit()

    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).all()
    return render_template('index.html', balance=user_balance.amount, transactions=[(t.date, t.type, t.amount) for t in transactions])

# Add Income
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
        
        balance = Balance.query.filter_by(user_id=current_user.id).first()
        if not balance:
            balance = Balance(amount=0.0, user_id=current_user.id)
            db.session.add(balance)
        
        balance.amount += amount
        transaction = Transaction(date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), type="Income", amount=amount, user_id=current_user.id)
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'balance': balance.amount,
            'transaction': {'date': transaction.date, 'type': 'Income', 'amount': amount}
        })
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid amount'}), 400

# Add Expense
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
        
        balance = Balance.query.filter_by(user_id=current_user.id).first()
        if not balance:
            balance = Balance(amount=0.0, user_id=current_user.id)
            db.session.add(balance)
        
        balance.amount -= amount
        transaction = Transaction(date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), type="Expense", amount=amount, user_id=current_user.id)
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'balance': balance.amount,
            'transaction': {'date': transaction.date, 'type': 'Expense', 'amount': amount}
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