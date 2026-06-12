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
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

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
    score = db.Column(db.Integer)
    total_questions = db.Column(db.Integer)
    correct_answers = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Enhanced Interview Questions (More roles and questions)
INTERVIEW_QUESTIONS = {
    'Python Developer': [
        {"question": "What is the difference between a list and a tuple?", "keywords": ["mutable", "immutable", "change", "modify"]},
        {"question": "What is a decorator in Python?", "keywords": ["function", "modify", "wrapper", "@"]},
        {"question": "Explain the Global Interpreter Lock (GIL).", "keywords": ["thread", "execution", "mutex", "concurrency"]},
        {"question": "What are list comprehensions?", "keywords": ["syntax", "loop", "expression", "list"]},
        {"question": "Explain the difference between deep and shallow copy.", "keywords": ["nested", "reference", "recursive", "copy"]},
    ],
    'JavaScript Developer': [
        {"question": "What is closure in JavaScript?", "keywords": ["inner function", "outer scope", "variables", "return"]},
        {"question": "Difference between == and ===?", "keywords": ["value", "type", "strict", "coercion"]},
        {"question": "What is hoisting?", "keywords": ["declaration", "move", "top", "var", "function"]},
        {"question": "Explain event delegation.", "keywords": ["bubbling", "parent", "child", "listener"]},
        {"question": "What is the difference between let, const, and var?", "keywords": ["scope", "block", "reassign", "temporal"]},
    ],
    'Data Scientist': [
        {"question": "Difference between supervised and unsupervised learning?", "keywords": ["labeled", "unlabeled", "output", "target"]},
        {"question": "What is overfitting?", "keywords": ["training", "noise", "generalization", "variance"]},
        {"question": "Explain bias-variance tradeoff.", "keywords": ["error", "complexity", "balance", "underfitting"]},
        {"question": "What is cross-validation?", "keywords": ["fold", "holdout", "validation", "testing"]},
        {"question": "Explain the difference between bagging and boosting.", "keywords": ["ensemble", "sequential", "parallel", "weight"]},
    ],
    'Full Stack Developer': [
        {"question": "What is REST API?", "keywords": ["representational", "state", "http", "endpoint"]},
        {"question": "Difference between SQL and NoSQL?", "keywords": ["structured", "schema", "scalability", "document"]},
        {"question": "Explain CORS.", "keywords": ["cross-origin", "resource", "sharing", "headers"]},
        {"question": "What is JWT?", "keywords": ["json", "token", "authentication", "claim"]},
        {"question": "Explain MVC architecture.", "keywords": ["model", "view", "controller", "pattern"]},
    ],
    'DevOps Engineer': [
        {"question": "What is Docker?", "keywords": ["container", "image", "isolate", "orchestration"]},
        {"question": "Explain CI/CD.", "keywords": ["continuous", "integration", "automation", "delivery"]},
        {"question": "What is Kubernetes?", "keywords": ["container", "orchestration", "pod", "cluster"]},
        {"question": "Explain Infrastructure as Code.", "keywords": ["terraform", "cloudformation", "automation", "version"]},
        {"question": "What is the difference between continuous delivery and deployment?", "keywords": ["automated", "manual", "release", "production"]},
    ],
    'Java Developer': [
        {"question": "Difference between abstract class and interface?", "keywords": ["implementation", "multiple", "inheritance", "abstract"]},
        {"question": "What is multithreading?", "keywords": ["concurrent", "threads", "parallel", "runnable"]},
        {"question": "Explain garbage collection.", "keywords": ["memory", "heap", "collector", "gc"]},
        {"question": "What is polymorphism?", "keywords": ["many", "forms", "override", "overload"]},
        {"question": "Explain the difference between ArrayList and LinkedList.", "keywords": ["array", "node", "index", "performance"]},
    ],
    'Cloud Engineer': [
        {"question": "What are cloud service models?", "keywords": ["iaas", "paas", "saas", "serverless"]},
        {"question": "Explain serverless computing.", "keywords": ["functions", "event-driven", "scale", "lambda"]},
        {"question": "What is the difference between scalability and elasticity?", "keywords": ["capacity", "automated", "demand", "resources"]},
        {"question": "Explain load balancer.", "keywords": ["traffic", "distribute", "server", "health"]},
        {"question": "What is a CDN?", "keywords": ["content", "delivery", "network", "cache"]},
    ],
    'Machine Learning Engineer': [
        {"question": "Explain AI vs ML vs DL.", "keywords": ["artificial", "intelligence", "deep", "learning"]},
        {"question": "What is transfer learning?", "keywords": ["pretrained", "fine-tune", "adapt", "weights"]},
        {"question": "Explain gradient descent.", "keywords": ["optimization", "minimize", "loss", "function"]},
        {"question": "What is regularization?", "keywords": ["overfitting", "penalty", "lasso", "ridge"]},
        {"question": "Explain the difference between precision and recall.", "keywords": ["accuracy", "false", "positive", "negative"]},
    ],
    'Frontend Developer': [
        {"question": "What is the DOM?", "keywords": ["document", "object", "model", "tree"]},
        {"question": "Explain flexbox.", "keywords": ["layout", "flexible", "container", "items"]},
        {"question": "What is responsive design?", "keywords": ["mobile", "screen", "viewport", "media"]},
        {"question": "Explain CSS specificity.", "keywords": ["id", "class", "element", "inline"]},
        {"question": "What is a virtual DOM?", "keywords": ["react", "render", "performance", "update"]},
    ],
    'Backend Developer': [
        {"question": "What is API rate limiting?", "keywords": ["throttle", "request", "limit", "429"]},
        {"question": "Explain database indexing.", "keywords": ["performance", "search", "b-tree", "optimize"]},
        {"question": "What is message queue?", "keywords": ["rabbitmq", "kafka", "async", "broker"]},
        {"question": "Explain ACID properties.", "keywords": ["atomicity", "consistency", "isolation", "durability"]},
        {"question": "What is a microservice?", "keywords": ["architecture", "independent", "deploy", "scalable"]},
    ],
    'Cybersecurity Analyst': [
        {"question": "What is a DDoS attack?", "keywords": ["distributed", "denial", "service", "traffic"]},
        {"question": "Explain encryption vs hashing.", "keywords": ["reversible", "one-way", "key", "salt"]},
        {"question": "What is XSS?", "keywords": ["cross-site", "scripting", "injection", "browser"]},
        {"question": "Explain SQL injection.", "keywords": ["query", "parameter", "sanitize", "prepared"]},
        {"question": "What is a firewall?", "keywords": ["network", "security", "filter", "traffic"]},
    ],
    'Product Manager': [
        {"question": "What is Agile methodology?", "keywords": ["sprint", "scrum", "iterative", "backlog"]},
        {"question": "Explain MVP.", "keywords": ["minimum", "viable", "product", "features"]},
        {"question": "What is a user story?", "keywords": ["feature", "requirement", "agile", "customer"]},
        {"question": "Explain KPI.", "keywords": ["performance", "metric", "measure", "goal"]},
        {"question": "What is market research?", "keywords": ["customer", "competition", "demand", "analysis"]},
    ],
    'UI/UX Designer': [
        {"question": "What is the difference between UI and UX?", "keywords": ["user", "interface", "experience", "design"]},
        {"question": "Explain design thinking.", "keywords": ["empathize", "define", "ideate", "prototype"]},
        {"question": "What is a wireframe?", "keywords": ["layout", "structure", "blueprint", "low-fidelity"]},
        {"question": "Explain usability testing.", "keywords": ["user", "feedback", "task", "observation"]},
        {"question": "What is a design system?", "keywords": ["component", "guideline", "consistency", "library"]},
    ],
}

