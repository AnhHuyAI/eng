# app/services/__init__.py

# Services are lazily initialized to avoid app context issues
# Import service factory functions instead of instances

from app.services.gemini_service import get_gemini_service
from app.services.stt_service import get_stt_service
from app.services.scoring_service import get_scoring_service
from app.services.email_service import get_email_service

__all__ = [
    'get_gemini_service',
    'get_stt_service',
    'get_scoring_service',
    'get_email_service'
]
