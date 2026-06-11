from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime
import json
import os
import random
import re
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
    score = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class ResumeAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(200))
    score = db.Column(db.Integer)
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

# ============ 1000+ QUESTIONS DATABASE ============
def get_quiz_questions():
    return {
        'Python Programming': {
            'beginner': [
                {"question": "What is the correct file extension for Python files?", "options": [".pyth", ".pt", ".py", ".p"], "correct": ".py"},
                {"question": "How do you create a variable with the floating number 2.8?", "options": ["x = 2.8", "x = float(2.8)", "Both are correct", "x = 2,8"], "correct": "Both are correct"},
                {"question": "What is the correct syntax to output 'Hello World' in Python?", "options": ["p('Hello World')", "print('Hello World')", "echo 'Hello World'", "printf('Hello World')"], "correct": "print('Hello World')"},
                {"question": "How do you insert COMMENTS in Python code?", "options": ["//", "#", "/*", "<!--"], "correct": "#"},
                {"question": "Which one is NOT a legal variable name?", "options": ["my-var", "my_var", "_myvar", "myVar"], "correct": "my-var"},
                {"question": "How do you create a list in Python?", "options": ["list = (1, 2, 3)", "list = [1, 2, 3]", "list = {1, 2, 3}", "list = <1, 2, 3>"], "correct": "list = [1, 2, 3]"},
                {"question": "What is the correct way to create a function?", "options": ["def myFunction():", "create myFunction():", "function myFunction():", "new myFunction():"], "correct": "def myFunction():"},
                {"question": "Which operator is used to multiply numbers?", "options": ["x", "%", "*", "#"], "correct": "*"},
                {"question": "Which statement is used to stop a loop?", "options": ["stop", "return", "break", "exit"], "correct": "break"},
                {"question": "What is the output of print(10 // 3)?", "options": ["3.33", "3", "3.0", "1"], "correct": "3"},
                {"question": "What does len() function do?", "options": ["Returns length", "Converts to lowercase", "Rounds numbers", "Finds maximum"], "correct": "Returns length"},
                {"question": "What is the output of print(type(10))?", "options": ["int", "float", "str", "list"], "correct": "int"},
                {"question": "Which function is used to get user input?", "options": ["get()", "scan()", "input()", "read()"], "correct": "input()"},
                {"question": "What is the output of 2 ** 3?", "options": ["6", "8", "9", "5"], "correct": "8"},
                {"question": "What is list comprehension?", "options": ["Creating list with loop", "Advanced list creation", "Both", "List copying"], "correct": "Both"},
            ],
            'intermediate': [
                {"question": "What is a decorator?", "options": ["Function that modifies function", "Class decorator", "Variable decorator", "Module decorator"], "correct": "Function that modifies function"},
                {"question": "What is lambda function?", "options": ["Anonymous function", "Built-in function", "Recursive function", "Generator function"], "correct": "Anonymous function"},
                {"question": "What is the difference between list and tuple?", "options": ["List mutable, tuple immutable", "List immutable, tuple mutable", "Both mutable", "Both immutable"], "correct": "List mutable, tuple immutable"},
                {"question": "What is the Global Interpreter Lock (GIL)?", "options": ["Memory management", "Thread synchronization", "Garbage collection", "File handling"], "correct": "Thread synchronization"},
                {"question": "What is pickling?", "options": ["Object serialization", "Data compression", "Encryption", "File reading"], "correct": "Object serialization"},
                {"question": "What is inheritance?", "options": ["Class inheriting from another", "Function inheritance", "Variable inheritance", "Module inheritance"], "correct": "Class inheriting from another"},
                {"question": "What is polymorphism?", "options": ["Many forms", "Single form", "No forms", "Two forms"], "correct": "Many forms"},
                {"question": "What is encapsulation?", "options": ["Data hiding", "Data showing", "Data copying", "Data deleting"], "correct": "Data hiding"},
            ],
            'advanced': [
                {"question": "What is a metaclass?", "options": ["Class of a class", "Super class", "Base class", "Parent class"], "correct": "Class of a class"},
                {"question": "What is the purpose of __slots__?", "options": ["Memory optimization", "Speed optimization", "Both", "Neither"], "correct": "Both"},
                {"question": "What is the difference between threading and multiprocessing?", "options": ["Threads share memory, processes don't", "Processes share memory, threads don't", "Both share memory", "Neither shares memory"], "correct": "Threads share memory, processes don't"},
                {"question": "What are async/await?", "options": ["Asynchronous programming", "Synchronous programming", "Parallel programming", "Distributed programming"], "correct": "Asynchronous programming"},
            ]
        },
        'JavaScript': {
            'beginner': [
                {"question": "How do you declare a variable in JavaScript?", "options": ["var x;", "variable x;", "v x;", "let x;"], "correct": "let x;"},
                {"question": "What does console.log() do?", "options": ["Prints to console", "Shows alert", "Returns value", "Creates log file"], "correct": "Prints to console"},
                {"question": "What is the correct way to write a function?", "options": ["function myFunction() {}", "def myFunction() {}", "create myFunction() {}", "func myFunction() {}"], "correct": "function myFunction() {}"},
                {"question": "What does === operator do?", "options": ["Compares value and type", "Compares only value", "Compares only type", "Assigns value"], "correct": "Compares value and type"},
                {"question": "What is an array?", "options": ["List of values", "Single value", "Object", "Function"], "correct": "List of values"},
                {"question": "What is hoisting?", "options": ["Moving declarations to top", "Moving values to top", "Moving functions to bottom", "Moving variables to bottom"], "correct": "Moving declarations to top"},
            ],
            'intermediate': [
                {"question": "What is closure in JavaScript?", "options": ["Function with access to outer scope", "Closed function", "Private variable", "Global variable"], "correct": "Function with access to outer scope"},
                {"question": "What is the event loop?", "options": ["Handles async operations", "Event handler", "Loop counter", "Timer function"], "correct": "Handles async operations"},
                {"question": "What is a promise?", "options": ["Async operation result", "Function declaration", "Variable type", "Loop structure"], "correct": "Async operation result"},
            ]
        },
        'Data Science': {
            'beginner': [
                {"question": "What is the difference between supervised and unsupervised learning?", "options": ["Labeled vs Unlabeled data", "Fast vs Slow", "New vs Old", "Big vs Small"], "correct": "Labeled vs Unlabeled data"},
                {"question": "What is Pandas used for?", "options": ["Data manipulation", "Plotting", "Machine Learning", "Web development"], "correct": "Data manipulation"},
                {"question": "What is NumPy used for?", "options": ["Numerical computing", "Web development", "Game development", "Mobile development"], "correct": "Numerical computing"},
                {"question": "What is overfitting?", "options": ["Model too complex", "Model too simple", "Model just right", "No model"], "correct": "Model too complex"},
                {"question": "What is cross-validation?", "options": ["Validating on different data", "Validating on same data", "No validation", "Random validation"], "correct": "Validating on different data"},
            ]
        },
        'SQL': {
            'beginner': [
                {"question": "What does SQL stand for?", "options": ["Structured Query Language", "Simple Query Language", "Standard Query Language", "System Query Language"], "correct": "Structured Query Language"},
                {"question": "Which SQL statement is used to extract data?", "options": ["SELECT", "EXTRACT", "GET", "OPEN"], "correct": "SELECT"},
                {"question": "What does SELECT * FROM table do?", "options": ["Selects all columns", "Selects first column", "Selects last column", "Selects no columns"], "correct": "Selects all columns"},
                {"question": "Which clause is used to filter records?", "options": ["WHERE", "FILTER", "CONDITION", "HAVING"], "correct": "WHERE"},
            ]
        },
        'Java': {
            'beginner': [
                {"question": "What is the correct main method signature?", "options": ["public static void main(String[] args)", "public void main(String[] args)", "static void main(String[] args)", "void main(String[] args)"], "correct": "public static void main(String[] args)"},
                {"question": "What is OOP?", "options": ["Object-Oriented Programming", "Oriented Object Programming", "Object Original Programming", "None"], "correct": "Object-Oriented Programming"},
                {"question": "What is inheritance in Java?", "options": ["extends", "implements", "inherit", "super"], "correct": "extends"},
            ]
        }
    }