# Enhanced Quiz Questions
QUIZ_QUESTIONS = {
    'Python': [
        {"question": "What is the correct way to create a function?", "options": ["def myFunc():", "function myFunc():", "create myFunc():", "func myFunc():"], "correct": "def myFunc():", "explanation": "def keyword is used to define functions in Python"},
        {"question": "What does len() function do?", "options": ["Returns length", "Converts to string", "Finds maximum", "Rounds number"], "correct": "Returns length", "explanation": "len() returns the number of items in an object"},
        {"question": "Which operator is used for exponentiation?", "options": ["**", "^", "exp()", "&&"], "correct": "**", "explanation": "** is the exponentiation operator (e.g., 2**3 = 8)"},
        {"question": "What is the output of print(type(10))?", "options": ["<class 'int'>", "<class 'float'>", "<class 'str'>", "<class 'list'>"], "correct": "<class 'int'>", "explanation": "10 is an integer, so type() returns int"},
        {"question": "How do you create a list?", "options": ["[1, 2, 3]", "(1, 2, 3)", "{1, 2, 3}", "<1, 2, 3>"], "correct": "[1, 2, 3]", "explanation": "Square brackets [] are used to create lists"},
        {"question": "What is the correct while loop syntax?", "options": ["while x > y:", "while (x > y)", "x > y while {", "while x > y then:"], "correct": "while x > y:", "explanation": "A colon is required after the while condition"},
        {"question": "What does append() do?", "options": ["Adds to end", "Removes item", "Inserts at start", "Sorts list"], "correct": "Adds to end", "explanation": "append() adds an element to the end of a list"},
        {"question": "What is 10 // 3?", "options": ["3", "3.33", "3.0", "1"], "correct": "3", "explanation": "// is floor division - it returns the integer part of division"},
        {"question": "What is the output of print('Hello'[1])?", "options": ["e", "H", "l", "o"], "correct": "e", "explanation": "String indexing starts at 0, so index 1 gives the second character 'e'"},
        {"question": "Which keyword is used for exception handling?", "options": ["try", "catch", "except", "both try and except"], "correct": "both try and except", "explanation": "try-except blocks are used for exception handling in Python"},
    ],
    'JavaScript': [
        {"question": "How to declare a variable in JavaScript?", "options": ["let x;", "variable x;", "v x;", "declare x;"], "correct": "let x;", "explanation": "let, const, and var are used to declare variables"},
        {"question": "What does console.log() do?", "options": ["Prints to console", "Shows alert", "Returns value", "Creates file"], "correct": "Prints to console", "explanation": "Outputs a message to the web console"},
        {"question": "How to write a function in JavaScript?", "options": ["function myFunc() {}", "def myFunc() {}", "create myFunc() {}", "func myFunc() {}"], "correct": "function myFunc() {}", "explanation": "function keyword defines functions in JavaScript"},
        {"question": "What does === do?", "options": ["Compares value and type", "Compares only value", "Compares only type", "Assigns value"], "correct": "Compares value and type", "explanation": "=== is the strict equality operator"},
        {"question": "What is an array in JavaScript?", "options": ["Data structure", "Function", "Loop", "Condition"], "correct": "Data structure", "explanation": "Arrays are data structures that store multiple values"},
        {"question": "How do you add a comment in JavaScript?", "options": ["// This is a comment", "<!-- This is a comment -->", "# This is a comment", "/* This is a comment"], "correct": "// This is a comment", "explanation": "// is used for single-line comments"},
    ],
    'SQL': [
        {"question": "What does SQL stand for?", "options": ["Structured Query Language", "Simple Query Language", "Standard Query Language", "System Query Language"], "correct": "Structured Query Language", "explanation": "SQL stands for Structured Query Language"},
        {"question": "Which statement is used to extract data?", "options": ["SELECT", "EXTRACT", "GET", "OPEN"], "correct": "SELECT", "explanation": "SELECT is used to retrieve data from databases"},
        {"question": "What does WHERE clause do?", "options": ["Filters records", "Sorts records", "Groups records", "Joins tables"], "correct": "Filters records", "explanation": "WHERE filters records based on specified conditions"},
        {"question": "What is a primary key?", "options": ["Unique identifier", "Foreign reference", "Index", "Constraint"], "correct": "Unique identifier", "explanation": "A primary key uniquely identifies each record in a table"},
        {"question": "What does JOIN do?", "options": ["Combines tables", "Separates tables", "Deletes tables", "Creates tables"], "correct": "Combines tables", "explanation": "JOIN combines rows from two or more tables"},
        {"question": "What is the difference between DELETE and TRUNCATE?", "options": ["DELETE can have WHERE, TRUNCATE cannot", "TRUNCATE can have WHERE, DELETE cannot", "Both are same", "DELETE is faster"], "correct": "DELETE can have WHERE, TRUNCATE cannot", "explanation": "DELETE can filter rows with WHERE; TRUNCATE removes all rows"},
    ],
    'Data Science': [
        {"question": "What is supervised learning?", "options": ["Learning with labeled data", "Learning with unlabeled data", "Learning with rewards", "Learning without data"], "correct": "Learning with labeled data", "explanation": "Supervised learning uses labeled input-output pairs"},
        {"question": "What is overfitting?", "options": ["Model too complex", "Model too simple", "Model perfect", "Model missing data"], "correct": "Model too complex", "explanation": "Overfitting occurs when a model learns noise in the training data"},
        {"question": "What is cross-validation?", "options": ["Validating on different data subsets", "Using same data", "No validation", "Random guessing"], "correct": "Validating on different data subsets", "explanation": "Cross-validation tests model generalization on unseen data"},
        {"question": "What is the purpose of train-test split?", "options": ["Evaluate model performance", "Increase data", "Decrease computation", "Remove outliers"], "correct": "Evaluate model performance", "explanation": "Train-test split helps evaluate how well the model generalizes"},
        {"question": "What is dimensionality reduction?", "options": ["Reducing number of features", "Reducing data size", "Reducing model complexity", "All of the above"], "correct": "Reducing number of features", "explanation": "Dimensionality reduction decreases the number of input variables"},
    ],
    'General Knowledge': [
        {"question": "What does RAM stand for?", "options": ["Random Access Memory", "Readily Available Memory", "Rapid Access Module", "Random Allocation Memory"], "correct": "Random Access Memory", "explanation": "RAM is computer memory that can be accessed randomly"},
        {"question": "What does CPU stand for?", "options": ["Central Processing Unit", "Computer Personal Unit", "Central Program Utility", "Core Processing Utility"], "correct": "Central Processing Unit", "explanation": "CPU is the primary component of a computer"},
        {"question": "What is the cloud in computing?", "options": ["Internet-based computing", "Weather storage", "Sky computing", "Virtual rain"], "correct": "Internet-based computing", "explanation": "Cloud computing delivers services over the internet"},
        {"question": "What is an IP address?", "options": ["Network identifier", "Computer password", "Internet provider", "Software license"], "correct": "Network identifier", "explanation": "IP address identifies devices on a network"},
    ],
}

