# app/models/class_management.py

from datetime import datetime
import random
import string
from app import db


class TeacherClass(db.Model):
    """Teacher's class/group"""
    __tablename__ = 'teacher_classes'

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                          nullable=False, index=True)

    # Class info
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)  # "ABC123" for students to join

    # Settings
    max_students = db.Column(db.Integer)  # NULL = unlimited

    # Status
    status = db.Column(db.String(20), default='active', nullable=False)  # 'active', 'archived'

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    teacher = db.relationship('User', backref='teacher_classes', foreign_keys=[teacher_id])

    class_students = db.relationship('ClassStudent', backref='teacher_class', lazy='dynamic',
                                    cascade='all, delete-orphan')

    assignments = db.relationship('Assignment', backref='teacher_class', lazy='dynamic',
                                 cascade='all, delete-orphan')

    def generate_code(self):
        """Generate unique 6-character code for class"""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not TeacherClass.query.filter_by(code=code).first():
                return code

    @property
    def student_count(self):
        """Get number of active students in class"""
        return self.class_students.filter_by(status='active').count()

    @property
    def students(self):
        """Get query for active student User objects in this class"""
        from app.models.user import User
        student_ids = [cs.student_id for cs in self.class_students.filter_by(status='active').all()]
        return User.query.filter(User.id.in_(student_ids)) if student_ids else User.query.filter_by(id=None)

    @property
    def assignment_count(self):
        """Get number of assignments"""
        return self.assignments.filter_by(published=True).count()

    def is_full(self):
        """Check if class is full"""
        if not self.max_students:
            return False
        return self.student_count >= self.max_students

    def __repr__(self):
        return f'<TeacherClass {self.name} ({self.code})>'


class ClassStudent(db.Model):
    """Student membership in a class"""
    __tablename__ = 'class_students'

    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('teacher_classes.id', ondelete='CASCADE'),
                        nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                          nullable=False, index=True)

    # Status
    status = db.Column(db.String(20), default='active', nullable=False)  # 'active', 'removed'

    # Timestamps
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    removed_at = db.Column(db.DateTime)

    # Relationships
    student = db.relationship('User', backref='class_memberships', foreign_keys=[student_id])

    # Unique constraint: student can only join a class once
    __table_args__ = (
        db.UniqueConstraint('class_id', 'student_id', name='unique_class_student'),
    )

    def __repr__(self):
        return f'<ClassStudent class={self.class_id} student={self.student_id}>'
