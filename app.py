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
import docx2txt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///interview.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

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
    score = db.Column(db.Integer)
    total_questions = db.Column(db.Integer)
    correct_answers = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============ 20+ JOB ROLES FOR MOCK INTERVIEW ============
INTERVIEW_QUESTIONS = {
    'Python Developer': [
        {"question": "What is the difference between a list and a tuple?", "keywords": ["mutable", "immutable", "change"]},
        {"question": "What is a decorator in Python?", "keywords": ["function", "modify", "wrapper"]},
        {"question": "Explain the Global Interpreter Lock (GIL).", "keywords": ["thread", "execution", "mutex"]},
        {"question": "What is list comprehension?", "keywords": ["concise", "create", "list"]},
        {"question": "How does exception handling work?", "keywords": ["try", "except", "finally"]},
        {"question": "What are generators?", "keywords": ["yield", "iterator", "memory"]},
    ],
    'JavaScript Developer': [
        {"question": "What is closure in JavaScript?", "keywords": ["inner function", "outer scope", "variables"]},
        {"question": "Difference between == and ===?", "keywords": ["value", "type", "strict"]},
        {"question": "What is hoisting?", "keywords": ["declaration", "move", "top"]},
        {"question": "What are promises?", "keywords": ["async", "future", "callback"]},
        {"question": "What is the event loop?", "keywords": ["async", "queue", "non-blocking"]},
    ],
    'Data Scientist': [
        {"question": "Difference between supervised and unsupervised learning?", "keywords": ["labeled", "unlabeled", "output"]},
        {"question": "What is overfitting and how to prevent it?", "keywords": ["training", "noise", "regularization"]},
        {"question": "Explain bias-variance tradeoff.", "keywords": ["error", "complexity", "balance"]},
        {"question": "What is cross-validation?", "keywords": ["k-fold", "validation", "split"]},
        {"question": "What evaluation metrics for classification?", "keywords": ["accuracy", "precision", "recall"]},
    ],
    'Full Stack Developer': [
        {"question": "What is REST API?", "keywords": ["representational", "state", "http"]},
        {"question": "Difference between SQL and NoSQL?", "keywords": ["structured", "schema", "scalability"]},
        {"question": "What is JWT authentication?", "keywords": ["json", "token", "stateless"]},
        {"question": "What is CORS?", "keywords": ["cross", "origin", "resource"]},
        {"question": "Explain MVC architecture.", "keywords": ["model", "view", "controller"]},
    ],
    'DevOps Engineer': [
        {"question": "What is Docker?", "keywords": ["container", "image", "isolate"]},
        {"question": "Explain CI/CD pipeline.", "keywords": ["continuous", "integration", "automation"]},
        {"question": "What is Kubernetes?", "keywords": ["orchestration", "cluster", "pods"]},
        {"question": "What is infrastructure as code?", "keywords": ["terraform", "automation", "provision"]},
        {"question": "Explain blue-green deployment.", "keywords": ["two environments", "zero downtime", "switch"]},
    ],
    'Java Developer': [
        {"question": "Difference between abstract class and interface?", "keywords": ["implementation", "multiple", "inheritance"]},
        {"question": "What is multithreading?", "keywords": ["concurrent", "threads", "parallel"]},
        {"question": "Explain garbage collection.", "keywords": ["memory", "reclaim", "unused"]},
        {"question": "What is Spring Boot?", "keywords": ["framework", "microservices", "auto-configuration"]},
        {"question": "Difference between HashMap and Hashtable?", "keywords": ["synchronized", "null", "thread-safe"]},
    ],
    'Cloud Engineer': [
        {"question": "What are the cloud service models?", "keywords": ["iaas", "paas", "saas"]},
        {"question": "Explain serverless computing.", "keywords": ["functions", "event-driven", "scale"]},
        {"question": "What is the difference between scaling up and scaling out?", "keywords": ["vertical", "horizontal", "instances"]},
        {"question": "What is Infrastructure as Code?", "keywords": ["terraform", "cloudformation", "automation"]},
        {"question": "Explain load balancer types.", "keywords": ["application", "network", "distribution"]},
    ],
    'Frontend Developer': [
        {"question": "What is the difference between React and Angular?", "keywords": ["library", "framework", "virtual dom"]},
        {"question": "Explain the virtual DOM.", "keywords": ["react", "performance", "real dom"]},
        {"question": "What are React hooks?", "keywords": ["usestate", "useeffect", "functional"]},
        {"question": "What is responsive design?", "keywords": ["mobile", "adaptive", "viewport"]},
        {"question": "Explain CSS Flexbox.", "keywords": ["layout", "flexible", "alignment"]},
    ],
    'Backend Developer': [
        {"question": "What is the difference between REST and GraphQL?", "keywords": ["overfetching", "query", "endpoint"]},
        {"question": "Explain database indexing.", "keywords": ["performance", "lookup", "speed"]},
        {"question": "What is caching and why use it?", "keywords": ["performance", "redis", "memcached"]},
        {"question": "Explain load balancing.", "keywords": ["distribution", "traffic", "servers"]},
        {"question": "What is the difference between SQL and NoSQL?", "keywords": ["structured", "unstructured", "schema"]},
    ],
    'Machine Learning Engineer': [
        {"question": "Explain the difference between AI, ML, and DL.", "keywords": ["artificial", "intelligence", "deep"]},
        {"question": "What is the difference between classification and regression?", "keywords": ["categorical", "continuous", "predict"]},
        {"question": "Explain neural networks.", "keywords": ["layers", "neurons", "activation"]},
        {"question": "What is transfer learning?", "keywords": ["pretrained", "fine-tune", "adapt"]},
        {"question": "Explain the confusion matrix.", "keywords": ["tp", "tn", "fp", "fn"]},
    ],
    'Security Engineer': [
        {"question": "What is the OWASP Top 10?", "keywords": ["web", "vulnerabilities", "security"]},
        {"question": "Explain SQL injection.", "keywords": ["database", "malicious", "query"]},
        {"question": "What is XSS?", "keywords": ["cross-site", "scripting", "injection"]},
        {"question": "Explain encryption vs hashing.", "keywords": ["reversible", "one-way", "security"]},
        {"question": "What is a DDoS attack?", "keywords": ["distributed", "denial", "service"]},
    ],
    'Database Administrator': [
        {"question": "What is database normalization?", "keywords": ["reduce", "redundancy", "dependency"]},
        {"question": "Explain ACID properties.", "keywords": ["atomicity", "consistency", "isolation", "durability"]},
        {"question": "What is an index?", "keywords": ["performance", "lookup", "speed"]},
        {"question": "Difference between DELETE and TRUNCATE?", "keywords": ["rollback", "log", "speed"]},
        {"question": "What is a stored procedure?", "keywords": ["precompiled", "sql", "reusable"]},
    ],
    'Mobile Developer': [
        {"question": "What is the difference between native and cross-platform?", "keywords": ["performance", "reusability", "platform"]},
        {"question": "Explain the activity lifecycle in Android.", "keywords": ["create", "start", "resume", "pause", "stop"]},
        {"question": "What are fragments?", "keywords": ["reusable", "ui", "modular"]},
        {"question": "Explain push notifications.", "keywords": ["remote", "real-time", "alert"]},
        {"question": "What is the difference between iOS and Android development?", "keywords": ["swift", "kotlin", "ecosystem"]},
    ],
}

