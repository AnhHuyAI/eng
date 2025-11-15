# app/routes/teacher.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
from app import db
from app.models import (
    User, TeacherClass, ClassStudent, Assignment,
    WritingTask, ReadingPassage, WritingSubmission, ReadingAttempt
)

bp = Blueprint('teacher', __name__, url_prefix='/teacher')

def teacher_required(f):
    """Decorator to require teacher role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_teacher():
            flash('Access denied. Teachers only.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/dashboard')
@login_required
@teacher_required
def dashboard():
    """Teacher dashboard"""
    # Get statistics
    total_students = current_user.students.count()
    total_classes = current_user.teacher_classes.filter_by(status='active').count()
    credits_balance = current_user.credits

    # Recent submissions
    recent_submissions = WritingSubmission.query.join(User).filter(
        User.teacher_id == current_user.id
    ).order_by(WritingSubmission.created_at.desc()).limit(10).all()

    return render_template('teacher/dashboard.html',
                          total_students=total_students,
                          total_classes=total_classes,
                          credits_balance=credits_balance,
                          recent_submissions=recent_submissions)

@bp.route('/classes')
@login_required
@teacher_required
def classes():
    """List all classes"""
    classes = current_user.teacher_classes.filter_by(status='active').all()
    return render_template('teacher/classes.html', classes=classes)

@bp.route('/classes/create', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_class():
    """Create a new class"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        max_students = request.form.get('max_students')

        if not name:
            flash('Class name is required', 'danger')
            return redirect(url_for('teacher.create_class'))

        # Create class
        new_class = TeacherClass(
            teacher_id=current_user.id,
            name=name,
            description=description,
            code=TeacherClass().generate_code(),
            max_students=int(max_students) if max_students else None,
            status='active'
        )

        db.session.add(new_class)
        db.session.commit()

        flash(f'Class created successfully! Code: {new_class.code}', 'success')
        return redirect(url_for('teacher.view_class', class_id=new_class.id))

    return render_template('teacher/create_class.html')

@bp.route('/classes/<int:class_id>')
@login_required
@teacher_required
def view_class(class_id):
    """View class details"""
    teacher_class = TeacherClass.query.get_or_404(class_id)

    if teacher_class.teacher_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('teacher.classes'))

    students = ClassStudent.query.filter_by(
        class_id=class_id,
        status='active'
    ).all()

    assignments = Assignment.query.filter_by(class_id=class_id).all()

    return render_template('teacher/view_class.html',
                          teacher_class=teacher_class,
                          students=students,
                          assignments=assignments)

@bp.route('/classes/<int:class_id>/add_student', methods=['POST'])
@login_required
@teacher_required
def add_student(class_id):
    """Add student to class by email"""
    teacher_class = TeacherClass.query.get_or_404(class_id)

    if teacher_class.teacher_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    student_email = request.form.get('student_email')
    student = User.query.filter_by(email=student_email, role='student').first()

    if not student:
        flash('Student not found', 'danger')
        return redirect(url_for('teacher.view_class', class_id=class_id))

    # Check if already in class
    existing = ClassStudent.query.filter_by(
        class_id=class_id,
        student_id=student.id
    ).first()

    if existing:
        flash('Student already in class', 'warning')
        return redirect(url_for('teacher.view_class', class_id=class_id))

    # Add to class
    class_student = ClassStudent(
        class_id=class_id,
        student_id=student.id,
        status='active'
    )
    db.session.add(class_student)
    db.session.commit()

    flash(f'Added {student.full_name} to class', 'success')
    return redirect(url_for('teacher.view_class', class_id=class_id))

@bp.route('/content')
@login_required
@teacher_required
def content():
    """Browse content library"""
    # Admin's public content
    public_writing = WritingTask.query.filter_by(is_public=True).all()
    public_reading = ReadingPassage.query.filter_by(is_public=True).all()

    # Teacher's private content
    my_writing = WritingTask.query.filter_by(
        created_by=current_user.id,
        is_public=False
    ).all()
    my_reading = ReadingPassage.query.filter_by(
        created_by=current_user.id,
        is_public=False
    ).all()

    return render_template('teacher/content.html',
                          public_writing=public_writing,
                          public_reading=public_reading,
                          my_writing=my_writing,
                          my_reading=my_reading)

@bp.route('/assignments/create', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_assignment():
    """Create assignment for a class"""
    if request.method == 'POST':
        class_id = request.form.get('class_id')
        content_type = request.form.get('content_type')
        content_id = request.form.get('content_id')
        title = request.form.get('title')
        due_date_str = request.form.get('due_date')

        teacher_class = TeacherClass.query.get_or_404(class_id)

        if teacher_class.teacher_id != current_user.id:
            flash('Access denied', 'danger')
            return redirect(url_for('teacher.classes'))

        # Create assignment
        assignment = Assignment(
            teacher_id=current_user.id,
            class_id=class_id,
            content_type=content_type,
            content_id=content_id,
            title=title,
            due_date=datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None,
            published=True
        )

        db.session.add(assignment)
        db.session.commit()

        flash('Assignment created successfully!', 'success')
        return redirect(url_for('teacher.view_class', class_id=class_id))

    # GET request - show form
    classes = current_user.teacher_classes.filter_by(status='active').all()
    public_writing = WritingTask.query.filter_by(is_public=True).all()
    public_reading = ReadingPassage.query.filter_by(is_public=True).all()

    return render_template('teacher/create_assignment.html',
                          classes=classes,
                          public_writing=public_writing,
                          public_reading=public_reading)

@bp.route('/submissions')
@login_required
@teacher_required
def submissions():
    """View all student submissions"""
    # Get all writing submissions from teacher's students
    writing_subs = WritingSubmission.query.join(User).filter(
        User.teacher_id == current_user.id
    ).order_by(WritingSubmission.created_at.desc()).limit(50).all()

    # Get all reading attempts from teacher's students
    reading_attempts = ReadingAttempt.query.join(User).filter(
        User.teacher_id == current_user.id
    ).order_by(ReadingAttempt.completed_at.desc()).limit(50).all()

    return render_template('teacher/submissions.html',
                          writing_submissions=writing_subs,
                          reading_attempts=reading_attempts)

@bp.route('/credits')
@login_required
@teacher_required
def credits():
    """View credits balance and purchase options"""
    from app.models import Transaction

    balance = current_user.credits
    transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(Transaction.created_at.desc()).limit(20).all()

    packages = current_app.config['PAYMENT_PACKAGES']

    return render_template('teacher/credits.html',
                          balance=balance,
                          transactions=transactions,
                          packages=packages,
                          BANK_INFO=current_app.config['BANK_INFO'])


@bp.route('/submissions/<int:submission_id>/comment', methods=['POST'])
@login_required
@teacher_required
def add_comment(submission_id):
    """Add teacher comment to a submission"""
    submission = WritingSubmission.query.get_or_404(submission_id)

    # Verify submission is from teacher's student
    if submission.user.teacher_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('teacher.submissions'))

    teacher_comment = request.form.get('teacher_comment')
    teacher_score = request.form.get('teacher_score')

    submission.teacher_comment = teacher_comment
    if teacher_score:
        try:
            submission.teacher_score = float(teacher_score)
        except ValueError:
            pass

    db.session.commit()

    flash('Comment saved successfully!', 'success')
    return redirect(url_for('teacher.submissions'))
