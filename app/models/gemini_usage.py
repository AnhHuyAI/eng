# app/models/gemini_usage.py

from datetime import datetime
from app import db


class GeminiUsage(db.Model):
    """Track Gemini API usage for cost monitoring"""
    __tablename__ = 'gemini_usage'

    id = db.Column(db.Integer, primary_key=True)

    # User (teacher who owns the credits)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                       nullable=False, index=True)

    # Submission reference
    submission_type = db.Column(db.String(50), nullable=False, index=True)
    # 'writing_task1', 'writing_task2', 'speaking'

    submission_id = db.Column(db.Integer, nullable=False, index=True)
    # FK to WritingSubmission or SpeakingSubmission

    # Token usage
    input_tokens = db.Column(db.Integer, nullable=False)
    output_tokens = db.Column(db.Integer, nullable=False)
    total_tokens = db.Column(db.Integer, nullable=False)

    # Cost calculation
    estimated_cost_usd = db.Column(db.Float, nullable=False)

    # Model used
    model_name = db.Column(db.String(100), nullable=False)  # 'gemini-1.5-flash', 'gemini-1.5-pro'

    # Performance
    response_time_ms = db.Column(db.Integer)  # Milliseconds

    # Status
    success = db.Column(db.Boolean, default=True, nullable=False)
    error_message = db.Column(db.Text)

    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = db.relationship('User', backref='gemini_usage_logs')

    @staticmethod
    def calculate_cost(input_tokens, output_tokens, model_name='gemini-1.5-flash'):
        """Calculate cost based on token usage"""
        # Gemini pricing (as of 2024)
        pricing = {
            'gemini-1.5-flash': {
                'input': 0.00001875 / 1000,   # per token
                'output': 0.000075 / 1000,
            },
            'gemini-1.5-pro': {
                'input': 0.00125 / 1000,
                'output': 0.005 / 1000,
            },
            'gemini-2.0-flash-exp': {  # Latest model
                'input': 0.00001875 / 1000,
                'output': 0.000075 / 1000,
            }
        }

        model_pricing = pricing.get(model_name, pricing['gemini-1.5-flash'])
        input_cost = input_tokens * model_pricing['input']
        output_cost = output_tokens * model_pricing['output']

        return round(input_cost + output_cost, 6)

    @staticmethod
    def log_usage(user_id, submission_type, submission_id, input_tokens, output_tokens,
                  model_name, response_time_ms=None, success=True, error_message=None):
        """Log Gemini API usage"""
        total_tokens = input_tokens + output_tokens
        cost = GeminiUsage.calculate_cost(input_tokens, output_tokens, model_name)

        usage = GeminiUsage(
            user_id=user_id,
            submission_type=submission_type,
            submission_id=submission_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=cost,
            model_name=model_name,
            response_time_ms=response_time_ms,
            success=success,
            error_message=error_message
        )

        db.session.add(usage)
        return usage

    @staticmethod
    def get_total_cost_for_user(user_id, days=30):
        """Get total cost for a user in last N days"""
        from datetime import timedelta
        start_date = datetime.utcnow() - timedelta(days=days)

        total = db.session.query(db.func.sum(GeminiUsage.estimated_cost_usd)).filter(
            GeminiUsage.user_id == user_id,
            GeminiUsage.created_at >= start_date,
            GeminiUsage.success == True
        ).scalar()

        return total or 0.0

    @staticmethod
    def get_total_tokens_for_user(user_id, days=30):
        """Get total tokens used by user in last N days"""
        from datetime import timedelta
        start_date = datetime.utcnow() - timedelta(days=days)

        total = db.session.query(db.func.sum(GeminiUsage.total_tokens)).filter(
            GeminiUsage.user_id == user_id,
            GeminiUsage.created_at >= start_date,
            GeminiUsage.success == True
        ).scalar()

        return total or 0

    def __repr__(self):
        return f'<GeminiUsage {self.submission_type} - {self.total_tokens} tokens - ${self.estimated_cost_usd}>'
