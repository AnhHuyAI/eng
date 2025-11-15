# app/routes/admin.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.user import User, Transaction
from app.models.vocabulary import VocabularyTopic, VocabularyWord, VocabularyQuiz, VocabularyQuestion
from app.models.listening import ListeningSection, ListeningQuestion
from app.models.reading import ReadingPassage, ReadingQuestion
from app.models.speaking import SpeakingTopic
from app.models.writing import WritingTask
from app.models.payment import PaymentRequest
from app.utils.decorators import admin_required
from app.utils.helpers import save_upload_file
from app.utils.validators import allowed_file
from datetime import datetime, timedelta
from sqlalchemy import func
import json

bp = Blueprint('admin', __name__, url_prefix='/admin')

# ============================================
# ADMIN DASHBOARD
# ============================================

@bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard"""
    
    # Statistics
    stats = {
        'total_users': User.query.filter_by(role='user').count(),
        'active_users_today': User.query.filter(
            User.last_login >= datetime.utcnow() - timedelta(days=1)
        ).count(),
        'pending_payments': PaymentRequest.query.filter_by(status='pending').count(),
        'total_revenue': db.session.query(func.sum(PaymentRequest.amount))\
            .filter_by(status='approved').scalar() or 0,
    }
    
    # Content stats
    stats['vocabulary_topics'] = VocabularyTopic.query.filter_by(is_active=True).count()
    stats['vocabulary_words'] = VocabularyWord.query.filter_by(deleted_at=None).count()
    stats['listening_sections'] = ListeningSection.query.filter_by(is_active=True).count()
    stats['reading_passages'] = ReadingPassage.query.filter_by(is_active=True).count()
    stats['speaking_topics'] = SpeakingTopic.query.filter_by(is_active=True).count()
    stats['writing_tasks'] = WritingTask.query.filter_by(is_active=True).count()
    
    # Recent pending payments
    pending_payments = PaymentRequest.query.filter_by(status='pending')\
        .order_by(PaymentRequest.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         pending_payments=pending_payments)


# ============================================
# PAYMENT MANAGEMENT
# ============================================

@bp.route('/payments/pending')
@admin_required
def payments_pending():
    """Pending payments"""
    
    payments = PaymentRequest.query.filter_by(status='pending')\
        .order_by(PaymentRequest.created_at.desc()).all()
    
    return render_template('admin/payments/pending.html', payments=payments)


@bp.route('/payments/<int:payment_id>/approve', methods=['POST'])
@admin_required
def payment_approve(payment_id):
    """Approve payment"""
    
    payment = PaymentRequest.query.get_or_404(payment_id)
    
    if payment.status != 'pending':
        return jsonify({'error': 'Payment already processed'}), 400
    
    # Update payment
    payment.status = 'approved'
    payment.reviewed_by = current_user.id
    payment.reviewed_at = datetime.utcnow()
    
    # Add credits to user
    user = User.query.get(payment.user_id)
    user.add_credits(
        amount=payment.credits_requested,
        reference_type='payment',
        reference_id=payment.id,
        note=f'Nạp {payment.amount:,} VNĐ - Package {payment.package_id}'
    )
    
    db.session.commit()
    
    # Send email notification
    from app.services.email_service import email_service
    email_service.send_payment_approved(user, payment)
    
    flash(f'Đã duyệt thanh toán và cộng {payment.credits_requested} credits cho {user.email}', 'success')
    return redirect(url_for('admin.payments_pending'))


@bp.route('/payments/<int:payment_id>/reject', methods=['POST'])
@admin_required
def payment_reject(payment_id):
    """Reject payment"""
    
    payment = PaymentRequest.query.get_or_404(payment_id)
    
    if payment.status != 'pending':
        return jsonify({'error': 'Payment already processed'}), 400
    
    reason = request.form.get('reason', '')
    
    # Update payment
    payment.status = 'rejected'
    payment.reviewed_by = current_user.id
    payment.reviewed_at = datetime.utcnow()
    payment.admin_note = reason
    
    db.session.commit()
    
    # Send email notification
    from app.services.email_service import email_service
    user = User.query.get(payment.user_id)
    email_service.send_payment_rejected(user, payment)
    
    flash(f'Đã từ chối thanh toán của {user.email}', 'info')
    return redirect(url_for('admin.payments_pending'))


@bp.route('/payments/history')
@admin_required
def payments_history():
    """Payment history"""
    
    status = request.args.get('status')
    
    query = PaymentRequest.query
    
    if status:
        query = query.filter_by(status=status)
    
    payments = query.order_by(PaymentRequest.created_at.desc()).all()
    
    return render_template('admin/payments/history.html', payments=payments)


# ============================================
# USER MANAGEMENT
# ============================================

@bp.route('/users')
@admin_required
def users():
    """List all users"""
    
    users = User.query.filter_by(role='user').order_by(User.created_at.desc()).all()
    
    return render_template('admin/users/list.html', users=users)


@bp.route('/user/<int:user_id>')
@admin_required
def user_detail(user_id):
    """User detail"""
    
    user = User.query.get_or_404(user_id)
    
    # Get user stats
    from app.models.writing import WritingSubmission
    from app.models.speaking import SpeakingSubmission
    from app.models.listening import ListeningAttempt
    from app.models.reading import ReadingAttempt
    
    stats = {
        'writings': WritingSubmission.query.filter_by(user_id=user.id).count(),
        'speakings': SpeakingSubmission.query.filter_by(user_id=user.id).count(),
        'listenings': ListeningAttempt.query.filter_by(user_id=user.id).count(),
        'readings': ReadingAttempt.query.filter_by(user_id=user.id).count(),
    }
    
    # Recent transactions
    transactions = user.transactions.order_by(db.desc('created_at')).limit(20).all()
    
    return render_template('admin/users/detail.html',
                         user=user,
                         stats=stats,
                         transactions=transactions)


@bp.route('/user/<int:user_id>/add-credits', methods=['POST'])
@admin_required
def user_add_credits(user_id):
    """Manually add credits to user"""
    
    user = User.query.get_or_404(user_id)
    amount = int(request.form.get('amount', 0))
    note = request.form.get('note', '')
    
    if amount <= 0:
        flash('Số credits phải lớn hơn 0', 'danger')
        return redirect(url_for('admin.user_detail', user_id=user_id))
    
    user.add_credits(
        amount=amount,
        reference_type='admin_bonus',
        reference_id=None,
        note=note or f'Admin cộng thủ công bởi {current_user.email}'
    )
    
    db.session.commit()
    
    flash(f'Đã cộng {amount} credits cho {user.email}', 'success')
    return redirect(url_for('admin.user_detail', user_id=user_id))


@bp.route('/user/<int:user_id>/toggle-active', methods=['POST'])
@admin_required
def user_toggle_active(user_id):
    """Ban/Unban user"""
    
    user = User.query.get_or_404(user_id)
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'kích hoạt' if user.is_active else 'khóa'
    flash(f'Đã {status} tài khoản {user.email}', 'success')
    
    return redirect(url_for('admin.user_detail', user_id=user_id))


# ============================================
# VOCABULARY MANAGEMENT
# ============================================

@bp.route('/vocabulary/topics')
@admin_required
def vocabulary_topics():
    """List vocabulary topics"""
    
    topics = VocabularyTopic.query.order_by(VocabularyTopic.order).all()
    
    return render_template('admin/vocabulary/topics.html', topics=topics)


@bp.route('/vocabulary/topic/add', methods=['GET', 'POST'])
@admin_required
def vocabulary_topic_add():
    """Add vocabulary topic"""
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        icon = request.form.get('icon')
        order = int(request.form.get('order', 0))
        
        topic = VocabularyTopic(
            name=name,
            description=description,
            icon=icon,
            order=order
        )
        
        db.session.add(topic)
        db.session.commit()
        
        flash(f'Đã thêm topic: {name}', 'success')
        return redirect(url_for('admin.vocabulary_topics'))
    
    return render_template('admin/vocabulary/topic_add.html')


@bp.route('/vocabulary/topic/<int:topic_id>/edit', methods=['GET', 'POST'])
@admin_required
def vocabulary_topic_edit(topic_id):
    """Edit vocabulary topic"""
    
    topic = VocabularyTopic.query.get_or_404(topic_id)
    
    if request.method == 'POST':
        topic.name = request.form.get('name')
        topic.description = request.form.get('description')
        topic.icon = request.form.get('icon')
        topic.order = int(request.form.get('order', 0))
        
        db.session.commit()
        
        flash(f'Đã cập nhật topic: {topic.name}', 'success')
        return redirect(url_for('admin.vocabulary_topics'))
    
    return render_template('admin/vocabulary/topic_edit.html', topic=topic)


@bp.route('/vocabulary/topic/<int:topic_id>/delete', methods=['POST'])
@admin_required
def vocabulary_topic_delete(topic_id):
    """Delete vocabulary topic (CASCADE deletes all words)"""
    
    topic = VocabularyTopic.query.get_or_404(topic_id)
    
    name = topic.name
    db.session.delete(topic)  # CASCADE will delete all related words
    db.session.commit()
    
    flash(f'Đã xóa topic: {name} và tất cả từ vựng bên trong', 'success')
    return redirect(url_for('admin.vocabulary_topics'))


@bp.route('/vocabulary/words')
@admin_required
def vocabulary_words():
    """List vocabulary words"""
    
    topic_id = request.args.get('topic_id', type=int)
    
    query = VocabularyWord.query.filter_by(deleted_at=None)
    
    if topic_id:
        query = query.filter_by(topic_id=topic_id)
    
    words = query.all()
    topics = VocabularyTopic.query.all()
    
    return render_template('admin/vocabulary/words.html',
                         words=words,
                         topics=topics,
                         selected_topic_id=topic_id)


@bp.route('/vocabulary/word/add', methods=['GET', 'POST'])
@admin_required
def vocabulary_word_add():
    """Add vocabulary word"""
    
    if request.method == 'POST':
        topic_id = int(request.form.get('topic_id'))
        word = request.form.get('word')
        pronunciation = request.form.get('pronunciation')
        part_of_speech = request.form.get('part_of_speech')
        definition_vi = request.form.get('definition_vi')
        definition_en = request.form.get('definition_en')
        level = request.form.get('level')
        frequency_band = int(request.form.get('frequency_band', 6))
        
        # Parse JSON fields
        example_sentences = request.form.get('example_sentences', '[]')
        synonyms = request.form.get('synonyms', '[]')
        antonyms = request.form.get('antonyms', '[]')
        
        try:
            example_sentences = json.loads(example_sentences)
            synonyms = json.loads(synonyms)
            antonyms = json.loads(antonyms)
        except:
            flash('JSON format không hợp lệ', 'danger')
            return redirect(url_for('admin.vocabulary_word_add'))
        
        # Handle audio upload
        audio_file = request.files.get('audio_file')
        audio_url = save_upload_file(audio_file, 'vocabulary/audio') if audio_file else None
        
        # Handle image upload
        image_file = request.files.get('image_file')
        image_url = save_upload_file(image_file, 'vocabulary/images') if image_file else None
        
        vocab_word = VocabularyWord(
            topic_id=topic_id,
            word=word,
            pronunciation=pronunciation,
            part_of_speech=part_of_speech,
            definition_vi=definition_vi,
            definition_en=definition_en,
            example_sentences=example_sentences,
            synonyms=synonyms,
            antonyms=antonyms,
            level=level,
            frequency_band=frequency_band,
            audio_url=audio_url,
            image_url=image_url
        )
        
        db.session.add(vocab_word)
        db.session.commit()
        
        flash(f'Đã thêm từ: {word}', 'success')
        return redirect(url_for('admin.vocabulary_words', topic_id=topic_id))
    
    topics = VocabularyTopic.query.all()
    return render_template('admin/vocabulary/word_add.html', topics=topics)


# app/routes/admin.py (tiếp tục)

# ============================================
# LISTENING MANAGEMENT
# ============================================

@bp.route('/listening/sections')
@admin_required
def listening_sections():
    """List listening sections"""
    
    sections = ListeningSection.query.filter_by(deleted_at=None)\
        .order_by(ListeningSection.created_at.desc()).all()
    
    return render_template('admin/listening/sections.html', sections=sections)


@bp.route('/listening/section/add', methods=['GET', 'POST'])
@admin_required
def listening_section_add():
    """Add listening section"""
    
    if request.method == 'POST':
        title = request.form.get('title')
        part_number = int(request.form.get('part_number'))
        description = request.form.get('description')
        difficulty = request.form.get('difficulty')
        topic = request.form.get('topic')
        transcript = request.form.get('transcript')
        
        # Handle audio upload
        audio_file = request.files.get('audio_file')
        
        if not audio_file:
            flash('Vui lòng upload file audio', 'danger')
            return redirect(url_for('admin.listening_section_add'))
        
        allowed_extensions = current_app.config['ALLOWED_AUDIO_EXTENSIONS']
        if not allowed_file(audio_file.filename, allowed_extensions):
            flash(f'Định dạng file không hợp lệ. Chỉ chấp nhận: {", ".join(allowed_extensions)}', 'danger')
            return redirect(url_for('admin.listening_section_add'))
        
        audio_url = save_upload_file(audio_file, 'audio')
        
        if not audio_url:
            flash('Lỗi khi upload audio', 'danger')
            return redirect(url_for('admin.listening_section_add'))
        
        # Create section
        section = ListeningSection(
            title=title,
            part_number=part_number,
            description=description,
            audio_url=audio_url,
            transcript=transcript,
            difficulty=difficulty,
            topic=topic
        )
        
        db.session.add(section)
        db.session.commit()
        
        flash(f'Đã thêm section: {title}. Bây giờ hãy thêm câu hỏi.', 'success')
        return redirect(url_for('admin.listening_questions', section_id=section.id))
    
    return render_template('admin/listening/section_add.html')


@bp.route('/listening/section/<int:section_id>/edit', methods=['GET', 'POST'])
@admin_required
def listening_section_edit(section_id):
    """Edit listening section"""
    
    section = ListeningSection.query.get_or_404(section_id)
    
    if request.method == 'POST':
        section.title = request.form.get('title')
        section.part_number = int(request.form.get('part_number'))
        section.description = request.form.get('description')
        section.difficulty = request.form.get('difficulty')
        section.topic = request.form.get('topic')
        section.transcript = request.form.get('transcript')
        
        # Handle new audio upload
        audio_file = request.files.get('audio_file')
        if audio_file and audio_file.filename:
            audio_url = save_upload_file(audio_file, 'audio')
            if audio_url:
                section.audio_url = audio_url
        
        db.session.commit()
        
        flash(f'Đã cập nhật section: {section.title}', 'success')
        return redirect(url_for('admin.listening_sections'))
    
    return render_template('admin/listening/section_edit.html', section=section)


@bp.route('/listening/section/<int:section_id>/delete', methods=['POST'])
@admin_required
def listening_section_delete(section_id):
    """Delete listening section (CASCADE deletes all questions)"""
    
    section = ListeningSection.query.get_or_404(section_id)
    
    title = section.title
    db.session.delete(section)
    db.session.commit()
    
    flash(f'Đã xóa section: {title}', 'success')
    return redirect(url_for('admin.listening_sections'))


@bp.route('/listening/section/<int:section_id>/questions')
@admin_required
def listening_questions(section_id):
    """Manage questions for listening section"""
    
    section = ListeningSection.query.get_or_404(section_id)
    questions = section.questions.all()
    
    return render_template('admin/listening/questions.html',
                         section=section,
                         questions=questions)


@bp.route('/listening/section/<int:section_id>/question/add', methods=['GET', 'POST'])
@admin_required
def listening_question_add(section_id):
    """Add listening question"""
    
    section = ListeningSection.query.get_or_404(section_id)
    
    if request.method == 'POST':
        question_number = int(request.form.get('question_number'))
        question_type = request.form.get('question_type')
        question_text = request.form.get('question_text')
        correct_answer = request.form.get('correct_answer')
        explanation = request.form.get('explanation')
        start_time = request.form.get('start_time', type=int)
        end_time = request.form.get('end_time', type=int)
        
        # Parse options (for MCQ)
        options_str = request.form.get('options', '[]')
        try:
            options = json.loads(options_str)
        except:
            options = None
        
        # Handle image upload (for map/diagram)
        image_file = request.files.get('image_file')
        image_url = save_upload_file(image_file, 'images') if image_file else None
        
        question = ListeningQuestion(
            section_id=section_id,
            question_number=question_number,
            question_type=question_type,
            question_text=question_text,
            options=options,
            correct_answer=correct_answer,
            explanation=explanation,
            start_time=start_time,
            end_time=end_time,
            image_url=image_url
        )
        
        db.session.add(question)
        db.session.commit()
        
        flash(f'Đã thêm câu hỏi #{question_number}', 'success')
        return redirect(url_for('admin.listening_questions', section_id=section_id))
    
    return render_template('admin/listening/question_add.html', section=section)


@bp.route('/listening/question/<int:question_id>/delete', methods=['POST'])
@admin_required
def listening_question_delete(question_id):
    """Delete listening question"""
    
    question = ListeningQuestion.query.get_or_404(question_id)
    section_id = question.section_id
    
    db.session.delete(question)
    db.session.commit()
    
    flash(f'Đã xóa câu hỏi', 'success')
    return redirect(url_for('admin.listening_questions', section_id=section_id))


# ============================================
# READING MANAGEMENT
# ============================================

@bp.route('/reading/passages')
@admin_required
def reading_passages():
    """List reading passages"""
    
    passages = ReadingPassage.query.filter_by(deleted_at=None)\
        .order_by(ReadingPassage.created_at.desc()).all()
    
    return render_template('admin/reading/passages.html', passages=passages)


@bp.route('/reading/passage/add', methods=['GET', 'POST'])
@admin_required
def reading_passage_add():
    """Add reading passage"""
    
    if request.method == 'POST':
        title = request.form.get('title')
        passage_text = request.form.get('passage_text')
        topic = request.form.get('topic')
        difficulty = request.form.get('difficulty')
        source = request.form.get('source')
        
        # Calculate word count
        word_count = len(passage_text.split())
        
        # Estimate reading time
        from app.utils.helpers import calculate_reading_time
        reading_time = calculate_reading_time(word_count)
        
        passage = ReadingPassage(
            title=title,
            passage_text=passage_text,
            topic=topic,
            difficulty=difficulty,
            word_count=word_count,
            reading_time=reading_time,
            source=source
        )
        
        db.session.add(passage)
        db.session.commit()
        
        flash(f'Đã thêm passage: {title}. Bây giờ hãy thêm câu hỏi.', 'success')
        return redirect(url_for('admin.reading_questions', passage_id=passage.id))
    
    return render_template('admin/reading/passage_add.html')


@bp.route('/reading/passage/<int:passage_id>/edit', methods=['GET', 'POST'])
@admin_required
def reading_passage_edit(passage_id):
    """Edit reading passage"""
    
    passage = ReadingPassage.query.get_or_404(passage_id)
    
    if request.method == 'POST':
        passage.title = request.form.get('title')
        passage.passage_text = request.form.get('passage_text')
        passage.topic = request.form.get('topic')
        passage.difficulty = request.form.get('difficulty')
        passage.source = request.form.get('source')
        
        # Recalculate word count
        passage.word_count = len(passage.passage_text.split())
        from app.utils.helpers import calculate_reading_time
        passage.reading_time = calculate_reading_time(passage.word_count)
        
        db.session.commit()
        
        flash(f'Đã cập nhật passage: {passage.title}', 'success')
        return redirect(url_for('admin.reading_passages'))
    
    return render_template('admin/reading/passage_edit.html', passage=passage)


@bp.route('/reading/passage/<int:passage_id>/delete', methods=['POST'])
@admin_required
def reading_passage_delete(passage_id):
    """Delete reading passage (CASCADE deletes all questions)"""
    
    passage = ReadingPassage.query.get_or_404(passage_id)
    
    title = passage.title
    db.session.delete(passage)
    db.session.commit()
    
    flash(f'Đã xóa passage: {title}', 'success')
    return redirect(url_for('admin.reading_passages'))


@bp.route('/reading/passage/<int:passage_id>/questions')
@admin_required
def reading_questions(passage_id):
    """Manage questions for reading passage"""
    
    passage = ReadingPassage.query.get_or_404(passage_id)
    questions = passage.questions.all()
    
    return render_template('admin/reading/questions.html',
                         passage=passage,
                         questions=questions)


@bp.route('/reading/passage/<int:passage_id>/question/add', methods=['GET', 'POST'])
@admin_required
def reading_question_add(passage_id):
    """Add reading question"""
    
    passage = ReadingPassage.query.get_or_404(passage_id)
    
    if request.method == 'POST':
        question_number = int(request.form.get('question_number'))
        question_type = request.form.get('question_type')
        question_text = request.form.get('question_text')
        correct_answer = request.form.get('correct_answer')
        explanation = request.form.get('explanation')
        paragraph_reference = request.form.get('paragraph_reference')
        difficulty = request.form.get('difficulty')
        
        # Parse options
        options_str = request.form.get('options', '[]')
        try:
            options = json.loads(options_str)
        except:
            options = None
        
        question = ReadingQuestion(
            passage_id=passage_id,
            question_number=question_number,
            question_type=question_type,
            question_text=question_text,
            options=options,
            correct_answer=correct_answer,
            explanation=explanation,
            paragraph_reference=paragraph_reference,
            difficulty=difficulty
        )
        
        db.session.add(question)
        db.session.commit()
        
        flash(f'Đã thêm câu hỏi #{question_number}', 'success')
        return redirect(url_for('admin.reading_questions', passage_id=passage_id))
    
    return render_template('admin/reading/question_add.html', passage=passage)


@bp.route('/reading/question/<int:question_id>/delete', methods=['POST'])
@admin_required
def reading_question_delete(question_id):
    """Delete reading question"""
    
    question = ReadingQuestion.query.get_or_404(question_id)
    passage_id = question.passage_id
    
    db.session.delete(question)
    db.session.commit()
    
    flash(f'Đã xóa câu hỏi', 'success')
    return redirect(url_for('admin.reading_questions', passage_id=passage_id))


# ============================================
# SPEAKING MANAGEMENT
# ============================================

@bp.route('/speaking/topics')
@admin_required
def speaking_topics():
    """List speaking topics"""
    
    topics = SpeakingTopic.query.filter_by(deleted_at=None)\
        .order_by(SpeakingTopic.part, SpeakingTopic.created_at.desc()).all()
    
    return render_template('admin/speaking/topics.html', topics=topics)


@bp.route('/speaking/topic/add', methods=['GET', 'POST'])
@admin_required
def speaking_topic_add():
    """Add speaking topic"""
    
    if request.method == 'POST':
        part = int(request.form.get('part'))
        topic = request.form.get('topic')
        category = request.form.get('category')
        difficulty = request.form.get('difficulty')
        
        # Parse JSON fields based on part
        part1_questions = None
        cue_card_title = None
        cue_card_points = None
        part3_questions = None
        sample_answers = None
        
        if part == 1:
            part1_questions_str = request.form.get('part1_questions', '[]')
            try:
                part1_questions = json.loads(part1_questions_str)
            except:
                flash('Part 1 questions JSON không hợp lệ', 'danger')
                return redirect(url_for('admin.speaking_topic_add'))
        
        elif part == 2:
            cue_card_title = request.form.get('cue_card_title')
            cue_card_points_str = request.form.get('cue_card_points', '[]')
            try:
                cue_card_points = json.loads(cue_card_points_str)
            except:
                flash('Cue card points JSON không hợp lệ', 'danger')
                return redirect(url_for('admin.speaking_topic_add'))
        
        elif part == 3:
            part3_questions_str = request.form.get('part3_questions', '[]')
            try:
                part3_questions = json.loads(part3_questions_str)
            except:
                flash('Part 3 questions JSON không hợp lệ', 'danger')
                return redirect(url_for('admin.speaking_topic_add'))
        
        # Sample answers (optional)
        sample_answers_str = request.form.get('sample_answers', '{}')
        try:
            sample_answers = json.loads(sample_answers_str) if sample_answers_str else None
        except:
            sample_answers = None
        
        speaking_topic = SpeakingTopic(
            part=part,
            topic=topic,
            category=category,
            part1_questions=part1_questions,
            cue_card_title=cue_card_title,
            cue_card_points=cue_card_points,
            part3_questions=part3_questions,
            sample_answers=sample_answers,
            difficulty=difficulty
        )
        
        db.session.add(speaking_topic)
        db.session.commit()
        
        flash(f'Đã thêm speaking topic: {topic}', 'success')
        return redirect(url_for('admin.speaking_topics'))
    
    return render_template('admin/speaking/topic_add.html')


@bp.route('/speaking/topic/<int:topic_id>/edit', methods=['GET', 'POST'])
@admin_required
def speaking_topic_edit(topic_id):
    """Edit speaking topic"""
    
    topic = SpeakingTopic.query.get_or_404(topic_id)
    
    if request.method == 'POST':
        topic.topic = request.form.get('topic')
        topic.category = request.form.get('category')
        topic.difficulty = request.form.get('difficulty')
        
        # Update JSON fields based on part
        if topic.part == 1:
            part1_questions_str = request.form.get('part1_questions', '[]')
            try:
                topic.part1_questions = json.loads(part1_questions_str)
            except:
                flash('Part 1 questions JSON không hợp lệ', 'danger')
                return redirect(url_for('admin.speaking_topic_edit', topic_id=topic_id))
        
        elif topic.part == 2:
            topic.cue_card_title = request.form.get('cue_card_title')
            cue_card_points_str = request.form.get('cue_card_points', '[]')
            try:
                topic.cue_card_points = json.loads(cue_card_points_str)
            except:
                flash('Cue card points JSON không hợp lệ', 'danger')
                return redirect(url_for('admin.speaking_topic_edit', topic_id=topic_id))
        
        elif topic.part == 3:
            part3_questions_str = request.form.get('part3_questions', '[]')
            try:
                topic.part3_questions = json.loads(part3_questions_str)
            except:
                flash('Part 3 questions JSON không hợp lệ', 'danger')
                return redirect(url_for('admin.speaking_topic_edit', topic_id=topic_id))
        
        db.session.commit()
        
        flash(f'Đã cập nhật topic: {topic.topic}', 'success')
        return redirect(url_for('admin.speaking_topics'))
    
    return render_template('admin/speaking/topic_edit.html', topic=topic)


@bp.route('/speaking/topic/<int:topic_id>/delete', methods=['POST'])
@admin_required
def speaking_topic_delete(topic_id):
    """Delete speaking topic"""
    
    topic = SpeakingTopic.query.get_or_404(topic_id)
    
    topic_name = topic.topic
    db.session.delete(topic)
    db.session.commit()
    
    flash(f'Đã xóa topic: {topic_name}', 'success')
    return redirect(url_for('admin.speaking_topics'))


# ============================================
# WRITING MANAGEMENT
# ============================================

@bp.route('/writing/tasks')
@admin_required
def writing_tasks():
    """List writing tasks"""
    
    tasks = WritingTask.query.filter_by(deleted_at=None)\
        .order_by(WritingTask.task_type, WritingTask.created_at.desc()).all()
    
    return render_template('admin/writing/tasks.html', tasks=tasks)


@bp.route('/writing/task/add', methods=['GET', 'POST'])
@admin_required
def writing_task_add():
    """Add writing task"""
    
    if request.method == 'POST':
        task_type = int(request.form.get('task_type'))
        question_text = request.form.get('question_text')
        instructions = request.form.get('instructions')
        difficulty = request.form.get('difficulty')
        
        # Task 1 specific
        chart_type = None
        chart_image_url = None
        
        if task_type == 1:
            chart_type = request.form.get('chart_type')
            chart_image = request.files.get('chart_image')
            
            if chart_image:
                allowed_extensions = current_app.config['ALLOWED_IMAGE_EXTENSIONS']
                if allowed_file(chart_image.filename, allowed_extensions):
                    chart_image_url = save_upload_file(chart_image, 'images')
        
        # Task 2 specific
        topic = None
        essay_type = None
        
        if task_type == 2:
            topic = request.form.get('topic')
            essay_type = request.form.get('essay_type')
        
        # Sample answers (optional)
        sample_answer_band_6 = request.form.get('sample_answer_band_6')
        sample_answer_band_7 = request.form.get('sample_answer_band_7')
        sample_answer_band_9 = request.form.get('sample_answer_band_9')
        
        task = WritingTask(
            task_type=task_type,
            chart_type=chart_type,
            chart_image_url=chart_image_url,
            question_text=question_text,
            instructions=instructions,
            topic=topic,
            essay_type=essay_type,
            difficulty=difficulty,
            sample_answer_band_6=sample_answer_band_6,
            sample_answer_band_7=sample_answer_band_7,
            sample_answer_band_9=sample_answer_band_9
        )
        
        db.session.add(task)
        db.session.commit()
        
        flash(f'Đã thêm writing task', 'success')
        return redirect(url_for('admin.writing_tasks'))
    
    return render_template('admin/writing/task_add.html')


@bp.route('/writing/task/<int:task_id>/edit', methods=['GET', 'POST'])
@admin_required
def writing_task_edit(task_id):
    """Edit writing task"""
    
    task = WritingTask.query.get_or_404(task_id)
    
    if request.method == 'POST':
        task.question_text = request.form.get('question_text')
        task.instructions = request.form.get('instructions')
        task.difficulty = request.form.get('difficulty')
        
        if task.task_type == 1:
            task.chart_type = request.form.get('chart_type')
            
            # Handle new chart image
            chart_image = request.files.get('chart_image')
            if chart_image and chart_image.filename:
                allowed_extensions = current_app.config['ALLOWED_IMAGE_EXTENSIONS']
                if allowed_file(chart_image.filename, allowed_extensions):
                    chart_image_url = save_upload_file(chart_image, 'images')
                    if chart_image_url:
                        task.chart_image_url = chart_image_url
        
        elif task.task_type == 2:
            task.topic = request.form.get('topic')
            task.essay_type = request.form.get('essay_type')
        
        # Update sample answers
        task.sample_answer_band_6 = request.form.get('sample_answer_band_6')
        task.sample_answer_band_7 = request.form.get('sample_answer_band_7')
        task.sample_answer_band_9 = request.form.get('sample_answer_band_9')
        
        db.session.commit()
        
        flash(f'Đã cập nhật task', 'success')
        return redirect(url_for('admin.writing_tasks'))
    
    return render_template('admin/writing/task_edit.html', task=task)


@bp.route('/writing/task/<int:task_id>/delete', methods=['POST'])
@admin_required
def writing_task_delete(task_id):
    """Delete writing task"""
    
    task = WritingTask.query.get_or_404(task_id)
    
    db.session.delete(task)
    db.session.commit()
    
    flash(f'Đã xóa task', 'success')
    return redirect(url_for('admin.writing_tasks'))