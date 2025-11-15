# app/services/gemini_service.py

import google.generativeai as genai
from flask import current_app
import json
import time

class GeminiService:
    """Service for Gemini API interactions"""
    
    def __init__(self):
        self.api_key = current_app.config['GEMINI_API_KEY']
        self.model_name = current_app.config['GEMINI_MODEL']
        self.temperature = current_app.config['GEMINI_TEMPERATURE']
        self.max_output_tokens = current_app.config['GEMINI_MAX_OUTPUT_TOKENS']
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
    
    def _call_api(self, prompt, temperature=None, max_tokens=None):
        """
        Internal method to call Gemini API
        Returns: (response_text, token_usage)
        """
        try:
            generation_config = {
                'temperature': temperature or self.temperature,
                'max_output_tokens': max_tokens or self.max_output_tokens,
            }
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # Extract token usage for cost tracking
            token_usage = {
                'input_tokens': response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
                'output_tokens': response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0,
                'total_tokens': response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0,
            }
            
            return response.text, token_usage
            
        except Exception as e:
            current_app.logger.error(f"Gemini API error: {str(e)}")
            raise Exception(f"Gemini API error: {str(e)}")
    
    def calculate_cost(self, token_usage):
        """Calculate cost in USD based on token usage"""
        # Gemini 2.0 Flash pricing (as of 2025)
        # Input: $0.15 per 1M tokens = $0.00000015 per token
        # Output: $0.60 per 1M tokens = $0.0000006 per token
        
        input_cost = token_usage['input_tokens'] * 0.00000015
        output_cost = token_usage['output_tokens'] * 0.0000006
        total_cost = input_cost + output_cost
        
        return round(total_cost, 6)
    
    def score_writing_task_2(self, essay, question):
        """
        Score IELTS Writing Task 2 essay
        Returns: (scores_dict, cost_usd)
        """
        prompt = f"""You are an experienced IELTS examiner with 15+ years of experience. Score this IELTS Writing Task 2 essay based on OFFICIAL IELTS band descriptors.

QUESTION:
{question}

ESSAY:
{essay}

SCORING CRITERIA (Official IELTS):

1. TASK RESPONSE (0-9):
Band 9: Fully addresses all parts of the task, presents fully developed position with relevant, extended, and supported ideas
Band 8: Sufficiently addresses all parts, presents well-developed response with relevant, extended, and supported ideas
Band 7: Addresses all parts though some parts may be more fully covered, presents clear position with main ideas but may lack focus
Band 6: Addresses all parts but some parts may be more fully covered, presents relevant position but conclusions may be unclear
Band 5: Addresses the task only partially, position unclear, limited development of ideas

2. COHERENCE AND COHESION (0-9):
Band 9: Uses cohesion in such a way that it attracts no attention, skillfully manages paragraphing
Band 8: Sequences information logically, manages all aspects of cohesion well, uses paragraphing sufficiently
Band 7: Logically organizes information, clear progression, uses range of cohesive devices appropriately
Band 6: Arranges information coherently, overall progression but may not always be clear, uses cohesive devices but not always appropriately
Band 5: Presents information with some organization but lack overall progression, inadequate/inaccurate cohesive devices

3. LEXICAL RESOURCE (0-9):
Band 9: Uses wide range of vocabulary with natural and sophisticated control, rare minor errors
Band 8: Uses wide range fluently and flexibly, uses less common and idiomatic items with awareness of style
Band 7: Uses sufficient range with some flexibility, uses less common vocabulary with some awareness
Band 6: Uses adequate range for the task, attempts less common vocabulary but with some inaccuracy
Band 5: Uses limited range, noticeable errors in spelling and word formation

4. GRAMMATICAL RANGE AND ACCURACY (0-9):
Band 9: Uses wide range of structures with full flexibility and accuracy, rare minor errors
Band 8: Uses wide range, majority error-free, makes only occasional errors
Band 7: Uses variety of complex structures, frequently error-free, good control with few errors
Band 6: Uses mix of simple and complex forms, makes some errors but they rarely reduce communication
Band 5: Uses limited range of structures, attempts complex sentences but tend to be less accurate

IMPORTANT INSTRUCTIONS:
- Be strict but fair
- Provide specific examples from the essay
- Give actionable improvement suggestions
- Scores can use half bands (e.g., 6.5, 7.5)

OUTPUT FORMAT (JSON only, no markdown):
{{
  "overall_band": 6.5,
  "task_response": {{
    "score": 6.5,
    "strengths": ["Specific strength 1", "Specific strength 2"],
    "weaknesses": ["Specific weakness 1", "Specific weakness 2"],
    "examples": ["Quote from essay showing strength/weakness"],
    "suggestions": ["Actionable tip 1", "Actionable tip 2"]
  }},
  "coherence_cohesion": {{
    "score": 7.0,
    "strengths": ["..."],
    "weaknesses": ["..."],
    "examples": ["..."],
    "suggestions": ["..."]
  }},
  "lexical_resource": {{
    "score": 6.0,
    "strengths": ["..."],
    "weaknesses": ["..."],
    "examples": ["..."],
    "suggestions": ["..."]
  }},
  "grammar_accuracy": {{
    "score": 6.5,
    "strengths": ["..."],
    "weaknesses": ["..."],
    "examples": ["..."],
    "suggestions": ["..."]
  }}
}}

DO NOT include any text outside the JSON. Start directly with {{ and end with }}.
"""
        
        response_text, token_usage = self._call_api(prompt)
        cost = self.calculate_cost(token_usage)
        
        # Parse JSON response
        try:
            # Remove markdown code blocks if present
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            scores = json.loads(response_text)
            return scores, cost
            
        except json.JSONDecodeError as e:
            current_app.logger.error(f"JSON parse error: {str(e)}")
            current_app.logger.error(f"Response text: {response_text}")
            raise Exception("Failed to parse AI response. Please try again.")
    
    def score_writing_task_1(self, essay, question, chart_type=None):
        """Score IELTS Writing Task 1"""
        
        prompt = f"""You are an experienced IELTS examiner. Score this IELTS Writing Task 1 report based on OFFICIAL IELTS band descriptors.

QUESTION:
{question}

{f"CHART TYPE: {chart_type}" if chart_type else ""}

REPORT:
{essay}

SCORING CRITERIA (Official IELTS Task 1):

1. TASK ACHIEVEMENT (0-9):
Band 9: Fully satisfies all requirements, presents fully developed response with clear overview, key features with relevant detail
Band 8: Covers requirements, presents clear overview, highlights key features with appropriate detail
Band 7: Covers requirements, presents clear overview, clearly highlights key features but could be more fully extended
Band 6: Addresses requirements, presents overview, highlights key features but may be inappropriate/inaccurate
Band 5: Generally addresses task, recounts detail mechanically, no clear overview, inadequate key features

2. COHERENCE AND COHESION (0-9):
[Same as Task 2]

3. LEXICAL RESOURCE (0-9):
[Same as Task 2]

4. GRAMMATICAL RANGE AND ACCURACY (0-9):
[Same as Task 2]

TASK 1 SPECIFIC CONSIDERATIONS:
- Is there a clear overview/summary statement?
- Are key features identified and highlighted?
- Is data described accurately?
- Are comparisons made where appropriate?
- Is the response organized logically?

OUTPUT FORMAT (JSON only, no markdown):
{{
  "overall_band": 6.5,
  "task_achievement": {{
    "score": 6.5,
    "strengths": ["..."],
    "weaknesses": ["..."],
    "examples": ["..."],
    "suggestions": ["..."]
  }},
  "coherence_cohesion": {{ "score": 7.0, ... }},
  "lexical_resource": {{ "score": 6.0, ... }},
  "grammar_accuracy": {{ "score": 6.5, ... }}
}}

DO NOT include any text outside the JSON.
"""
        
        response_text, token_usage = self._call_api(prompt)
        cost = self.calculate_cost(token_usage)
        
        try:
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            scores = json.loads(response_text)
            return scores, cost
            
        except json.JSONDecodeError as e:
            current_app.logger.error(f"JSON parse error: {str(e)}")
            raise Exception("Failed to parse AI response.")
    
    def score_speaking(self, transcript, topic, part, duration_seconds):
        """Score IELTS Speaking based on transcript"""
        
        # Calculate words per minute
        word_count = len(transcript.split())
        wpm = int((word_count / duration_seconds) * 60) if duration_seconds > 0 else 0
        
        prompt = f"""You are an experienced IELTS speaking examiner. Score this IELTS Speaking Part {part} response based on the transcript.

TOPIC:
{topic}

TRANSCRIPT:
{transcript}

DURATION: {duration_seconds} seconds
WORD COUNT: {word_count} words
WORDS PER MINUTE: {wpm}

SCORING CRITERIA (Official IELTS Speaking):

1. FLUENCY AND COHERENCE (0-9):
Band 9: Speaks fluently, rare repetition/self-correction, hesitation content-related, coherent with fully appropriate cohesive features
Band 8: Fluent with occasional repetition/self-correction, coherent, develops topics coherently
Band 7: Speaks at length with little repetition, demonstrates flexibility, uses range of connectives though not always appropriately
Band 6: Willing to speak at length but loses coherence due to hesitation/repetition, uses range of connectives but not always appropriately
Band 5: Usually maintains flow but uses repetition/self-correction, over-uses certain connectives, simple speech only

Consider: Hesitations, repetitions, self-corrections, flow, logical organization

2. LEXICAL RESOURCE (0-9):
Band 9: Uses vocabulary with full flexibility and precision, uses idiomatic language naturally
Band 8: Uses wide vocabulary resource readily and flexibly, uses less common and idiomatic items
Band 7: Uses vocabulary resource flexibly for less common topics, uses some less common items, paraphrases effectively
Band 6: Has sufficient vocabulary to discuss topics at length, attempts paraphrasing but not always successful
Band 5: Manages to talk about familiar topics, limited flexibility, attempts paraphrase but often unsuccessful

Consider: Range, sophistication, accuracy, paraphrasing ability

3. GRAMMATICAL RANGE AND ACCURACY (0-9):
Band 9: Uses full range of structures naturally and appropriately, rare errors
Band 8: Uses wide range, flexibly, produces majority error-free sentences with only occasional errors
Band 7: Uses range of complex structures with flexibility, frequently produces error-free sentences
Band 6: Uses mix of simple and complex structures but with limited flexibility, errors occur but rarely impede communication
Band 5: Produces basic sentence forms, subordinate clauses less accurate, errors frequent but meaning usually clear

Consider: Sentence complexity, variety, accuracy, error frequency

4. PRONUNCIATION (0-9):
Band 9: Uses full range of pronunciation features, sustained flexibility, rare mispronunciations
Band 8: Wide range of features, flexible, generally intelligible, occasional lapses
Band 7: Shows features positively, sustained intelligibility, mispronunciation reduces clarity occasionally
Band 6: Uses range of features but control variable, generally intelligible but mispronunciation causes some difficulty
Band 5: Shows some effective features but control limited, attempts at intonation but often faulty

NOTE: Since we only have transcript, pronunciation score will be estimated based on:
- Clarity indicators in transcript quality
- Vocabulary sophistication (suggests good pronunciation)
- Grammar accuracy (suggests clear articulation)

OUTPUT FORMAT (JSON only):
{{
  "overall_band": 6.5,
  "fluency_coherence": {{
    "score": 6.5,
    "strengths": ["..."],
    "weaknesses": ["..."],
    "examples": ["..."],
    "suggestions": ["..."]
  }},
  "lexical_resource": {{ ... }},
  "grammar_accuracy": {{ ... }},
  "pronunciation": {{
    "score": 6.5,
    "note": "Estimated based on transcript quality",
    "strengths": ["..."],
    "suggestions": ["..."]
  }},
  "metrics": {{
    "words_per_minute": {wpm},
    "hesitation_count": 5,
    "repetition_count": 3,
    "filler_words": ["um", "uh", "like"]
  }}
}}

DO NOT include any text outside the JSON.
"""
        
        response_text, token_usage = self._call_api(prompt)
        cost = self.calculate_cost(token_usage)
        
        try:
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            scores = json.loads(response_text)
            return scores, cost
            
        except json.JSONDecodeError as e:
            current_app.logger.error(f"JSON parse error: {str(e)}")
            raise Exception("Failed to parse AI response.")


# Global instance
gemini_service = GeminiService()