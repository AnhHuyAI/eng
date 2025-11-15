# app/routes/speaking.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.speaking import SpeakingTopic, SpeakingSubmission
from app.services.scoring_service import scoring_service
from app.utils.decorators import credits_required
from app.utils.helpers import save_upload_file
from app.utils.validators import allowed_file, validate_audio_duration
from datetime import datetime
import os

bp = Blueprint('speaking', __name__, url_prefix='/speaking')

@bp.route('/')
@login_required
def index():
    """Speaking home"""
    return render_template('speaking/index.html')


@bp.route('/part-1')
@login_required
def part_1_topics():
    """List Part 1 topics"""
    
    topics = SpeakingTopic.query.filter_by(
        part=1,
        is_active=True,
        deleted_at=None
    ).all()
    
    return render_template('speaking/part_1_topics.html', topics=topics)


@bp.route('/part-2')
@login_required
def part_2_topics():
    """List Part 2 topics (Cue cards)"""
    
    topics = SpeakingTopic.query.filter_by(
        part=2,
        is_active=True,
        deleted_at=None
    ).all()
    
    return render_template('speaking/part_2_topics.html', topics=topics)


@bp.route('/part-3')
@login_required
def part_3_topics():
    """List Part 3 topics"""
    
    topics = SpeakingTopic.query.filter_by(
        part=3,
        is_active=True,
        deleted_at=None
    ).all()
    
    return render_template('speaking/part_3_topics.html', topics=topics)


@bp.route('/topic/<int:topic_id>')
@login_required
def topic_practice(topic_id):
    """Practice speaking topic"""
    
    topic = SpeakingTopic.query.get_or_404(topic_id)
    
    # Get credit cost
    credit_cost = current_app.config['CREDIT_COSTS']['speaking_practice']
    
    return render_template('speaking/topic_practice.html',
                         topic=topic,
                         credit_cost=credit_cost)


@bp.route('/topic/<int:topic_id>/submit', methods=['POST'])
@login_required
@credits_required(2)
def topic_submit(topic_id):
    """Submit speaking recording"""
    
    topic = SpeakingTopic.query.get_or_404(topic_id)
    audio_file = request.files.get('audio_file')
    duration = int(request.form.get('duration', 0))  # seconds
    
    # Validate audio file
    if not audio_file:
        flash('Vui lòng upload file audio.', 'danger')
        return redirect(url_for('speaking.topic_practice', topic_id=topic_id))
    
    allowed_extensions = current_app.config['ALLOWED_AUDIO_EXTENSIONS']
    if not allowed_file(audio_file.filename, allowed_extensions):
        flash(f'Định dạng file không hợp lệ. Chỉ chấp nhận: {", ".join(allowed_extensions)}', 'danger')
        return redirect(url_for('speaking.topic_practice', topic_id=topic_id))
    
    # Validate duration
    if not validate_audio_duration(duration, max_duration=600):  # Max 10 minutes
        flash('Audio quá dài. Tối đa 10 phút.', 'danger')
        return redirect(url_for('speaking.topic_practice', topic_id=topic_id))
    
    # Deduct credits
    try:
        current_user.deduct_credits(
            amount=2,
            reference_type='speaking',
            reference_id=None,
            note=f'Speaking Part {topic.part} submission'
        )
        db.session.commit()
        
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('payment.packages'))
    
    # Save audio file
    audio_url = save_upload_file(audio_file, 'user-audio')
    
    if not audio_url:
        # Refund credits
        current_user.add_credits(
            amount=2,
            reference_type='refund',
            reference_id=None,
            note='Refund: Audio upload failed'
        )
        db.session.commit()
        
        flash('Lỗi khi upload audio. Vui lòng thử lại.', 'danger')
        return redirect(url_for('speaking.topic_practice', topic_id=topic_id))
    
    # Create submission
    submission = SpeakingSubmission(
        user_id=current_user.id,
        topic_id=topic.id,
        part=topic.part,
        audio_url=audio_url,
        duration=duration,
        credits_used=2
    )
    
    db.session.add(submission)
    db.session.commit()
    
    # Update transaction reference
    last_transaction = current_user.transactions.order_by(
        db.desc('created_at')
    ).first()
    if last_transaction:
        last_transaction.reference_id = submission.id
        db.session.commit()
    
    # Score with AI (STT + Gemini)
    try:
        scores, cost = scoring_service.score_speaking(submission, topic)
        
        flash('Bài nói đã được chấm điểm!', 'success')
        return redirect(url_for('speaking.submission_result', submission_id=submission.id))
        
    except Exception as e:
        current_app.logger.error(f"Speaking scoring error: {str(e)}")
        
        # Refund credits on error
        current_user.add_credits(
            amount=2,
            reference_type='refund',
            reference_id=submission.id,
            note='Refund: AI scoring failed'
        )
        db.session.commit()
        
        flash(f'Lỗi khi chấm bài: {str(e)}. Credits đã được hoàn lại.', 'danger')
        return redirect(url_for('speaking.topic_practice', topic_id=topic_id))


@bp.route('/submission/<int:submission_id>')
@login_required
def submission_result(submission_id):
    """View speaking submission result"""
    
    submission = SpeakingSubmission.query.get_or_404(submission_id)
    
    # Check ownership
    if submission.user_id != current_user.id and not current_user.is_admin():
        flash('Bạn không có quyền xem kết quả này.', 'danger')
        return redirect(url_for('speaking.index'))
    
    topic = submission.topic
    
    return render_template('speaking/submission_result.html',
                         submission=submission,
                         topic=topic)


@bp.route('/history')
@login_required
def history():
    """Speaking submission history"""
    
    submissions = SpeakingSubmission.query.filter_by(user_id=current_user.id)\
        .order_by(db.desc(SpeakingSubmission.created_at)).all()
    
    return render_template('speaking/history.html', submissions=submissions)