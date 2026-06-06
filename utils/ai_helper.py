# utils/ai_helper.py
import json
import random

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
    if role_key in QUESTION_BANK:
        bank = QUESTION_BANK[role_key]
    else:
        # Default to generic questions
        bank = QUESTION_BANK.get(list(QUESTION_BANK.keys())[0])
    
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
    AI-powered resume analysis with comprehensive scoring.
    """
    
    analysis = {
        "strengths": [],
        "weaknesses": [],
        "score": 0,
        "recommendations": []
    }
    
    resume_lower = resume_text.lower()
    
    # Check for key elements
    if any(word in resume_lower for word in ["project", "developed", "created", "built", "implemented"]):
        analysis["strengths"].append("✅ Clear project descriptions")
        analysis["score"] += 15
    else:
        analysis["weaknesses"].append("⚠️ Limited project details")
        analysis["recommendations"].append("Add 3-4 key projects with measurable impact")
    
    if any(word in resume_lower for word in ["leadership", "managed", "led", "supervised", "mentored"]):
        analysis["strengths"].append("✅ Leadership experience shown")
        analysis["score"] += 12
    else:
        analysis["recommendations"].append("Highlight any leadership or mentoring experience")
    
    if any(char.isdigit() for char in resume_text):
        analysis["strengths"].append("✅ Quantifiable achievements included")
        analysis["score"] += 15
    else:
        analysis["weaknesses"].append("⚠️ Missing metrics and numbers")
        analysis["recommendations"].append("Add specific metrics (% improvement, users reached, revenue generated)")
    
    # Technical skills check
    tech_skills = ["python", "java", "javascript", "react", "node", "sql", "mongodb", "aws", "docker", "kubernetes", "git", "api", "rest", "graphql"]
    tech_count = sum(1 for skill in tech_skills if skill in resume_lower)
    if tech_count >= 3:
        analysis["strengths"].append(f"✅ Strong technical skills ({tech_count} technologies mentioned)")
        analysis["score"] += 15
    else:
        analysis["recommendations"].append(f"Include more technical skills (currently has {tech_count})")
    
    # Education check
    if any(word in resume_lower for word in ["certification", "degree", "bachelor", "master", "diploma", "bootcamp"]):
        analysis["strengths"].append("✅ Education and certifications included")
        analysis["score"] += 10
    else:
        analysis["recommendations"].append("Highlight relevant education and certifications")
    
    # Length check
    if len(resume_text) > 500:
        analysis["strengths"].append("✅ Comprehensive resume with good detail")
        analysis["score"] += 10
    elif len(resume_text) > 300:
        analysis["score"] += 5
    else:
        analysis["weaknesses"].append("⚠️ Resume might be too brief")
        analysis["recommendations"].append("Expand resume with more achievements and responsibilities")
    
    # Achievement keywords
    achievement_keywords = ["improved", "increased", "reduced", "optimized", "accelerated", "streamlined", "enhanced", "launched", "delivered"]
    achievement_count = sum(1 for keyword in achievement_keywords if keyword in resume_lower)
    if achievement_count >= 3:
        analysis["strengths"].append("✅ Action-oriented language and achievements")
        analysis["score"] += 12
    else:
        analysis["recommendations"].append("Use more action verbs (improved, increased, optimized, etc.)")
    
    # Ensure score doesn't exceed 100
    analysis["score"] = min(analysis["score"] + 11, 100)
    
    if not analysis["weaknesses"]:
        analysis["recommendations"] = [
            "✅ Your resume is well-structured!",
            "💡 Consider adding:",
            "   • Links to GitHub or portfolio",
            "   • Open source contributions",
            "   • Notable achievements and awards",
            "   • Certifications and training courses"
        ]
    
    return analysis


def get_ai_suggestions(role, level):
    """
    Get AI-powered interview preparation suggestions.
    """
    
    role_lower = role.lower()
    
    suggestions_map = {
        "python": {
            "key_topics": ["Data structures", "OOP concepts", "Algorithms", "Django/Flask", "Testing", "Async Programming"],
            "common_questions": [
                "Explain decorators in Python",
                "What is a list comprehension?",
                "Explain GIL in Python",
                "What are generators?",
                "Explain exception handling"
            ],
            "tips": [
                "Practice coding problems on LeetCode",
                "Master Python frameworks (Django/Flask)",
                "Understand async/await programming",
                "Know Python best practices and PEP 8"
            ]
        },
        "java": {
            "key_topics": ["OOP", "Collections", "Multithreading", "Spring Boot", "Design Patterns", "JVM"],
            "common_questions": [
                "Explain JVM memory management",
                "What are Design Patterns?",
                "Explain Spring dependency injection",
                "What is immutability?",
                "Explain exception handling in Java"
            ],
            "tips": [
                "Master Spring Framework and annotations",
                "Understand JVM internals and garbage collection",
                "Practice multithreading concepts",
                "Know common design patterns"
            ]
        },
        "javascript": {
            "key_topics": ["Async/Await", "Closures", "DOM", "React/Vue", "Event Loop", "Promises"],
            "common_questions": [
                "Explain event delegation",
                "What is closure?",
                "How does async/await work?",
                "Explain hoisting",
                "What is the event loop?"
            ],
            "tips": [
                "Master React or Vue deeply",
                "Understand the event loop and callbacks",
                "Know ES6+ features and arrow functions",
                "Practice async/promise patterns"
            ]
        },
        "data science": {
            "key_topics": ["ML Algorithms", "Statistics", "Feature Engineering", "Data Preprocessing", "Evaluation Metrics"],
            "common_questions": [
                "Explain supervised vs unsupervised learning",
                "What is overfitting and regularization?",
                "Explain cross-validation",
                "What are evaluation metrics?",
                "How do you handle imbalanced data?"
            ],
            "tips": [
                "Learn statistics and probability well",
                "Master popular ML libraries (scikit-learn, TensorFlow)",
                "Understand feature engineering techniques",
                "Practice with Kaggle competitions"
            ]
        },
        "devops": {
            "key_topics": ["Docker", "Kubernetes", "CI/CD", "Infrastructure as Code", "Cloud Platforms", "Monitoring"],
            "common_questions": [
                "Explain containerization and Docker",
                "What is Kubernetes orchestration?",
                "How do CI/CD pipelines work?",
                "Explain infrastructure as code",
                "What is monitoring and logging?"
            ],
            "tips": [
                "Get hands-on with Docker and Kubernetes",
                "Master at least one cloud platform (AWS/Azure/GCP)",
                "Learn infrastructure as code tools (Terraform)",
                "Understand CI/CD tools like Jenkins, GitLab CI"
            ]
        }
    }
    
    # Try to find matching suggestions
    for key, value in suggestions_map.items():
        if key in role_lower:
            return value
    
    # Default suggestions
    return {
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
            "Practice speaking clearly",
            "Research the company thoroughly"
        ]
    }