def extract_text_from_file(filepath):
    """Extract text from PDF and TXT files"""
    text = ""
    try:
        if filepath.endswith('.pdf'):
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        elif filepath.endswith('.txt'):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
    except Exception as e:
        print(f"Extraction error: {e}")
        text = ""
    return text

def analyze_resume(text):
    """Enhanced resume analysis"""
    text_lower = text.lower()
    
    role_keywords = {
        'Python Developer': ['python', 'django', 'flask', 'pandas', 'numpy', 'fastapi', 'requests', 'pytest'],
        'JavaScript Developer': ['javascript', 'react', 'angular', 'vue', 'node', 'express', 'typescript'],
        'Data Scientist': ['data science', 'machine learning', 'python', 'analytics', 'sql', 'statistics', 'pandas'],
        'Full Stack Developer': ['react', 'angular', 'node', 'html', 'css', 'mongodb', 'express', 'api'],
        'DevOps Engineer': ['docker', 'kubernetes', 'jenkins', 'aws', 'ci/cd', 'terraform', 'linux'],
        'Java Developer': ['java', 'spring', 'hibernate', 'maven', 'gradle', 'junit', 'eclipse'],
        'Cloud Engineer': ['aws', 'azure', 'gcp', 'cloud', 'terraform', 'lambda', 'ec2', 's3'],
        'Machine Learning Engineer': ['machine learning', 'deep learning', 'tensorflow', 'keras', 'pytorch', 'nlp'],
        'Frontend Developer': ['react', 'vue', 'angular', 'css', 'html', 'javascript', 'bootstrap', 'tailwind'],
        'Backend Developer': ['node', 'python', 'java', 'api', 'database', 'sql', 'redis', 'microservices'],
        'Cybersecurity Analyst': ['security', 'firewall', 'encryption', 'vulnerability', 'penetration', 'cissp'],
        'Product Manager': ['product', 'agile', 'scrum', 'roadmap', 'user story', 'jira', 'market'],
        'UI/UX Designer': ['ui', 'ux', 'design', 'figma', 'adobe', 'wireframe', 'prototype', 'user research'],
    }
    
    # Calculate scores
    scores = {}
    matched_skills = {}
    for role, keywords in role_keywords.items():
        score = 0
        matched = []
        for kw in keywords:
            count = text_lower.count(kw)
            if count > 0:
                score += min(15, count * 5)
                matched.append(kw)
        scores[role] = min(score, 100)
        matched_skills[role] = matched
    
    # Find best match
    best_role = max(scores, key=scores.get) if scores else "Python Developer"
    best_score = scores.get(best_role, 50)
    
    # Get suitable roles
    suitable_roles = []
    for role, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        if score >= 25 and role != best_role:
            suitable_roles.append({
                'role': role,
                'score': score,
                'skills': matched_skills.get(role, [])[:3]
            })
    
    # Generate feedback
    strengths = []
    improvements = []
    
    # Content analysis
    word_count = len(text.split())
    if word_count > 500:
        strengths.append("✅ Excellent resume length and detail")
    elif word_count > 300:
        strengths.append("✅ Good resume length")
    else:
        improvements.append("📈 Add more details about your experience (aim for 300+ words)")
    
    if '@' in text and any(domain in text for domain in ['.com', '.in', '.org']):
        strengths.append("✅ Professional contact information included")
    else:
        improvements.append("📈 Add professional contact information (email with proper domain)")
    
    if best_score >= 70:
        strengths.append(f"✅ Strong match for {best_role} ({best_score}%)")
    elif best_score >= 50:
        strengths.append(f"✅ Good match for {best_role}")
    else:
        improvements.append(f"📈 Add more {best_role}-related keywords to improve match")
    
    # Skill analysis
    skills_found = set()
    for skills in matched_skills.values():
        skills_found.update(skills)
    
    if len(skills_found) >= 5:
        strengths.append(f"✅ Great technical skills detected ({len(skills_found)}+ skills)")
    elif len(skills_found) >= 3:
        strengths.append(f"✅ Good technical skills found")
    else:
        improvements.append("📈 List more technical skills relevant to your target role")
    
    # Education section check
    education_words = ['bachelor', 'master', 'phd', 'degree', 'university', 'college', 'b.tech', 'm.tech', 'b.e', 'm.e']
    if any(word in text_lower for word in education_words):
        strengths.append("✅ Education information present")
    else:
        improvements.append("📈 Add your educational qualifications")
    
    # Experience section check
    experience_words = ['experience', 'worked', 'intern', 'job', 'position', 'role', 'company']
    if any(word in text_lower for word in experience_words):
        strengths.append("✅ Work experience included")
    else:
        improvements.append("📈 Add work experience or internship details")
    
    if not strengths:
        strengths = ["✅ Resume uploaded successfully - we can help improve it!"]
    if not improvements:
        improvements = ["🎉 Great resume! Consider adding more metrics/achievements"]
    
    # Add a few improvement suggestions by default
    if len(improvements) < 2:
        improvements.append("📈 Add quantifiable achievements (e.g., 'Improved performance by 20%')")
    
    return {
        'best_role': best_role,
        'best_score': best_score,
        'suitable_roles': suitable_roles[:5],
        'strengths': strengths[:5],
        'improvements': improvements[:5],
        'skills': list(skills_found)[:15],
        'word_count': word_count,
        'score_grade': get_score_grade(best_score)
    }