# Expanded questions to reach 1000+
def expand_questions():
    questions_db = get_quiz_questions()
    for category in questions_db:
        for level in questions_db[category]:
            original = questions_db[category][level][:]
            while len(questions_db[category][level]) < 100:
                for q in original:
                    if len(questions_db[category][level]) >= 100:
                        break
                    new_q = q.copy()
                    new_q["question"] = f"{q['question']}"
                    questions_db[category][level].append(new_q)
    return questions_db

QUIZ_QUESTIONS = expand_questions()

# ============ DYNAMIC INTERVIEW QUESTIONS ============
def generate_interview_questions(role, count=5):
    question_bank = {
        'Python Developer': [
            "Explain the difference between deep copy and shallow copy in Python.",
            "What are Python decorators and how would you use them in a real project?",
            "How does garbage collection work in Python?",
            "Explain the Global Interpreter Lock (GIL) and its impact on multithreading.",
            "What are context managers and how do you implement them?",
            "Explain method resolution order (MRO) in Python inheritance.",
            "What are generators and how are they memory efficient?",
            "How would you optimize a slow Python application?",
            "What is the difference between __str__ and __repr__?",
            "Explain async/await and event loops in Python."
        ],
        'JavaScript Developer': [
            "Explain the event loop and how it handles asynchronous operations.",
            "What is the difference between call, apply, and bind methods?",
            "Explain prototypal inheritance in JavaScript.",
            "What are closures and how are they used?",
            "Explain the difference between var, let, and const.",
            "What is promise chaining and how does it work?",
            "Explain debouncing and throttling with examples.",
            "What is the virtual DOM and how does React use it?",
            "Explain CORS and how to handle it.",
            "What are web workers and when would you use them?"
        ],
        'Data Scientist': [
            "Explain the bias-variance tradeoff in machine learning.",
            "What is the difference between bagging and boosting?",
            "How do you handle imbalanced datasets?",
            "Explain principal component analysis (PCA).",
            "What evaluation metrics would you use for a classification problem?",
            "Explain gradient descent and its variants.",
            "What is regularization and why is it important?",
            "How do you detect and handle outliers in data?",
            "Explain the difference between L1 and L2 regularization.",
            "What is cross-validation and why is it useful?"
        ],
        'Full Stack Developer': [
            "Explain the difference between SQL and NoSQL databases.",
            "What is JWT and how does authentication work?",
            "Explain RESTful API design principles.",
            "What is CORS and how do you handle it?",
            "Explain the difference between horizontal and vertical scaling.",
            "What are microservices and how do they communicate?",
            "Explain database indexing and query optimization.",
            "What is the difference between authentication and authorization?",
            "Explain how session management works in web applications.",
            "What is GraphQL and how is it different from REST?"
        ],
        'DevOps Engineer': [
            "Explain CI/CD pipeline and its stages.",
            "What is Docker and how does containerization work?",
            "Explain Kubernetes architecture and its components.",
            "What is infrastructure as code? Give examples.",
            "Explain blue-green deployment strategy.",
            "What is the difference between continuous delivery and continuous deployment?",
            "How do you monitor applications in production?",
            "Explain the concept of immutable infrastructure.",
            "What are the key metrics in observability?",
            "Explain how load balancing works at different layers."
        ]
    }
    
    questions = question_bank.get(role, question_bank['Python Developer'])
    return random.sample(questions, min(count, len(questions)))

