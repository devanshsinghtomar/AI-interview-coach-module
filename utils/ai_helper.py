# utils/ai_helper.py
import json
import random

# More comprehensive question bank
QUESTION_BANK = {
    "general": [
        "Tell me about yourself and your professional background.",
        "Why are you interested in this position?",
        "What are your key strengths?",
        "What are areas you'd like to improve?",
        "Describe your most significant achievement.",
        "Tell me about a time you failed and what you learned.",
        "How do you handle pressure and tight deadlines?",
        "Describe your ideal work environment.",
        "Where do you see yourself in 5 years?",
        "What motivates you in your career?"
    ],
    "technical": [
        "Explain your experience with relevant technologies.",
        "Tell me about a complex technical problem you solved.",
        "How do you approach learning new technologies?",
        "Describe your development workflow and best practices.",
        "Explain a project where you optimized performance.",
        "How do you ensure code quality and testing?",
        "Tell me about your experience with {role}-specific tools.",
        "Describe a technical challenge and your solution.",
        "How do you handle code reviews?",
        "What's your approach to system design?"
    ],
    "behavioral": [
        "Tell me about a conflict with a team member and how you resolved it.",
        "Describe a time you led a project or team.",
        "Tell me about working in an agile environment.",
        "How do you communicate with non-technical stakeholders?",
        "Describe a situation where you adapted to change.",
        "Tell me about your collaboration style.",
        "How do you mentor or help junior team members?",
        "Describe a time you received critical feedback.",
        "Tell me about your experience with remote work.",
        "How do you prioritize when you have multiple tasks?"
    ]
}

def generate_questions(role, level):
    """
    Generate AI-powered interview questions based on role and level.
    """
    
    # Select question mix based on level
    if level == "Beginner":
        general_count = 4
        technical_count = 3
        behavioral_count = 3
    elif level == "Intermediate":
        general_count = 3
        technical_count = 4
        behavioral_count = 3
    else:  # Advanced
        general_count = 2
        technical_count = 5
        behavioral_count = 3
    
    # Select random questions
    questions = []
    questions.extend(random.sample(QUESTION_BANK["general"], general_count))
    questions.extend(random.sample(QUESTION_BANK["technical"], technical_count))
    questions.extend(random.sample(QUESTION_BANK["behavioral"], behavioral_count))
    
    # Format role-specific questions
    questions = [q.format(role=role) if "{role}" in q else q for q in questions]
    
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
    has_examples = any(word in answer.lower() for word in ["example", "project", "built", "created", "developed"])
    has_metrics = any(char.isdigit() for char in answer)
    has_star = any(word in answer.lower() for word in ["situation", "task", "action", "result"])
    
    suggestions = [
        "• Include specific examples and metrics" if not has_metrics else "✓ Great use of metrics!",
        "• Use the STAR method for structured responses" if not has_star else "✓ Perfect STAR method usage!",
        "• Add real project examples" if not has_examples else "✓ Excellent use of examples!",
        "• Be more concise while maintaining detail" if len(answer.split()) > 100 else "• Consider adding more detail",
        "• Show enthusiasm and confidence" if score < 70 else "✓ Great confidence level!"
    ]
    
    feedback = f"""
📊 AI EVALUATION REPORT
{'='*50}

🎯 Question:
{question}

💬 Your Answer:
{answer}

{'='*50}

📈 EVALUATION METRICS:

✨ Communication: {communication}
🎯 Relevance: {relevance}  
💪 Confidence: {confidence}

🏆 OVERALL SCORE: {score}/100

{'='*50}

💡 IMPROVEMENT SUGGESTIONS:
{chr(10).join(suggestions)}

{'='*50}

🚀 NEXT STEPS:
• Practice this answer with the STAR method
• Add more quantifiable results
• Record yourself and review
• Practice with similar questions
"""
    
    return feedback, score, communication


