# app/models/user.py

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

class User(UserMixin, db.Model):
    """User model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    
    # Role: 'admin' or 'user'
    role = db.Column(db.String(20), default='user', nullable=False, index=True)
    
    # Credits
    credits = db.Column(db.Integer, default=10, nullable=False)  # 10 free credits
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    vocabulary_progress = db.relationship('UserVocabularyProgress', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    listening_attempts = db.relationship('ListeningAttempt', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    reading_attempts = db.relationship('ReadingAttempt', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    speaking_submissions = db.relationship('SpeakingSubmission', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    writing_submissions = db.relationship('WritingSubmission', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    payment_requests = db.relationship('PaymentRequest', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'
    
    def has_credits(self, amount=1):
        """Check if user has enough credits"""
        return self.credits >= amount
    
    def deduct_credits(self, amount, reference_type, reference_id, note=''):
        """Deduct credits and log transaction"""
        if not self.has_credits(amount):
            raise ValueError('Insufficient credits')
        
        old_balance = self.credits
        self.credits -= amount
        
        # Log transaction
        transaction = Transaction(
            user_id=self.id,
            type='usage',
            amount=-amount,
            balance_after=self.credits,
            reference_type=reference_type,
            reference_id=reference_id,
            note=note
        )
        db.session.add(transaction)
        return transaction
    
    def add_credits(self, amount, reference_type, reference_id, note=''):
        """Add credits and log transaction"""
        old_balance = self.credits
        self.credits += amount
        
        transaction = Transaction(
            user_id=self.id,
            type='topup',
            amount=amount,
            balance_after=self.credits,
            reference_type=reference_type,
            reference_id=reference_id,
            note=note
        )
        db.session.add(transaction)
        return transaction
    
    def get_rate_limit(self):
        """Get rate limit based on credit balance"""
        from flask import current_app
        if self.credits > 0:
            return current_app.config['RATE_LIMIT_PAID']
        return current_app.config['RATE_LIMIT_FREE']
    
    def __repr__(self):
        return f'<User {self.email}>'


class Transaction(db.Model):
    """Transaction log for credits"""
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Type: 'topup', 'usage', 'refund', 'bonus'
    type = db.Column(db.String(20), nullable=False, index=True)
    
    # Amount (positive for topup, negative for usage)
    amount = db.Column(db.Integer, nullable=False)
    balance_after = db.Column(db.Integer, nullable=False)
    
    # Reference
    reference_type = db.Column(db.String(50))  # 'payment', 'writing', 'speaking', etc.
    reference_id = db.Column(db.Integer)
    
    note = db.Column(db.String(200))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f'<Transaction {self.type} {self.amount} credits>'


@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    return User.query.get(int(user_id))