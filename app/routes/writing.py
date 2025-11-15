# app/routes/writing.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app import db
from app.models.writing import WritingTask, WritingSubmission
from app.services.scoring_service import scoring_service
from app.utils.decorators import credits_required
from app.utils.validators import validate_essay
from datetime import datetime

bp = Blueprint('writing', __name__, url_prefix='/writing')

@bp.route('/')
@login_required
def index():
    """Writing home"""
    return render_template('writing/index.html')


@bp.route('/task-1')
@login_required
def task_1_list():
    """List Writing Task 1 questions"""
    
    tasks = WritingTask.query.filter_by(
        task_type=1,
        is_active=True,
        deleted_at=None
    ).all()
    
    return render_template('writing/task_1_list.html', tasks=tasks)


@bp.route('/task-2')
@login_required
def task_2_list():
    """List Writing Task 2 questions"""
    
    tasks = WritingTask.query.filter_by(
        task_type=2,
        is_active=True,
        deleted_at=None
    ).all()
    
    return render_template('writing/task_2_list.html', tasks=tasks)


@bp.route('/task/<int:task_id>')
@login_required
def task_practice(task_id):
    """Practice writing task"""
    
    task = WritingTask.query.get_or_404(task_id)
    
    # Get credit cost
    credit_cost = current_app.config['CREDIT_COSTS']['writing_task_1'] \
        if task.task_type == 1 else current_app.config['CREDIT_COSTS']['writing_task_2']
    
    return render_template('writing/task_practice.html', 
                         task=task,
                         credit_cost=credit_cost)


@bp.route('/task/<int:task_id>/submit', methods=['POST'])
@login_required
@credits_required(1)
def task_submit(task_id):
    """Submit writing task"""
    
    task = WritingTask.query.get_or_404(task_id)
    essay_text = request.form.get('essay_text', '').strip()
    
    # Validate essay
    is_valid, result = validate_essay(essay_text, min_words=150 if task.task_type == 1 else 250)
    
    if not is_valid:
        flash(result, 'danger')
        return redirect(url_for('writing.task_practice', task_id=task_id))
    
    essay_text = result  # In case it was truncated
    word_count = len(essay_text.split())
    
    # Deduct credits
    try:
        current_user.deduct_credits(
            amount=1,
            reference_type='writing',
            reference_id=None,  # Will update after creating submission
            note=f'Writing Task {task.task_type} submission'
        )
        db.session.commit()
        
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('payment.packages'))
    
    # Create submission
    submission = WritingSubmission(
        user_id=current_user.id,
        task_id=task.id,
        essay_text=essay_text,
        word_count=word_count,
        credits_used=1
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
    
    # Score with AI (async in production)
    try:
        scores, cost = scoring_service.score_writing(submission, task)
        
        flash('Bài viết đã được chấm điểm!', 'success')
        return redirect(url_for('writing.submission_result', submission_id=submission.id))
        
    except Exception as e:
        # Refund credits on error
        current_user.add_credits(
            amount=1,
            reference_type='refund',
            reference_id=submission.id,
            note='Refund: AI scoring failed'
        )
        db.session.commit()
        
        flash(f'Lỗi khi chấm bài: {str(e)}. Credits đã được hoàn lại.', 'danger')
        return redirect(url_for('writing.task_practice', task_id=task_id))


@bp.route('/submission/<int:submission_id>')
@login_required
def submission_result(submission_id):
    """View submission result"""
    
    submission = WritingSubmission.query.get_or_404(submission_id)
    
    # Check ownership
    if submission.user_id != current_user.id and not current_user.is_admin():
        flash('Bạn không có quyền xem kết quả này.', 'danger')
        return redirect(url_for('writing.index'))
    
    task = submission.task
    
    return render_template('writing/submission_result.html',
                         submission=submission,
                         task=task)


@bp.route('/history')
@login_required
def history():
    """Writing submission history"""
    
    submissions = WritingSubmission.query.filter_by(user_id=current_user.id)\
        .order_by(db.desc(WritingSubmission.created_at)).all()
    
    return render_template('writing/history.html', submissions=submissions)