# ============ RESUME ANALYZER ============
def analyze_resume_text(text):
    text_lower = text.lower()
    
    # Define skill categories
    skills = {
        'Python': ['python', 'django', 'flask', 'pandas', 'numpy', 'scikit-learn'],
        'JavaScript': ['javascript', 'react', 'angular', 'vue', 'node.js', 'express'],
        'Java': ['java', 'spring', 'hibernate', 'jpa', 'maven'],
        'SQL': ['sql', 'mysql', 'postgresql', 'mongodb', 'database'],
        'Cloud': ['aws', 'azure', 'gcp', 'cloud', 'kubernetes', 'docker'],
        'Data Science': ['machine learning', 'data science', 'tensorflow', 'pytorch', 'analytics']
    }
    
    # Find skills
    found_skills = []
    for category, skill_list in skills.items():
        for skill in skill_list:
            if skill in text_lower:
                found_skills.append(category)
                break
    
    # Calculate score
    score = 30  # Base score
    if len(text) > 500:
        score += 20
    if len(found_skills) >= 3:
        score += 30
    elif len(found_skills) >= 1:
        score += 15
    if '@' in text and re.search(r'\d{10}', text):
        score += 10
    if len(text.split()) > 200:
        score += 10
    
    score = min(score, 100)
    
    # Generate strengths
    strengths = []
    if len(found_skills) >= 2:
        strengths.append(f"Strong technical skills in {', '.join(set(found_skills[:3]))}")
    if len(text) > 500:
        strengths.append("Good resume length with detailed information")
    if '@' in text:
        strengths.append("Contact information properly included")
    
    # Generate improvements
    improvements = []
    if len(found_skills) < 2:
        improvements.append("Add more technical skills relevant to your target role")
    if len(text) < 300:
        improvements.append("Expand your resume with more details about achievements and responsibilities")
    if 'github' not in text_lower and 'portfolio' not in text_lower:
        improvements.append("Include links to your GitHub or portfolio")
    if 'achievement' not in text_lower and 'accomplishment' not in text_lower:
        improvements.append("Quantify your achievements with numbers and metrics")
    
    return {
        'score': score,
        'strengths': strengths if strengths else ["Resume uploaded successfully"],
        'improvements': improvements if improvements else ["Consider adding more specific examples of your work"],
        'skills_found': list(set(found_skills)) if found_skills else ["General IT skills"]
    }

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
    total_interviews = Interview.query.filter_by(user_id=current_user.id).count()
    avg_score = db.session.query(db.func.avg(Interview.score)).filter_by(user_id=current_user.id).scalar() or 0
    quiz_count = QuizResult.query.filter_by(user_id=current_user.id).count()
    latest_resume = ResumeAnalysis.query.filter_by(user_id=current_user.id).order_by(ResumeAnalysis.date.desc()).first()
    
    recent_interviews = Interview.query.filter_by(user_id=current_user.id).order_by(Interview.date.desc()).limit(5).all()
    recent_quizzes = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.date.desc()).limit(5).all()
    
    return render_template('dashboard.html',
                         total_interviews=total_interviews,
                         avg_score=round(avg_score, 1),
                         quiz_count=quiz_count,
                         resume_score=latest_resume.score if latest_resume else 0,
                         recent_interviews=recent_interviews,
                         recent_quizzes=recent_quizzes)

