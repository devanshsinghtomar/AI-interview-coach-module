import json
import random
from utils.job_recommendation import recommend_job_roles


# =====================================================
# QUESTION BANK
# =====================================================
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
            "Describe a situation where your code failed in production.",
            "How do you approach writing maintainable code?",
            "Tell me about your experience with code reviews."
        ]
    }
}


# =====================================================
# GENERATE QUESTIONS
# =====================================================
def generate_questions(role, level):
    """
    Generate AI-powered interview questions based on role and level.
    """

    # Normalize role
    role_key = role.lower().replace(" ", "_")

    # Role Mapping
   role_key = role.lower().strip().replace(" ", "_")

role_mapping = {
    "python": "python_developer",
    "python_developer": "python_developer",

    "java": "java_developer",
    "java_developer": "java_developer",

    "javascript": "javascript_developer",
    "javascript_developer": "javascript_developer",

    "react": "full_stack_developer",
    "react_developer": "full_stack_developer",

    "full_stack": "full_stack_developer",
    "full_stack_developer": "full_stack_developer",

    "data_science": "data_scientist",
    "data_scientist": "data_scientist",

    "data_analyst": "data_scientist",

    "devops": "devops_engineer",
    "devops_engineer": "devops_engineer"
}

role_key = role_mapping.get(role_key, "python_developer")

bank = QUESTION_BANK[role_key]

    # Get correct question bank
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

    questions.extend(
        random.sample(
            bank["general"],
            min(general_count, len(bank["general"]))
        )
    )

    questions.extend(
        random.sample(
            bank["technical"],
            min(technical_count, len(bank["technical"]))
        )
    )

    questions.extend(
        random.sample(
            bank["behavioral"],
            min(behavioral_count, len(bank["behavioral"]))
        )
    )

    display_role = role.replace("_", " ").title()

    formatted_questions = "\n\n".join(
        [f"{i+1}. {q}" for i, q in enumerate(questions)]
    )

    return f"""
🎯 AI-Generated Interview Questions for {display_role} ({level})

{formatted_questions}

---
💡 TIP: Use the STAR method (Situation, Task, Action, Result) for behavioral questions!
"""


# =====================================================
# EVALUATE ANSWER
# =====================================================
def evaluate_answer(role, question, answer):

    if not answer or len(answer.strip()) < 10:
        score = 20
        comm = "Poor"
    elif len(answer.split()) < 20:
        score = 40
        comm = "Fair"
    elif len(answer.split()) < 50:
        score = 65
        comm = "Good"
    elif len(answer.split()) < 100:
        score = 80
        comm = "Very Good"
    else:
        score = 90
        comm = "Excellent"

    suggestions = []

    if "example" in answer.lower():
        suggestions.append("Good use of examples")
    else:
        suggestions.append("Add real project examples")

    if any(char.isdigit() for char in answer):
        suggestions.append("Good use of metrics")
    else:
        suggestions.append("Add numbers/impact")

    feedback = f"""
AI FEEDBACK REPORT
====================

Question:
{question}

Answer:
{answer}

Score: {score}/100
Communication: {comm}

Suggestions:
- {' '.join(suggestions)}
"""

    return feedback, score, comm


# =====================================================
# RESUME ANALYSIS
# =====================================================
def analyze_resume_ai(resume_text):

    resume_lower = resume_text.lower()

    if len(resume_text.split()) < 100:
        return {
            "valid": False,
            "message": "Resume too short"
        }

    detected_skills = []

    skills = ["python", "java", "sql", "react", "docker"]

    for s in skills:
        if s in resume_lower:
            detected_skills.append(s)

    score = 50 + len(detected_skills) * 5
    score = min(score, 100)

    recommendations = {
        "best_match": {
            "role": "Python Developer"
        }
    }

    missing = ["flask", "django", "api"]

    return {
        "valid": True,
        "score": score,
        "skills": detected_skills,
        "strengths": ["Good resume"],
        "weaknesses": [],
        "missing_skills": missing,
        "recommendations": recommendations
    }


# =====================================================
# AI SUGGESTIONS (FIXED)
# =====================================================
def get_ai_suggestions(role, level):

    role_lower = role.lower()

    if "python" in role_lower:
        return {
            "key_topics": ["Python", "OOP", "SQL"],
            "common_questions": ["What is Python?", "Explain OOP"],
            "tips": ["Practice coding daily", "Build projects"]
        }

    if "java" in role_lower:
        return {
            "key_topics": ["Java", "JVM", "Spring"],
            "common_questions": ["What is JVM?", "What is Spring?"],
            "tips": ["Practice Java", "Learn Spring Boot"]
        }

    return {
        "key_topics": ["DSA", "System Design", "Communication"],
        "common_questions": ["Tell me about yourself"],
        "tips": ["Practice daily", "Improve communication"]
    }
