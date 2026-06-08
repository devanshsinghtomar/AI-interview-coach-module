# utils/ai_helper.py
import json
import random
from utils.job_recommendation import recommend_job_roles
# Comprehensive question bank for multiple domains
QUESTION_BANK = {
    "python_developer": {
        "general": [
            "Tell me about yourself and your Python experience.",
            "Why are you interested in this Python Developer role?",
            "What are your key strengths as a Python developer?",
            "Describe a challenging Python project you completed.",
            "How do you stay updated with Python trends?"
        ],
        "technical": [
            "Explain the difference between list and tuple in Python.",
            "What is a decorator in Python? Give an example.",
            "Explain list comprehension and its advantages.",
            "How does the GIL (Global Interpreter Lock) work?",
            "What are generators and why use them?",
            "Explain the difference between *args and **kwargs.",
            "What is the difference between shallow and deep copy?",
            "Explain async/await in Python."
        ],
        "behavioral": [
            "Tell me about a time you debugged a complex Python issue.",
            "Describe a situation where your code failed in production and how you handled it.",
            "How do you approach writing maintainable code?",
            "Tell me about your experience with code reviews."
        ]
    },
    "java_developer": {
        "general": [
            "Tell me about your Java experience and expertise.",
            "Why do you want to work as a Java Developer?",
            "What are your strongest areas in Java development?",
            "Describe the most complex Java project you've worked on.",
            "How do you keep up with Java advancements?"
        ],
        "technical": [
            "Explain the difference between Abstract Class and Interface.",
            "What is the difference between HashMap and Hashtable?",
            "Explain the concept of Exception Handling in Java.",
            "What is JVM and how does it work?",
            "Explain the Spring Framework and its benefits.",
            "What are design patterns? Name a few you've used.",
            "Explain multithreading in Java.",
            "What is Java Stream API and how do you use it?"
        ],
        "behavioral": [
            "Tell me about a Java bug you fixed and how you solved it.",
            "Describe your experience working with large-scale Java applications.",
            "How do you approach performance optimization in Java?",
            "Tell me about your collaboration with your team on Java projects."
        ]
    },
    "javascript_developer": {
        "general": [
            "Tell me about your JavaScript expertise.",
            "Why are you interested in JavaScript development?",
            "What are your core JavaScript strengths?",
            "Describe your most complex JavaScript project.",
            "How do you keep updated with JavaScript ecosystem?"
        ],
        "technical": [
            "Explain the event loop in JavaScript.",
            "What is closure and why is it useful?",
            "Explain the difference between var, let, and const.",
            "What is async/await and how does it work?",
            "Explain Promise in JavaScript.",
            "What is the difference between == and ===?",
            "Explain the 'this' keyword in JavaScript.",
            "What is hoisting in JavaScript?"
        ],
        "behavioral": [
            "Tell me about a JavaScript performance issue you solved.",
            "Describe your experience with React or Vue frameworks.",
            "How do you debug complex JavaScript issues?",
            "Tell me about your experience with Node.js."
        ]
    },
    "data_scientist": {
        "general": [
            "Tell me about your data science background.",
            "Why do you want to work as a Data Scientist?",
            "What are your key skills in data science?",
            "Describe your most impactful data science project.",
            "How do you approach a new data science problem?"
        ],
        "technical": [
            "Explain the difference between supervised and unsupervised learning.",
            "What is overfitting and how do you prevent it?",
            "Explain various evaluation metrics for classification models.",
            "What is cross-validation and why is it important?",
            "Explain the difference between regression and classification.",
            "What is feature engineering and why is it important?",
            "Explain PCA (Principal Component Analysis).",
            "What is the curse of dimensionality?"
        ],
        "behavioral": [
            "Tell me about a data science project where your model improved business metrics.",
            "Describe how you handle imbalanced datasets.",
            "How do you communicate complex ML findings to non-technical stakeholders?",
            "Tell me about your experience with big data tools."
        ]
    },
    "full_stack_developer": {
        "general": [
            "Tell me about your full-stack development experience.",
            "Why are you interested in full-stack development?",
            "What are your strongest areas as a full-stack developer?",
            "Describe your most complex full-stack project.",
            "How do you balance frontend and backend development?"
        ],
        "technical": [
            "Explain the MVC architecture.",
            "What is REST API and how do you design it?",
            "Explain the difference between SQL and NoSQL databases.",
            "What is authentication vs authorization?",
            "Explain responsive web design and CSS media queries.",
            "What is Git and how do you use version control?",
            "Explain deployment and CI/CD pipelines.",
            "What is API rate limiting and why is it important?"
        ],
        "behavioral": [
            "Tell me about a full-stack project where you optimized both frontend and backend.",
            "Describe your experience with agile methodology.",
            "How do you approach testing in full-stack development?",
            "Tell me about your experience deploying applications to production."
        ]
    },
    "devops_engineer": {
        "general": [
            "Tell me about your DevOps experience.",
            "Why do you want to work as a DevOps Engineer?",
            "What are your core DevOps skills?",
            "Describe your most complex DevOps project.",
            "How do you approach infrastructure as code?"
        ],
        "technical": [
            "Explain containerization and Docker.",
            "What is Kubernetes and its benefits?",
            "Explain CI/CD pipelines and their importance.",
            "What is infrastructure as code (IaC)?",
            "Explain monitoring and logging in DevOps.",
            "What is the difference between vertical and horizontal scaling?",
            "Explain load balancing.",
            "What is a microservices architecture?"
        ],
        "behavioral": [
            "Tell me about a production incident you handled.",
            "Describe your experience with cloud platforms (AWS, Azure, GCP).",
            "How do you ensure system reliability and uptime?",
            "Tell me about your experience automating deployment processes."
        ]
    }
}