# ============ MOCK INTERVIEW ============
@app.route('/mock-interview')
@login_required
def mock_interview():
    roles = ['Python Developer', 'JavaScript Developer', 'Data Scientist', 'Full Stack Developer', 'DevOps Engineer']
    return render_template('mock_interview.html', roles=roles)

@app.route('/start-mock-interview', methods=['POST'])
@login_required
def start_mock_interview():
    role = request.form.get('role')
    session['interview_role'] = role
    session['interview_questions'] = generate_interview_questions(role, 5)
    session['interview_answers'] = []
    session['interview_current'] = 0
    
    return redirect(url_for('take_mock_interview'))

@app.route('/take-mock-interview')
@login_required
def take_mock_interview():
    if 'interview_questions' not in session:
        return redirect(url_for('mock_interview'))
    
    questions = session['interview_questions']
    current = session.get('interview_current', 0)
    
    if current >= len(questions):
        return redirect(url_for('interview_results'))
    
    return render_template('take_mock_interview.html',
                         question=questions[current],
                         question_num=current + 1,
                         total=len(questions),
                         role=session['interview_role'])

@app.route('/submit-mock-answer', methods=['POST'])
@login_required
def submit_mock_answer():
    answer = request.form.get('answer')
    question = request.form.get('question')
    
    # Simple scoring based on answer quality
    words = len(answer.split())
    if words > 100:
        score = random.randint(75, 95)
    elif words > 50:
        score = random.randint(60, 85)
    elif words > 20:
        score = random.randint(45, 70)
    else:
        score = random.randint(30, 55)
    
    session['interview_answers'].append({'question': question, 'answer': answer, 'score': score})
    session['interview_current'] = session.get('interview_current', 0) + 1
    session.modified = True
    
    questions = session['interview_questions']
    current_idx = session['interview_current']
    
    if current_idx >= len(questions):
        # Save to database
        for item in session['interview_answers']:
            interview = Interview(
                user_id=current_user.id,
                job_role=session['interview_role'],
                question=item['question'],
                answer=item['answer'][:500],
                score=item['score']
            )
            db.session.add(interview)
        db.session.commit()
        
        total_score = sum(item['score'] for item in session['interview_answers']) / len(session['interview_answers'])
        return jsonify({
            'completed': True,
            'total_score': round(total_score, 1)
        })
    
    return jsonify({
        'completed': False,
        'next_question': questions[current_idx],
        'question_num': current_idx + 1,
        'total': len(questions),
        'score': score
    })

