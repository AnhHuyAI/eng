# run.py

import os
from app import create_app, db
from app.models import *  # Import all models

app = create_app(os.getenv('FLASK_ENV') or 'development')

@app.shell_context_processor
def make_shell_context():
    """Shell context for flask shell"""
    return {
        'db': db,
        # Users
        'User': User,
        'Transaction': Transaction,
        # Teacher-Student
        'TeacherClass': TeacherClass,
        'ClassStudent': ClassStudent,
        'Assignment': Assignment,
        # Tracking
        'GeminiUsage': GeminiUsage,
        # Content
        'VocabularyTopic': VocabularyTopic,
        'VocabularyWord': VocabularyWord,
        'ListeningSection': ListeningSection,
        'ReadingPassage': ReadingPassage,
        'SpeakingTopic': SpeakingTopic,
        'WritingTask': WritingTask,
        # Payment
        'PaymentRequest': PaymentRequest,
    }

@app.cli.command()
def init_db():
    """Initialize database with sample data"""
    from flask import current_app
    from datetime import datetime

    db.create_all()

    # Create admin user
    admin = User.query.filter_by(email='admin@ielts.com').first()
    if not admin:
        admin = User(
            email='admin@ielts.com',
            full_name='Administrator',
            role='admin',
            credits=999999,  # Unlimited for admin
            is_active=True,
            email_verified=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.flush()  # Get admin.id

        print("✅ Admin created!")

    # Create test teacher
    teacher = User.query.filter_by(email='teacher@test.com').first()
    if not teacher:
        trial_credits = current_app.config.get('TEACHER_TRIAL_CREDITS', 50)
        teacher = User(
            email='teacher@test.com',
            full_name='Test Teacher',
            center_name='ABC IELTS Center',
            phone='0901234567',
            role='teacher',
            credits=trial_credits,  # Trial credits
            is_active=True,
            email_verified=True,
            approved_at=datetime.utcnow(),
            approved_by=admin.id
        )
        teacher.set_password('teacher123')
        db.session.add(teacher)
        db.session.flush()  # Get teacher.id

        print("✅ Test teacher created!")

        # Create a test class for the teacher
        from app.models.class_management import TeacherClass as TC
        test_class = TC(
            teacher_id=teacher.id,
            name='IELTS Foundation - June 2024',
            description='Beginner level IELTS preparation class',
            code=TC().generate_code(),
            status='active'
        )
        db.session.add(test_class)
        db.session.flush()

        print(f"✅ Test class created with code: {test_class.code}")

    # Create test student
    student = User.query.filter_by(email='student@test.com').first()
    if not student:
        if not teacher:
            teacher = User.query.filter_by(email='teacher@test.com').first()

        student = User(
            email='student@test.com',
            full_name='Test Student',
            role='student',
            teacher_id=teacher.id if teacher else None,
            credits=0,  # Students don't have credits
            is_active=True,
            email_verified=True
        )
        student.set_password('student123')
        db.session.add(student)
        db.session.flush()

        # Add student to test class
        if teacher:
            from app.models.class_management import TeacherClass as TC
            test_class = TC.query.filter_by(teacher_id=teacher.id).first()
            if test_class:
                class_student = ClassStudent(
                    class_id=test_class.id,
                    student_id=student.id,
                    status='active'
                )
                db.session.add(class_student)

        print("✅ Test student created!")

    # Create sample content by admin
    if not admin:
        admin = User.query.filter_by(role='admin').first()

    if admin:
        # Sample Writing Task 2
        writing_task = WritingTask.query.filter_by(created_by=admin.id).first()
        if not writing_task:
            writing_task = WritingTask(
                created_by=admin.id,
                is_public=True,
                task_type=2,
                topic='Education',
                essay_type='opinion',
                question_text='Some people believe that university students should be required to attend classes. Others believe that going to classes should be optional. Discuss both views and give your own opinion.',
                instructions='Write at least 250 words.',
                difficulty='medium',
                sample_answer_band_7='In recent years, the debate over mandatory class attendance has intensified. While some argue that university students should be required to attend classes, others believe attendance should be optional. This essay will discuss both perspectives before presenting my own view.\n\nOn one hand, proponents of mandatory attendance argue that it ensures students engage with course material regularly...'
            )
            db.session.add(writing_task)
            print("✅ Sample writing task created!")

        # Sample Reading Passage
        reading_passage = ReadingPassage.query.filter_by(created_by=admin.id).first()
        if not reading_passage:
            reading_passage = ReadingPassage(
                created_by=admin.id,
                is_public=True,
                title='The History of the Bicycle',
                passage_text='''The bicycle has been around for over 200 years and has undergone numerous transformations since its inception. The first verifiable claim for a practically used bicycle belongs to German inventor Baron Karl von Drais who invented his Laufmaschine (running machine) in 1817, which was called a velocipede or draisine by the press.

The design of the bicycle has evolved considerably over the years. The safety bicycle, which resembles modern bicycles, became popular in the 1880s. This design featured a chain-driven rear wheel and equally sized wheels, making it much more stable than its predecessors...''',
                topic='History',
                difficulty='medium',
                word_count=650,
                reading_time=20
            )
            db.session.add(reading_passage)
            print("✅ Sample reading passage created!")

    db.session.commit()

    print("\n" + "="*60)
    print("✅ Database initialized successfully!")
    print("="*60)
    print("\n👤 LOGIN CREDENTIALS:")
    print("-" * 60)
    print("Admin:    admin@ielts.com / admin123")
    print("Teacher:  teacher@test.com / teacher123")
    print("Student:  student@test.com / student123")
    print("-" * 60)
    if not teacher:
        teacher = User.query.filter_by(email='teacher@test.com').first()
    if teacher:
        from app.models.class_management import TeacherClass as TC
        test_class = TC.query.filter_by(teacher_id=teacher.id).first()
        if test_class:
            print(f"\n📚 Test Class Code: {test_class.code}")
            print("   Students can use this code to join the class")
    print("="*60 + "\n")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
