import google.generativeai as genai
import os
import json
from typing import List, Dict

class AIHelper:
    def __init__(self):
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        self.model = genai.GenerativeModel('gemini-pro')
    
    def generate_question(self, job_role: str, experience_level: str, asked_questions: List[str]) -> str:
        """Generate a unique question that hasn't been asked before"""
        
        # Create prompt for question generation
        prompt = f"""Generate a technical or behavioral interview question for a {experience_level} level {job_role} position.
        
        Previous questions asked (DO NOT repeat any of these):
        {chr(10).join(asked_questions) if asked_questions else 'None yet'}
        
        Rules:
        1. Question must be completely different from all previous questions
        2. Question should be specific and detailed
        3. Focus on {experience_level} level expectations
        4. Include scenario-based questions for behavioral rounds
        
        Generate ONLY the question text, no explanations or numbering."""
        
        response = self.model.generate_content(prompt)
        return response.text.strip()
    
    def evaluate_answer(self, question: str, answer: str, job_role: str) -> Dict:
        """Evaluate the user's answer and provide detailed feedback"""
        
        prompt = f"""Evaluate this interview answer for a {job_role} position.

Question: {question}

Candidate's Answer: {answer}

Provide a detailed evaluation in JSON format with the following structure:
{{
    "communication": {{
        "score": (0-100),
        "feedback": "Feedback on clarity, structure, and articulation"
    }},
    "relevance": {{
        "score": (0-100),
        "feedback": "How relevant the answer is to the question"
    }},
    "technical_accuracy": {{
        "score": (0-100),
        "feedback": "Technical correctness and depth"
    }},
    "completeness": {{
        "score": (0-100),
        "feedback": "Whether all aspects were covered"
    }},
    "overall_score": (average of all scores),
    "strengths": ["strength1", "strength2", "strength3"],
    "improvements": ["improvement1", "improvement2", "improvement3"],
    "sample_better_answer": "A concise example of a better answer"
}}

Be specific, constructive, and encouraging."""
        
        response = self.model.generate_content(prompt)
        
        # Parse JSON from response
        try:
            evaluation = json.loads(response.text)
        except:
            # Fallback evaluation
            evaluation = {
                "communication": {"score": 70, "feedback": "Good effort, could be more structured"},
                "relevance": {"score": 75, "feedback": "Relevant but could be more focused"},
                "technical_accuracy": {"score": 65, "feedback": "Basic understanding shown"},
                "completeness": {"score": 70, "feedback": "Could add more details"},
                "overall_score": 70,
                "strengths": ["Good attempt", "Shows understanding"],
                "improvements": ["Add more examples", "Structure better"],
                "sample_better_answer": "I would recommend structuring answers using STAR method"
            }
        
        return evaluation
    
    def analyze_resume(self, resume_text: str) -> Dict:
        """Analyze resume and provide detailed feedback"""
        
        prompt = f"""Analyze this resume and provide comprehensive feedback in JSON format:

Resume Text:
{resume_text[:3000]}

Return JSON with:
{{
    "overall_score": (0-100),
    "strengths": ["strength1", "strength2", "strength3"],
    "weaknesses": ["weakness1", "weakness2", "weakness3"],
    "recommendations": ["recommendation1", "recommendation2", "recommendation3"],
    "formatting_score": (0-100),
    "content_score": (0-100),
    "keywords_score": (0-100),
    "missing_keywords": ["keyword1", "keyword2"],
    "ats_compatibility": (0-100),
    "suggested_improvements": {{
        "summary": "Suggestions for professional summary",
        "experience": "Suggestions for work experience section",
        "skills": "Suggestions for skills section",
        "education": "Suggestions for education section"
    }}
}}

Be specific and actionable."""
        
        response = self.model.generate_content(prompt)
        
        try:
            analysis = json.loads(response.text)
        except:
            analysis = {
                "overall_score": 75,
                "strengths": ["Good structure", "Relevant experience"],
                "weaknesses": ["Missing metrics", "Could add more keywords"],
                "recommendations": ["Add quantifiable achievements", "Include more industry keywords"],
                "formatting_score": 80,
                "content_score": 70,
                "keywords_score": 75,
                "missing_keywords": [],
                "ats_compatibility": 75,
                "suggested_improvements": {
                    "summary": "Add a compelling professional summary",
                    "experience": "Highlight achievements with numbers",
                    "skills": "Add technical skills section",
                    "education": "List relevant coursework"
                }
            }
        
        return analysis
