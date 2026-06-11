from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime
import json
import os
import random
import re
import PyPDF2
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///interview.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Interview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_role = db.Column(db.String(100))
    question = db.Column(db.Text)
    answer = db.Column(db.Text)
    score = db.Column(db.Integer)
    feedback = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class ResumeAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(200))
    extracted_text = db.Column(db.Text)
    score = db.Column(db.Integer)
    suggested_role = db.Column(db.String(100))
    suggested_roles = db.Column(db.Text)
    strengths = db.Column(db.Text)
    improvements = db.Column(db.Text)
    skills_found = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(100))
    difficulty = db.Column(db.String(50))
    score = db.Column(db.Integer)
    total_questions = db.Column(db.Integer)
    correct_answers = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============ 15+ JOB ROLES FOR MOCK INTERVIEW ============
INTERVIEW_QUESTIONS_WITH_ANSWERS = {
    'Python Developer': [
        {"question": "What is the difference between a list and a tuple in Python?", "keywords": ["mutable", "immutable", "change", "modify", "fixed"], "sample_answer": "Lists are mutable (can be changed) while tuples are immutable."},
        {"question": "What is a decorator in Python?", "keywords": ["function", "modify", "wrapper", "@", "syntax"], "sample_answer": "A decorator is a function that takes another function and extends its behavior."},
        {"question": "Explain the Global Interpreter Lock (GIL).", "keywords": ["mutex", "thread", "execution", "bytecode", "simultaneously"], "sample_answer": "The GIL prevents multiple threads from executing Python bytecode at once."},
        {"question": "What is list comprehension?", "keywords": ["concise", "create", "list", "loop", "condition"], "sample_answer": "List comprehension provides a concise way to create lists."},
        {"question": "How does exception handling work?", "keywords": ["try", "except", "finally", "raise", "error"], "sample_answer": "Exception handling uses try-except blocks to handle errors gracefully."},
        {"question": "What are generators in Python?", "keywords": ["yield", "iterator", "memory", "efficient", "lazy"], "sample_answer": "Generators yield values one at a time using yield keyword."},
        {"question": "What is the difference between deep and shallow copy?", "keywords": ["recursive", "reference", "nested", "objects", "copy"], "sample_answer": "Deep copy creates independent copies while shallow copy shares references."}
    ],
    'JavaScript Developer': [
        {"question": "What is closure in JavaScript?", "keywords": ["inner function", "outer scope", "variables", "return", "access"], "sample_answer": "A closure has access to its outer function's scope even after the outer function returns."},
        {"question": "Explain the difference between == and ===.", "keywords": ["value", "type", "strict", "equality", "comparison"], "sample_answer": "== compares value after coercion, === compares both value and type."},
        {"question": "What is hoisting?", "keywords": ["declaration", "move", "top", "scope", "var"], "sample_answer": "Hoisting moves declarations to the top of their scope during compilation."},
        {"question": "What are promises in JavaScript?", "keywords": ["async", "await", "future", "value", "callback"], "sample_answer": "Promises represent the eventual completion of async operations."},
        {"question": "What is the event loop?", "keywords": ["async", "queue", "call stack", "non-blocking", "execution"], "sample_answer": "The event loop handles async callbacks in JavaScript."}
    ],
    'Data Scientist': [
        {"question": "Difference between supervised and unsupervised learning?", "keywords": ["labeled", "unlabeled", "output", "target", "training"], "sample_answer": "Supervised uses labeled data, unsupervised finds patterns in unlabeled data."},
        {"question": "What is overfitting and how to prevent it?", "keywords": ["training", "noise", "generalization", "regularization", "validation"], "sample_answer": "Overfitting occurs when model learns noise; prevent with cross-validation."},
        {"question": "Explain bias-variance tradeoff.", "keywords": ["underfitting", "overfitting", "error", "complexity", "balance"], "sample_answer": "Bias is error from wrong assumptions, variance is sensitivity to training data."},
        {"question": "What is cross-validation?", "keywords": ["k-fold", "validation", "testing", "training", "split"], "sample_answer": "Cross-validation splits data multiple times for robust evaluation."},
        {"question": "What evaluation metrics for classification?", "keywords": ["accuracy", "precision", "recall", "f1", "roc"], "sample_answer": "Metrics include accuracy, precision, recall, F1-score, and AUC-ROC."}
    ],
    'Full Stack Developer': [
        {"question": "What is REST API?", "keywords": ["representational", "state", "transfer", "http", "endpoint"], "sample_answer": "REST is an architectural style for designing networked applications."},
        {"question": "Difference between SQL and NoSQL?", "keywords": ["structured", "unstructured", "schema", "scalability", "flexible"], "sample_answer": "SQL has fixed schema, NoSQL is flexible and horizontally scalable."},
        {"question": "What is JWT authentication?", "keywords": ["json", "web", "token", "stateless", "signature"], "sample_answer": "JWT is a stateless authentication method using signed JSON tokens."},
        {"question": "What is CORS?", "keywords": ["cross", "origin", "resource", "sharing", "browser"], "sample_answer": "CORS allows web pages to request resources from different domains."},
        {"question": "Explain MVC architecture.", "keywords": ["model", "view", "controller", "separation", "concerns"], "sample_answer": "MVC separates application into Model, View, and Controller components."}
    ],
    'DevOps Engineer': [
        {"question": "What is Docker?", "keywords": ["container", "image", "isolate", "deploy", "environment"], "sample_answer": "Docker packages applications in containers for consistent deployment."},
        {"question": "Explain CI/CD pipeline.", "keywords": ["continuous", "integration", "delivery", "deployment", "automation"], "sample_answer": "CI/CD automates building, testing, and deploying code changes."},
        {"question": "What is Kubernetes?", "keywords": ["orchestration", "container", "cluster", "pods", "scaling"], "sample_answer": "Kubernetes orchestrates and manages containerized applications."},
        {"question": "What is infrastructure as code?", "keywords": ["terraform", "cloudformation", "automation", "version", "provision"], "sample_answer": "IaC manages infrastructure using code instead of manual processes."},
        {"question": "Explain blue-green deployment.", "keywords": ["two", "environments", "switch", "zero", "downtime"], "sample_answer": "Blue-green deployment uses two identical environments for zero-downtime releases."}
    ],
    'Java Developer': [
        {"question": "Difference between abstract class and interface?", "keywords": ["implementation", "multiple", "inheritance", "abstract", "methods"], "sample_answer": "Abstract classes can have implemented methods, interfaces are fully abstract (Java 8+ has defaults)."},
        {"question": "What is multithreading in Java?", "keywords": ["concurrent", "threads", "parallel", "execution", "runnable"], "sample_answer": "Multithreading allows multiple threads to execute concurrently."},
        {"question": "Explain garbage collection in Java.", "keywords": ["memory", "reclaim", "unused", "objects", "jvm"], "sample_answer": "GC automatically removes unused objects from memory."},
        {"question": "What is Spring Boot?", "keywords": ["framework", "microservices", "auto-configuration", "production", "ready"], "sample_answer": "Spring Boot simplifies Spring application setup and deployment."},
        {"question": "Difference between HashMap and Hashtable?", "keywords": ["synchronized", "null", "thread-safe", "performance", "legacy"], "sample_answer": "HashMap is not thread-safe but allows null, Hashtable is synchronized."}
    ],
    'Cloud Engineer': [
        {"question": "What are the cloud service models?", "keywords": ["iaas", "paas", "saas", "infrastructure", "platform"], "sample_answer": "IaaS, PaaS, and SaaS are the three main cloud service models."},
        {"question": "Explain serverless computing.", "keywords": ["functions", "event-driven", "no server", "scale", "automatic"], "sample_answer": "Serverless runs code without managing servers, scaling automatically."},
        {"question": "What is the difference between scaling up and scaling out?", "keywords": ["vertical", "horizontal", "more power", "more instances", "resources"], "sample_answer": "Scaling up adds more power to existing server, scaling out adds more servers."},
        {"question": "What is Infrastructure as Code?", "keywords": ["terraform", "cloudformation", "automation", "version", "provision"], "sample_answer": "IaC manages and provisions infrastructure through code."},
        {"question": "Explain load balancer types.", "keywords": ["application", "network", "classic", "distribution", "traffic"], "sample_answer": "Load balancers distribute traffic across multiple servers."}
    ],
    'Frontend Developer': [
        {"question": "What is the difference between React and Angular?", "keywords": ["library", "framework", "virtual dom", "two-way", "binding"], "sample_answer": "React is a UI library, Angular is a full-featured framework."},
        {"question": "Explain the virtual DOM.", "keywords": ["react", "performance", "real dom", "diffing", "update"], "sample_answer": "Virtual DOM is a lightweight copy of real DOM for efficient updates."},
        {"question": "What are React hooks?", "keywords": ["usestate", "useeffect", "functional", "components", "state"], "sample_answer": "Hooks let you use state and lifecycle in functional components."},
        {"question": "What is responsive design?", "keywords": ["mobile", "adaptive", "viewport", "media", "queries"], "sample_answer": "Responsive design makes websites work on all screen sizes."},
        {"question": "Explain CSS Flexbox.", "keywords": ["layout", "flexible", "alignment", "distribution", "container"], "sample_answer": "Flexbox provides efficient layout, alignment, and space distribution."}
    ],
    'Backend Developer': [
        {"question": "What is the difference between REST and GraphQL?", "keywords": ["overfetching", "underfetching", "query", "endpoint", "schema"], "sample_answer": "GraphQL allows clients to request exactly what they need, REST has fixed endpoints."},
        {"question": "Explain database indexing.", "keywords": ["performance", "lookup", "b-tree", "speed", "query"], "sample_answer": "Indexes speed up data retrieval at the cost of storage."},
        {"question": "What is caching and why use it?", "keywords": ["performance", "memory", "redis", "memcached", "reduce"], "sample_answer": "Caching stores frequently accessed data for faster retrieval."},
        {"question": "Explain load balancing.", "keywords": ["distribution", "traffic", "servers", "availability", "performance"], "sample_answer": "Load balancing distributes incoming traffic across multiple servers."},
        {"question": "What is the difference between SQL and NoSQL?", "keywords": ["structured", "unstructured", "schema", "scalability", "flexible"], "sample_answer": "SQL has rigid schema, NoSQL is schema-less and scalable."}
    ],
    'Machine Learning Engineer': [
        {"question": "Explain the difference between AI, ML, and DL.", "keywords": ["artificial", "intelligence", "machine", "learning", "deep"], "sample_answer": "AI is the broad field, ML is subset of AI, DL is subset of ML using neural networks."},
        {"question": "What is the difference between classification and regression?", "keywords": ["categorical", "continuous", "predict", "label", "value"], "sample_answer": "Classification predicts categories, regression predicts continuous values."},
        {"question": "Explain neural networks.", "keywords": ["layers", "neurons", "activation", "weights", "backpropagation"], "sample_answer": "Neural networks are computing systems inspired by biological brains."},
        {"question": "What is transfer learning?", "keywords": ["pretrained", "model", "fine-tune", "adapt", "knowledge"], "sample_answer": "Transfer learning reuses a pretrained model for a new task."},
        {"question": "Explain the confusion matrix.", "keywords": ["tp", "tn", "fp", "fn", "accuracy"], "sample_answer": "Confusion matrix shows true/false positives/negatives for classification."}
    ]
}

# ============ 100+ QUIZ QUESTIONS WITH PROPER OPTIONS ============
QUIZ_QUESTIONS = {
    'Python': [
        {"question": "What is the correct way to create a function in Python?", "options": ["def myFunction():", "function myFunction():", "create myFunction():", "func myFunction():"], "correct": "def myFunction():", "explanation": "In Python, functions are defined using the 'def' keyword followed by the function name and parentheses."},
        {"question": "What does the 'len()' function do in Python?", "options": ["Returns the length of an object", "Converts to lowercase", "Rounds a number", "Finds the maximum value"], "correct": "Returns the length of an object", "explanation": "len() returns the number of items in a container like list, string, tuple, or dictionary."},
        {"question": "Which operator is used for exponentiation in Python?", "options": ["**", "^", "exp()", "&&"], "correct": "**", "explanation": "** is the exponentiation operator. For example, 2**3 returns 8 (2 to the power of 3)."},
        {"question": "What is the output of print(type(10)) in Python?", "options": ["<class 'int'>", "<class 'float'>", "<class 'str'>", "<class 'list'>"], "correct": "<class 'int'>", "explanation": "10 is an integer literal, so type() returns the int class."},
        {"question": "How do you create a list in Python?", "options": ["my_list = [1, 2, 3]", "my_list = (1, 2, 3)", "my_list = {1, 2, 3}", "my_list = <1, 2, 3>"], "correct": "my_list = [1, 2, 3]", "explanation": "Lists are created using square brackets [] containing comma-separated values."},
        {"question": "What is the correct syntax for a while loop in Python?", "options": ["while x > y:", "while (x > y)", "x > y while {", "while x > y then:"], "correct": "while x > y:", "explanation": "while loops use 'while condition:' syntax with a colon at the end."},
        {"question": "What does the 'append()' method do to a list?", "options": ["Adds an element to the end", "Removes an element", "Inserts at beginning", "Sorts the list"], "correct": "Adds an element to the end", "explanation": "append() adds a single element to the end of an existing list."},
        {"question": "What is the result of 10 // 3 in Python?", "options": ["3", "3.33", "3.0", "1"], "correct": "3", "explanation": "// is floor division, which returns the integer quotient (3 with remainder 1)."},
        {"question": "Which keyword is used to define a class in Python?", "options": ["class", "def", "object", "struct"], "correct": "class", "explanation": "Classes are defined using the 'class' keyword followed by the class name."},
        {"question": "What does the 'break' statement do?", "options": ["Exits the loop", "Skips current iteration", "Pauses the loop", "Restarts the loop"], "correct": "Exits the loop", "explanation": "break terminates the loop completely and continues with the next statement after the loop."},
        {"question": "What is the correct way to import a module in Python?", "options": ["import module", "include module", "using module", "require module"], "correct": "import module", "explanation": "The 'import' keyword is used to import modules into your Python code."},
        {"question": "What is the output of print(2 ** 3)?", "options": ["6", "8", "9", "5"], "correct": "8", "explanation": "2 ** 3 means 2 raised to power 3, which equals 8."},
        {"question": "Which of the following is a mutable data type in Python?", "options": ["Tuple", "String", "List", "Integer"], "correct": "List", "explanation": "Lists are mutable (can be changed), while tuples, strings, and integers are immutable."},
        {"question": "What is a decorator in Python?", "options": ["A function that modifies another function", "A class decorator", "A variable decorator", "A module decorator"], "correct": "A function that modifies another function", "explanation": "Decorators are functions that take another function and extend its behavior without modifying it directly."},
        {"question": "What is list comprehension?", "options": ["Creating list with loop", "Advanced list creation", "Both A and B", "List copying"], "correct": "Both A and B", "explanation": "List comprehension provides a concise way to create lists using a single line of code."},
        {"question": "What is a lambda function?", "options": ["Anonymous function", "Built-in function", "Recursive function", "Generator function"], "correct": "Anonymous function", "explanation": "Lambda functions are small anonymous functions defined using the 'lambda' keyword."}
    ],
    'JavaScript': [
        {"question": "How do you declare a variable in JavaScript?", "options": ["let x;", "variable x;", "v x;", "declare x;"], "correct": "let x;", "explanation": "let, const, and var are the three ways to declare variables in JavaScript."},
        {"question": "What does 'console.log()' do?", "options": ["Prints to console", "Shows an alert", "Returns a value", "Creates a log file"], "correct": "Prints to console", "explanation": "console.log() outputs messages to the browser's developer console."},
        {"question": "What is the correct way to write a function in JavaScript?", "options": ["function myFunction() {}", "def myFunction() {}", "create myFunction() {}", "func myFunction() {}"], "correct": "function myFunction() {}", "explanation": "Functions are defined using the 'function' keyword followed by the function name and parentheses."},
        {"question": "What does '===' operator do?", "options": ["Compares value and type", "Compares only value", "Compares only type", "Assigns value"], "correct": "Compares value and type", "explanation": "=== is the strict equality operator that checks both value and type without type coercion."},
        {"question": "What is closure in JavaScript?", "options": ["Function with access to outer scope", "Closed function", "Private variable", "Global variable"], "correct": "Function with access to outer scope", "explanation": "A closure is a function that has access to its outer function's scope even after the outer function has returned."},
        {"question": "What is hoisting?", "options": ["Moving declarations to top", "Moving values to top", "Moving functions to bottom", "Moving variables to bottom"], "correct": "Moving declarations to top", "explanation": "Hoisting is JavaScript's behavior of moving variable and function declarations to the top of their scope."},
        {"question": "What is the event loop?", "options": ["Handles async operations", "Event handler", "Loop counter", "Timer function"], "correct": "Handles async operations", "explanation": "The event loop handles asynchronous callbacks and manages the execution queue in JavaScript."},
        {"question": "What is a promise?", "options": ["Async operation result", "Function declaration", "Variable type", "Loop structure"], "correct": "Async operation result", "explanation": "A Promise represents the eventual completion (or failure) of an asynchronous operation."}
    ],
    'SQL': [
        {"question": "What does SQL stand for?", "options": ["Structured Query Language", "Simple Query Language", "Standard Query Language", "System Query Language"], "correct": "Structured Query Language", "explanation": "SQL stands for Structured Query Language, used to communicate with databases."},
        {"question": "Which SQL statement is used to extract data from a database?", "options": ["SELECT", "EXTRACT", "GET", "OPEN"], "correct": "SELECT", "explanation": "The SELECT statement is used to retrieve data from one or more database tables."},
        {"question": "What does the WHERE clause do?", "options": ["Filters records", "Sorts records", "Groups records", "Joins tables"], "correct": "Filters records", "explanation": "The WHERE clause filters records based on specified conditions."},
        {"question": "Which SQL statement is used to update data?", "options": ["UPDATE", "MODIFY", "CHANGE", "ALTER"], "correct": "UPDATE", "explanation": "The UPDATE statement is used to modify existing records in a table."},
        {"question": "Which SQL statement is used to delete data?", "options": ["DELETE", "REMOVE", "DROP", "TRUNCATE"], "correct": "DELETE", "explanation": "The DELETE statement is used to remove rows from a table."},
        {"question": "What is a primary key?", "options": ["Unique identifier for a record", "Foreign key reference", "Index field", "Default value"], "correct": "Unique identifier for a record", "explanation": "A primary key uniquely identifies each record in a database table."}
    ],
    'Data Science': [
        {"question": "What is the difference between supervised and unsupervised learning?", "options": ["Labeled vs Unlabeled data", "Fast vs Slow", "New vs Old", "Big vs Small"], "correct": "Labeled vs Unlabeled data", "explanation": "Supervised learning uses labeled data with known outputs, while unsupervised learning finds patterns in unlabeled data."},
        {"question": "What is overfitting?", "options": ["Model too complex", "Model too simple", "Model just right", "No model"], "correct": "Model too complex", "explanation": "Overfitting occurs when a model learns the training data too well, including noise, and fails to generalize."},
        {"question": "What is cross-validation?", "options": ["Validating on different data", "Validating on same data", "No validation", "Random validation"], "correct": "Validating on different data", "explanation": "Cross-validation is a technique for evaluating model performance by splitting data into multiple training and validation sets."},
        {"question": "What is the bias-variance tradeoff?", "options": ["Balance between underfitting and overfitting", "Model speed vs accuracy", "Data size vs quality", "Training time vs performance"], "correct": "Balance between underfitting and overfitting", "explanation": "The bias-variance tradeoff balances model simplicity (bias) and complexity (variance) to avoid underfitting or overfitting."},
        {"question": "What evaluation metrics for classification?", "options": ["Accuracy, Precision, Recall", "MSE, RMSE", "R-squared, Adjusted R-squared", "All of the above"], "correct": "Accuracy, Precision, Recall", "explanation": "Common classification metrics include accuracy, precision, recall, F1-score, and AUC-ROC."}
    ]
}

