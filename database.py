# database.py
from flask_sqlalchemy import SQLAlchemy # type: ignore
from flask_login import UserMixin # type: ignore
from werkzeug.security import check_password_hash # type: ignore

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'  # Explicitly name the table
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)