# app/models/__init__.py

from app.models.user import User, Transaction
from app.models.class_management import TeacherClass, ClassStudent
from app.models.assignment import Assignment
from app.models.gemini_usage import GeminiUsage
from app.models.vocabulary import (
    VocabularyTopic, VocabularyWord, VocabularyQuiz,
    VocabularyQuestion, UserVocabularyProgress, VocabularyQuizAttempt
)
from app.models.listening import ListeningSection, ListeningQuestion, ListeningAttempt
from app.models.reading import ReadingPassage, ReadingQuestion, ReadingAttempt
from app.models.speaking import SpeakingTopic, SpeakingSubmission
from app.models.writing import WritingTask, WritingSubmission
from app.models.payment import PaymentRequest

__all__ = [
    # User & Auth
    'User', 'Transaction',

    # Teacher-Student System
    'TeacherClass', 'ClassStudent', 'Assignment',

    # API Tracking
    'GeminiUsage',

    # Content
    'VocabularyTopic', 'VocabularyWord', 'VocabularyQuiz', 'VocabularyQuestion',
    'UserVocabularyProgress', 'VocabularyQuizAttempt',
    'ListeningSection', 'ListeningQuestion', 'ListeningAttempt',
    'ReadingPassage', 'ReadingQuestion', 'ReadingAttempt',
    'SpeakingTopic', 'SpeakingSubmission',
    'WritingTask', 'WritingSubmission',

    # Payment
    'PaymentRequest'
]