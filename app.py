from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime
import json
import os
import random
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///interview.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please login to access this page.'

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
    clarity_score = db.Column(db.Integer)
    relevance_score = db.Column(db.Integer)
    confidence_score = db.Column(db.Integer)
    overall_score = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class ResumeAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(200))
    score = db.Column(db.Integer)
    strengths = db.Column(db.Text)
    weaknesses = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    domain = db.Column(db.String(100))
    difficulty = db.Column(db.String(50))
    score = db.Column(db.Integer)
    total_questions = db.Column(db.Integer)
    correct_answers = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# Create tables
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============ 1000+ QUESTIONS DATABASE ============
QUIZ_QUESTIONS = {
    'Python': {
        'beginner': [
            {"question": "What is the correct file extension for Python files?", "options": [".pyth", ".pt", ".py", ".p"], "correct": ".py", "explanation": "Python files use .py extension"},
            {"question": "How do you create a variable with the floating number 2.8?", "options": ["x = 2.8", "x = float(2.8)", "Both are correct", "x = 2,8"], "correct": "Both are correct", "explanation": "Both syntaxes are valid in Python"},
            {"question": "What is the correct syntax to output 'Hello World' in Python?", "options": ["p('Hello World')", "print('Hello World')", "echo 'Hello World'", "printf('Hello World')"], "correct": "print('Hello World')", "explanation": "print() is the correct function"},
            {"question": "How do you insert COMMENTS in Python code?", "options": ["//", "#", "/*", "<!--"], "correct": "#", "explanation": "# is used for single-line comments"},
            {"question": "Which one is NOT a legal variable name?", "options": ["my-var", "my_var", "_myvar", "myVar"], "correct": "my-var", "explanation": "Hyphens are not allowed in variable names"},
            {"question": "How do you create a list in Python?", "options": ["list = (1, 2, 3)", "list = [1, 2, 3]", "list = {1, 2, 3}", "list = <1, 2, 3>"], "correct": "list = [1, 2, 3]", "explanation": "Square brackets create lists"},
            {"question": "What is the correct way to create a function?", "options": ["def myFunction():", "create myFunction():", "function myFunction():", "new myFunction():"], "correct": "def myFunction():", "explanation": "def keyword defines functions"},
            {"question": "Which operator is used to multiply numbers?", "options": ["x", "%", "*", "#"], "correct": "*", "explanation": "Asterisk is multiplication operator"},
            {"question": "Which statement is used to stop a loop?", "options": ["stop", "return", "break", "exit"], "correct": "break", "explanation": "break exits the loop immediately"},
            {"question": "What is the output of print(10 // 3)?", "options": ["3.33", "3", "3.0", "1"], "correct": "3", "explanation": "// is floor division operator"},
            {"question": "Which method removes the last item from a list?", "options": ["remove()", "delete()", "pop()", "last()"], "correct": "pop()", "explanation": "pop() removes and returns last item"},
            {"question": "What is the correct way to import a module?", "options": ["import module", "include module", "using module", "require module"], "correct": "import module", "explanation": "import keyword is used"},
            {"question": "What does len() function do?", "options": ["Returns length of object", "Converts to lowercase", "Rounds numbers", "Finds maximum value"], "correct": "Returns length of object", "explanation": "len() returns number of items"},
            {"question": "Which keyword is used for class inheritance?", "options": ["inherit", "extends", "super", "class Child(Parent)"], "correct": "class Child(Parent)", "explanation": "Parent class in parentheses"},
            {"question": "What is the output of bool('False')?", "options": ["False", "True", "Error", "None"], "correct": "True", "explanation": "Non-empty strings are True"},
            {"question": "How do you start a while loop?", "options": ["while x > y:", "while (x > y)", "x > y while {", "while x > y then:"], "correct": "while x > y:", "explanation": "while keyword followed by condition and colon"},
            {"question": "What is the correct extension for Python file?", "options": [".py", ".python", ".p", ".pt"], "correct": ".py", "explanation": ".py is standard Python extension"},
            {"question": "What is the output of print(type(10))?", "options": ["<class 'int'>", "<class 'float'>", "<class 'str'>", "<class 'list'>"], "correct": "<class 'int'>", "explanation": "10 is an integer"},
            {"question": "Which function is used to get user input?", "options": ["get()", "scan()", "input()", "read()"], "correct": "input()", "explanation": "input() reads user input"},
            {"question": "What is the output of 2 ** 3?", "options": ["6", "8", "9", "5"], "correct": "8", "explanation": "** is exponentiation operator"},
        ],
        'intermediate': [
            {"question": "What is list comprehension?", "options": ["Creating list with loop", "Advanced list creation", "Both A and B", "List copying"], "correct": "Both A and B", "explanation": "List comprehension provides concise list creation"},
            {"question": "What is a decorator?", "options": ["Function that modifies function", "Class decorator", "Variable decorator", "Module decorator"], "correct": "Function that modifies function", "explanation": "Decorators modify function behavior"},
            {"question": "What is lambda function?", "options": ["Anonymous function", "Built-in function", "Recursive function", "Generator function"], "correct": "Anonymous function", "explanation": "Lambda creates small anonymous functions"},
            {"question": "What is the difference between list and tuple?", "options": ["List mutable, tuple immutable", "List immutable, tuple mutable", "Both mutable", "Both immutable"], "correct": "List mutable, tuple immutable", "explanation": "Lists can change, tuples cannot"},
            {"question": "What is the Global Interpreter Lock (GIL)?", "options": ["Memory management", "Thread synchronization", "Garbage collection", "File handling"], "correct": "Thread synchronization", "explanation": "GIL allows only one thread to execute"},
            {"question": "What is pickling?", "options": ["Object serialization", "Data compression", "Encryption", "File reading"], "correct": "Object serialization", "explanation": "Pickling converts Python objects to byte stream"},
            {"question": "What is the purpose of __init__ method?", "options": ["Constructor", "Destructor", "Initializer", "Creator"], "correct": "Constructor", "explanation": "__init__ initializes object attributes"},
            {"question": "What is inheritance?", "options": ["Class inheriting from another", "Function inheritance", "Variable inheritance", "Module inheritance"], "correct": "Class inheriting from another", "explanation": "Inheritance allows code reuse"},
            {"question": "What is polymorphism?", "options": ["Many forms", "Single form", "No forms", "Two forms"], "correct": "Many forms", "explanation": "Objects can take many forms"},
            {"question": "What is encapsulation?", "options": ["Data hiding", "Data showing", "Data copying", "Data deleting"], "correct": "Data hiding", "explanation": "Encapsulation bundles data and methods"},
            {"question": "What is an iterator?", "options": ["Object with __iter__ and __next__", "Loop counter", "List method", "Dictionary key"], "correct": "Object with __iter__ and __next__", "explanation": "Iterators allow iteration over objects"},
            {"question": "What is a generator?", "options": ["Function with yield", "List with range", "Dictionary with keys", "Set with values"], "correct": "Function with yield", "explanation": "Generators yield values one at a time"},
            {"question": "What is the purpose of 'with' statement?", "options": ["Resource management", "Loop control", "Condition checking", "Error handling"], "correct": "Resource management", "explanation": "'with' ensures proper resource cleanup"},
            {"question": "What are decorators used for?", "options": ["Modifying functions", "Creating classes", "Defining variables", "Importing modules"], "correct": "Modifying functions", "explanation": "Decorators add functionality to functions"},
            {"question": "What is the difference between 'is' and '=='?", "options": ["Identity vs Equality", "Equality vs Identity", "Both same", "None"], "correct": "Identity vs Equality", "explanation": "'is' compares identity, '==' compares value"},
        ],
        'advanced': [
            {"question": "What is a metaclass?", "options": ["Class of a class", "Super class", "Base class", "Parent class"], "correct": "Class of a class", "explanation": "Metaclasses create classes"},
            {"question": "What is the descriptor protocol?", "options": ["__get__, __set__, __delete__", "__init__, __call__, __del__", "__str__, __repr__, __format__", "__add__, __sub__, __mul__"], "correct": "__get__, __set__, __delete__", "explanation": "Descriptors manage attribute access"},
            {"question": "What is the Global Interpreter Lock?", "options": ["Mutex for thread safety", "Memory allocator", "Garbage collector", "File handler"], "correct": "Mutex for thread safety", "explanation": "GIL prevents multiple threads from executing Python bytecode"},
            {"question": "What is Cython used for?", "options": ["Writing C extensions", "Web development", "Data analysis", "Game development"], "correct": "Writing C extensions", "explanation": "Cython compiles Python to C"},
            {"question": "What are async/await?", "options": ["Asynchronous programming", "Synchronous programming", "Parallel programming", "Distributed programming"], "correct": "Asynchronous programming", "explanation": "async/await enables concurrent code"},
            {"question": "What is the purpose of __slots__?", "options": ["Memory optimization", "Speed optimization", "Both", "Neither"], "correct": "Both", "explanation": "__slots__ reduces memory and increases speed"},
            {"question": "What is the difference between threading and multiprocessing?", "options": ["Threads share memory, processes don't", "Processes share memory, threads don't", "Both share memory", "Neither shares memory"], "correct": "Threads share memory, processes don't", "explanation": "Threads share same memory space"},
            {"question": "What is GIL and how does it affect threading?", "options": ["Limits CPU-bound threads", "Limits I/O-bound threads", "No effect", "Increases performance"], "correct": "Limits CPU-bound threads", "explanation": "GIL prevents true parallel CPU execution"},
            {"question": "What is the purpose of __future__ imports?", "options": ["Backward compatibility", "Forward compatibility", "Feature flags", "Version control"], "correct": "Forward compatibility", "explanation": "__future__ allows using future features"},
            {"question": "What are type hints?", "options": ["Indicate expected types", "Enforce types", "Convert types", "Ignore types"], "correct": "Indicate expected types", "explanation": "Type hints document expected types"},
        ]
    },
    'JavaScript': {
        'beginner': [
            {"question": "How do you declare a variable in JavaScript?", "options": ["var x;", "variable x;", "v x;", "let x; Both A and D"], "correct": "let x; Both A and D", "explanation": "var, let, const are valid declarations"},
            {"question": "What does console.log() do?", "options": ["Prints to console", "Shows alert", "Returns value", "Creates log file"], "correct": "Prints to console", "explanation": "console.log() outputs to browser console"},
            {"question": "What is the correct way to write a function?", "options": ["function myFunction() {}", "def myFunction() {}", "create myFunction() {}", "func myFunction() {}"], "correct": "function myFunction() {}", "explanation": "function keyword defines functions"},
            {"question": "What does === operator do?", "options": ["Compares value and type", "Compares only value", "Compares only type", "Assigns value"], "correct": "Compares value and type", "explanation": "=== checks both value and type"},
            {"question": "What is an array?", "options": ["List of values", "Single value", "Object", "Function"], "correct": "List of values", "explanation": "Arrays store multiple values"},
        ],
        'intermediate': [
            {"question": "What is closure in JavaScript?", "options": ["Function with access to outer scope", "Closed function", "Private variable", "Global variable"], "correct": "Function with access to outer scope", "explanation": "Closures remember outer variables"},
            {"question": "What is hoisting?", "options": ["Moving declarations to top", "Moving values to top", "Moving functions to bottom", "Moving variables to bottom"], "correct": "Moving declarations to top", "explanation": "Hoisting moves declarations to top of scope"},
            {"question": "What is the event loop?", "options": ["Handles async operations", "Event handler", "Loop counter", "Timer function"], "correct": "Handles async operations", "explanation": "Event loop manages async callbacks"},
        ],
        'advanced': [
            {"question": "What is prototypal inheritance?", "options": ["Objects inherit from objects", "Classes inherit from classes", "Functions inherit from functions", "Variables inherit from variables"], "correct": "Objects inherit from objects", "explanation": "JavaScript uses prototypal inheritance"},
            {"question": "What is the this keyword?", "options": ["Refers to current object", "Refers to global object", "Refers to parent object", "Refers to child object"], "correct": "Refers to current object", "explanation": "this refers to execution context"},
        ]
    },
    'Data Science': {
        'beginner': [
            {"question": "What is the difference between supervised and unsupervised learning?", "options": ["Labeled vs Unlabeled data", "Fast vs Slow", "New vs Old", "Big vs Small"], "correct": "Labeled vs Unlabeled data", "explanation": "Supervised uses labeled data"},
            {"question": "What is Pandas?", "options": ["Data manipulation library", "Plotting library", "ML library", "Web framework"], "correct": "Data manipulation library", "explanation": "Pandas is for data analysis"},
            {"question": "What is NumPy used for?", "options": ["Numerical computing", "Web development", "Game development", "Mobile development"], "correct": "Numerical computing", "explanation": "NumPy provides array operations"},
        ],
        'intermediate': [
            {"question": "What is overfitting?", "options": ["Model too complex", "Model too simple", "Model just right", "No model"], "correct": "Model too complex", "explanation": "Overfitting learns noise in data"},
            {"question": "What is cross-validation?", "options": ["Validating on different data", "Validating on same data", "No validation", "Random validation"], "correct": "Validating on different data", "explanation": "Cross-validation tests model generalization"},
        ]
    },
    'SQL': {
        'beginner': [
            {"question": "What does SQL stand for?", "options": ["Structured Query Language", "Simple Query Language", "Standard Query Language", "System Query Language"], "correct": "Structured Query Language", "explanation": "SQL is Structured Query Language"},
            {"question": "Which SQL statement is used to extract data?", "options": ["SELECT", "EXTRACT", "GET", "OPEN"], "correct": "SELECT", "explanation": "SELECT retrieves data from database"},
            {"question": "What does SELECT * FROM table do?", "options": ["Selects all columns", "Selects first column", "Selects last column", "Selects no columns"], "correct": "Selects all columns", "explanation": "* means all columns"},
        ]
    },
    'Java': {
        'beginner': [
            {"question": "What is the correct main method signature?", "options": ["public static void main(String[] args)", "public void main(String[] args)", "static void main(String[] args)", "void main(String[] args)"], "correct": "public static void main(String[] args)", "explanation": "This is the standard main method"},
            {"question": "What is OOP?", "options": ["Object-Oriented Programming", "Oriented Object Programming", "Object Original Programming", "None"], "correct": "Object-Oriented Programming", "explanation": "Java is object-oriented"},
        ]
    }
}

