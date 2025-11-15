# app/models/payment.py

from datetime import datetime
from app import db

class PaymentRequest(db.Model):
    """User payment request"""
    __tablename__ = 'payment_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                       nullable=False, index=True)
    
    # Payment info
    amount = db.Column(db.Integer, nullable=False)  # VNĐ
    credits_requested = db.Column(db.Integer, nullable=False)
    package_id = db.Column(db.String(50))  # 'starter', 'basic', 'premium'
    
    payment_method = db.Column(db.String(50), nullable=False)  # 'bank_transfer', 'momo'
    
    # Proof
    proof_image_url = db.Column(db.String(500), nullable=False)
    transaction_id = db.Column(db.String(100))
    transfer_note = db.Column(db.String(200))
    
    # Status: 'pending', 'approved', 'rejected'
    status = db.Column(db.String(20), default='pending', nullable=False, index=True)
    
    # Admin review
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    reviewed_at = db.Column(db.DateTime)
    admin_note = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationship to reviewer
    reviewer = db.relationship('User', foreign_keys=[reviewed_by], backref='reviewed_payments')
    
    def __repr__(self):
        return f'<PaymentRequest {self.id} {self.amount} VNĐ {self.status}>'