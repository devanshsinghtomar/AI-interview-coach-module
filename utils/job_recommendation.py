# utils/job_recommendation.py

def recommend_job_roles(resume_text: str, skills: list) -> dict:
    """
    Recommend suitable job roles based on resume content and skills.
    """
    
    resume_lower = resume_text.lower()
    
    # Job role criteria
    job_roles = {
        "Python Developer": {
            "score": 0,
            "required_skills": ["python", "django", "flask", "fastapi"],
            "keywords": ["python", "scripting", "backend", "automation"],
            "description": "Build scalable backend services with Python"
        },
        "Data Scientist": {
            "score": 0,
            "required_skills": ["python", "machine learning", "ml", "data", "tensorflow", "pandas", "scikit"],
            "keywords": ["data analysis", "ml", "machine learning", "neural network", "deep learning", "data science"],
            "description": "Work with data and build intelligent models"
        },
        "JavaScript Developer": {
            "score": 0,
            "required_skills": ["javascript", "react", "vue", "node", "angular"],
            "keywords": ["javascript", "frontend", "react", "node.js", "web development"],
            "description": "Create engaging web applications"
        },
        "Full Stack Developer": {
            "score": 0,
            "required_skills": ["python", "javascript", "sql", "database", "api", "react", "django"],
            "keywords": ["full stack", "frontend", "backend", "api", "database", "devops"],
            "description": "Develop complete web applications"
        },
        "DevOps Engineer": {
            "score": 0,
            "required_skills": ["docker", "kubernetes", "jenkins", "aws", "ci/cd"],
            "keywords": ["devops", "docker", "kubernetes", "ci/cd", "deployment", "infrastructure"],
            "description": "Manage infrastructure and deployment pipelines"
        },
        "Java Developer": {
            "score": 0,
            "required_skills": ["java", "spring", "maven", "microservices"],
            "keywords": ["java", "spring", "enterprise", "microservices"],
            "description": "Build enterprise Java applications"
        },
        "Frontend Developer": {
            "score": 0,
            "required_skills": ["javascript", "react", "css", "html", "vue", "angular"],
            "keywords": ["frontend", "ui", "css", "html", "responsive", "design"],
            "description": "Create beautiful user interfaces"
        },
        "Backend Developer": {
            "score": 0,
            "required_skills": ["python", "java", "node", "sql", "api", "database"],
            "keywords": ["backend", "api", "database", "server", "microservices"],
            "description": "Build robust backend systems"
        }
    }
    
    # Score each job role
    for role, details in job_roles.items():
        # Check required skills
        for skill in details["required_skills"]:
            if skill in resume_lower:
                details["score"] += 25
        
        # Check keywords
        for keyword in details["keywords"]:
            if keyword in resume_lower:
                details["score"] += 10
    
    # Sort roles by score
    ranked_roles = sorted(job_roles.items(), key=lambda x: x[1]["score"], reverse=True)
    
    # Filter roles with score > 0 and prepare results
    recommended = []
    for role_name, details in ranked_roles:
        if details["score"] > 0:
            recommended.append({
                "role": role_name,
                "score": min(details["score"], 100),
                "description": details["description"],
                "match_percentage": min(details["score"], 100)
            })
    
    return {
        "top_roles": recommended[:3] if recommended else [{"role": "General Software Developer", "score": 50, "description": "Based on your skills", "match_percentage": 50}],
        "all_scores": {role: details["score"] for role, details in ranked_roles},
        "best_match": recommended[0] if recommended else {"role": "Software Developer", "score": 50, "description": "Based on your background", "match_percentage": 50}
    }
