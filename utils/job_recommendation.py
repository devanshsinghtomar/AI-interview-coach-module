import json
import os
from typing import List, Dict

# Try to import Google AI, but provide fallback if not available
try:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv('GOOGLE_API_KEY', ''))
    HAS_GOOGLE_AI = True
except:
    HAS_GOOGLE_AI = False
    print("Warning: Google Generative AI not available. Using fallback recommendations.")

class JobRecommender:
    def __init__(self):
        self.skill_to_roles = {
            'python': ['Python Developer', 'Data Scientist', 'Backend Developer', 'DevOps Engineer'],
            'java': ['Java Developer', 'Android Developer', 'Backend Developer'],
            'javascript': ['JavaScript Developer', 'Frontend Developer', 'Full Stack Developer'],
            'react': ['Frontend Developer', 'React Developer', 'Full Stack Developer'],
            'sql': ['Data Analyst', 'Database Administrator', 'Backend Developer'],
            'aws': ['Cloud Engineer', 'DevOps Engineer', 'Solutions Architect'],
            'docker': ['DevOps Engineer', 'Platform Engineer', 'System Administrator'],
            'machine learning': ['Machine Learning Engineer', 'Data Scientist', 'AI Engineer'],
            'data science': ['Data Scientist', 'Data Analyst', 'Business Intelligence Analyst']
        }
    
    def recommend_jobs(self, resume_text: str, analysis: Dict) -> List[Dict]:
        """Recommend job roles based on resume content"""
        
        # Extract skills from resume text
        skills_found = self._extract_skills_from_text(resume_text.lower())
        
        # Score each potential role
        role_scores = {}
        for skill in skills_found:
            for role in self.skill_to_roles.get(skill, []):
                role_scores[role] = role_scores.get(role, 0) + 20  # Add 20 points per matching skill
        
        # Get top 5 roles
        sorted_roles = sorted(role_scores.items(), key=lambda x: x[1], reverse=True)[:5]
        
        if not sorted_roles:
            # Fallback recommendations
            return self._get_fallback_recommendations()
        
        # Format recommendations
        recommendations = []
        for role, score in sorted_roles:
            match_percentage = min(score, 95)  # Cap at 95%
            recommendations.append({
                "job_title": role,
                "match_percentage": match_percentage,
                "reason": f"Your skills align well with this role. Match based on {len(skills_found)} relevant skills.",
                "required_skills": self._get_required_skills_for_role(role),
                "missing_skills": self._get_missing_skills(role, skills_found),
                "salary_range": self._get_salary_range(role),
                "growth_potential": self._get_growth_potential(role)
            })
        
        return recommendations
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills from resume text"""
        skills = []
        for skill in self.skill_to_roles.keys():
            if skill in text:
                skills.append(skill)
        return skills
    
    def _get_required_skills_for_role(self, role: str) -> List[str]:
        """Get required skills for a role"""
        role_skills = {
            'Python Developer': ['Python', 'Django/Flask', 'SQL', 'Git', 'REST APIs'],
            'Java Developer': ['Java', 'Spring Boot', 'Hibernate', 'SQL', 'Maven/Gradle'],
            'JavaScript Developer': ['JavaScript', 'ES6+', 'Node.js', 'React/Vue', 'HTML/CSS'],
            'Full Stack Developer': ['JavaScript', 'Python/Java', 'React/Angular', 'Node.js', 'MongoDB/SQL'],
            'Data Scientist': ['Python', 'Pandas/NumPy', 'Machine Learning', 'SQL', 'Statistics'],
            'DevOps Engineer': ['Docker', 'Kubernetes', 'AWS/Azure', 'Jenkins', 'Linux'],
            'Frontend Developer': ['JavaScript', 'React/Vue/Angular', 'HTML5', 'CSS3', 'Responsive Design'],
            'Backend Developer': ['Python/Java/Node.js', 'REST APIs', 'Databases', 'Authentication', 'Server Logic'],
            'Data Analyst': ['SQL', 'Excel', 'Tableau/Power BI', 'Python', 'Statistical Analysis'],
            'Machine Learning Engineer': ['Python', 'TensorFlow/PyTorch', 'ML Algorithms', 'Data Processing', 'Model Deployment']
        }
        return role_skills.get(role, ['Technical skills', 'Problem solving', 'Communication'])
    
    def _get_missing_skills(self, role: str, skills_found: List[str]) -> List[str]:
        """Identify missing skills for a role"""
        required = self._get_required_skills_for_role(role)
        # Simplified - in production, this would do actual matching
        return required[:2]  # Return first 2 required skills as "missing" for demo
    
    def _get_salary_range(self, role: str) -> str:
        """Get estimated salary range for role"""
        salary_ranges = {
            'Python Developer': '$80k - $130k',
            'Java Developer': '$85k - $135k',
            'JavaScript Developer': '$75k - $125k',
            'Full Stack Developer': '$85k - $140k',
            'Data Scientist': '$90k - $150k',
            'DevOps Engineer': '$95k - $160k',
            'Frontend Developer': '$70k - $120k',
            'Backend Developer': '$80k - $130k',
            'Data Analyst': '$65k - $110k',
            'Machine Learning Engineer': '$100k - $170k'
        }
        return salary_ranges.get(role, '$70k - $120k')
    
    def _get_growth_potential(self, role: str) -> str:
        """Get growth potential for role"""
        high_growth_roles = ['Data Scientist', 'Machine Learning Engineer', 'DevOps Engineer', 'Full Stack Developer']
        if role in high_growth_roles:
            return 'High'
        return 'Medium'
    
    def _get_fallback_recommendations(self) -> List[Dict]:
        """Fallback recommendations when no skills detected"""
        return [
            {
                "job_title": "Software Developer",
                "match_percentage": 65,
                "reason": "General software development role suitable for various skill sets",
                "required_skills": ["Programming", "Problem Solving", "Version Control"],
                "missing_skills": ["Specific framework experience", "Cloud knowledge"],
                "salary_range": "$70k - $120k",
                "growth_potential": "High"
            },
            {
                "job_title": "Web Developer",
                "match_percentage": 60,
                "reason": "Focus on building web applications and websites",
                "required_skills": ["HTML/CSS", "JavaScript", "Basic Backend"],
                "missing_skills": ["Modern framework experience", "Responsive design"],
                "salary_range": "$65k - $110k",
                "growth_potential": "Medium"
            }
        ]

# For backward compatibility
job_recommender = JobRecommender()
