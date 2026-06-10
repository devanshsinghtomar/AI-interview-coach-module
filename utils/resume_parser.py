import PyPDF2
import re
from typing import Dict, List

class ResumeParser:
    """Parse and extract text from PDF resumes"""
    
    def __init__(self):
        pass
    
    def parse_pdf(self, filepath: str) -> str:
        """Extract text from PDF file"""
        try:
            text = ""
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
            return text
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            return ""
    
    def extract_email(self, text: str) -> str:
        """Extract email from resume text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else ""
    
    def extract_phone(self, text: str) -> str:
        """Extract phone number from resume text"""
        phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'
        phones = re.findall(phone_pattern, text)
        return phones[0] if phones else ""
    
    def extract_skills(self, text: str, skills_list: List[str] = None) -> List[str]:
        """Extract skills from resume text"""
        if skills_list is None:
            skills_list = [
                'Python', 'Java', 'JavaScript', 'React', 'Node.js', 'Django', 'Flask',
                'SQL', 'MongoDB', 'AWS', 'Docker', 'Kubernetes', 'Git', 'Machine Learning',
                'Data Science', 'C++', 'C#', 'PHP', 'Ruby', 'Swift', 'Kotlin', 'HTML', 'CSS',
                'TypeScript', 'Angular', 'Vue.js', 'Spring Boot', 'Hibernate', 'REST API',
                'GraphQL', 'TensorFlow', 'PyTorch', 'Pandas', 'NumPy', 'Tableau', 'Power BI'
            ]
        
        found_skills = []
        text_lower = text.lower()
        for skill in skills_list:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        return found_skills
    
    def extract_experience_years(self, text: str) -> float:
        """Extract years of experience from resume"""
        patterns = [
            r'(\d+)\+?\s*years?\s+of\s+experience',
            r'experience\s+of\s+(\d+)\+?\s*years?',
            r'(\d+)\s*years?\s+experience'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return float(match.group(1))
        return 0.0

# For backward compatibility - also export as lowercase name
resume_parser = ResumeParser()
