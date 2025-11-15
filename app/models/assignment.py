# app/models/assignment.py

from datetime import datetime
from app import db


class Assignment(db.Model):
    """Assignment created by teacher for a class"""
    __tablename__ = 'assignments'

    id = db.Column(db.Integer, primary_key=True)

    # Creator & target
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                          nullable=False, index=True)
    class_id = db.Column(db.Integer, db.ForeignKey('teacher_classes.id', ondelete='CASCADE'),
                        nullable=False, index=True)

    # Assignment info
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    # Content reference
    content_type = db.Column(db.String(50), nullable=False, index=True)
    # 'vocabulary', 'reading', 'writing_task1', 'writing_task2', 'listening', 'speaking'

    content_id = db.Column(db.Integer, nullable=False, index=True)
    # FK to specific content (WritingTask, ReadingPassage, etc.)

    # Settings
    due_date = db.Column(db.DateTime)
    max_attempts = db.Column(db.Integer, default=1)  # How many times student can submit
    time_limit_minutes = db.Column(db.Integer)  # Optional time limit

    # Status
    published = db.Column(db.Boolean, default=True, nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships will be added via backref from submission models

    def get_content(self):
        """Get the actual content object (WritingTask, ReadingPassage, etc.)"""
        if self.content_type == 'writing_task1' or self.content_type == 'writing_task2':
            from app.models.writing import WritingTask
            return WritingTask.query.get(self.content_id)
        elif self.content_type == 'reading':
            from app.models.reading import ReadingPassage
            return ReadingPassage.query.get(self.content_id)
        elif self.content_type == 'listening':
            from app.models.listening import ListeningSection
            return ListeningSection.query.get(self.content_id)
        elif self.content_type == 'speaking':
            from app.models.speaking import SpeakingTopic
            return SpeakingTopic.query.get(self.content_id)
        elif self.content_type == 'vocabulary':
            from app.models.vocabulary import VocabularyTopic
            return VocabularyTopic.query.get(self.content_id)
        return None

    def get_submissions_for_student(self, student_id):
        """Get all submissions from a specific student for this assignment"""
        if self.content_type in ['writing_task1', 'writing_task2']:
            from app.models.writing import WritingSubmission
            return WritingSubmission.query.filter_by(
                user_id=student_id,
                task_id=self.content_id
            ).order_by(WritingSubmission.created_at.desc()).all()
        elif self.content_type == 'reading':
            from app.models.reading import ReadingAttempt
            return ReadingAttempt.query.filter_by(
                user_id=student_id,
                passage_id=self.content_id
            ).order_by(ReadingAttempt.completed_at.desc()).all()
        elif self.content_type == 'listening':
            from app.models.listening import ListeningAttempt
            return ListeningAttempt.query.filter_by(
                user_id=student_id,
                section_id=self.content_id
            ).order_by(ListeningAttempt.completed_at.desc()).all()
        elif self.content_type == 'speaking':
            from app.models.speaking import SpeakingSubmission
            return SpeakingSubmission.query.filter_by(
                user_id=student_id,
                topic_id=self.content_id
            ).order_by(SpeakingSubmission.created_at.desc()).all()
        return []

    def student_attempts_count(self, student_id):
        """Get number of attempts by student"""
        submissions = self.get_submissions_for_student(student_id)
        return len(submissions)

    def can_student_submit(self, student_id):
        """Check if student can submit (not exceeded max attempts)"""
        if not self.max_attempts:
            return True
        return self.student_attempts_count(student_id) < self.max_attempts

    def is_past_due(self):
        """Check if assignment is past due date"""
        if not self.due_date:
            return False
        return datetime.utcnow() > self.due_date

    def get_student_attempts(self, student_id):
        """Get all attempts by a student for this assignment"""
        return self.get_submissions_for_student(student_id)

    def get_latest_attempt(self, student_id):
        """Get most recent attempt by a student"""
        attempts = self.get_student_attempts(student_id)
        return attempts[0] if attempts else None

    def is_completed_by(self, student_id):
        """Check if student has completed this assignment"""
        attempts = self.get_student_attempts(student_id)
        return len(attempts) > 0

    def get_practice_url(self):
        """Get URL for practicing/starting this assignment"""
        from flask import url_for

        if self.content_type in ['writing_task1', 'writing_task2']:
            return url_for('writing.practice', task_id=self.content_id)
        elif self.content_type == 'reading':
            return url_for('reading.practice', passage_id=self.content_id)
        elif self.content_type == 'listening':
            return url_for('listening.practice', section_id=self.content_id)
        elif self.content_type == 'speaking':
            return url_for('speaking.practice', topic_id=self.content_id)
        return '#'

    def __repr__(self):
        return f'<Assignment {self.title} ({self.content_type})>'