def get_score_grade(score):
    if score >= 80:
        return {'grade': 'A+', 'color': '#10b981', 'text': 'Excellent Match!'}
    elif score >= 65:
        return {'grade': 'B+', 'color': '#3b82f6', 'text': 'Good Match'}
    elif score >= 50:
        return {'grade': 'C', 'color': '#f59e0b', 'text': 'Fair Match'}
    else:
        return {'grade': 'D', 'color': '#ef4444', 'text': 'Needs Improvement'}

def evaluate_answer(question, answer, role):
    """Enhanced answer evaluation"""
    answer_lower = answer.lower().strip()
    
    if len(answer_lower.split()) < 5:
        return 15, "❌ Answer too short (minimum 5 words). Please provide more details."
    
    if len(answer_lower.split()) < 15:
        return 25, "⚠️ Good start! Add more details to strengthen your answer."
    
    for q in INTERVIEW_QUESTIONS.get(role, []):
        if q['question'] == question:
            keywords = q['keywords']
            matched = [kw for kw in keywords if kw in answer_lower]
            
            if not matched:
                return 20, f"❌ Incorrect. Key concepts to mention: {', '.join(keywords[:3])}"
            
            # Calculate score based on keyword matches
            base_score = int((len(matched) / len(keywords)) * 80) + 20
            
            # Bonus for answer length
            word_count = len(answer_lower.split())
            if word_count > 50:
                base_score += 10
            elif word_count > 30:
                base_score += 5
            
            final_score = min(98, base_score)
            
            # Detailed feedback
            missing = [kw for kw in keywords if kw not in answer_lower][:3]
            
            if final_score >= 85:
                feedback = f"✅ Excellent answer! Score: {final_score}% - You covered key concepts well."
            elif final_score >= 70:
                missing_text = f"Consider mentioning: {', '.join(missing)}" if missing else "Great job!"
                feedback = f"👍 Good answer! Score: {final_score}% - {missing_text}"
            elif final_score >= 50:
                feedback = f"📝 Fair answer. Score: {final_score}% - Missing: {', '.join(missing)}"
            else:
                feedback = f"⚠️ Needs improvement. Score: {final_score}% - Expected keywords: {', '.join(keywords[:3])}"
            
            return final_score, feedback
    
    return 50, "Good attempt! Keep practicing to improve your answers."

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        
        if not all([username, email, password]):
            flash('All fields are required', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password_hash=hashed)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    interviews = Interview.query.filter_by(user_id=current_user.id).all()
    quizzes = QuizResult.query.filter_by(user_id=current_user.id).all()
    resumes = ResumeAnalysis.query.filter_by(user_id=current_user.id).all()
    
    total_interviews = len(interviews)
    avg_score = round(sum(i.score for i in interviews) / total_interviews, 1) if total_interviews > 0 else 0
    total_quizzes = len(quizzes)
    avg_quiz = round(sum(q.score for q in quizzes) / total_quizzes, 1) if total_quizzes > 0 else 0
    latest_resume = resumes[-1].score if resumes else 0
    
    # Get recent activities
    recent_interviews = interviews[-5:] if interviews else []
    recent_quizzes = quizzes[-5:] if quizzes else []
    
    return render_template('dashboard.html',
                         total_interviews=total_interviews,
                         avg_score=avg_score,
                         total_quizzes=total_quizzes,
                         avg_quiz=avg_quiz,
                         resume_score=latest_resume,
                         recent_interviews=recent_interviews,
                         recent_quizzes=recent_quizzes)

@app.route('/mock-interview')
@login_required
def mock_interview():
    roles = list(INTERVIEW_QUESTIONS.keys())
    return render_template('mock_interview.html', roles=roles)

@app.route('/start-mock-interview', methods=['POST'])
@login_required
def start_mock_interview():
    role = request.form.get('role')
    if not role:
        flash('Please select a role', 'danger')
        return redirect(url_for('mock_interview'))
    
    questions = [q['question'] for q in INTERVIEW_QUESTIONS.get(role, [])]
    random.shuffle(questions)
    
    session['interview_role'] = role
    session['interview_questions'] = questions[:4]
    session['interview_answers'] = []
    session['interview_scores'] = []
    session['interview_current'] = 0
    
    return redirect(url_for('take_interview'))

@app.route('/take-interview')
@login_required
def take_interview():
    if 'interview_questions' not in session:
        return redirect(url_for('mock_interview'))
    
    questions = session['interview_questions']
    current = session.get('interview_current', 0)
    
    if current >= len(questions):
        return redirect(url_for('interview_complete'))
    
    return render_template('take_interview.html',
                         question=questions[current],
                         num=current + 1,
                         total=len(questions),
                         role=session.get('interview_role'))

@app.route('/submit-answer', methods=['POST'])
@login_required
def submit_answer():
    answer = request.form.get('answer')
    question = request.form.get('question')
    role = session.get('interview_role', '')
    
    score, feedback = evaluate_answer(question, answer, role)
    
    session['interview_answers'].append({'question': question, 'answer': answer})
    session['interview_scores'].append(score)
    session['interview_current'] = session.get('interview_current', 0) + 1
    
    questions = session['interview_questions']
    current = session['interview_current']
    
    if current >= len(questions):
        # Save all answers to database
        for item in session['interview_answers']:
            # Get score for this specific answer
            q_score, q_feedback = evaluate_answer(item['question'], item['answer'], role)
            interview = Interview(
                user_id=current_user.id,
                job_role=role,
                question=item['question'],
                answer=item['answer'][:1000],
                score=q_score,
                feedback=q_feedback
            )
            db.session.add(interview)
        db.session.commit()
        
        total = sum(session['interview_scores']) / len(session['interview_scores'])
        session.clear()
        return jsonify({'completed': True, 'total': round(total, 1)})
    
    return jsonify({
        'completed': False,
        'next': questions[current],
        'num': current + 1,
        'total': len(questions),
        'score': score,
        'feedback': feedback
    })

@app.route('/interview-complete')
@
