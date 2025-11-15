# app/models/listening.py

from datetime import datetime
from app import db

class ListeningSection(db.Model):
    """Listening section (Part 1, 2, 3, 4)"""
    __tablename__ = 'listening_sections'
    
    id = db.Column(db.Integer, primary_key=True)
    
    title = db.Column(db.String(200), nullable=False)
    part_number = db.Column(db.Integer, nullable=False, index=True)  # 1, 2, 3, 4
    description = db.Column(db.Text)
    
    # Audio
    audio_url = db.Column(db.String(500), nullable=False)
    duration = db.Column(db.Integer)  # seconds
    transcript = db.Column(db.Text)  # Full transcript
    
    # Metadata
    difficulty = db.Column(db.String(20), default='medium')
    topic = db.Column(db.String(100))  # conversation, monologue, academic, etc.
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    deleted_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    questions = db.relationship('ListeningQuestion', backref='section', lazy='dynamic',
                               cascade='all, delete-orphan', order_by='ListeningQuestion.question_number')
    attempts = db.relationship('ListeningAttempt', backref='section', lazy='dynamic',
                              cascade='all, delete-orphan')
    
    def question_count(self):
        return self.questions.count()
    
    def __repr__(self):
        return f'<ListeningSection Part {self.part_number}: {self.title}>'


class ListeningQuestion(db.Model):
    """Listening question"""
    __tablename__ = 'listening_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('listening_sections.id', ondelete='CASCADE'),
                          nullable=False, index=True)
    
    question_number = db.Column(db.Integer, nullable=False)
    
    # Type: 'multiple_choice', 'fill_blank', 'matching', 'map_labeling', 'diagram_labeling'
    question_type = db.Column(db.String(50), nullable=False)
    
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON)  # For multiple choice: ["A", "B", "C", "D"]
    
    # Correct answer (can be multiple for fill_blank: "answer1|answer2|answer3")
    correct_answer = db.Column(db.String(500), nullable=False)
    
    # Audio timing
    start_time = db.Column(db.Integer)  # seconds
    end_time = db.Column(db.Integer)
    
    explanation = db.Column(db.Text)
    
    # Optional image for map/diagram
    image_url = db.Column(db.String(500))
    
    def check_answer(self, user_answer):
        """Check if user answer is correct"""
        user_answer = user_answer.strip().lower()
        correct_answers = [ans.strip().lower() for ans in self.correct_answer.split('|')]
        return user_answer in correct_answers
    
    def __repr__(self):
        return f'<ListeningQuestion {self.question_number}>'


class ListeningAttempt(db.Model):
    """User's listening attempt"""
    __tablename__ = 'listening_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                       nullable=False, index=True)
    section_id = db.Column(db.Integer, db.ForeignKey('listening_sections.id', ondelete='CASCADE'),
                          nullable=False, index=True)
    
    # Results
    score = db.Column(db.Float)  # Raw score (e.g., 25/40)
    band_score = db.Column(db.Float)  # IELTS band (e.g., 6.5)
    correct_answers = db.Column(db.Integer)
    total_questions = db.Column(db.Integer)
    
    # User answers (JSON: {question_id: user_answer})
    answers = db.Column(db.JSON, nullable=False)
    
    # Detailed results per question
    question_results = db.Column(db.JSON)  # {question_id: {correct: true/false, user_answer: "", correct_answer: ""}}
    
    time_taken = db.Column(db.Integer)  # seconds
    completed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def calculate_band_score(self):
        """Convert raw score to IELTS band score"""
        # IELTS Listening band score conversion (approximate)
        band_conversion = {
            40: 9.0, 39: 8.5, 38: 8.5, 37: 8.0, 36: 8.0,
            35: 7.5, 34: 7.5, 33: 7.0, 32: 7.0, 31: 7.0,
            30: 6.5, 29: 6.5, 28: 6.5, 27: 6.5, 26: 6.0,
            25: 6.0, 24: 6.0, 23: 5.5, 22: 5.5, 21: 5.5,
            20: 5.5, 19: 5.0, 18: 5.0, 17: 5.0, 16: 5.0,
            15: 4.5, 14: 4.5, 13: 4.0, 12: 4.0, 11: 4.0,
            10: 3.5, 9: 3.5, 8: 3.0, 7: 3.0, 6: 2.5,
            5: 2.5, 4: 2.0, 3: 2.0, 2: 1.5, 1: 1.0, 0: 0.0
        }
        return band_conversion.get(self.correct_answers, 0.0)
    
    def __repr__(self):
        return f'<ListeningAttempt user={self.user_id} band={self.band_score}>'