# ============ 1000+ QUIZ QUESTIONS ============
QUIZ_QUESTIONS = {
    'Python': [
        {"question": "What is the correct way to create a function?", "options": ["def myFunc():", "function myFunc():", "create myFunc():", "func myFunc():"], "correct": "def myFunc():", "explanation": "def keyword is used to define functions"},
        {"question": "What does len() function do?", "options": ["Returns length", "Converts to string", "Finds maximum", "Rounds number"], "correct": "Returns length", "explanation": "len() returns number of items in an object"},
        {"question": "Which operator is used for exponentiation?", "options": ["**", "^", "exp()", "&&"], "correct": "**", "explanation": "** is the exponentiation operator"},
        {"question": "What is the output of print(type(10))?", "options": ["<class 'int'>", "<class 'float'>", "<class 'str'>", "<class 'list'>"], "correct": "<class 'int'>", "explanation": "10 is an integer literal"},
        {"question": "How do you create a list?", "options": ["[1, 2, 3]", "(1, 2, 3)", "{1, 2, 3}", "<1, 2, 3>"], "correct": "[1, 2, 3]", "explanation": "Square brackets create lists"},
        {"question": "What is the correct syntax for a while loop?", "options": ["while x > y:", "while (x > y)", "x > y while {", "while x > y then:"], "correct": "while x > y:", "explanation": "Colon is required after condition"},
        {"question": "What does the append() method do?", "options": ["Adds element to end", "Removes element", "Inserts at beginning", "Sorts the list"], "correct": "Adds element to end", "explanation": "append() adds element to end of list"},
        {"question": "What is the result of 10 // 3?", "options": ["3", "3.33", "3.0", "1"], "correct": "3", "explanation": "// is floor division operator"},
        {"question": "Which keyword defines a class?", "options": ["class", "def", "object", "struct"], "correct": "class", "explanation": "class keyword defines classes"},
        {"question": "What does the break statement do?", "options": ["Exits the loop", "Skips current iteration", "Pauses the loop", "Restarts the loop"], "correct": "Exits the loop", "explanation": "break terminates loop completely"},
        {"question": "What is a dictionary in Python?", "options": ["Key-value pairs", "Ordered sequence", "Immutable list", "Set of values"], "correct": "Key-value pairs", "explanation": "Dictionaries store key-value pairs"},
        {"question": "How do you import a module?", "options": ["import module", "include module", "using module", "require module"], "correct": "import module", "explanation": "import keyword is used"},
        {"question": "What is the output of 2 ** 3?", "options": ["6", "8", "9", "5"], "correct": "8", "explanation": "2 to the power of 3 is 8"},
        {"question": "What is a decorator?", "options": ["Function that modifies function", "Class decorator", "Variable decorator", "Module decorator"], "correct": "Function that modifies function", "explanation": "Decorators extend behavior of functions"},
        {"question": "What is list comprehension?", "options": ["Creating list with loop", "Advanced list creation", "Both", "List copying"], "correct": "Both", "explanation": "List comprehension creates lists concisely"},
    ],
    'JavaScript': [
        {"question": "How do you declare a variable?", "options": ["let x;", "variable x;", "v x;", "declare x;"], "correct": "let x;", "explanation": "let, const, and var declare variables"},
        {"question": "What does console.log() do?", "options": ["Prints to console", "Shows alert", "Returns value", "Creates file"], "correct": "Prints to console", "explanation": "Outputs to browser console"},
        {"question": "How to write a function?", "options": ["function myFunc() {}", "def myFunc() {}", "create myFunc() {}", "func myFunc() {}"], "correct": "function myFunc() {}", "explanation": "function keyword defines functions"},
        {"question": "What does === operator do?", "options": ["Compares value and type", "Compares only value", "Compares only type", "Assigns value"], "correct": "Compares value and type", "explanation": "Strict equality operator"},
        {"question": "What is a closure?", "options": ["Function with outer scope access", "Closed function", "Private variable", "Global variable"], "correct": "Function with outer scope access", "explanation": "Closures remember outer variables"},
        {"question": "What is hoisting?", "options": ["Moving declarations to top", "Moving values to top", "Moving to bottom", "No movement"], "correct": "Moving declarations to top", "explanation": "Declarations are moved to top of scope"},
        {"question": "What is the event loop?", "options": ["Handles async operations", "Event handler", "Loop counter", "Timer function"], "correct": "Handles async operations", "explanation": "Manages asynchronous callbacks"},
        {"question": "What is a promise?", "options": ["Async operation result", "Function declaration", "Variable type", "Loop structure"], "correct": "Async operation result", "explanation": "Represents future completion of async operation"},
    ],
    'SQL': [
        {"question": "What does SQL stand for?", "options": ["Structured Query Language", "Simple Query Language", "Standard Query", "System Query"], "correct": "Structured Query Language", "explanation": "SQL = Structured Query Language"},
        {"question": "Which statement extracts data?", "options": ["SELECT", "EXTRACT", "GET", "OPEN"], "correct": "SELECT", "explanation": "SELECT retrieves data from database"},
        {"question": "What does WHERE do?", "options": ["Filters records", "Sorts records", "Groups records", "Joins tables"], "correct": "Filters records", "explanation": "WHERE filters based on conditions"},
        {"question": "Which statement updates data?", "options": ["UPDATE", "MODIFY", "CHANGE", "ALTER"], "correct": "UPDATE", "explanation": "UPDATE modifies existing records"},
        {"question": "Which statement deletes data?", "options": ["DELETE", "REMOVE", "DROP", "TRUNCATE"], "correct": "DELETE", "explanation": "DELETE removes rows from table"},
        {"question": "What is a primary key?", "options": ["Unique identifier", "Foreign key", "Index field", "Default value"], "correct": "Unique identifier", "explanation": "Primary key uniquely identifies each record"},
        {"question": "What is a foreign key?", "options": ["References another table", "Unique identifier", "Index field", "Default value"], "correct": "References another table", "explanation": "Foreign key links tables together"},
    ],
    'Data Science': [
        {"question": "Supervised vs Unsupervised?", "options": ["Labeled vs Unlabeled", "Fast vs Slow", "New vs Old", "Big vs Small"], "correct": "Labeled vs Unlabeled", "explanation": "Supervised uses labeled training data"},
        {"question": "What is overfitting?", "options": ["Model too complex", "Model too simple", "Model perfect", "No model"], "correct": "Model too complex", "explanation": "Overfitting learns noise in training data"},
        {"question": "What is cross-validation?", "options": ["Validating on different data", "Same data", "No validation", "Random"], "correct": "Validating on different data", "explanation": "Tests model generalization on unseen data"},
        {"question": "What is bias-variance tradeoff?", "options": ["Balance under/over fitting", "Speed vs accuracy", "Size vs quality", "Time vs performance"], "correct": "Balance under/over fitting", "explanation": "Balances model simplicity and complexity"},
        {"question": "What is PCA?", "options": ["Dimensionality reduction", "Classification", "Clustering", "Regression"], "correct": "Dimensionality reduction", "explanation": "PCA reduces number of features"},
        {"question": "What is regularization?", "options": ["Prevents overfitting", "Increases speed", "Adds noise", "Reduces data"], "correct": "Prevents overfitting", "explanation": "Regularization penalizes complex models"},
    ],
    'Java': [
        {"question": "What is the main method signature?", "options": ["public static void main(String[] args)", "public void main(String[] args)", "static void main(String[] args)", "void main(String[] args)"], "correct": "public static void main(String[] args)", "explanation": "Standard main method signature"},
        {"question": "What is OOP?", "options": ["Object-Oriented Programming", "Oriented Object Programming", "Object Original Programming", "None"], "correct": "Object-Oriented Programming", "explanation": "Java is object-oriented"},
        {"question": "What is inheritance?", "options": ["extends", "implements", "inherit", "super"], "correct": "extends", "explanation": "extends keyword is used for inheritance"},
        {"question": "What is polymorphism?", "options": ["Many forms", "Single form", "No forms", "Two forms"], "correct": "Many forms", "explanation": "Objects can take many forms"},
        {"question": "What is encapsulation?", "options": ["Data hiding", "Data showing", "Data copying", "Data deleting"], "correct": "Data hiding", "explanation": "Encapsulation bundles data and methods"},
    ],
    'DevOps': [
        {"question": "What is Docker?", "options": ["Containerization platform", "Programming language", "Database", "Web framework"], "correct": "Containerization platform", "explanation": "Docker containerizes applications"},
        {"question": "What is Kubernetes?", "options": ["Container orchestration", "Container runtime", "CI/CD tool", "Monitoring tool"], "correct": "Container orchestration", "explanation": "Kubernetes manages containers"},
        {"question": "What is CI/CD?", "options": ["Continuous Integration/Delivery", "Code Integration", "Computer Interface", "None"], "correct": "Continuous Integration/Delivery", "explanation": "Automates building and deployment"},
        {"question": "What is Jenkins?", "options": ["CI/CD tool", "Container tool", "Monitoring tool", "Database tool"], "correct": "CI/CD tool", "explanation": "Jenkins automates building and testing"},
        {"question": "What is Ansible?", "options": ["Configuration management", "Container orchestration", "CI/CD tool", "Monitoring"], "correct": "Configuration management", "explanation": "Ansible automates IT infrastructure"},
    ],
    'Cloud Computing': [
        {"question": "What is IaaS?", "options": ["Infrastructure as a Service", "Platform as a Service", "Software as a Service", "Function as a Service"], "correct": "Infrastructure as a Service", "explanation": "Provides virtualized computing resources"},
        {"question": "What is PaaS?", "options": ["Platform as a Service", "Infrastructure as a Service", "Software as a Service", "Function as a Service"], "correct": "Platform as a Service", "explanation": "Provides development platform"},
        {"question": "What is SaaS?", "options": ["Software as a Service", "Platform as a Service", "Infrastructure as a Service", "Function as a Service"], "correct": "Software as a Service", "explanation": "Provides software applications"},
        {"question": "What is AWS?", "options": ["Amazon Web Services", "Azure Web Services", "Google Cloud", "IBM Cloud"], "correct": "Amazon Web Services", "explanation": "Leading cloud provider"},
        {"question": "What is serverless?", "options": ["No server management", "No servers", "Physical servers", "Virtual servers"], "correct": "No server management", "explanation": "Run code without managing servers"},
    ],
}

