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
        'User': User,
        'Transaction': Transaction,
        'VocabularyTopic': VocabularyTopic,
        'VocabularyWord': VocabularyWord,
        'ListeningSection': ListeningSection,
        'ReadingPassage': ReadingPassage,
        'SpeakingTopic': SpeakingTopic,
        'WritingTask': WritingTask,
        'PaymentRequest': PaymentRequest,
    }

@app.cli.command()
def init_db():
    """Initialize database with sample data"""
    db.create_all()
    
    # Create admin user
    admin = User.query.filter_by(email='admin@ielts.com').first()
    if not admin:
        admin = User(
            email='admin@ielts.com',
            full_name='Administrator',
            role='admin',
            credits=9999,
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
    
    # Create test user
    test_user = User.query.filter_by(email='user@test.com').first()
    if not test_user:
        test_user = User(
            email='user@test.com',
            full_name='Test User',
            role='user',
            credits=10,
            is_active=True
        )
        test_user.set_password('user123')
        db.session.add(test_user)
    
    db.session.commit()
    
    print("✅ Database initialized!")
    print("👤 Admin: admin@ielts.com / admin123")
    print("👤 User: user@test.com / user123")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)