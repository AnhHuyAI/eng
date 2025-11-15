# app/routes/listening.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import ListeningSection, ListeningAttempt

bp = Blueprint('listening', __name__, url_prefix='/listening')

@bp.route('/')
@login_required
def index():
    """List all listening sections"""
    sections = ListeningSection.query.filter_by(is_active=True).all()
    return render_template('listening/index.html', sections=sections)

@bp.route('/<int:section_id>')
@login_required
def practice(section_id):
    """Practice a listening section"""
    section = ListeningSection.query.get_or_404(section_id)
    return render_template('listening/practice.html', section=section)

@bp.route('/<int:section_id>/submit', methods=['POST'])
@login_required
def submit(section_id):
    """Submit listening answers"""
    section = ListeningSection.query.get_or_404(section_id)

    # Get answers from form
    answers = {}
    for question in section.questions:
        answer_key = f'question_{question.id}'
        answers[str(question.id)] = request.form.get(answer_key, '').strip()

    # Create attempt
    attempt = ListeningAttempt(
        user_id=current_user.id,
        section_id=section.id,
        answers=answers
    )

    # Auto-grade
    from app.services import get_scoring_service
    scoring_service = get_scoring_service()
    band_score, question_results = scoring_service.auto_grade_listening(attempt, section)

    db.session.add(attempt)
    db.session.commit()

    flash(f'Band score: {band_score}', 'success')
    return redirect(url_for('listening.result', attempt_id=attempt.id))

@bp.route('/result/<int:attempt_id>')
@login_required
def result(attempt_id):
    """View listening result"""
    attempt = ListeningAttempt.query.get_or_404(attempt_id)

    if attempt.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('listening.index'))

    return render_template('listening/result.html', attempt=attempt)