def generate_questions(role, level):
    """
    Generate AI-powered interview questions based on role and level.
    """
    
    # Normalize role
    role_key = role.lower().replace(" ", "_")
    
    # Get question bank for the role or use generic questions
   role_key = role.lower().replace(" ", "_")

role_mapping = {
    "python": "python_developer",
    "python_developer": "python_developer",

    "java": "java_developer",
    "java_developer": "java_developer",

    "javascript": "javascript_developer",
    "javascript_developer": "javascript_developer",

    "data_science": "data_scientist",
    "data_scientist": "data_scientist",

    "full_stack": "full_stack_developer",
    "full_stack_developer": "full_stack_developer",

    "devops": "devops_engineer",
    "devops_engineer": "devops_engineer"
}

role_key = role_mapping.get(role_key)

if role_key:
    bank = QUESTION_BANK[role_key]
else:
    bank = QUESTION_BANK["python_developer"]
    
    # Select question mix based on level
    if level == "Beginner":
        general_count = 3
        technical_count = 3
        behavioral_count = 2
    elif level == "Intermediate":
        general_count = 2
        technical_count = 4
        behavioral_count = 3
    else:  # Advanced
        general_count = 2
        technical_count = 5
        behavioral_count = 3
    
    # Select random questions
    questions = []
    questions.extend(random.sample(bank["general"], min(general_count, len(bank["general"]))))
    questions.extend(random.sample(bank["technical"], min(technical_count, len(bank["technical"]))))
    questions.extend(random.sample(bank["behavioral"], min(behavioral_count, len(bank["behavioral"]))))
    
    formatted_questions = "\n\n".join(
        [f"{i+1}. {q}" for i, q in enumerate(questions)]
    )
    
    return f"""
🎯 AI-Generated Interview Questions for {role.title()} ({level})

{formatted_questions}

---
💡 TIP: Use the STAR method (Situation, Task, Action, Result) for behavioral questions!
"""


def evaluate_answer(role, question, answer):
    """
    AI-powered answer evaluation with detailed feedback.
    """
    
    if not answer or len(answer.strip()) < 10:
        score = 20
        communication = "Poor"
        relevance = "Poor"
        confidence = "Poor"
        
    elif len(answer.split()) < 20:
        score = 40
        communication = "Fair"
        relevance = "Fair"
        confidence = "Fair"
        
    elif len(answer.split()) < 50:
        score = 65
        communication = "Good"
        relevance = "Good"
        confidence = "Good"
        
    elif len(answer.split()) < 100:
        score = 80
        communication = "Excellent"
        relevance = "Excellent"
        confidence = "Very Good"
        
    else:
        score = 90
        communication = "Excellent"
        relevance = "Excellent"
        confidence = "Excellent"
    
    # Check for quality indicators
    has_examples = any(word in answer.lower() for word in ["example", "project", "built", "created", "developed", "implemented"])
    has_metrics = any(char.isdigit() for char in answer)
    has_star = any(word in answer.lower() for word in ["situation", "task", "action", "result", "challenge", "solved"])
    has_technical = any(word in answer.lower() for word in ["python", "java", "javascript", "sql", "api", "database", "algorithm"])
    
    suggestions = []
    
    if has_examples:
        suggestions.append("✅ Great use of concrete examples!")
    else:
        suggestions.append("📌 Include specific examples from your projects")
    
    if has_metrics:
        suggestions.append("✅ Excellent use of metrics and numbers!")
    else:
        suggestions.append("📊 Add quantifiable results (% improvement, $ saved, etc.)")
    
    if has_star:
        suggestions.append("✅ Perfect use of structured methodology!")
    else:
        suggestions.append("🎯 Use the STAR method for better structure")
    
    if has_technical:
        suggestions.append("✅ Good technical depth shown!")
    else:
        suggestions.append("💻 Include more technical terminology relevant to the role")
    
    suggestions.append("🚀 Practice with similar questions to improve confidence")
    
    feedback = f"""
📊 AI EVALUATION REPORT
{'='*60}

🎯 Question:
{question}

💬 Your Answer:
{answer}

{'='*60}

📈 EVALUATION METRICS:

✨ Communication: {communication}
🎯 Relevance: {relevance}  
💪 Confidence: {confidence}

🏆 OVERALL SCORE: {score}/100

{'='*60}

💡 IMPROVEMENT SUGGESTIONS:
{chr(10).join('• ' + s for s in suggestions)}

{'='*60}

🎓 NEXT STEPS:
• Review the feedback and identify areas for improvement
• Practice similar questions using STAR method
• Record yourself and review the recording
• Practice with peers for better feedback
"""
    
    return feedback, score, communication


