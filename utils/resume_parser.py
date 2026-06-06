# utils/resume_parser.py

import PyPDF2
import re
from typing import Tuple

def extract_resume_text(filepath: str) -> str:
    """
    Extract text from resume files (PDF, TXT, DOCX).
    """
    
    if filepath.endswith(".txt"):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    
    elif filepath.endswith(".pdf"):
        text = ""
        try:
            with open(filepath, "rb") as pdf_file:
                pdf = PyPDF2.PdfReader(pdf_file)
                for page_num, page in enumerate(pdf.pages):
                    extracted = page.extract_text()
                    if extracted:
                        text += f"\n--- Page {page_num + 1} ---\n"
                        text += extracted + "\n"
            return text if text else "No text could be extracted from PDF"
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
    
    elif filepath.endswith(".docx"):
        try:
            from docx import Document
            doc = Document(filepath)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text if text else "No text found in document"
        except Exception as e:
            return f"Error reading DOCX: {str(e)}"
    
    return "Unsupported file format. Please use PDF, TXT, or DOCX."


def extract_contact_info(resume_text: str) -> dict:
    """
    Extract contact information from resume.
    """
    
    contact = {
        "email": None,
        "phone": None,
        "linkedin": None,
        "github": None
    }
    
    # Extract email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, resume_text)
    if emails:
        contact["email"] = emails[0]
    
    # Extract phone
    phone_pattern = r'\b(?:\+?1[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b'
    phones = re.findall(phone_pattern, resume_text)
    if phones:
        contact["phone"] = phones[0]
    
    # Extract LinkedIn
    if "linkedin.com" in resume_text.lower():
        contact["linkedin"] = "✅ LinkedIn URL found"
    
    # Extract GitHub
    if "github.com" in resume_text.lower():
        contact["github"] = "✅ GitHub URL found"
    
    return contact


def extract_skills(resume_text: str) -> list:
    """
    Extract technical skills from resume.
    """
    
    technical_skills = [
        "Python", "Java", "JavaScript", "C++", "C#", "Go", "Rust",
        "React", "Vue", "Angular", "Node.js", "Express",
        "Django", "Flask", "Spring", "FastAPI",
        "SQL", "MongoDB", "PostgreSQL", "MySQL", "Redis",
        "Docker", "Kubernetes", "AWS", "Azure", "GCP",
        "Git", "GitHub", "GitLab", "Jenkins", "CI/CD",
        "REST API", "GraphQL", "Microservices",
        "Machine Learning", "TensorFlow", "PyTorch", "Scikit-learn"
    ]
    
    found_skills = []
    resume_lower = resume_text.lower()
    
    for skill in technical_skills:
        if skill.lower() in resume_lower:
            found_skills.append(skill)
    
    return list(set(found_skills))  # Remove duplicates


def extract_experience(resume_text: str) -> list:
    """
    Extract work experience from resume.
    """
    
    # Look for common patterns like "Company Name | Position | Duration"
    experience_pattern = r'(?:worked|at|position|role|experience)\s+(?:as|:)?\s+([A-Za-z\s,]+)'
    experiences = re.findall(experience_pattern, resume_text, re.IGNORECASE)
    
    return list(set(experiences[:5]))  # Return first 5 unique entries


def analyze_resume_structure(resume_text: str) -> dict:
    """
    Analyze the structure and completeness of the resume.
    """
    
    analysis = {
        "sections_found": [],
        "missing_sections": [],
        "completeness": 0
    }
    
    common_sections = {
        "summary": ["summary", "objective", "professional summary"],
        "experience": ["experience", "work experience", "employment"],
        "education": ["education", "degree", "bachelor", "master"],
        "skills": ["skills", "technical skills", "competencies"],
        "projects": ["projects", "portfolio"],
        "certifications": ["certification", "certified", "licenses"]
    }
    
    resume_lower = resume_text.lower()
    
    for section, keywords in common_sections.items():
        if any(keyword in resume_lower for keyword in keywords):
            analysis["sections_found"].append(section)
        else:
            analysis["missing_sections"].append(section)
    
    analysis["completeness"] = (len(analysis["sections_found"]) / len(common_sections)) * 100
    
    return analysis
