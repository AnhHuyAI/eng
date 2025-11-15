# app/utils/decorators.py

from functools import wraps
from flask import redirect, url_for, flash, abort
from flask_login import current_user

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Vui lòng đăng nhập để truy cập trang này.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_admin():
            flash('Bạn không có quyền truy cập trang này.', 'danger')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def credits_required(amount=1):
    """Decorator to check if user has enough credits"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Vui lòng đăng nhập để sử dụng chức năng này.', 'warning')
                return redirect(url_for('auth.login'))
            
            if not current_user.has_credits(amount):
                flash(f'Bạn không đủ credits. Cần {amount} credits, bạn có {current_user.credits} credits.', 'danger')
                return redirect(url_for('payment.packages'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator