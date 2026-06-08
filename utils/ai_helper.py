import random

# =====================================================
# QUESTION BANK
# =====================================================

QUESTION_BANK = {

    "python_developer": {
        "general": [
            "Tell me about your Python experience.",
            "What Python projects have you built?",
            "Why do you prefer Python?"
        ],
        "technical": [
            "Explain decorators.",
            "What is list comprehension?",
            "Difference between tuple and list?",
            "Explain generators.",
            "What is GIL?",
            "What are *args and **kwargs?"
        ],
        "behavioral": [
            "Describe a Python bug you fixed.",
            "Tell me about a project challenge."
        ]
    },

    "java_developer": {
        "general": [
            "Tell me about your Java experience.",
            "Why do you use Java?"
        ],
        "technical": [
            "What is JVM?",
            "Difference between JDK and JRE?",
            "Explain OOP principles.",
            "What is Spring Boot?",
            "Difference between HashMap and Hashtable?"
        ],
        "behavioral": [
            "Describe a challenging Java project."
        ]
    },

    "react_developer": {
        "general": [
            "Tell me about your React experience."
        ],
        "technical": [
            "What are Hooks?",
            "What is Virtual DOM?",
            "Difference between state and props?",
            "Explain useEffect.",
            "What is Redux?"
        ],
        "behavioral": [
            "Describe a frontend challenge."
        ]
    },

    "data_scientist": {
        "general": [
            "Tell me about your ML experience."
        ],
        "technical": [
            "What is overfitting?",
            "Explain train-test split.",
            "Difference between supervised and unsupervised learning.",
            "What is random forest?",
            "What is cross validation?"
        ],
        "behavioral": [
            "Describe your best ML project."
        ]
    },

    "devops_engineer": {
        "general": [
            "Tell me about your DevOps experience."
        ],
        "technical": [
            "What is Docker?",
            "What is Kubernetes?",
            "Explain CI/CD.",
            "Difference between containers and VMs?",
            "What is Infrastructure as Code?"
        ],
        "behavioral": [
            "Describe a deployment issue you solved."
        ]
    }
}

# =====================================================
# ROLE MAPPING
# =====================================================

ROLE_MAPPING = {

    "python": "python_developer",
    "python_developer": "python_developer",

    "java": "java_developer",
    "java_developer": "java_developer",

    "react": "react_developer",
    "react_developer": "react_developer",

    "javascript": "react_developer",
    "javascript_developer": "react_developer",

    "data_science": "data_scientist",
    "data_scientist": "data_scientist",

    "machine_learning": "data_scientist",

    "devops": "devops_engineer",
    "devops_engineer": "devops_engineer",

    "full_stack": "react_developer",
    "full_stack_developer": "react_developer"
}

# =====================================================
# QUESTION GENERATOR
# =====================================================

def generate_questions(role, level):
    """
    Generate AI-powered interview questions based on role and level.
    """

    role_key = role.lower().strip().replace(" ", "_")

    role_mapping = {
        "python": "python_developer",
        "python_developer": "python_developer",

        "java": "java_developer",
        "java_developer": "java_developer",

        "javascript": "javascript_developer",
        "javascript_developer": "javascript_developer",

        "react": "javascript_developer",

        "data_science": "data_scientist",
        "data_scientist": "data_scientist",

        "data_scientist": "data_scientist",

        "full_stack": "full_stack_developer",
        "full_stack_developer": "full_stack_developer",

        "devops": "devops_engineer",
        "devops_engineer": "devops_engineer"
    }

    role_key = role_mapping.get(role_key)

    if role_key and role_key in QUESTION_BANK:
        bank = QUESTION_BANK[role_key]
    else:
        bank = QUESTION_BANK["python_developer"]

    # Question count based on level
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

    formatted_questions = "\n\n".join(
        [f"{i+1}. {q}" for i, q in enumerate(questions)]
    )

    return f"""
🎯 AI Interview Questions ({level})

Role: {role}

{formatted_questions}
"""

# =====================================================
# ANSWER EVALUATION
# =====================================================

def evaluate_answer(role, question, answer):

    words = len(answer.split())

    if words < 15:
        score = 30
        communication = "Poor"

    elif words < 40:
        score = 55
        communication = "Average"

    elif words < 80:
        score = 75
        communication = "Good"

    elif words < 150:
        score = 90
        communication = "Excellent"

    else:
        score = 95
        communication = "Outstanding"

    strengths = []

    if "project" in answer.lower():
        strengths.append("Project experience mentioned")

    if any(ch.isdigit() for ch in answer):
        strengths.append("Metrics included")

    if not strengths:
        strengths.append("Answer addresses question")

    feedback = f"""
Question:
{question}

Score:
{score}/100

Communication:
{communication}

Strengths:
{', '.join(strengths)}

Suggestions:
Use STAR Method and include project examples.
"""

    return feedback, score, communication

# =====================================================
# RESUME ANALYSIS
# =====================================================

def analyze_resume_ai(resume_text):

    text = resume_text.lower()

    sections = [
        "education",
        "experience",
        "skills",
        "projects",
        "internship",
        "summary",
        "profile"
    ]

    section_count = sum(
        1 for s in sections
        if s in text
    )

    if len(resume_text.split()) < 120 or section_count < 3:

        return {
            "valid": False,
            "message": "Uploaded file does not appear to be a professional resume."
        }

    skill_map = {

        "python": [
            "Python Developer",
            "Backend Developer",
            "Django Developer",
            "Flask Developer"
        ],

        "java": [
            "Java Developer",
            "Spring Boot Developer",
            "Backend Engineer"
        ],

        "react": [
            "React Developer",
            "Frontend Developer",
            "UI Engineer"
        ],

        "javascript": [
            "JavaScript Developer",
            "Frontend Developer"
        ],

        "sql": [
            "Data Analyst",
            "Database Developer"
        ],

        "machine learning": [
            "ML Engineer",
            "AI Engineer",
            "Data Scientist"
        ],

        "docker": [
            "DevOps Engineer"
        ],

        "aws": [
            "Cloud Engineer",
            "DevOps Engineer"
        ]
    }

    detected_skills = []
    roles = []

    for skill, role_list in skill_map.items():

        if skill in text:

            detected_skills.append(skill)

            roles.extend(role_list)

    roles = list(set(roles))

    score = min(
        60 + len(detected_skills) * 5,
        100
    )

    return {

        "valid": True,

        "score": score,

        "skills": detected_skills,

        "strengths": [
            "Resume structure detected",
            "Technical skills identified",
            "Relevant keywords present"
        ],

        "weaknesses": [] if len(detected_skills) >= 3 else [
            "Add more technical skills",
            "Include more project details"
        ],

        "missing_skills": [
            "Git",
            "REST API",
            "Testing"
        ],

        "recommended_roles": roles,

        "recommendations": {
            "best_match": {
                "role": roles[0] if roles else "Software Engineer",
                "match_percentage": score,
                "description": "Based on detected skills and experience."
            },
            "top_roles": [
                {
                    "role": role,
                    "match_percentage": max(score - i * 5, 60),
                    "description": "Recommended from resume skills."
                }
                for i, role in enumerate(roles[:5])
            ]
        }
    }

# =====================================================
# AI SUGGESTIONS
# =====================================================

def get_ai_suggestions(role, level):

    return {
        "key_topics": [
            "Communication",
            "Problem Solving",
            "Projects",
            "Technical Concepts"
        ],
        "common_questions": [
            "Tell me about yourself",
            "Describe a project",
            "What challenges did you face?"
        ],
        "tips": [
            "Use STAR method",
            "Give real examples",
            "Include measurable impact"
        ]
    }
