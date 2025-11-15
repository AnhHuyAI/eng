# app/models/writing.py

from datetime import datetime
from app import db

class WritingTask(db.Model):
    """Writing task (Task 1 or Task 2)"""
    __tablename__ = 'writing_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    
    task_type = db.Column(db.Integer, nullable=False, index=True)  # 1 or 2
    
    # Task 1 specific
    chart_type = db.Column(db.String(50))  # line_graph, bar_chart, pie_chart, table, map, process
    chart_image_url = db.Column(db.String(500))
    
    # Question
    question_text = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text)
    
    # Task 2 specific
    topic = db.Column(db.String(100), index=True)
    essay_type = db.Column(db.String(50))  # opinion, discussion, advantage_disadvantage, problem_solution
    
    difficulty = db.Column(db.String(20), default='medium')
    
    # Sample answers
    sample_answer_band_6 = db.Column(db.Text)
    sample_answer_band_7 = db.Column(db.Text)
    sample_answer_band_9 = db.Column(db.Text)
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    deleted_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    submissions = db.relationship('WritingSubmission', backref='task', lazy='dynamic',
                                 cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<WritingTask Task {self.task_type}: {self.topic or self.chart_type}>'


class WritingSubmission(db.Model):
    """User's writing submission"""
    __tablename__ = 'writing_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                       nullable=False, index=True)
    task_id = db.Column(db.Integer, db.ForeignKey('writing_tasks.id', ondelete='CASCADE'),
                       nullable=False, index=True)
    
    essay_text = db.Column(db.Text, nullable=False)
    word_count = db.Column(db.Integer)
    
    # AI Scores
    overall_band = db.Column(db.Float, index=True)
    
    # Task 1: Task Achievement, Task 2: Task Response
    task_achievement = db.Column(db.Float)  # For Task 1
    task_response = db.Column(db.Float)     # For Task 2
    
    coherence_cohesion = db.Column(db.Float)
    lexical_resource = db.Column(db.Float)
    grammar_accuracy = db.Column(db.Float)
    
    # Detailed feedback (JSON)
    detailed_feedback = db.Column(db.JSON)
    # {
    #   "task_response": {
    #     "score": 6.5,
    #     "strengths": ["point 1", "point 2"],
    #     "weaknesses": ["point 1", "point 2"],
    #     "examples": ["quote from essay"],
    #     "suggestions": ["tip 1", "tip 2"]
    #   },
    #   // ... similar for other criteria
    # }
    
    # Cost tracking
    credits_used = db.Column(db.Integer, default=1)
    api_cost_usd = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f'<WritingSubmission user={self.user_id} band={self.overall_band}>'