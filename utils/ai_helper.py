import random

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
# ROLE MAPPING
# =====================================================

ROLE_MAPPING = {
    "python": "python_developer",
    "python_developer": "python_developer",

    "java": "python_developer",
    "java_developer": "python_developer",

    "javascript": "python_developer",
    "javascript_developer": "python_developer",

    "react": "python_developer",
    "react_developer": "python_developer",

    "full_stack": "python_developer",
    "full_stack_developer": "python_developer",

    "data_science": "python_developer",
    "data_scientist": "python_developer",

    "data_analyst": "python_developer",

    "devops": "python_developer",
    "devops_engineer": "python_developer"
}

# =====================================================
# GENERATE QUESTIONS
# =====================================================

def generate_questions(role, level):

    role_key = role.lower().strip().replace(" ", "_")
    role_key = ROLE_MAPPING.get(role_key, "python_developer")

    bank = QUESTION_BANK[role_key]

    if level == "Beginner":
        general_count = 3
        technical_count = 3
        behavioral_count = 2

    elif level == "Intermediate":
        general_count = 2
        technical_count = 4
        behavioral_count = 3

    else:
        general_count = 2
        technical_count = 5
        behavioral_count = 3

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
🎯 AI Interview Questions for {display_role} ({level})

{formatted_questions}

------------------------------------------------

💡 TIP:
Use the STAR Method:
Situation → Task → Action → Result
"""

# =====================================================
# EVALUATE ANSWER
# =====================================================

def evaluate_answer(role, question, answer):

    if not answer or len(answer.strip()) < 10:
        score = 20
        communication = "Poor"

    elif len(answer.split()) < 20:
        score = 40
        communication = "Fair"

    elif len(answer.split()) < 50:
        score = 65
        communication = "Good"

    elif len(answer.split()) < 100:
        score = 80
        communication = "Very Good"

    else:
        score = 90
        communication = "Excellent"

    suggestions = []

    if "example" in answer.lower():
        suggestions.append("Good use of examples.")
    else:
        suggestions.append("Add real project examples.")

    if any(char.isdigit() for char in answer):
        suggestions.append("Good use of metrics.")
    else:
        suggestions.append("Add measurable impact and numbers.")

    feedback = f"""
AI FEEDBACK REPORT
==============================

Question:
{question}

Answer:
{answer}

Score: {score}/100

Communication:
{communication}

Suggestions:
- {' '.join(suggestions)}
"""

    return feedback, score, communication

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

    skills = [
        "python",
        "java",
        "sql",
        "react",
        "docker",
        "flask",
        "django"
    ]

    for skill in skills:
        if skill in resume_lower:
            detected_skills.append(skill)

    score = min(50 + len(detected_skills) * 7, 100)

    return {
        "valid": True,
        "score": score,
        "skills": detected_skills,
        "strengths": [
            "Good technical keywords",
            "Relevant skill coverage"
        ],
        "weaknesses": [],
        "missing_skills": [
            "REST APIs",
            "Git",
            "Testing"
        ],
        "recommendations": {
            "best_match": {
                "role": "Python Developer"
            }
        }
    }

# =====================================================
# AI SUGGESTIONS
# =====================================================

def get_ai_suggestions(role, level):

    role_lower = role.lower()

    if "python" in role_lower:
        return {
            "key_topics": [
                "Python",
                "OOP",
                "Flask",
                "Django",
                "SQL"
            ],
            "common_questions": [
                "What is OOP?",
                "What are decorators?",
                "What is Flask?"
            ],
            "tips": [
                "Practice coding daily",
                "Build projects",
                "Revise Python fundamentals"
            ]
        }

    if "java" in role_lower:
        return {
            "key_topics": [
                "Java",
                "JVM",
                "Spring Boot"
            ],
            "common_questions": [
                "Explain JVM",
                "What is Spring Boot?"
            ],
            "tips": [
                "Practice Java coding",
                "Learn Spring Framework"
            ]
        }

    return {
        "key_topics": [
            "DSA",
            "System Design",
            "Communication"
        ],
        "common_questions": [
            "Tell me about yourself"
        ],
        "tips": [
            "Practice daily",
            "Improve communication skills"
        ]
    }
