# app/routes/student.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
from app import db
from app.models import (
    User, TeacherClass, ClassStudent, Assignment,
    WritingSubmission, ReadingAttempt, ListeningAttempt, SpeakingSubmission
)

bp = Blueprint('student', __name__, url_prefix='/student')

def student_required(f):
    """Decorator to require student role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_student():
            flash('Access denied. Students only.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/classes')
@login_required
@student_required
def classes():
    """View all classes student is enrolled in"""
    student_classes = current_user.class_memberships.filter_by(status='active').all()
    return render_template('student/classes.html', student_classes=student_classes)

@bp.route('/classes/<int:class_id>')
@login_required
@student_required
def view_class(class_id):
    """View class details"""
    # Check if student is member
    class_membership = ClassStudent.query.filter_by(
        class_id=class_id,
        student_id=current_user.id,
        status='active'
    ).first_or_404()

    teacher_class = class_membership.teacher_class
    assignments = Assignment.query.filter_by(
        class_id=class_id,
        published=True
    ).order_by(Assignment.created_at.desc()).all()

    return render_template('student/view_class.html',
                          teacher_class=teacher_class,
                          assignments=assignments)

@bp.route('/assignments')
@login_required
@student_required
def assignments():
    """View all assignments"""
    # Get all classes student is enrolled in
    class_ids = [cs.class_id for cs in current_user.class_memberships.filter_by(status='active').all()]

    if not class_ids:
        return render_template('student/assignments.html',
                              active_assignments=[],
                              completed_assignments=[],
                              all_assignments=[],
                              now=datetime.utcnow())

    # Get all assignments from these classes
    all_assignments = Assignment.query.filter(
        Assignment.class_id.in_(class_ids),
        Assignment.published == True
    ).order_by(Assignment.due_date.asc()).all()

    # Separate into active and completed
    active_assignments = []
    completed_assignments = []

    for assignment in all_assignments:
        if assignment.is_completed_by(current_user.id):
            completed_assignments.append(assignment)
        else:
            active_assignments.append(assignment)

    return render_template('student/assignments.html',
                          active_assignments=active_assignments,
                          completed_assignments=completed_assignments,
                          all_assignments=all_assignments,
                          now=datetime.utcnow())

@bp.route('/join', methods=['GET', 'POST'])
@login_required
@student_required
def join_class():
    """Join a class using code"""
    if request.method == 'POST':
        code = request.form.get('class_code', '').strip().upper()

        if not code:
            flash('Please enter a class code', 'danger')
            return redirect(url_for('student.join_class'))

        # Find class
        teacher_class = TeacherClass.query.filter_by(code=code, status='active').first()

        if not teacher_class:
            flash('Invalid class code', 'danger')
            return redirect(url_for('student.join_class'))

        # Check if class is full
        if teacher_class.is_full():
            flash('This class is full', 'danger')
            return redirect(url_for('student.join_class'))

        # Check if already enrolled
        existing = ClassStudent.query.filter_by(
            class_id=teacher_class.id,
            student_id=current_user.id
        ).first()

        if existing:
            if existing.status == 'active':
                flash('You are already enrolled in this class', 'warning')
            else:
                # Reactivate membership
                existing.status = 'active'
                existing.joined_at = datetime.utcnow()
                db.session.commit()
                flash(f'Rejoined class: {teacher_class.name}', 'success')
            return redirect(url_for('student.view_class', class_id=teacher_class.id))

        # Add student to class
        class_student = ClassStudent(
            class_id=teacher_class.id,
            student_id=current_user.id,
            status='active'
        )

        # Also set teacher relationship if not already set
        if not current_user.teacher_id:
            current_user.teacher_id = teacher_class.teacher_id

        db.session.add(class_student)
        db.session.commit()

        flash(f'Successfully joined class: {teacher_class.name}!', 'success')
        return redirect(url_for('student.view_class', class_id=teacher_class.id))

    return render_template('student/join_class.html')
