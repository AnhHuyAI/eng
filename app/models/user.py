# app/models/user.py

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

class User(UserMixin, db.Model):
    """User model - Supports admin, teacher, and student roles"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))

    # Role: 'admin', 'teacher', or 'student'
    role = db.Column(db.String(20), default='student', nullable=False, index=True)

    # Teacher-specific fields
    center_name = db.Column(db.String(200))  # For teachers: center/institution name
    phone = db.Column(db.String(20))
    address = db.Column(db.String(500))
    tax_code = db.Column(db.String(50))  # For invoicing
    website = db.Column(db.String(200))

    # Credits (for teachers - students use teacher's credits)
    credits = db.Column(db.Integer, default=0, nullable=False)

    # For students: which teacher they belong to
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), index=True)

    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False)

    # Approval (for teachers)
    approved_at = db.Column(db.DateTime)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime)

    # Relationships

    # For teachers: their students
    students = db.relationship('User',
                              backref=db.backref('teacher', remote_side=[id]),
                              foreign_keys=[teacher_id],
                              lazy='dynamic')

    # For teachers: their classes (defined in class_management.py)
    # teacher_classes relationship will be added when TeacherClass model is created

    # For teachers: assignments they created (defined in assignment.py)
    # created_assignments relationship will be added when Assignment model is created

    # Student progress
    vocabulary_progress = db.relationship('UserVocabularyProgress', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    listening_attempts = db.relationship('ListeningAttempt', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    reading_attempts = db.relationship('ReadingAttempt', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    speaking_submissions = db.relationship('SpeakingSubmission', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    writing_submissions = db.relationship('WritingSubmission', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    # Payment & transactions
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

    def is_teacher(self):
        """Check if user is teacher"""
        return self.role == 'teacher'

    def is_student(self):
        """Check if user is student"""
        return self.role == 'student'

    def has_credits(self, amount=1):
        """Check if user/teacher has enough credits"""
        if self.is_student() and self.teacher:
            # Students use their teacher's credits
            return self.teacher.credits >= amount
        return self.credits >= amount

    def deduct_credits(self, amount, reference_type, reference_id, note=''):
        """Deduct credits and log transaction"""
        # For students, deduct from teacher's credits
        if self.is_student() and self.teacher:
            target_user = self.teacher
            note = f"{note} (Student: {self.full_name or self.email})"
        else:
            target_user = self

        if not target_user.has_credits(amount):
            raise ValueError('Insufficient credits')

        target_user.credits -= amount

        # Log transaction
        transaction = Transaction(
            user_id=target_user.id,
            type='usage',
            amount=-amount,
            balance_after=target_user.credits,
            reference_type=reference_type,
            reference_id=reference_id,
            note=note
        )
        db.session.add(transaction)
        return transaction

    def add_credits(self, amount, reference_type, reference_id, note=''):
        """Add credits and log transaction"""
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

    def get_credits_balance(self):
        """Get effective credits balance (for students, return teacher's balance)"""
        if self.is_student() and self.teacher:
            return self.teacher.credits
        return self.credits

    def __repr__(self):
        return f'<User {self.role}: {self.email}>'


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
