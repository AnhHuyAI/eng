# app/services/scoring_service.py

from flask import current_app
from app import db

class ScoringService:
    """High-level scoring service that orchestrates AI scoring"""

    def __init__(self):
        # Lazy load services
        self._gemini = None
        self._stt = None

    @property
    def gemini_service(self):
        """Lazy load Gemini service"""
        if self._gemini is None:
            from app.services.gemini_service import get_gemini_service
            self._gemini = get_gemini_service()
        return self._gemini

    @property
    def stt_service(self):
        """Lazy load STT service"""
        if self._stt is None:
            from app.services.stt_service import get_stt_service
            self._stt = get_stt_service()
        return self._stt

    def score_writing(self, submission, task):
        """
        Score writing submission
        Returns: (scores_dict, total_cost_usd)
        """
        try:
            # Determine task type
            is_task_1 = task.task_type == 1
            
            # Call Gemini API
            if is_task_1:
                scores, cost = self.gemini_service.score_writing_task_1(
                    essay=submission.essay_text,
                    question=task.question_text,
                    chart_type=task.chart_type
                )
            else:
                scores, cost = self.gemini_service.score_writing_task_2(
                    essay=submission.essay_text,
                    question=task.question_text
                )
            
            # Update submission with scores
            submission.overall_band = scores['overall_band']
            
            if is_task_1:
                submission.task_achievement = scores['task_achievement']['score']
            else:
                submission.task_response = scores['task_response']['score']
            
            submission.coherence_cohesion = scores['coherence_cohesion']['score']
            submission.lexical_resource = scores['lexical_resource']['score']
            submission.grammar_accuracy = scores['grammar_accuracy']['score']
            submission.detailed_feedback = scores
            submission.api_cost_usd = cost
            
            db.session.commit()
            
            return scores, cost
            
        except Exception as e:
            current_app.logger.error(f"Scoring error: {str(e)}")
            raise
    
    def score_speaking(self, submission, topic):
        """
        Score speaking submission
        1. Transcribe audio to text
        2. Score transcript with Gemini
        Returns: (scores_dict, total_cost_usd)
        """
        try:
            # Step 1: Transcribe audio
            audio_path = f"app/static/uploads/{submission.audio_url}"
            
            transcript, confidence, stt_cost = self.stt_service.transcribe_audio(audio_path)
            
            if not transcript:
                raise Exception("Failed to transcribe audio. Please try again.")
            
            # Save transcript
            submission.transcript = transcript
            
            # Step 2: Score with Gemini
            topic_text = self._get_speaking_topic_text(topic, submission.part)
            
            scores, gemini_cost = self.gemini_service.score_speaking(
                transcript=transcript,
                topic=topic_text,
                part=submission.part,
                duration_seconds=submission.duration
            )
            
            # Update submission with scores
            submission.overall_band = scores['overall_band']
            submission.fluency_coherence = scores['fluency_coherence']['score']
            submission.lexical_resource = scores['lexical_resource']['score']
            submission.grammar_accuracy = scores['grammar_accuracy']['score']
            submission.pronunciation = scores['pronunciation']['score']
            submission.detailed_feedback = scores
            
            # Metrics
            if 'metrics' in scores:
                submission.words_per_minute = scores['metrics'].get('words_per_minute', 0)
                submission.hesitation_count = scores['metrics'].get('hesitation_count', 0)
                submission.repetition_count = scores['metrics'].get('repetition_count', 0)
                submission.filler_words_count = len(scores['metrics'].get('filler_words', []))
            
            # Total cost
            total_cost = stt_cost + gemini_cost
            submission.api_cost_usd = total_cost
            
            db.session.commit()
            
            return scores, total_cost
            
        except Exception as e:
            current_app.logger.error(f"Speaking scoring error: {str(e)}")
            raise
    
    def _get_speaking_topic_text(self, topic, part):
        """Get topic text based on part"""
        if part == 1 and topic.part1_questions:
            return f"Part 1 Questions: {', '.join(topic.part1_questions)}"
        elif part == 2 and topic.cue_card_title:
            return f"Part 2 Cue Card: {topic.cue_card_title}"
        elif part == 3 and topic.part3_questions:
            return f"Part 3 Questions: {', '.join(topic.part3_questions)}"
        return topic.topic
    
    def auto_grade_listening(self, attempt, section):
        """
        Auto-grade listening attempt
        Returns: (band_score, question_results)
        """
        questions = section.questions.all()
        correct_count = 0
        total_questions = len(questions)
        question_results = {}
        
        for question in questions:
            user_answer = attempt.answers.get(str(question.id), '').strip()
            is_correct = question.check_answer(user_answer)
            
            if is_correct:
                correct_count += 1
            
            question_results[question.id] = {
                'correct': is_correct,
                'user_answer': user_answer,
                'correct_answer': question.correct_answer,
                'explanation': question.explanation
            }
        
        # Update attempt
        attempt.correct_answers = correct_count
        attempt.total_questions = total_questions
        attempt.score = correct_count
        attempt.band_score = attempt.calculate_band_score()
        attempt.question_results = question_results
        
        db.session.commit()
        
        return attempt.band_score, question_results
    
    def auto_grade_reading(self, attempt, passage):
        """
        Auto-grade reading attempt
        Returns: (band_score, question_results)
        """
        questions = passage.questions.all()
        correct_count = 0
        total_questions = len(questions)
        question_results = {}
        
        for question in questions:
            user_answer = attempt.answers.get(str(question.id), '').strip()
            is_correct = question.check_answer(user_answer)
            
            if is_correct:
                correct_count += 1
            
            question_results[question.id] = {
                'correct': is_correct,
                'user_answer': user_answer,
                'correct_answer': question.correct_answer,
                'explanation': question.explanation,
                'paragraph_reference': question.paragraph_reference
            }
        
        # Update attempt
        attempt.correct_answers = correct_count
        attempt.total_questions = total_questions
        attempt.score = correct_count
        attempt.band_score = attempt.calculate_band_score()
        attempt.question_results = question_results
        
        db.session.commit()
        
        return attempt.band_score, question_results


# Lazy initialization
_scoring_service = None

def get_scoring_service():
    """Get or create Scoring service instance"""
    global _scoring_service
    if _scoring_service is None:
        _scoring_service = ScoringService()
    return _scoring_service

# For backward compatibility
def scoring_service():
    return get_scoring_service()