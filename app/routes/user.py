# app/routes/user.py

from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.user import Transaction
from app.models.writing import WritingSubmission
from app.models.speaking import SpeakingSubmission
from app.models.listening import ListeningAttempt
from app.models.reading import ReadingAttempt
from app.models.vocabulary import VocabularyQuizAttempt
from sqlalchemy import func, desc
from datetime import datetime, timedelta

bp = Blueprint('user', __name__, url_prefix='/user')

@bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    
    # Recent submissions (last 10)
    recent_writings = WritingSubmission.query.filter_by(user_id=current_user.id)\
        .order_by(desc(WritingSubmission.created_at)).limit(5).all()
    
    recent_speakings = SpeakingSubmission.query.filter_by(user_id=current_user.id)\
        .order_by(desc(SpeakingSubmission.created_at)).limit(5).all()
    
    # Statistics
    stats = {
        'total_writings': WritingSubmission.query.filter_by(user_id=current_user.id).count(),
        'total_speakings': SpeakingSubmission.query.filter_by(user_id=current_user.id).count(),
        'total_listenings': ListeningAttempt.query.filter_by(user_id=current_user.id).count(),
        'total_readings': ReadingAttempt.query.filter_by(user_id=current_user.id).count(),
    }
    
    # Average scores
    avg_writing = db.session.query(func.avg(WritingSubmission.overall_band))\
        .filter_by(user_id=current_user.id).scalar()
    avg_speaking = db.session.query(func.avg(SpeakingSubmission.overall_band))\
        .filter_by(user_id=current_user.id).scalar()
    avg_listening = db.session.query(func.avg(ListeningAttempt.band_score))\
        .filter_by(user_id=current_user.id).scalar()
    avg_reading = db.session.query(func.avg(ReadingAttempt.band_score))\
        .filter_by(user_id=current_user.id).scalar()
    
    stats['avg_writing'] = round(avg_writing, 1) if avg_writing else None
    stats['avg_speaking'] = round(avg_speaking, 1) if avg_speaking else None
    stats['avg_listening'] = round(avg_listening, 1) if avg_listening else None
    stats['avg_reading'] = round(avg_reading, 1) if avg_reading else None
    
    # Calculate overall estimate
    scores = [s for s in [avg_writing, avg_speaking, avg_listening, avg_reading] if s]
    stats['overall_estimate'] = round(sum(scores) / len(scores), 1) if scores else None
    
    # Recent transactions
    recent_transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(desc(Transaction.created_at)).limit(10).all()
    
    return render_template('user/dashboard.html',
                         stats=stats,
                         recent_writings=recent_writings,
                         recent_speakings=recent_speakings,
                         recent_transactions=recent_transactions)


@bp.route('/progress')
@login_required
def progress():
    """User progress page with charts"""
    
    # Get data for last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Writing progress
    writings = WritingSubmission.query.filter(
        WritingSubmission.user_id == current_user.id,
        WritingSubmission.created_at >= thirty_days_ago
    ).order_by(WritingSubmission.created_at).all()
    
    # Speaking progress
    speakings = SpeakingSubmission.query.filter(
        SpeakingSubmission.user_id == current_user.id,
        SpeakingSubmission.created_at >= thirty_days_ago
    ).order_by(SpeakingSubmission.created_at).all()
    
    # Listening progress
    listenings = ListeningAttempt.query.filter(
        ListeningAttempt.user_id == current_user.id,
        ListeningAttempt.completed_at >= thirty_days_ago
    ).order_by(ListeningAttempt.completed_at).all()
    
    # Reading progress
    readings = ReadingAttempt.query.filter(
        ReadingAttempt.user_id == current_user.id,
        ReadingAttempt.completed_at >= thirty_days_ago
    ).order_by(ReadingAttempt.completed_at).all()
    
    return render_template('user/progress.html',
                         writings=writings,
                         speakings=speakings,
                         listenings=listenings,
                         readings=readings)


@bp.route('/api/progress-data')
@login_required
def progress_data():
    """API endpoint for progress chart data"""
    
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Writing data
    writings = WritingSubmission.query.filter(
        WritingSubmission.user_id == current_user.id,
        WritingSubmission.created_at >= thirty_days_ago
    ).order_by(WritingSubmission.created_at).all()
    
    writing_data = [{
        'date': w.created_at.strftime('%Y-%m-%d'),
        'score': w.overall_band
    } for w in writings]
    
    # Speaking data
    speakings = SpeakingSubmission.query.filter(
        SpeakingSubmission.user_id == current_user.id,
        SpeakingSubmission.created_at >= thirty_days_ago
    ).order_by(SpeakingSubmission.created_at).all()
    
    speaking_data = [{
        'date': s.created_at.strftime('%Y-%m-%d'),
        'score': s.overall_band
    } for s in speakings]
    
    return jsonify({
        'writing': writing_data,
        'speaking': speaking_data
    })


@bp.route('/profile')
@login_required
def profile():
    """User profile"""
    return render_template('user/profile.html')