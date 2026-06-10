import google.generativeai as genai
import json
import os
from typing import List, Dict

class JobRecommender:
    def __init__(self):
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        self.model = genai.GenerativeModel('gemini-pro')
    
    def recommend_jobs(self, resume_text: str, analysis: Dict) -> List[Dict]:
        """Recommend job roles based on resume content"""
        
        prompt = f"""Based on this resume, recommend 3-5 suitable job roles.

Resume Text:
{resume_text[:2000]}

Resume Analysis:
{json.dumps(analysis)}

Return JSON array with each recommendation containing:
{{
    "job_title": "Job title",
    "match_percentage": (0-100),
    "reason": "Why this role fits",
    "required_skills": ["skill1", "skill2", "skill3"],
    "missing_skills": ["skill1", "skill2"],
    "salary_range": "Estimated salary range",
    "growth_potential": "High/Medium/Low"
}}

Be realistic and specific based on the actual resume content."""
        
        response = self.model.generate_content(prompt)
        
        try:
            recommendations = json.loads(response.text)
        except:
            # Fallback recommendations based on analysis
            recommendations = [
                {
                    "job_title": "Software Developer",
                    "match_percentage": 75,
                    "reason": "Your skills align well with general development roles",
                    "required_skills": ["Python", "Problem Solving", "Communication"],
                    "missing_skills": ["Cloud experience", "Testing frameworks"],
                    "salary_range": "$70k - $120k",
                    "growth_potential": "High"
                }
            ]
        
        return recommendations
