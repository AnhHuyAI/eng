# app/models/vocabulary.py

from datetime import datetime, timedelta
from app import db

class VocabularyTopic(db.Model):
    """Vocabulary topic (Education, Technology, etc.)"""
    __tablename__ = 'vocabulary_topics'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))  # emoji or icon class
    order = db.Column(db.Integer, default=0)
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships (CASCADE delete)
    words = db.relationship('VocabularyWord', backref='topic', lazy='dynamic', 
                           cascade='all, delete-orphan')
    quizzes = db.relationship('VocabularyQuiz', backref='topic', lazy='dynamic',
                             cascade='all, delete-orphan')
    
    def word_count(self):
        """Count active words"""
        return self.words.filter_by(deleted_at=None).count()
    
    def __repr__(self):
        return f'<VocabularyTopic {self.name}>'


class VocabularyWord(db.Model):
    """Individual vocabulary word"""
    __tablename__ = 'vocabulary_words'
    
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('vocabulary_topics.id', ondelete='CASCADE'), 
                        nullable=False, index=True)
    
    word = db.Column(db.String(100), nullable=False, index=True)
    pronunciation = db.Column(db.String(100))
    part_of_speech = db.Column(db.String(20))  # noun, verb, adjective, adverb
    
    definition_vi = db.Column(db.Text, nullable=False)
    definition_en = db.Column(db.Text)
    
    # JSON fields
    example_sentences = db.Column(db.JSON)  # ["sentence 1", "sentence 2"]
    synonyms = db.Column(db.JSON)  # ["word1", "word2"]
    antonyms = db.Column(db.JSON)
    
    # Level: 'basic', 'intermediate', 'advanced'
    level = db.Column(db.String(20), default='intermediate')
    frequency_band = db.Column(db.Integer, default=6)  # IELTS band 5-9
    
    # Media
    audio_url = db.Column(db.String(500))
    image_url = db.Column(db.String(500))
    
    # Soft delete
    deleted_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<VocabularyWord {self.word}>'


class VocabularyQuiz(db.Model):
    """Vocabulary quiz"""
    __tablename__ = 'vocabulary_quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('vocabulary_topics.id', ondelete='CASCADE'),
                        nullable=False, index=True)
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    difficulty = db.Column(db.String(20), default='medium')  # easy, medium, hard
    
    time_limit = db.Column(db.Integer)  # minutes (null = no limit)
    pass_score = db.Column(db.Integer, default=70)  # percentage
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    questions = db.relationship('VocabularyQuestion', backref='quiz', lazy='dynamic',
                               cascade='all, delete-orphan', order_by='VocabularyQuestion.order')
    
    def question_count(self):
        return self.questions.count()
    
    def __repr__(self):
        return f'<VocabularyQuiz {self.title}>'


class VocabularyQuestion(db.Model):
    """Quiz question"""
    __tablename__ = 'vocabulary_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('vocabulary_quizzes.id', ondelete='CASCADE'),
                       nullable=False, index=True)
    word_id = db.Column(db.Integer, db.ForeignKey('vocabulary_words.id', ondelete='CASCADE'))
    
    # Type: 'multiple_choice', 'fill_blank', 'match', 'definition'
    question_type = db.Column(db.String(50), nullable=False)
    
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON)  # ["option1", "option2", "option3", "option4"]
    correct_answer = db.Column(db.String(500), nullable=False)
    explanation = db.Column(db.Text)
    
    order = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<VocabularyQuestion {self.id}>'


class UserVocabularyProgress(db.Model):
    """Track user's vocabulary learning"""
    __tablename__ = 'user_vocabulary_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                       nullable=False, index=True)
    word_id = db.Column(db.Integer, db.ForeignKey('vocabulary_words.id', ondelete='CASCADE'),
                       nullable=False, index=True)
    
    # Status: 'learning', 'mastered', 'review'
    status = db.Column(db.String(20), default='learning')
    
    # Practice stats
    correct_count = db.Column(db.Integer, default=0)
    incorrect_count = db.Column(db.Integer, default=0)
    
    # Spaced repetition
    last_reviewed = db.Column(db.DateTime)
    next_review = db.Column(db.DateTime, index=True)
    
    # Mastery level (0-5)
    mastery_level = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'word_id', name='unique_user_word'),
    )
    
    def update_mastery(self, is_correct):
        """Update mastery level based on answer"""
        if is_correct:
            self.correct_count += 1
            self.mastery_level = min(5, self.mastery_level + 1)
        else:
            self.incorrect_count += 1
            self.mastery_level = max(0, self.mastery_level - 1)
        
        self.last_reviewed = datetime.utcnow()
        
        # Calculate next review (spaced repetition)
        intervals = [1, 3, 7, 14, 30, 60]  # days
        interval = intervals[self.mastery_level] if self.mastery_level < len(intervals) else 90
        self.next_review = datetime.utcnow() + timedelta(days=interval)
        
        # Update status
        if self.mastery_level >= 4:
            self.status = 'mastered'
        elif self.mastery_level >= 2:
            self.status = 'learning'
        else:
            self.status = 'review'
    
    def __repr__(self):
        return f'<UserVocabularyProgress user={self.user_id} word={self.word_id}>'


class VocabularyQuizAttempt(db.Model):
    """User quiz attempt"""
    __tablename__ = 'vocabulary_quiz_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                       nullable=False, index=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('vocabulary_quizzes.id', ondelete='CASCADE'),
                       nullable=False, index=True)
    
    # Results
    score = db.Column(db.Float)  # percentage
    correct_answers = db.Column(db.Integer)
    total_questions = db.Column(db.Integer)
    
    # Answers (JSON: {question_id: user_answer})
    answers = db.Column(db.JSON)
    
    # Time
    time_taken = db.Column(db.Integer)  # seconds
    started_at = db.Column(db.DateTime, nullable=False)
    completed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<VocabularyQuizAttempt {self.id} score={self.score}>'