def analyze_resume_ai(resume_text):
    """
    AI-powered resume analysis.
    """
    
    analysis = {
        "strengths": [],
        "weaknesses": [],
        "score": 0,
        "recommendations": []
    }
    
    # Check for key elements
    if any(word in resume_text.lower() for word in ["project", "developed", "created", "built"]):
        analysis["strengths"].append("✓ Good project descriptions")
        analysis["score"] += 15
    else:
        analysis["weaknesses"].append("✗ Limited project details")
        analysis["recommendations"].append("Add 3-4 key projects with impact metrics")
    
    if any(word in resume_text.lower() for word in ["leadership", "managed", "led", "supervised"]):
        analysis["strengths"].append("✓ Leadership experience shown")
        analysis["score"] += 10
    
    if any(char.isdigit() for char in resume_text):
        analysis["strengths"].append("✓ Uses metrics and numbers")
        analysis["score"] += 15
    else:
        analysis["weaknesses"].append("✗ Missing quantifiable results")
        analysis["recommendations"].append("Add specific metrics (% improvement, $X saved, Y users)")
    
    if any(word in resume_text.lower() for word in ["python", "javascript", "java", "c++", "sql"]):
        analysis["strengths"].append("✓ Technical skills listed")
        analysis["score"] += 15
    
    if any(word in resume_text.lower() for word in ["certification", "degree", "bachelor", "master"]):
        analysis["strengths"].append("✓ Education and certifications included")
        analysis["score"] += 10
    else:
        analysis["recommendations"].append("Highlight relevant certifications and education")
    
    if len(resume_text) > 500:
        analysis["strengths"].append("✓ Comprehensive resume")
        analysis["score"] += 10
    else:
        analysis["weaknesses"].append("✗ Resume might be too brief")
        analysis["recommendations"].append("Add more detail to achievements and projects")
    
    analysis["score"] = min(analysis["score"] + 25, 100)
    
    if not analysis["recommendations"]:
        analysis["recommendations"] = [
            "✓ Great resume! Consider adding:",
            "  • Links to portfolio or GitHub",
            "  • Additional technical skills",
            "  • Awards or recognitions"
        ]
    
    return analysis


def get_ai_suggestions(role, level):
    """
    Get AI-powered interview preparation suggestions.
    """
    
    role_lower = role.lower()
    
    suggestions = {
        "python": {
            "key_topics": ["Data structures", "OOP concepts", "Algorithms", "Django/Flask", "Testing"],
            "common_questions": [
                "Explain decorators in Python",
                "What is a list comprehension?",
                "Explain GIL in Python",
                "How do you handle errors?"
            ],
            "tips": [
                "Practice coding problems on LeetCode",
                "Know Python frameworks well",
                "Understand async programming"
            ]
        },
        "java": {
            "key_topics": ["OOP", "Collections", "Multithreading", "Spring Boot", "Design Patterns"],
            "common_questions": [
                "Explain JVM memory management",
                "What are Design Patterns?",
                "Explain Spring dependency injection",
                "What is immutability?"
            ],
            "tips": [
                "Master Spring Framework",
                "Understand JVM internals",
                "Practice multithreading concepts"
            ]
        },
        "javascript": {
            "key_topics": ["Async/Await", "Closures", "DOM", "React/Vue", "Event Loop"],
            "common_questions": [
                "Explain event delegation",
                "What is closure?",
                "How does async/await work?",
                "Explain hoisting"
            ],
            "tips": [
                "Practice React or Vue deeply",
                "Understand the event loop",
                "Know ES6+ features well"
            ]
        },
        "default": {
            "key_topics": [
                "Core fundamentals",
                "System design",
                "Algorithms",
                "Problem solving",
                "Communication"
            ],
            "common_questions": [
                "Why this role?",
                "Tell about your experience",
                "How do you approach problems?",
                "Describe a challenging project"
            ],
            "tips": [
                "Practice problem-solving",
                "Prepare concrete examples",
                "Practice speaking clearly"
            ]
        }
    }
    
    # Get role-specific suggestions
    role_suggestions = suggestions.get(role_lower, suggestions["default"])
    
    return role_suggestions
