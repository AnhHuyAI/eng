# app/routes/auth.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app import db
from app.models.user import User

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Simple login - just select user"""
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('Email không tồn tại.', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('Tài khoản đã bị khóa.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Update last login
        from datetime import datetime
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user, remember=True)
        
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        
        if user.is_admin():
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('user.dashboard'))
    
    # Get all users for selection
    users = User.query.filter_by(is_active=True).all()
    
    return render_template('auth/login.html', users=users)


@bp.route('/logout')
def logout():
    """Logout"""
    logout_user()
    flash('Đã đăng xuất thành công.', 'success')
    return redirect(url_for('auth.login'))


@bp.route('/teacher/register', methods=['GET', 'POST'])
def teacher_register():
    """Teacher registration"""
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        # Get form data
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        center_name = request.form.get('center_name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        tax_code = request.form.get('tax_code')

        # Validation
        if not all([full_name, email, password, center_name, phone]):
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('auth.teacher_register'))

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('auth.teacher_register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters', 'danger')
            return redirect(url_for('auth.teacher_register'))

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.teacher_register'))

        # Create teacher account
        from datetime import datetime
        from flask import current_app

        new_teacher = User(
            email=email,
            full_name=full_name,
            role='teacher',
            center_name=center_name,
            phone=phone,
            address=address,
            tax_code=tax_code,
            credits=current_app.config.get('TEACHER_TRIAL_CREDITS', 50),
            is_active=True,
            email_verified=False,
            approved_at=datetime.utcnow()  # Auto-approve for demo
        )
        new_teacher.set_password(password)

        db.session.add(new_teacher)
        db.session.commit()

        # Auto login
        login_user(new_teacher, remember=True)

        flash(f'Welcome! Your account has been created with {new_teacher.credits} FREE trial credits!', 'success')
        return redirect(url_for('teacher.dashboard'))

    return render_template('auth/teacher_register.html')


@bp.route('/student/register', methods=['GET', 'POST'])
def student_register():
    """Student registration"""
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        # Get form data
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone = request.form.get('phone')
        class_code = request.form.get('class_code', '').strip().upper()

        # Validation
        if not all([full_name, email, password]):
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('auth.student_register'))

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('auth.student_register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters', 'danger')
            return redirect(url_for('auth.student_register'))

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.student_register'))

        # Create student account
        new_student = User(
            email=email,
            full_name=full_name,
            role='student',
            phone=phone,
            credits=0,
            is_active=True,
            email_verified=False
        )
        new_student.set_password(password)

        db.session.add(new_student)
        db.session.flush()  # Get student ID

        # Join class if code provided
        if class_code:
            from app.models import TeacherClass, ClassStudent
            teacher_class = TeacherClass.query.filter_by(code=class_code, status='active').first()

            if teacher_class and not teacher_class.is_full():
                # Add to class
                class_student = ClassStudent(
                    class_id=teacher_class.id,
                    student_id=new_student.id,
                    status='active'
                )
                new_student.teacher_id = teacher_class.teacher_id
                db.session.add(class_student)

        db.session.commit()

        # Auto login
        login_user(new_student, remember=True)

        if class_code and teacher_class:
            flash(f'Welcome! You have been enrolled in {teacher_class.name}', 'success')
        else:
            flash('Welcome! Your account has been created.', 'success')

        return redirect(url_for('user.dashboard'))

    return render_template('auth/student_register.html')