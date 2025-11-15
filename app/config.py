# config.py

import os
from datetime import timedelta

class Config:
    """Base configuration"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:password@localhost/ielts_platform?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20
    }
    
    # Upload folders
    UPLOAD_FOLDER = 'app/static/uploads'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'webm', 'm4a'}
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # API Keys
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    GOOGLE_SPEECH_API_KEY = os.environ.get('GOOGLE_SPEECH_API_KEY')
    
    # Gemini settings
    GEMINI_MODEL = 'gemini-2.0-flash-exp'  # Cost-effective model
    GEMINI_TEMPERATURE = 0.3  # Lower = more consistent
    GEMINI_MAX_OUTPUT_TOKENS = 2048
    
    # Credits pricing
    CREDIT_COSTS = {
        'vocabulary_quiz': 0,      # Free
        'listening_practice': 0,   # Free (auto-grading)
        'reading_practice': 0,     # Free (auto-grading)
        'speaking_practice': 2,    # 2 credits (STT + AI)
        'writing_task_1': 1,       # 1 credit (AI only)
        'writing_task_2': 1,       # 1 credit (AI only)
        'mock_test': 5,            # 5 credits (bundle)
    }
    
    # Rate limiting
    RATE_LIMIT_FREE = {
        'daily_submissions': 10,
        'hourly_submissions': 5,
    }
    RATE_LIMIT_PAID = {
        'daily_submissions': 100,
        'hourly_submissions': 30,
    }
    
    # Email (SendGrid)
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    MAIL_DEFAULT_SENDER = 'noreply@ieltsplatform.com'
    
    # Payment - B2B Packages for Teachers
    PAYMENT_PACKAGES = {
        'starter': {
            'name': 'Starter Package',
            'price_usd': 50,
            'price_vnd': 1200000,  # ~50 USD
            'credits': 500,
            'description': '500 credits - Perfect for small centers (~250 writing tests)',
            'recommended_for': '20-30 students'
        },
        'pro': {
            'name': 'Pro Package',
            'price_usd': 100,
            'price_vnd': 2400000,  # ~100 USD
            'credits': 1100,
            'description': '1100 credits - 10% bonus (save 100 credits)',
            'recommended_for': '50-100 students',
            'popular': True
        },
        'enterprise': {
            'name': 'Enterprise Package',
            'price_usd': 200,
            'price_vnd': 4800000,  # ~200 USD
            'credits': 2400,
            'description': '2400 credits - 20% bonus (save 400 credits)',
            'recommended_for': '100+ students',
            'best_value': True
        }
    }

    # Trial credits for new teachers
    TEACHER_TRIAL_CREDITS = 50  # Free credits for new teachers to test platform
    
    BANK_INFO = {
        'bank_name': 'Techcombank',
        'account_number': '1234567890',
        'account_name': 'NGUYEN VAN A',
        'momo_phone': '0901234567',
        'momo_name': 'NGUYEN VAN A'
    }
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # Set True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Redis (for caching & rate limiting)
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Celery (async tasks)
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}