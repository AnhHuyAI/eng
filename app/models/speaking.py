# app/models/speaking.py

from datetime import datetime
from app import db

class SpeakingTopic(db.Model):
    """Speaking topic"""
    __tablename__ = 'speaking_topics'
    
    id = db.Column(db.Integer, primary_key=True)
    
    part = db.Column(db.Integer, nullable=False, index=True)  # 1, 2, or 3
    topic = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100))  # Work, Study, Hobbies, etc.
    
    # Part 1: Quick questions
    part1_questions = db.Column(db.JSON)  # ["Question 1", "Question 2", ...]
    
    # Part 2: Cue card
    cue_card_title = db.Column(db.String(200))
    cue_card_points = db.Column(db.JSON)  # ["Who", "When", "Where", "Why"]
    
    # Part 3: Discussion questions
    part3_questions = db.Column(db.JSON)
    
    # Sample answers
    sample_answers = db.Column(db.JSON)  # {band_7: "...", band_8: "...", band_9: "..."}
    
    difficulty = db.Column(db.String(20), default='medium')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    deleted_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    submissions = db.relationship('SpeakingSubmission', backref='topic', lazy='dynamic',
                                 cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<SpeakingTopic Part {self.part}: {self.topic}>'


class SpeakingSubmission(db.Model):
    """User's speaking submission"""
    __tablename__ = 'speaking_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                       nullable=False, index=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('speaking_topics.id', ondelete='CASCADE'),
                        nullable=False, index=True)
    
    part = db.Column(db.Integer, nullable=False)
    
    # Audio & transcript
    audio_url = db.Column(db.String(500), nullable=False)
    transcript = db.Column(db.Text)  # From Speech-to-Text
    duration = db.Column(db.Integer)  # seconds
    
    # AI Scores
    overall_band = db.Column(db.Float, index=True)
    fluency_coherence = db.Column(db.Float)
    lexical_resource = db.Column(db.Float)
    grammar_accuracy = db.Column(db.Float)
    pronunciation = db.Column(db.Float)
    
    # Detailed feedback (JSON)
    detailed_feedback = db.Column(db.JSON)
    # {
    #   "fluency": {"strengths": [], "weaknesses": [], "examples": []},
    #   "lexical": {...},
    #   "grammar": {...},
    #   "pronunciation": {...},
    #   "overall_comment": "..."
    # }
    
    # Metrics
    words_per_minute = db.Column(db.Integer)
    hesitation_count = db.Column(db.Integer)
    repetition_count = db.Column(db.Integer)
    filler_words_count = db.Column(db.Integer)
    
    # Cost tracking
    credits_used = db.Column(db.Integer, default=2)
    api_cost_usd = db.Column(db.Float)  # STT + Gemini cost
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f'<SpeakingSubmission user={self.user_id} band={self.overall_band}>'