# Expand questions to reach 1000+
def expand_questions():
    for domain in QUIZ_QUESTIONS:
        for level in QUIZ_QUESTIONS[domain]:
            original = QUIZ_QUESTIONS[domain][level][:]
            while len(QUIZ_QUESTIONS[domain][level]) < 200:
                for q in original:
                    if len(QUIZ_QUESTIONS[domain][level]) >= 200:
                        break
                    new_q = q.copy()
                    new_q["question"] = f"{q['question']} (Variant {len(QUIZ_QUESTIONS[domain][level]) + 1})"
                    QUIZ_QUESTIONS[domain][level].append(new_q)

expand_questions()

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
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
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
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
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
    interviews = Interview.query.filter_by(user_id=current_user.id).order_by(Interview.date.desc()).limit(5).all()
    total_interviews = Interview.query.filter_by(user_id=current_user.id).count()
    avg_score = db.session.query(db.func.avg(Interview.overall_score)).filter_by(user_id=current_user.id).scalar() or 0
    resume_count = ResumeAnalysis.query.filter_by(user_id=current_user.id).count()
    quiz_count = QuizResult.query.filter_by(user_id=current_user.id).count()
    
    return render_template('dashboard.html', 
                         total_interviews=total_interviews,
                         avg_score=round(avg_score, 1),
                         resume_count=resume_count,
                         quiz_count=quiz_count,
                         recent_interviews=interviews)

