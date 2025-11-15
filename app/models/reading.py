# app/models/reading.py

from datetime import datetime
from app import db

class ReadingPassage(db.Model):
    """Reading passage"""
    __tablename__ = 'reading_passages'
    
    id = db.Column(db.Integer, primary_key=True)
    
    title = db.Column(db.String(200), nullable=False)
    passage_text = db.Column(db.Text, nullable=False)  # Full passage
    
    topic = db.Column(db.String(100), index=True)
    difficulty = db.Column(db.String(20), default='medium')
    word_count = db.Column(db.Integer)
    reading_time = db.Column(db.Integer)  # Estimated minutes
    
    source = db.Column(db.String(200))
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    deleted_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    questions = db.relationship('ReadingQuestion', backref='passage', lazy='dynamic',
                               cascade='all, delete-orphan', order_by='ReadingQuestion.question_number')
    attempts = db.relationship('ReadingAttempt', backref='passage', lazy='dynamic',
                              cascade='all, delete-orphan')
    
    def question_count(self):
        return self.questions.count()
    
    def __repr__(self):
        return f'<ReadingPassage {self.title}>'


class ReadingQuestion(db.Model):
    """Reading question"""
    __tablename__ = 'reading_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    passage_id = db.Column(db.Integer, db.ForeignKey('reading_passages.id', ondelete='CASCADE'),
                          nullable=False, index=True)
    
    question_number = db.Column(db.Integer, nullable=False)
    
    # Type: 'multiple_choice', 'true_false_not_given', 'yes_no_not_given',
    #       'matching_headings', 'matching_information', 'sentence_completion', 'summary_completion'
    question_type = db.Column(db.String(50), nullable=False)
    
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON)  # For multiple choice or matching
    correct_answer = db.Column(db.String(500), nullable=False)
    
    paragraph_reference = db.Column(db.String(50))  # "Paragraph A", "Paragraph C"
    explanation = db.Column(db.Text)
    difficulty = db.Column(db.String(20), default='medium')
    
    def check_answer(self, user_answer):
        """Check if user answer is correct"""
        user_answer = user_answer.strip().lower()
        correct_answers = [ans.strip().lower() for ans in self.correct_answer.split('|')]
        return user_answer in correct_answers
    
    def __repr__(self):
        return f'<ReadingQuestion {self.question_number}>'


class ReadingAttempt(db.Model):
    """User's reading attempt"""
    __tablename__ = 'reading_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                       nullable=False, index=True)
    passage_id = db.Column(db.Integer, db.ForeignKey('reading_passages.id', ondelete='CASCADE'),
                          nullable=False, index=True)
    
    # Results
    score = db.Column(db.Float)
    band_score = db.Column(db.Float)
    correct_answers = db.Column(db.Integer)
    total_questions = db.Column(db.Integer)
    
    # User answers
    answers = db.Column(db.JSON, nullable=False)
    question_results = db.Column(db.JSON)
    
    time_taken = db.Column(db.Integer)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def calculate_band_score(self):
        """Convert raw score to IELTS band score (Academic)"""
        band_conversion = {
            40: 9.0, 39: 8.5, 38: 8.5, 37: 8.0, 36: 8.0,
            35: 7.5, 34: 7.5, 33: 7.0, 32: 7.0, 31: 7.0,
            30: 6.5, 29: 6.5, 28: 6.0, 27: 6.0, 26: 6.0,
            25: 5.5, 24: 5.5, 23: 5.5, 22: 5.0, 21: 5.0,
            20: 5.0, 19: 4.5, 18: 4.5, 17: 4.5, 16: 4.0,
            15: 4.0, 14: 4.0, 13: 3.5, 12: 3.5, 11: 3.0,
            10: 3.0, 9: 2.5, 8: 2.5, 7: 2.5, 6: 2.0,
            5: 2.0, 4: 1.5, 3: 1.0, 2: 1.0, 1: 0.5, 0: 0.0
        }
        return band_conversion.get(self.correct_answers, 0.0)
    
    def __repr__(self):
        return f'<ReadingAttempt user={self.user_id} band={self.band_score}>'