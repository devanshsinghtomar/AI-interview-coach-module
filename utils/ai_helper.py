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

    role_key = ROLE_MAPPING.get(
        role.lower().strip(),
        "python_developer"
    )

    bank = QUESTION_BANK[role_key]

    questions = []

    if level == "Beginner":
        g, t, b = 2, 3, 2

    elif level == "Intermediate":
        g, t, b = 2, 4, 2

    else:
        g, t, b = 2, 5, 3

    questions.extend(
        random.sample(
            bank["general"],
            min(g, len(bank["general"]))
        )
    )

    questions.extend(
        random.sample(
            bank["technical"],
            min(t, len(bank["technical"]))
        )
    )

    questions.extend(
        random.sample(
            bank["behavioral"],
            min(b, len(bank["behavioral"]))
        )
    )

    return questions

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