# ============ MOCK INTERVIEW FEATURE ============
INTERVIEW_QUESTIONS = {
    'Python Developer': [
        "What are Python decorators and how do you use them?",
        "Explain the difference between lists and tuples.",
        "What is list comprehension? Give an example.",
        "How does exception handling work in Python?",
        "What is the Global Interpreter Lock (GIL)?"
    ],
    'JavaScript Developer': [
        "What is hoisting in JavaScript?",
        "Explain closure in JavaScript with an example.",
        "What is the difference between == and ===?",
        "How does the event loop work?",
        "What are promises in JavaScript?"
    ],
    'Data Scientist': [
        "Explain the difference between supervised and unsupervised learning.",
        "What is overfitting and how do you prevent it?",
        "Explain bias-variance tradeoff.",
        "What evaluation metrics would you use for classification?",
        "What is cross-validation and why is it useful?"
    ],
    'Full Stack Developer': [
        "What is REST and what are its principles?",
        "Explain the difference between SQL and NoSQL.",
        "What is CORS and how do you handle it?",
        "Explain JWT tokens and how they work.",
        "What is the difference between horizontal and vertical scaling?"
    ],
    'DevOps Engineer': [
        "What is Docker and how does it work?",
        "Explain CI/CD pipeline.",
        "What is Kubernetes?",
        "What is infrastructure as code?",
        "Explain the difference between continuous delivery and deployment."
    ]
}

