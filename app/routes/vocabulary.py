# app/routes/vocabulary.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.vocabulary import (
    VocabularyTopic, VocabularyWord, VocabularyQuiz, 
    VocabularyQuestion, UserVocabularyProgress, VocabularyQuizAttempt
)
from datetime import datetime
from sqlalchemy import or_

bp = Blueprint('vocabulary', __name__, url_prefix='/vocabulary')

@bp.route('/')
@login_required
def index():
    """Vocabulary home - list topics"""
    
    topics = VocabularyTopic.query.filter_by(is_active=True)\
        .order_by(VocabularyTopic.order).all()
    
    # Get user progress for each topic
    for topic in topics:
        # Count learned words
        learned = UserVocabularyProgress.query.join(VocabularyWord)\
            .filter(
                UserVocabularyProgress.user_id == current_user.id,
                VocabularyWord.topic_id == topic.id,
                UserVocabularyProgress.status.in_(['mastered', 'learning'])
            ).count()
        
        topic.user_learned = learned
        topic.total_words = topic.word_count()
    
    return render_template('vocabulary/index.html', topics=topics)


@bp.route('/topic/<int:topic_id>')
@login_required
def topic_words(topic_id):
    """View words in a topic"""
    
    topic = VocabularyTopic.query.get_or_404(topic_id)
    
    # Get words
    words = VocabularyWord.query.filter_by(
        topic_id=topic_id,
        deleted_at=None
    ).all()
    
    # Get user progress for each word
    for word in words:
        progress = UserVocabularyProgress.query.filter_by(
            user_id=current_user.id,
            word_id=word.id
        ).first()
        
        word.user_progress = progress
    
    return render_template('vocabulary/topic_words.html', topic=topic, words=words)


@bp.route('/word/<int:word_id>')
@login_required
def word_detail(word_id):
    """Word detail page"""
    
    word = VocabularyWord.query.get_or_404(word_id)
    
    # Get or create user progress
    progress = UserVocabularyProgress.query.filter_by(
        user_id=current_user.id,
        word_id=word.id
    ).first()
    
    if not progress:
        progress = UserVocabularyProgress(
            user_id=current_user.id,
            word_id=word.id
        )
        db.session.add(progress)
        db.session.commit()
    
    return render_template('vocabulary/word_detail.html', word=word, progress=progress)


@bp.route('/word/<int:word_id>/mark-learned', methods=['POST'])
@login_required
def mark_word_learned(word_id):
    """Mark word as learned"""
    
    word = VocabularyWord.query.get_or_404(word_id)
    
    progress = UserVocabularyProgress.query.filter_by(
        user_id=current_user.id,
        word_id=word.id
    ).first()
    
    if not progress:
        progress = UserVocabularyProgress(
            user_id=current_user.id,
            word_id=word.id
        )
        db.session.add(progress)
    
    progress.status = 'learning'
    progress.mastery_level = 1
    progress.last_reviewed = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True})


@bp.route('/quizzes')
@login_required
def quizzes():
    """List all quizzes"""
    
    quizzes = VocabularyQuiz.query.filter_by(is_active=True).all()
    
    # Get user attempts
    for quiz in quizzes:
        attempts = VocabularyQuizAttempt.query.filter_by(
            user_id=current_user.id,
            quiz_id=quiz.id
        ).count()
        
        best_score = db.session.query(db.func.max(VocabularyQuizAttempt.score))\
            .filter_by(user_id=current_user.id, quiz_id=quiz.id).scalar()
        
        quiz.user_attempts = attempts
        quiz.user_best_score = best_score
    
    return render_template('vocabulary/quizzes.html', quizzes=quizzes)


@bp.route('/quiz/<int:quiz_id>')
@login_required
def quiz_start(quiz_id):
    """Start quiz"""
    
    quiz = VocabularyQuiz.query.get_or_404(quiz_id)
    questions = quiz.questions.all()
    
    return render_template('vocabulary/quiz_start.html', 
                         quiz=quiz, 
                         questions=questions)


@bp.route('/quiz/<int:quiz_id>/submit', methods=['POST'])
@login_required
def quiz_submit(quiz_id):
    """Submit quiz answers"""
    
    quiz = VocabularyQuiz.query.get_or_404(quiz_id)
    questions = quiz.questions.all()
    
    # Get user answers
    answers = {}
    for question in questions:
        answer = request.form.get(f'question_{question.id}', '').strip()
        answers[question.id] = answer
    
    # Grade quiz
    correct_count = 0
    for question in questions:
        user_answer = answers.get(question.id, '').lower()
        correct_answer = question.correct_answer.lower()
        
        if user_answer == correct_answer:
            correct_count += 1
            
            # Update word progress if applicable
            if question.word_id:
                progress = UserVocabularyProgress.query.filter_by(
                    user_id=current_user.id,
                    word_id=question.word_id
                ).first()
                
                if not progress:
                    progress = UserVocabularyProgress(
                        user_id=current_user.id,
                        word_id=question.word_id
                    )
                    db.session.add(progress)
                
                progress.update_mastery(True)
    
    total_questions = len(questions)
    score_percent = (correct_count / total_questions * 100) if total_questions > 0 else 0
    
    # Save attempt
    attempt = VocabularyQuizAttempt(
        user_id=current_user.id,
        quiz_id=quiz.id,
        score=score_percent,
        correct_answers=correct_count,
        total_questions=total_questions,
        answers=answers,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )
    
    db.session.add(attempt)
    db.session.commit()
    
    return redirect(url_for('vocabulary.quiz_result', attempt_id=attempt.id))


@bp.route('/quiz/result/<int:attempt_id>')
@login_required
def quiz_result(attempt_id):
    """Quiz result page"""
    
    attempt = VocabularyQuizAttempt.query.get_or_404(attempt_id)
    
    # Check ownership
    if attempt.user_id != current_user.id:
        flash('Bạn không có quyền xem kết quả này.', 'danger')
        return redirect(url_for('vocabulary.quizzes'))
    
    quiz = attempt.quiz
    questions = quiz.questions.all()
    
    # Build results
    results = []
    for question in questions:
        user_answer = attempt.answers.get(str(question.id), '')
        is_correct = user_answer.lower() == question.correct_answer.lower()
        
        results.append({
            'question': question,
            'user_answer': user_answer,
            'is_correct': is_correct
        })
    
    return render_template('vocabulary/quiz_result.html',
                         attempt=attempt,
                         quiz=quiz,
                         results=results)