# ============ RESUME PARSER FUNCTIONS ============
def extract_text_from_pdf(filepath):
    try:
        with open(filepath, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
            return text
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return ""

def analyze_resume_content(text):
    text_lower = text.lower()
    
    # Role matching with more comprehensive keywords
    role_keywords = {
        'Python Developer': ['python', 'django', 'flask', 'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'fastapi', 'celery', 'sqlalchemy'],
        'JavaScript Developer': ['javascript', 'react', 'angular', 'vue', 'node.js', 'express', 'typescript', 'jquery', 'redux', 'next.js', 'webpack'],
        'Data Scientist': ['data science', 'machine learning', 'python', 'analytics', 'statistics', 'pandas', 'scikit-learn', 'tensorflow', 'deep learning', 'nlp'],
        'Full Stack Developer': ['react', 'angular', 'node.js', 'express', 'mongodb', 'postgresql', 'html', 'css', 'javascript', 'rest api', 'graphql'],
        'DevOps Engineer': ['docker', 'kubernetes', 'jenkins', 'aws', 'azure', 'gcp', 'terraform', 'ansible', 'ci/cd', 'linux', 'bash', 'prometheus'],
        'Java Developer': ['java', 'spring', 'spring boot', 'hibernate', 'maven', 'gradle', 'junit', 'microservices', 'jpa', 'thymeleaf', 'j2ee'],
        'Cloud Engineer': ['aws', 'azure', 'gcp', 'cloud', 'terraform', 'cloudformation', 'serverless', 'lambda', 'ec2', 's3', 'vpc', 'cloudfront'],
        'Frontend Developer': ['react', 'angular', 'vue', 'html5', 'css3', 'javascript', 'typescript', 'webpack', 'bootstrap', 'tailwind', 'sass', 'less'],
        'Backend Developer': ['python', 'java', 'node.js', 'go', 'ruby', 'php', 'rest api', 'microservices', 'sql', 'nosql', 'graphql', 'redis'],
        'Machine Learning Engineer': ['machine learning', 'deep learning', 'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'nlp', 'computer vision', 'llm']
    }
    
    # Score each role
    role_scores = {}
    role_matched = {}
    for role, keywords in role_keywords.items():
        score = 0
        matched = []
        for keyword in keywords:
            if keyword in text_lower:
                score += 15
                matched.append(keyword)
        role_scores[role] = min(score, 100)
        role_matched[role] = matched
    
    # Get best match
    best_role = max(role_scores, key=role_scores.get) if role_scores else "Python Developer"
    best_score = role_scores.get(best_role, 50)
    
    # Get other suggestions (all roles with >30% match)
    suggested_roles = []
    for role, score in sorted(role_scores.items(), key=lambda x: x[1], reverse=True):
        if score >= 30 and role != best_role:
            suggested_roles.append({
                'role': role,
                'match_percentage': score,
                'matched_skills': role_matched.get(role, [])[:5]
            })
    
    # Generate strengths
    strengths = []
    if len(text) > 500:
        strengths.append("✅ Resume has good length and detailed information")
    if len(text) > 1000:
        strengths.append("✅ Comprehensive resume with extensive details")
    if '@' in text:
        strengths.append("✅ Contact information properly included")
    if 'github' in text_lower or 'linkedin' in text_lower:
        strengths.append("✅ Professional portfolio links included")
    if best_score >= 70:
        strengths.append(f"✅ Strong keyword match for {best_role} role")
    if len(text.split()) > 300:
        strengths.append("✅ Excellent word count with substantial content")
    
    # Generate improvements
    improvements = []
    if len(text) < 300:
        improvements.append("📈 Add more details about your experience and skills")
    if best_score < 50:
        improvements.append(f"📈 Add more {best_role}-specific keywords to your resume")
    if 'github' not in text_lower and 'portfolio' not in text_lower:
        improvements.append("📈 Include links to your GitHub or portfolio website")
    if 'achievement' not in text_lower and 'accomplishment' not in text_lower:
        improvements.append("📈 Quantify your achievements with numbers and metrics")
    if 'certification' not in text_lower:
        improvements.append("📈 Consider adding relevant certifications")
    
    if not strengths:
        strengths = ["✅ Resume uploaded successfully"]
    if not improvements:
        improvements = ["📈 Consider adding more quantifiable achievements"]
    
    return {
        'overall_score': best_score,
        'best_role': best_role,
        'suggested_roles': suggested_roles[:5],  # Top 5 suggestions
        'strengths': strengths,
        'improvements': improvements,
        'skills_found': list(set([kw for keywords in role_keywords.values() for kw in keywords if kw in text_lower]))[:12],
        'word_count': len(text.split())
    }

# ============ ANSWER EVALUATION FUNCTION ============
def evaluate_answer(question_text, user_answer, job_role):
    user_answer_lower = user_answer.lower()
    
    # Find the question in database
    question_data = None
    for q in INTERVIEW_QUESTIONS_WITH_ANSWERS.get(job_role, []):
        if q["question"] == question_text:
            question_data = q
            break
    
    if not question_data:
        word_count = len(user_answer.split())
        if word_count > 80:
            return 75, "Good answer length! Try to include more technical keywords specific to the role."
        elif word_count > 40:
            return 55, "Fair answer. Add more specific technical details related to the question."
        else:
            return 35, "Answer is too brief. Please provide more detailed response with technical concepts."
    
    # Evaluate based on keywords
    keywords = question_data["keywords"]
    matched_keywords = [kw for kw in keywords if kw.lower() in user_answer_lower]
    matched_count = len(matched_keywords)
    score = int((matched_count / len(keywords)) * 100)
    
    # Adjust score based on answer length
    word_count = len(user_answer.split())
    if word_count < 15:
        score = max(20, score - 25)
    elif word_count > 120:
        score = min(95, score + 10)
    elif word_count > 60:
        score = min(95, score + 5)
    
    # Generate detailed feedback
    if score >= 85:
        feedback = f"🌟 Excellent answer! You covered all key points including: {', '.join(matched_keywords[:3])}. Perfect understanding!"
    elif score >= 70:
        missing = [kw for kw in keywords if kw.lower() not in user_answer_lower][:2]
        feedback = f"👍 Good answer! You mentioned {', '.join(matched_keywords[:2])}. Consider also discussing: {', '.join(missing)}"
    elif score >= 50:
        missing = [kw for kw in keywords if kw.lower() not in user_answer_lower][:3]
        feedback = f"📝 Fair answer. You touched on {', '.join(matched_keywords[:2])}. The interview expects you to also cover: {', '.join(missing)}"
    else:
        feedback = f"⚠️ Answer needs improvement. The question expects discussion of: {', '.join(keywords[:4])}. Please review these concepts."
    
    return score, feedback

# ============ ROUTES ============
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        if len(password) < 4:
            flash('Password must be at least 4 characters', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return render_template('register.html')
        
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password_hash=hashed)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    total_interviews = Interview.query.filter_by(user_id=current_user.id).count()
    avg_score = db.session.query(db.func.avg(Interview.score)).filter_by(user_id=current_user.id).scalar() or 0
    quiz_count = QuizResult.query.filter_by(user_id=current_user.id).count()
    avg_quiz_score = db.session.query(db.func.avg(QuizResult.score)).filter_by(user_id=current_user.id).scalar() or 0
    latest_resume = ResumeAnalysis.query.filter_by(user_id=current_user.id).order_by(ResumeAnalysis.date.desc()).first()
    recent_interviews = Interview.query.filter_by(user_id=current_user.id).order_by(Interview.date.desc()).limit(5).all()
    
    return render_template('dashboard.html',
                         total_interviews=total_interviews,
                         avg_score=round(avg_score, 1),
                         quiz_count=quiz_count,
                         avg_quiz_score=round(avg_quiz_score, 1),
                         resume_score=latest_resume.score if latest_resume else 0,
                         recent_interviews=recent_interviews)

# ============ MOCK INTERVIEW ROUTES ============
@app.route('/mock-interview')
@login_required
def mock_interview():
    roles = list(INTERVIEW_QUESTIONS_WITH_ANSWERS.keys())
    return render_template('mock_interview.html', roles=roles)

@app.route('/start-mock-interview', methods=['POST'])
@login_required
def start_mock_interview():
    role = request.form.get('role')
    if not role:
        flash('Please select a role', 'danger')
        return redirect(url_for('mock_interview'))
    
    questions = [q["question"] for q in INTERVIEW_QUESTIONS_WITH_ANSWERS.get(role, [])]
    random.shuffle(questions)
    
    session['interview_role'] = role
    session['interview_questions'] = questions[:7]  # 7 questions per interview
    session['interview_answers'] = []
    session['interview_scores'] = []
    session['interview_feedbacks'] = []
    session['interview_current'] = 0
    
    return redirect(url_for('take_mock_interview'))

@app.route('/take-mock-interview')
@login_required
def take_mock_interview():
    if 'interview_questions' not in session:
        return redirect(url_for('mock_interview'))
    
    questions = session.get('interview_questions', [])
    current = session.get('interview_current', 0)
    
    if current >= len(questions):
        return redirect(url_for('interview_results'))
    
    return render_template('take_mock_interview.html',
                         question=questions[current],
                         question_num=current + 1,
                         total=len(questions),
                         role=session.get('interview_role', 'Unknown'))

@app.route('/submit-mock-answer', methods=['POST'])
@login_required
def submit_mock_answer():
    answer = request.form.get('answer')
    question = request.form.get('question')
    role = session.get('interview_role', '')
    
    # Evaluate answer
    score, feedback = evaluate_answer(question, answer, role)
    
    session['interview_answers'].append({'question': question, 'answer': answer, 'score': score})
    session['interview_scores'].append(score)
    session['interview_feedbacks'].append(feedback)
    session['interview_current'] = session.get('interview_current', 0) + 1
    session.modified = True
    
    questions = session.get('interview_questions', [])
    current_idx = session.get('interview_current', 0)
    
    if current_idx >= len(questions):
        # Save to database
        for i, item in enumerate(session['interview_answers']):
            interview = Interview(
                user_id=current_user.id,
                job_role=role,
                question=item['question'],
                answer=item['answer'][:1000],
                score=item['score'],
                feedback=session['interview_feedbacks'][i]
            )
            db.session.add(interview)
        db.session.commit()
        
        total_score = sum(session['interview_scores']) / len(session['interview_scores'])
        
        # Clear session
        session.pop('interview_questions', None)
        session.pop('interview_answers', None)
        session.pop('interview_scores', None)
        session.pop('interview_feedbacks', None)
        session.pop('interview_current', None)
        session.pop('interview_role', None)
        
        return jsonify({'completed': True, 'total_score': round(total_score, 1)})
    
    return jsonify({
        'completed': False,
        'next_question': questions[current_idx],
        'question_num': current_idx + 1,
        'total': len(questions),
        'score': score,
        'feedback': feedback
    })

@app.route('/interview-results')
@login_required
def interview_results():
    return render_template('interview_results.html')

# ============ RESUME ANALYSIS ROUTES ============
@app.route('/resume-analysis', methods=['GET', 'POST'])
@login_required
def resume_analysis():
    if request.method == 'POST':
        if 'resume' not in request.files:
            flash('No file uploaded', 'danger')
            return redirect(url_for('resume_analysis'))
        
        file = request.files['resume']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(url_for('resume_analysis'))
        
        if not file.filename.endswith('.pdf'):
            flash('Please upload a PDF file', 'danger')
            return redirect(url_for('resume_analysis'))
        
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Extract text from PDF
            extracted_text = extract_text_from_pdf(filepath)
            
            if not extracted_text or len(extracted_text.strip()) < 50:
                flash('Could not extract text from PDF. Please ensure it\'s a valid text-based PDF.', 'danger')
                os.remove(filepath)
                return redirect(url_for('resume_analysis'))
            
            # Analyze resume
            analysis = analyze_resume_content(extracted_text)
            
            # Save to database
            resume_record = ResumeAnalysis(
                user_id=current_user.id,
                filename=filename,
                extracted_text=extracted_text[:2000],
                score=analysis['overall_score'],
                suggested_role=analysis['best_role'],
                suggested_roles=json.dumps(analysis['suggested_roles']),
                strengths=json.dumps(analysis['strengths']),
                improvements=json.dumps(analysis['improvements']),
                skills_found=json.dumps(analysis['skills_found'])
            )
            db.session.add(resume_record)
            db.session.commit()
            
            flash(f'✅ Resume analyzed successfully! Best match: {analysis["best_role"]}', 'success')
            
            return render_template('resume_results.html', analysis=analysis)
            
        except Exception as e:
            print(f"Resume analysis error: {str(e)}")
            flash('Error analyzing resume. Please try again.', 'danger')
            return redirect(url_for('resume_analysis'))
    
    return render_template('resume_analysis.html')

# ============ HELPER ROUTES ============
@app.route('/start-mock-interview-direct', methods=['POST'])
@login_required
def start_mock_interview_direct():
    role = request.form.get('role')
    if not role:
        flash('No role specified', 'danger')
        return redirect(url_for('resume_analysis'))
    
    questions = [q["question"] for q in INTERVIEW_QUESTIONS_WITH_ANSWERS.get(role, [])]
    random.shuffle(questions)
    
    session['interview_role'] = role
    session['interview_questions'] = questions[:7]
    session['interview_answers'] = []
    session['interview_scores'] = []
    session['interview_feedbacks'] = []
    session['interview_current'] = 0
    
    return redirect(url_for('take_mock_interview'))

@app.route('/start-quiz-direct', methods=['POST'])
@login_required
def start_quiz_direct():
    category = request.form.get('category')
    if not category:
        flash('No category specified', 'danger')
        return redirect(url_for('resume_analysis'))
    
    # Check if it's a role from interview (has questions) or a quiz category
    if category in QUIZ_QUESTIONS:
        all_questions = QUIZ_QUESTIONS[category]
    else:
        # Try to map to a quiz category
        mapped_category = None
        for quiz_cat in QUIZ_QUESTIONS.keys():
            if quiz_cat.lower() in category.lower() or category.lower() in quiz_cat.lower():
                mapped_category = quiz_cat
                break
        if mapped_category:
            all_questions = QUIZ_QUESTIONS[mapped_category]
        else:
            all_questions = QUIZ_QUESTIONS['Python']
    
    if not all_questions:
        flash('No questions available', 'danger')
        return redirect(url_for('skill_quiz'))
    
    # Get 15 random questions
    num_questions = min(15, len(all_questions))
    selected_questions = random.sample(all_questions, num_questions)
    
    session['quiz_category'] = category
    session['quiz_questions'] = selected_questions
    session['quiz_answers'] = []
    session['quiz_current'] = 0
    
    return redirect(url_for('take_quiz'))

# ============ QUIZ ROUTES ============
@app.route('/skill-quiz')
@login_required
def skill_quiz():
    categories = list(QUIZ_QUESTIONS.keys())
    return render_template('skill_quiz.html', categories=categories)

@app.route('/start-quiz', methods=['POST'])
@login_required
def start_quiz():
    category = request.form.get('category')
    all_questions = QUIZ_QUESTIONS.get(category, [])
    
    if not all_questions:
        flash('No questions available', 'danger')
        return redirect(url_for('skill_quiz'))
    
    # Get 15 random questions
    num_questions = min(15, len(all_questions))
    selected_questions = random.sample(all_questions, num_questions)
    
    session['quiz_category'] = category
    session['quiz_questions'] = selected_questions
    session['quiz_answers'] = []
    session['quiz_current'] = 0
    
    return redirect(url_for('take_quiz'))

@app.route('/take-quiz')
@login_required
def take_quiz():
    if 'quiz_questions' not in session:
        return redirect(url_for('skill_quiz'))
    
    questions = session['quiz_questions']
    current = session.get('quiz_current', 0)
    
    if current >= len(questions):
        return redirect(url_for('quiz_results'))
    
    return render_template('take_quiz.html',
                         question=questions[current],
                         question_num=current + 1,
                         total=len(questions),
                         category=session['quiz_category'])

@app.route('/submit-quiz-answer', methods=['POST'])
@login_required
def submit_quiz_answer():
    data = request.json
    user_answer = data.get('answer')
    correct_answer = data.get('correct')
    question_text = data.get('question')
    explanation = data.get('explanation', '')
    
    is_correct = (user_answer == correct_answer)
    
    # Find the full question object to get explanation
    for q in session.get('quiz_questions', []):
        if q['question'] == question_text:
            explanation = q.get('explanation', explanation)
            break
    
    session['quiz_answers'].append({
        'question': question_text,
        'user_answer': user_answer,
        'correct_answer': correct_answer,
        'is_correct': is_correct,
        'explanation': explanation
    })
    session['quiz_current'] = session.get('quiz_current', 0) + 1
    session.modified = True
    
    questions = session['quiz_questions']
    current_idx = session['quiz_current']
    
    if current_idx >= len(questions):
        correct_count = sum(1 for a in session['quiz_answers'] if a['is_correct'])
        score = int((correct_count / len(questions)) * 100)
        
        # Save to database
        quiz_result = QuizResult(
            user_id=current_user.id,
            category=session['quiz_category'],
            difficulty='intermediate',
            score=score,
            total_questions=len(questions),
            correct_answers=correct_count
        )
        db.session.add(quiz_result)
        db.session.commit()
        
        # Prepare results data
        results = {
            'completed': True,
            'score': score,
            'correct': correct_count,
            'total': len(questions),
            'answers': session['quiz_answers']
        }
        
        # Store results in session for results page
        session['quiz_results'] = results
        
        session.pop('quiz_questions', None)
        session.pop('quiz_answers', None)
        session.pop('quiz_current', None)
        
        return jsonify(results)
    
    next_question = questions[current_idx]
    return jsonify({
        'completed': False,
        'next_question': next_question,
        'question_num': current_idx + 1,
        'total': len(questions)
    })

@app.route('/quiz-results')
@login_required
def quiz_results():
    results = session.get('quiz_results', None)
    if not results:
        return redirect(url_for('skill_quiz'))
    
    # Clear results from session after displaying
    session.pop('quiz_results', None)
    
    return render_template('quiz_results.html', results=results)

@app.route('/performance')
@login_required
def performance():
    interviews = Interview.query.filter_by(user_id=current_user.id).order_by(Interview.date).all()
    quizzes = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.date).all()
    
    interview_dates = [i.date.strftime('%Y-%m-%d') for i in interviews]
    interview_scores = [i.score for i in interviews]
    
    return render_template('performance.html',
                         interviews=interviews,
                         quizzes=quizzes,
                         interview_dates=json.dumps(interview_dates),
                         interview_scores=json.dumps(interview_scores))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