def analyze_resume_ai(resume_text):
    """
    Advanced ATS Resume Analysis + Job Recommendation
    """

    resume_lower = resume_text.lower()

    # =====================================================
    # VALIDATE RESUME
    # =====================================================

    resume_sections = [
        "education",
        "skills",
        "experience",
        "projects",
        "internship",
        "technical skills",
        "certification",
        "work experience",
        "summary",
        "objective"
    ]

    section_count = sum(
        1 for section in resume_sections
        if section in resume_lower
    )

    if len(resume_text.split()) < 100:
        return {
            "valid": False,
            "message": "Uploaded document is too short and does not appear to be a professional resume."
        }

    if section_count < 2:
        return {
            "valid": False,
            "message": "Uploaded file does not appear to be a valid resume. Please upload a professional resume."
        }

    # =====================================================
    # SKILL EXTRACTION
    # =====================================================

    skills_database = [
        "python","java","c","c++","javascript",
        "typescript","react","angular","vue",
        "node","express","mongodb","mysql",
        "postgresql","sql","flask","django",
        "html","css","bootstrap","tailwind",
        "machine learning","deep learning",
        "nlp","tensorflow","pytorch",
        "power bi","tableau","excel",
        "aws","azure","gcp",
        "docker","kubernetes",
        "git","github","rest api",
        "fastapi"
    ]

    detected_skills = []

    for skill in skills_database:
        if skill.lower() in resume_lower:
            detected_skills.append(skill)

    # =====================================================
    # SCORE CALCULATION
    # =====================================================

    score = 40

    # Skills
    score += min(len(detected_skills) * 2, 20)

    # Projects
    if "project" in resume_lower:
        score += 10

    # Experience
    if "experience" in resume_lower:
        score += 10

    # Metrics
    if any(char.isdigit() for char in resume_text):
        score += 10

    # Education
    if any(word in resume_lower for word in [
        "bachelor",
        "master",
        "degree",
        "b.tech",
        "m.tech",
        "certification"
    ]):
        score += 10

    score = min(score, 100)

    # =====================================================
    # JOB RECOMMENDATIONS
    # =====================================================

    recommendations = recommend_job_roles(
        resume_text,
        detected_skills
    )

    # =====================================================
    # STRENGTHS
    # =====================================================

    strengths = []

    if len(detected_skills) >= 5:
        strengths.append(
            "Strong technical skill set detected."
        )

    if "project" in resume_lower:
        strengths.append(
            "Project experience included."
        )

    if any(char.isdigit() for char in resume_text):
        strengths.append(
            "Quantifiable achievements found."
        )

    if "internship" in resume_lower:
        strengths.append(
            "Internship experience included."
        )

    # =====================================================
    # WEAKNESSES
    # =====================================================

    weaknesses = []

    if len(detected_skills) < 3:
        weaknesses.append(
            "Limited technical skills detected."
        )

    if "project" not in resume_lower:
        weaknesses.append(
            "Projects section missing."
        )

    if "experience" not in resume_lower:
        weaknesses.append(
            "Professional experience section missing."
        )

    # =====================================================
    # MISSING SKILLS
    # =====================================================

    missing_skills = []

    best_role = recommendations["best_match"]["role"]

    role_skills = {
        "Python Developer": ["flask", "django", "fastapi", "docker"],
        "Data Scientist": ["tensorflow", "pytorch", "pandas"],
        "Frontend Developer": ["react", "typescript", "tailwind"],
        "Backend Developer": ["docker", "aws", "sql"],
        "DevOps Engineer": ["docker", "kubernetes", "aws"]
    }

    if best_role in role_skills:

        missing_skills = [
            skill
            for skill in role_skills[best_role]
            if skill not in detected_skills
        ]

    # =====================================================
    # RETURN
    # =====================================================

    return {
        "valid": True,
        "score": score,
        "skills": detected_skills,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "missing_skills": missing_skills,
        "recommendations": recommendations
    }
# Default suggestions
return {
    "key_topics": [
        "Data Structures",
        "Algorithms",
        "System Design",
        "Problem Solving",
        "Communication Skills"
    ],

    "common_questions": [
        "Tell me about yourself",
        "Describe a challenging project",
        "What are your strengths and weaknesses?",
        "Why should we hire you?",
        "Where do you see yourself in 5 years?"
    ],

    "tips": [
        "Research the company before the interview",
        "Practice explaining your projects clearly",
        "Prepare behavioral questions using STAR method",
        "Review fundamentals of your domain",
        "Communicate confidently and clearly"
    ]
}