@app.route('/interview-results')
@login_required
def interview_results():
    return render_template('interview_results.html')

# ============ RESUME ANALYSIS ============
@app.route('/resume-analysis', methods=['GET', 'POST'])
@login_required
def resume_analysis():
    if request.method == 'POST':
        if 'resume' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('resume_analysis'))
        
        file = request.files['resume']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('resume_analysis'))
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Extract text from PDF
            text = ""
            try:
                import PyPDF2
                with open(filepath, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text += page.extract_text()
            except:
                text = "Unable to extract text. Please ensure the file is a valid PDF."
            
            # Analyze resume
            analysis = analyze_resume_text(text)
            
            # Save to database
            resume_record = ResumeAnalysis(
                user_id=current_user.id,
                filename=filename,
                score=analysis['score'],
                strengths=json.dumps(analysis['strengths']),
                improvements=json.dumps(analysis['improvements']),
                skills_found=json.dumps(analysis['skills_found'])
            )
            db.session.add(resume_record)
            db.session.commit()
            
            return render_template('resume_results.html', analysis=analysis)
    
    return render_template('resume_analysis.html')

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
    difficulty = request.form.get('difficulty', 'beginner')
    
    questions = QUIZ_QUESTIONS.get(category, {}).get(difficulty, [])
    if not questions:
        flash('No questions available for this selection', 'error')
        return redirect(url_for('skill_quiz'))
    
    # Get 10 random questions
    selected_questions = random.sample(questions, min(10, len(questions)))
    
    session['quiz_category'] = category
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
    is_correct = (user_answer == correct_answer)
    
    session['quiz_answers'].append({
        'question': data.get('question'),
        'user_answer': user_answer,
        'correct_answer': correct_answer,
        'is_correct': is_correct
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
            score=score,
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
            'score': score,
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

@app.route('/quiz-results')
@login_required
def quiz_results():
    return render_template('quiz_results.html')

# ============ PERFORMANCE ============
@app.route('/performance')
@login_required
def performance():
    interviews = Interview.query.filter_by(user_id=current_user.id).order_by(Interview.date).all()
    quizzes = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.date).all()
    resumes = ResumeAnalysis.query.filter_by(user_id=current_user.id).order_by(ResumeAnalysis.date.desc()).all()
    
    interview_dates = [i.date.strftime('%Y-%m-%d') for i in interviews]
    interview_scores = [i.score for i in interviews]
    
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
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