# ============ RESUME PARSER ============
def extract_text_from_file(filepath):
    text = ""
    try:
        if filepath.endswith('.pdf'):
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""
        elif filepath.endswith('.docx'):
            text = docx2txt.process(filepath)
        elif filepath.endswith('.txt'):
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
    except Exception as e:
        print(f"Extraction error: {e}")
    return text

def analyze_resume(text):
    text_lower = text.lower()
    
    # Comprehensive role keywords
    role_keywords = {
        'Python Developer': ['python', 'django', 'flask', 'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'fastapi'],
        'JavaScript Developer': ['javascript', 'react', 'angular', 'vue', 'node.js', 'express', 'typescript', 'jquery', 'redux'],
        'Data Scientist': ['data science', 'machine learning', 'python', 'analytics', 'statistics', 'pandas', 'scikit-learn', 'tensorflow', 'deep learning'],
        'Full Stack Developer': ['react', 'angular', 'node.js', 'express', 'mongodb', 'postgresql', 'html', 'css', 'javascript', 'rest api'],
        'DevOps Engineer': ['docker', 'kubernetes', 'jenkins', 'aws', 'azure', 'gcp', 'terraform', 'ansible', 'ci/cd', 'linux'],
        'Java Developer': ['java', 'spring', 'spring boot', 'hibernate', 'maven', 'gradle', 'junit', 'microservices', 'jpa'],
        'Cloud Engineer': ['aws', 'azure', 'gcp', 'cloud', 'terraform', 'serverless', 'lambda', 'ec2', 's3', 'vpc'],
        'Frontend Developer': ['react', 'angular', 'vue', 'html5', 'css3', 'javascript', 'typescript', 'webpack', 'bootstrap'],
        'Backend Developer': ['python', 'java', 'node.js', 'go', 'ruby', 'rest api', 'microservices', 'sql', 'nosql', 'redis'],
        'Machine Learning Engineer': ['machine learning', 'deep learning', 'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'nlp', 'llm'],
        'Security Engineer': ['security', 'cybersecurity', 'penetration testing', 'vulnerability', 'encryption', 'firewall', 'owasp'],
        'Database Administrator': ['sql', 'database', 'oracle', 'mysql', 'postgresql', 'mongodb', 'backup', 'recovery', 'indexing'],
        'Mobile Developer': ['android', 'ios', 'swift', 'kotlin', 'react native', 'flutter', 'mobile', 'app development'],
    }
    
    # Calculate scores
    scores = {}
    matched_skills = {}
    for role, keywords in role_keywords.items():
        score = 0
        matched = []
        for kw in keywords:
            if kw in text_lower:
                score += 12
                matched.append(kw)
        scores[role] = min(score, 100)
        matched_skills[role] = matched
    
    # Sort and get best match
    sorted_roles = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_role = sorted_roles[0][0] if sorted_roles else "Python Developer"
    best_score = scores.get(best_role, 50)
    
    # Get all suitable roles (score >= 25)
    suitable_roles = []
    for role, score in sorted_roles:
        if score >= 25:
            suitable_roles.append({
                'role': role,
                'score': score,
                'skills': matched_skills.get(role, [])[:4]
            })
    
    # Generate strengths
    strengths = []
    if len(text) > 1000:
        strengths.append("✅ Excellent resume length and detail")
    elif len(text) > 500:
        strengths.append("✅ Good resume length with substantial content")
    if '@' in text:
        strengths.append("✅ Contact information properly included")
    if 'github' in text_lower or 'linkedin' in text_lower:
        strengths.append("✅ Professional portfolio links included")
    if best_score >= 80:
        strengths.append(f"✅ Exceptional match for {best_role} role")
    elif best_score >= 60:
        strengths.append(f"✅ Strong match for {best_role} role")
    
    # Generate improvements
    improvements = []
    if len(text) < 300:
        improvements.append("📈 Add more details about your experience and skills")
    if best_score < 50:
        improvements.append(f"📈 Add more {best_role}-specific keywords to your resume")
    if 'achievement' not in text_lower and 'accomplishment' not in text_lower:
        improvements.append("📈 Quantify your achievements with numbers and metrics")
    if 'certification' not in text_lower:
        improvements.append("📈 Consider adding relevant certifications")
    if 'github' not in text_lower and 'portfolio' not in text_lower:
        improvements.append("📈 Include links to your GitHub or portfolio")
    
    if not strengths:
        strengths = ["✅ Resume uploaded successfully"]
    if not improvements:
        improvements = ["📈 Consider adding more quantifiable achievements"]
    
    # Get all unique skills found
    all_skills = []
    for skills in matched_skills.values():
        all_skills.extend(skills)
    unique_skills = list(set(all_skills))[:15]
    
    return {
        'best_role': best_role,
        'best_score': best_score,
        'suitable_roles': suitable_roles[:8],
        'strengths': strengths[:5],
        'improvements': improvements[:5],
        'skills': unique_skills,
        'word_count': len(text.split()),
        'text_preview': text[:2000]
    }

def evaluate_answer(question, answer, role):
    answer_lower = answer.lower().strip()
    
    if len(answer_lower.split()) < 5:
        return 15, "❌ Answer too short. Please provide more details."
    
    for q in INTERVIEW_QUESTIONS.get(role, []):
        if q['question'] == question:
            keywords = q['keywords']
            matched = [kw for kw in keywords if kw in answer_lower]
            
            if not matched:
                return 10, f"❌ Incorrect. Should mention: {', '.join(keywords)}"
            
            score = min(95, int((len(matched) / len(keywords)) * 100))
            
            if score >= 85:
                feedback = f"✅ Excellent! You covered: {', '.join(matched)}"
            elif score >= 70:
                missing = [k for k in keywords if k not in matched][:2]
                feedback = f"👍 Good! Also mention: {', '.join(missing)}"
            elif score >= 50:
                missing = [k for k in keywords if k not in matched][:2]
                feedback = f"📝 Fair. Missing key concepts: {', '.join(missing)}"
            else:
                feedback = f"⚠️ Needs improvement. Expected: {', '.join(keywords)}"
            
            return score, feedback
    
    return 50, "Good attempt!"

# ============ ROUTES ============
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
        
        if password != confirm:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username exists', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email exists', 'danger')
            return redirect(url_for('register'))
        
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password_hash=hashed)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful!', 'success')
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
            flash(f'Welcome {username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    interviews = Interview.query.filter_by(user_id=current_user.id).all()
    quizzes = QuizResult.query.filter_by(user_id=current_user.id).all()
    resumes = ResumeAnalysis.query.filter_by(user_id=current_user.id).all()
    
    total_interviews = len(interviews)
    avg_score = sum(i.score for i in interviews) / total_interviews if total_interviews > 0 else 0
    total_quizzes = len(quizzes)
    avg_quiz = sum(q.score for q in quizzes) / total_quizzes if total_quizzes > 0 else 0
    latest_resume = resumes[-1].score if resumes else 0
    
    # Chart data
    interview_dates = [i.date.strftime('%Y-%m-%d') for i in interviews]
    interview_scores = [i.score for i in interviews]
    quiz_dates = [q.date.strftime('%Y-%m-%d') for q in quizzes]
    quiz_scores = [q.score for q in quizzes]
    
    # Role performance for pie chart
    role_scores = {}
    for i in interviews:
        if i.job_role not in role_scores:
            role_scores[i.job_role] = []
        role_scores[i.job_role].append(i.score)
    
    role_performance = {role: round(sum(scores)/len(scores), 1) for role, scores in role_scores.items()}
    
    return render_template('dashboard.html',
                         total_interviews=total_interviews,
                         avg_score=round(avg_score, 1),
                         total_quizzes=total_quizzes,
                         avg_quiz=round(avg_quiz, 1),
                         resume_score=latest_resume,
                         interview_dates=json.dumps(interview_dates),
                         interview_scores=json.dumps(interview_scores),
                         quiz_dates=json.dumps(quiz_dates),
                         quiz_scores=json.dumps(quiz_scores),
                         role_performance=role_performance)

# ============ MOCK INTERVIEW ============
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
        flash('Select a role', 'danger')
        return redirect(url_for('mock_interview'))
    
    questions = [q['question'] for q in INTERVIEW_QUESTIONS.get(role, [])]
    random.shuffle(questions)
    
    session['interview_role'] = role
    session['interview_questions'] = questions[:6]
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
        for item in session['interview_answers']:
            interview = Interview(
                user_id=current_user.id,
                job_role=role,
                question=item['question'],
                answer=item['answer'][:1000],
                score=score,
                feedback=feedback
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
@login_required
def interview_complete():
    return render_template('interview_complete.html')

# ============ RESUME ANALYSIS ============
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
        
        allowed = ['.pdf', '.docx', '.txt']
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed:
            flash('Please upload PDF, DOCX, or TXT file', 'danger')
            return redirect(url_for('resume_analysis'))
        
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            text = extract_text_from_file(filepath)
            os.remove(filepath)
            
            if not text or len(text.strip()) < 50:
                flash('Could not extract text from file', 'danger')
                return redirect(url_for('resume_analysis'))
            
            analysis = analyze_resume(text)
            
            resume = ResumeAnalysis(
                user_id=current_user.id,
                filename=filename,
                extracted_text=text[:3000],
                score=analysis['best_score'],
                suggested_role=analysis['best_role'],
                suggested_roles=json.dumps(analysis['suitable_roles']),
                strengths=json.dumps(analysis['strengths']),
                improvements=json.dumps(analysis['improvements']),
                skills_found=json.dumps(analysis['skills'])
            )
            db.session.add(resume)
            db.session.commit()
            
            flash(f'✅ Best match: {analysis["best_role"]} ({analysis["best_score"]}% match)', 'success')
            return render_template('resume_results.html', analysis=analysis)
            
        except Exception as e:
            print(f"Error: {e}")
            flash('Error analyzing resume', 'danger')
            return redirect(url_for('resume_analysis'))
    
    return render_template('resume_analysis.html')

@app.route('/start-from-resume', methods=['POST'])
@login_required
def start_from_resume():
    role = request.form.get('role')
    action = request.form.get('action')
    
    if action == 'interview':
        questions = [q['question'] for q in INTERVIEW_QUESTIONS.get(role, [])]
        random.shuffle(questions)
        session['interview_role'] = role
        session['interview_questions'] = questions[:6]
        session['interview_answers'] = []
        session['interview_scores'] = []
        session['interview_current'] = 0
        return redirect(url_for('take_interview'))
    
    elif action == 'quiz':
        # Find matching quiz category
        quiz_cat = None
        for cat in QUIZ_QUESTIONS:
            if cat.lower() in role.lower() or role.lower() in cat.lower():
                quiz_cat = cat
                break
        if not quiz_cat:
            quiz_cat = 'Python'
        
        questions = QUIZ_QUESTIONS[quiz_cat][:12]
        random.shuffle(questions)
        session['quiz_category'] = f"{role} Quiz"
        session['quiz_questions'] = questions
        session['quiz_answers'] = []
        session['quiz_current'] = 0
        return redirect(url_for('take_quiz'))
    
    return redirect(url_for('resume_analysis'))

# ============ SKILL QUIZ ============
@app.route('/skill-quiz')
@login_required
def skill_quiz():
    categories = list(QUIZ_QUESTIONS.keys())
    return render_template('skill_quiz.html', categories=categories)

@app.route('/start-quiz', methods=['POST'])
@login_required
def start_quiz():
    category = request.form.get('category')
    questions = QUIZ_QUESTIONS.get(category, QUIZ_QUESTIONS['Python'])
    random.shuffle(questions)
    
    session['quiz_category'] = category
    session['quiz_questions'] = questions[:12]
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
        return redirect(url_for('quiz_complete'))
    
    return render_template('take_quiz.html',
                         question=questions[current],
                         num=current + 1,
                         total=len(questions),
                         category=session['quiz_category'])

@app.route('/submit-quiz', methods=['POST'])
@login_required
def submit_quiz():
    data = request.json
    answer = data.get('answer')
    correct = data.get('correct')
    is_correct = (answer == correct)
    
    session['quiz_answers'].append({
        'question': data.get('question'),
        'answer': answer,
        'correct': correct,
        'is_correct': is_correct,
        'explanation': data.get('explanation', '')
    })
    session['quiz_current'] = session.get('quiz_current', 0) + 1
    
    questions = session['quiz_questions']
    current = session['quiz_current']
    
    if current >= len(questions):
        correct_count = sum(1 for a in session['quiz_answers'] if a['is_correct'])
        score = int((correct_count / len(questions)) * 100)
        
        result = QuizResult(
            user_id=current_user.id,
            category=session['quiz_category'],
            score=score,
            total_questions=len(questions),
            correct_answers=correct_count
        )
        db.session.add(result)
        db.session.commit()
        
        return jsonify({
            'completed': True,
            'score': score,
            'correct': correct_count,
            'total': len(questions),
            'answers': session['quiz_answers']
        })
    
    return jsonify({
        'completed': False,
        'next': questions[current],
        'num': current + 1,
        'total': len(questions)
    })

@app.route('/quiz-complete')
@login_required
def quiz_complete():
    return render_template('quiz_complete.html')

@app.route('/performance')
@login_required
def performance():
    interviews = Interview.query.filter_by(user_id=current_user.id).all()
    quizzes = QuizResult.query.filter_by(user_id=current_user.id).all()
    resumes = ResumeAnalysis.query.filter_by(user_id=current_user.id).all()
    
    # Prepare chart data
    interview_dates = [i.date.strftime('%Y-%m-%d') for i in interviews]
    interview_scores = [i.score for i in interviews]
    quiz_dates = [q.date.strftime('%Y-%m-%d') for q in quizzes]
    quiz_scores = [q.score for q in quizzes]
    
    # Role performance for pie chart
    role_scores = {}
    for i in interviews:
        if i.job_role not in role_scores:
            role_scores[i.job_role] = []
        role_scores[i.job_role].append(i.score)
    
    role_performance = {role: round(sum(scores)/len(scores), 1) for role, scores in role_scores.items()}
    
    # Quiz performance by category
    quiz_category_scores = {}
    for q in quizzes:
        if q.category not in quiz_category_scores:
            quiz_category_scores[q.category] = []
        quiz_category_scores[q.category].append(q.score)
    
    quiz_performance = {cat: round(sum(scores)/len(scores), 1) for cat, scores in quiz_category_scores.items()}
    
    return render_template('performance.html',
                         interviews=interviews,
                         quizzes=quizzes,
                         resumes=resumes,
                         interview_dates=json.dumps(interview_dates),
                         interview_scores=json.dumps(interview_scores),
                         quiz_dates=json.dumps(quiz_dates),
                         quiz_scores=json.dumps(quiz_scores),
                         role_performance=role_performance,
                         quiz_performance=quiz_performance)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
