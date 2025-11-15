# app/utils/helpers.py

import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app

def save_upload_file(file, folder):
    """Save uploaded file and return URL"""
    if not file:
        return None
    
    # Generate unique filename
    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    
    # Create folder if not exists
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
    os.makedirs(upload_path, exist_ok=True)
    
    # Save file
    filepath = os.path.join(upload_path, unique_filename)
    file.save(filepath)
    
    # Return relative URL
    return f"{folder}/{unique_filename}"


def format_currency(amount):
    """Format currency (VNĐ)"""
    return f"{amount:,} VNĐ"


def calculate_reading_time(word_count, wpm=200):
    """Calculate reading time in minutes"""
    return max(1, round(word_count / wpm))


def time_ago(dt):
    """Convert datetime to 'time ago' string"""
    if not dt:
        return ""
    
    now = datetime.utcnow()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "vừa xong"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} phút trước"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} giờ trước"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} ngày trước"
    else:
        weeks = int(seconds / 604800)
        return f"{weeks} tuần trước"


def get_band_color(band_score):
    """Get color class for band score"""
    if band_score >= 8.0:
        return 'success'
    elif band_score >= 7.0:
        return 'info'
    elif band_score >= 6.0:
        return 'warning'
    else:
        return 'danger'