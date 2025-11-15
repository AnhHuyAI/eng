# app/routes/reading.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.reading import ReadingPassage, ReadingQuestion, ReadingAttempt
from app.services.scoring_service import scoring_service
from datetime import datetime

bp = Blueprint('reading', __name__, url_prefix='/reading')

@bp.route('/')
@login_required
def index():
    """Reading home"""
    return render_template('reading/index.html')


@bp.route('/passages')
@login_required
def passages():
    """List all reading passages"""
    
    topic = request.args.get('topic')
    difficulty = request.args.get('difficulty')
    
    query = ReadingPassage.query.filter_by(
        is_active=True,
        deleted_at=None
    )
    
    if topic:
        query = query.filter_by(topic=topic)
    
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    
    passages = query.all()
    
    return render_template('reading/passages.html', passages=passages)


@bp.route('/passage/<int:passage_id>')
@login_required
def passage_practice(passage_id):
    """Practice reading passage"""
    
    passage = ReadingPassage.query.get_or_404(passage_id)
    questions = passage.questions.all()
    
    return render_template('reading/passage_practice.html',
                         passage=passage,
                         questions=questions)


@bp.route('/passage/<int:passage_id>/submit', methods=['POST'])
@login_required
def passage_submit(passage_id):
    """Submit reading answers (FREE - auto grading)"""
    
    passage = ReadingPassage.query.get_or_404(passage_id)
    questions = passage.questions.all()
    
    # Get user answers
    answers = {}
    for question in questions:
        answer = request.form.get(f'question_{question.id}', '').strip()
        answers[question.id] = answer
    
    # Get time taken
    time_taken = int(request.form.get('time_taken', 0))
    
    # Create attempt
    attempt = ReadingAttempt(
        user_id=current_user.id,
        passage_id=passage.id,
        answers=answers,
        total_questions=len(questions),
        time_taken=time_taken
    )
    
    db.session.add(attempt)
    db.session.commit()
    
    # Auto-grade (FREE)
    band_score, question_results = scoring_service.auto_grade_reading(attempt, passage)
    
    flash(f'Bài đọc đã được chấm! Band score: {band_score}', 'success')
    return redirect(url_for('reading.attempt_result', attempt_id=attempt.id))


@bp.route('/attempt/<int:attempt_id>')
@login_required
def attempt_result(attempt_id):
    """View reading attempt result"""
    
    attempt = ReadingAttempt.query.get_or_404(attempt_id)
    
    # Check ownership
    if attempt.user_id != current_user.id and not current_user.is_admin():
        flash('Bạn không có quyền xem kết quả này.', 'danger')
        return redirect(url_for('reading.index'))
    
    passage = attempt.passage
    questions = passage.questions.all()
    
    # Build results
    results = []
    for question in questions:
        result_data = attempt.question_results.get(str(question.id), {})
        results.append({
            'question': question,
            'user_answer': result_data.get('user_answer', ''),
            'correct_answer': result_data.get('correct_answer', ''),
            'is_correct': result_data.get('correct', False),
            'explanation': result_data.get('explanation', ''),
            'paragraph_reference': result_data.get('paragraph_reference', '')
        })
    
    return render_template('reading/attempt_result.html',
                         attempt=attempt,
                         passage=passage,
                         results=results)


@bp.route('/history')
@login_required
def history():
    """Reading attempt history"""
    
    attempts = ReadingAttempt.query.filter_by(user_id=current_user.id)\
        .order_by(db.desc(ReadingAttempt.completed_at)).all()
    
    return render_template('reading/history.html', attempts=attempts)