# app/routes/__init__.py

from app.routes import auth, user, payment, vocabulary, listening, reading, speaking, writing, admin

__all__ = [
    'auth', 'user', 'payment', 'vocabulary', 
    'listening', 'reading', 'speaking', 'writing', 'admin'
]