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