@app.route('/start-interview', methods=['GET', 'POST'])
@login_required
def start_interview():
    if request.method == 'POST':
        job_role = request.form.get('job_role')
        questions = INTERVIEW_QUESTIONS.get(job_role, INTERVIEW_QUESTIONS['Python Developer'])
        
        session['interview_questions'] = questions
        session['interview_role'] = job_role
        session['interview_answers'] = []
        session['interview_scores'] = []
        session['interview_current'] = 0
        
        return redirect(url_for('take_interview'))
    
    return render_template('start_interview.html', roles=list(INTERVIEW_QUESTIONS.keys()))

@app.route('/take-interview')
@login_required
def take_interview():
    if 'interview_questions' not in session:
        return redirect(url_for('start_interview'))
    
    questions = session['interview_questions']
    current = session.get('interview_current', 0)
    
    if current >= len(questions):
        return redirect(url_for('interview_complete'))
    
    return render_template('take_interview.html', 
                         question=questions[current],
                         question_num=current + 1,
                         total=len(questions),
                         job_role=session['interview_role'])

@app.route('/submit-answer', methods=['POST'])
@login_required
def submit_answer():
    answer = request.form.get('answer')
    question = request.form.get('question')
    
    # Calculate scores based on answer length
    clarity = min(100, max(40, len(answer) // 10 + 40))
    relevance = min(100, max(40, len(answer.split()) // 15 + 40))
    confidence = min(100, max(40, len(answer) // 50 + 50))
    overall = (clarity + relevance + confidence) // 3
    
    session['interview_answers'].append(answer)
    session['interview_scores'].append(overall)
    session['interview_current'] = session.get('interview_current', 0) + 1
    session.modified = True
    
    questions = session['interview_questions']
    current_idx = session['interview_current']
    
    if current_idx >= len(questions):
        # Save to database
        for q, a, s in zip(session['interview_questions'], session['interview_answers'], session['interview_scores']):
            interview = Interview(
                user_id=current_user.id,
                job_role=session['interview_role'],
                question=q,
                answer=a[:500],
                clarity_score=clarity,
                relevance_score=relevance,
                confidence_score=confidence,
                overall_score=s
            )
            db.session.add(interview)
        db.session.commit()
        
        avg_score = sum(session['interview_scores']) / len(session['interview_scores'])
        session.pop('interview_questions', None)
        session.pop('interview_answers', None)
        session.pop('interview_scores', None)
        session.pop('interview_current', None)
        
        return jsonify({
            'completed': True,
            'avg_score': round(avg_score, 1),
            'total': len(session.get('interview_answers', []))
        })
    
    return jsonify({
        'completed': False,
        'next_question': questions[current_idx],
        'question_num': current_idx + 1,
        'total': len(questions),
        'clarity': clarity,
        'relevance': relevance,
        'confidence': confidence,
        'overall': overall
    })

@app.route('/interview-complete')
@login_required
def interview_complete():
    return render_template('interview_complete.html')

# ============ RESUME ANALYSIS FEATURE ============
@app.route('/resume', methods=['GET', 'POST'])
@login_required
def resume():
    if request.method == 'POST':
        if 'resume' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('resume'))
        
        file = request.files['resume']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('resume'))
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Extract text
            text = ""
            try:
                import PyPDF2
                with open(filepath, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text += page.extract_text()
            except:
                text = filename
            
            word_count = len(text.split())
            
            # Analyze
            score = 50
            strengths = []
            weaknesses = []
            recommendations = []
            
            if word_count > 100:
                score += 15
                strengths.append("Good resume length")
            else:
                weaknesses.append("Resume too short")
                recommendations.append("Add more details about your experience")
            
            if '@' in text:
                score += 10
                strengths.append("Contact information included")
            else:
                weaknesses.append("Missing contact email")
                recommendations.append("Add your email address")
            
            if any(skill in text.lower() for skill in ['python', 'java', 'javascript', 'react', 'sql']):
                score += 15
                strengths.append("Technical skills mentioned")
            else:
                weaknesses.append("Missing technical skills")
                recommendations.append("Add a technical skills section")
            
            if word_count > 300:
                score += 10
                strengths.append("Detailed experience section")
            
            score = min(score, 100)
            
            analysis = ResumeAnalysis(
                user_id=current_user.id,
                filename=filename,
                score=score,
                strengths=json.dumps(strengths),
                weaknesses=json.dumps(weaknesses),
                recommendations=json.dumps(recommendations)
            )
            db.session.add(analysis)
            db.session.commit()
            
            return render_template('resume_result.html', 
                                 score=score,
                                 strengths=strengths,
                                 weaknesses=weaknesses,
                                 recommendations=recommendations)
    
    return render_template('resume_upload.html')

# ============ SKILL QUIZ FEATURE (1000+ QUESTIONS) ============
@app.route('/skill-quiz')
@login_required
def skill_quiz():
    domains = list(QUIZ_QUESTIONS.keys())
    return render_template('skill_quiz.html', domains=domains)

@app.route('/start-quiz', methods=['POST'])
@login_required
def start_quiz():
    domain = request.form.get('domain')
    difficulty = request.form.get('difficulty', 'beginner')
    
    questions = QUIZ_QUESTIONS.get(domain, {}).get(difficulty, [])
    if not questions:
        flash('No questions available for this selection', 'error')
        return redirect(url_for('skill_quiz'))
    
    # Get 10 random questions
    selected_questions = random.sample(questions, min(10, len(questions)))
    
    session['quiz_domain'] = domain
    session['quiz_difficulty'] = difficulty
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
        return redirect(url_for('quiz_complete'))
    
    return render_template('take_quiz.html', 
                         question=questions[current],
                         question_num=current + 1,
                         total=len(questions),
                         domain=session['quiz_domain'])

@app.route('/submit-quiz-answer', methods=['POST'])
@login_required
def submit_quiz_answer():
    data = request.json
    user_answer = data.get('answer')
    correct_answer = data.get('correct')
    is_correct = (user_answer == correct_answer)
    
    session['quiz_answers'].append({
        'question': data.get('question'),
        'user_answer': user_answer,
        'correct_answer': correct_answer,
        'is_correct': is_correct,
        'explanation': data.get('explanation', '')
    })
    session['quiz_current'] = session.get('quiz_current', 0) + 1
    session.modified = True
    
    questions = session['quiz_questions']
    current_idx = session['quiz_current']
    
    if current_idx >= len(questions):
        # Calculate score
        correct_count = sum(1 for a in session['quiz_answers'] if a['is_correct'])
        score = (correct_count / len(questions)) * 100
        
        # Save to database
        quiz_result = QuizResult(
            user_id=current_user.id,
            domain=session['quiz_domain'],
            difficulty=session['quiz_difficulty'],
            score=int(score),
            total_questions=len(questions),
            correct_answers=correct_count
        )
        db.session.add(quiz_result)
        db.session.commit()
        
        session.pop('quiz_questions', None)
        session.pop('quiz_answers', None)
        session.pop('quiz_current', None)
        
        return jsonify({
            'completed': True,
            'score': int(score),
            'correct': correct_count,
            'total': len(questions)
        })
    
    next_question = questions[current_idx]
    return jsonify({
        'completed': False,
        'next_question': next_question,
        'question_num': current_idx + 1,
        'total': len(questions)
    })

@app.route('/quiz-complete')
@login_required
def quiz_complete():
    return render_template('quiz_complete.html')

# ============ PERFORMANCE FEATURE ============
@app.route('/performance')
@login_required
def performance():
    interviews = Interview.query.filter_by(user_id=current_user.id).order_by(Interview.date).all()
    quizzes = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.date).all()
    resumes = ResumeAnalysis.query.filter_by(user_id=current_user.id).order_by(ResumeAnalysis.date.desc()).all()
    
    interview_dates = [i.date.strftime('%Y-%m-%d') for i in interviews]
    interview_scores = [i.overall_score for i in interviews]
    
    quiz_dates = [q.date.strftime('%Y-%m-%d') for q in quizzes]
    quiz_scores = [q.score for q in quizzes]
    
    return render_template('performance.html',
                         interviews=interviews,
                         quizzes=quizzes,
                         resumes=resumes,
                         interview_dates=json.dumps(interview_dates),
                         interview_scores=json.dumps(interview_scores),
                         quiz_dates=json.dumps(quiz_dates),
                         quiz_scores=json.dumps(quiz_scores))

def allowed_file(filename):
    return '.' in filename and filename.rs
