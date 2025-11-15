# app/utils/validators.py

import re
from werkzeug.utils import secure_filename

def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def validate_essay(text, min_words=150, max_words=500):
    """Validate essay text"""
    if not text or not text.strip():
        return False, "Essay cannot be empty"
    
    word_count = len(text.split())
    
    if word_count < min_words:
        return False, f"Essay too short ({word_count} words). Minimum {min_words} words."
    
    if word_count > max_words:
        # Truncate instead of reject
        words = text.split()[:max_words]
        text = ' '.join(words)
    
    return True, text


def sanitize_filename(filename):
    """Sanitize filename"""
    return secure_filename(filename)


def is_valid_email(email):
    """Check if email is valid"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_audio_duration(duration, max_duration=600):
    """Validate audio duration (max 10 minutes)"""
    return duration <= max_duration