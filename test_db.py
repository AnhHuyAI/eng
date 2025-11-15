#!/usr/bin/env python3
"""Simple script to test database models without loading routes"""

import os
os.environ['FLASK_ENV'] = 'development'

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.config import Config

# Create minimal app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize DB
db = SQLAlchemy()
db.init_app(app)

# Import models
with app.app_context():
    from app.models import *

    print("✅ All models imported successfully!")

    # Create tables
    db.create_all()
    print("✅ Database tables created successfully!")

    # Test creating objects
    admin = User(
        email='test@admin.com',
        full_name='Test Admin',
        role='admin',
        credits=999,
        is_active=True
    )
    admin.set_password('test123')
    db.session.add(admin)
    db.session.commit()

    print("✅ Test admin user created!")
    print(f"   Email: {admin.email}")
    print(f"   Role: {admin.role}")

    print("\n🎉 Database test passed!")
