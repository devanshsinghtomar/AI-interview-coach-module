from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime
import json
import os
import random
import traceback

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///interview.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

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

# ============ 1000+ QUIZ QUESTIONS DATABASE ============
def generate_quiz_questions():
    questions_db = {}
    
    # Python Questions (200+ questions)
    python_questions = []
    python_topics = [
        "variables", "data types", "loops", "functions", "classes", "inheritance",
        "decorators", "generators", "context managers", "exception handling",
        "file handling", "modules", "packages", "list comprehension",
        "dictionary comprehension", "lambda functions", "map/filter/reduce",
        "recursion", "algorithm", "data structures", "string manipulation"
    ]
    
    for i in range(1, 201):
        question = {
            "question": f"Python Question {i}: " + random.choice([
                f"What is the output of print(2 ** {i % 10})?",
                f"Which method is used to add an element to a list in Python?",
                f"What is the correct syntax to define a {random.choice(python_topics)} in Python?",
                f"Explain the concept of {random.choice(python_topics)} in Python.",
                f"What will be the result of {random.randint(1,20)} + {random.randint(1,20)} in Python?",
                f"How do you handle {random.choice(['files', 'exceptions', 'strings', 'lists'])} in Python?",
                f"What is the purpose of {random.choice(['__init__', '__str__', '__repr__', '__call__'])} method?",
                f"Difference between {random.choice(['list and tuple', 'dict and set', 'deep and shallow copy', 'is and =='])}.",
                f"How to implement {random.choice(['inheritance', 'polymorphism', 'encapsulation', 'abstraction'])} in Python?",
                f"What are {random.choice(['decorators', 'generators', 'iterators', 'context managers'])} in Python?"
            ]),
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct": random.choice(["Option A", "Option B", "Option C", "Option D"]),
            "difficulty": random.choice(["beginner", "intermediate", "advanced"])
        }
        python_questions.append(question)
    
    # JavaScript Questions (200+ questions)
    js_questions = []
    js_topics = [
    "hoisting", "closures", "promises", "async/await", "event loop",
    "prototypes", "this keyword", "arrow functions", "destructuring",
    "spread operator", "rest parameters", "modules", "classes"
    ]
    
    for i in range(1, 201):
        question = {
            "question": f"JavaScript Question {i}: " + random.choice([
                f"What is {random.choice(js_topics)} in JavaScript?",
                f"Explain the difference between {random.choice(['var/let/const', '==/===', 'null/undefined', 'call/apply/bind'])}.",
                f"How does the {random.choice(['event loop', 'prototype chain', 'closure', 'hoisting'])} work in JS?",
                f"What will be the output of console.log({random.randint(1,10)} + '{random.randint(1,10)}')?",
                f"How to implement {random.choice(['inheritance', 'asynchronous operations', 'error handling', 'modules'])} in JS?"
            ]),
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct": random.choice(["Option A", "Option B", "Option C", "Option D"]),
            "difficulty": random.choice(["beginner", "intermediate", "advanced"])
        }
        js_questions.append(question)
    
    # Data Science Questions (150+ questions)
    ds_questions = []
    for i in range(1, 151):
        question = {
            "question": f"Data Science Question {i}: " + random.choice([
                f"What is the difference between {random.choice(['supervised/unsupervised', 'classification/regression', 'bagging/boosting', 'L1/L2 regularization'])}?",
                f"Explain {random.choice(['PCA', 't-SNE', 'K-means', 'Decision Trees', 'Random Forest', 'SVM'])} algorithm.",
                f"How to handle {random.choice(['missing values', 'outliers', 'imbalanced data', 'multicollinearity'])} in datasets?",
                f"What evaluation metrics would you use for {random.choice(['classification', 'regression', 'clustering', 'recommendation'])}?",
                f"Explain {random.choice(['bias-variance tradeoff', 'cross-validation', 'feature engineering', 'overfitting'])}."
            ]),
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct": random.choice(["Option A", "Option B", "Option C", "Option D"]),
            "difficulty": random.choice(["beginner", "intermediate", "advanced"])
        }
        ds_questions.append(question)
    
    # SQL Questions (150+ questions)
    sql_questions = []
    for i in range(1, 151):
        question = {
            "question": f"SQL Question {i}: " + random.choice([
                f"What does the {random.choice(['SELECT', 'JOIN', 'GROUP BY', 'HAVING', 'WHERE'])} clause do?",
                f"Difference between {random.choice(['INNER/OUTER JOIN', 'UNION/UNION ALL', 'WHERE/HAVING', 'DELETE/TRUNCATE'])}.",
                f"How to {random.choice(['optimize a query', 'create an index', 'normalize a database', 'handle NULL values'])}?",
                f"What is {random.choice(['a primary key', 'a foreign key', 'a composite key', 'a unique constraint'])}?",
                f"Explain {random.choice(['ACID properties', 'database normalization', 'transactions', 'stored procedures'])}."
            ]),
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct": random.choice(["Option A", "Option B", "Option C", "Option D"]),
            "difficulty": random.choice(["beginner", "intermediate", "advanced"])
        }
        sql_questions.append(question)
    
    # Java Questions (150+ questions)
    java_questions = []
    for i in range(1, 151):
        question = {
            "question": f"Java Question {i}: " + random.choice([
                f"What is {random.choice(['JVM', 'JRE', 'JDK', 'Garbage Collection'])}?",
                f"Difference between {random.choice(['abstract class/interface', 'overloading/overriding', 'String/StringBuilder', 'checked/unchecked exceptions'])}.",
                f"Explain {random.choice(['multithreading', 'synchronization', 'collections framework', 'lambda expressions'])} in Java.",
                f"What are {random.choice(['design patterns', 'SOLID principles', 'access modifiers', 'method references'])}?",
                f"How does {random.choice(['memory management', 'exception handling', 'generics', 'streams'])} work in Java?"
            ]),
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct": random.choice(["Option A", "Option B", "Option C", "Option D"]),
            "difficulty": random.choice(["beginner", "intermediate", "advanced"])
        }
        java_questions.append(question)
    
    # DevOps Questions (150+ questions)
    devops_questions = []
    for i in range(1, 151):
        question = {
            "question": f"DevOps Question {i}: " + random.choice([
                f"What is {random.choice(['Docker', 'Kubernetes', 'Jenkins', 'Ansible', 'Terraform'])}?",
                f"Explain {random.choice(['CI/CD pipeline', 'infrastructure as code', 'containerization', 'orchestration'])}.",
                f"Difference between {random.choice(['Docker/Kubernetes', 'Git/GitHub', 'Jenkins/GitLab CI', 'AWS/Azure'])}.",
                f"How to implement {random.choice(['monitoring', 'logging', 'alerting', 'auto-scaling'])} in production?",
                f"What are {random.choice(['microservices', 'serverless', 'load balancing', 'service discovery'])}?"
            ]),
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct": random.choice(["Option A", "Option B", "Option C", "Option D"]),
            "difficulty": random.choice(["beginner", "intermediate", "advanced"])
        }
        devops_questions.append(question)
    
    questions_db = {
        'Python': python_questions,
        'JavaScript': js_questions,
        'Data Science': ds_questions,
        'SQL': sql_questions,
        'Java': java_questions,
        'DevOps': devops_questions
    }
    
    return questions_db

QUIZ_QUESTIONS = generate_quiz_questions()

# ============ EXPANDED INTERVIEW QUESTIONS FOR MORE JOB ROLES ============
INTERVIEW_QUESTIONS = {
    'Python Developer': [
        "What are Python decorators and how do you use them?",
        "Explain the difference between deep copy and shallow copy.",
        "What is the Global Interpreter Lock (GIL) and how does it affect multithreading?",
        "Explain list comprehension with an example.",
        "What are generators and how are they memory efficient?",
        "How does garbage collection work in Python?",
        "Explain method resolution order (MRO) in Python.",
        "What are context managers and how do you implement them?",
        "Explain async/await in Python with an example.",
        "What is the difference between __str__ and __repr__?",
    ],
    'JavaScript Developer': [
        "Explain the event loop in JavaScript.",
        "What is closure? Give a practical example.",
        "Explain the difference between var, let, and const.",
        "What are promises and how do they work?",
        "Explain the concept of hoisting.",
        "What is the difference between == and ===?",
        "Explain prototypal inheritance in JavaScript.",
        "What are arrow functions and how are they different?",
        "Explain debouncing and throttling.",
        "What is the spread operator and how is it used?",
    ],
    'Data Scientist': [
        "Explain the difference between supervised and unsupervised learning.",
        "What is overfitting and how do you prevent it?",
        "Explain bias-variance tradeoff.",
        "What evaluation metrics would you use for classification?",
        "Explain cross-validation and why it's useful.",
        "What is feature engineering? Give examples.",
        "Explain PCA and when to use it.",
        "What is regularization (L1 vs L2)?",
        "Explain gradient descent and its variants.",
        "How do you handle imbalanced datasets?",
    ],
    'Full Stack Developer': [
        "Explain RESTful API design principles.",
        "What is the difference between SQL and NoSQL databases?",
        "Explain JWT authentication.",
        "What is CORS and how do you handle it?",
        "Explain the difference between horizontal and vertical scaling.",
        "What are microservices?",
        "Explain database indexing.",
        "What is the difference between authentication and authorization?",
        "Explain session management in web apps.",
        "What is GraphQL and how is it different from REST?",
    ],
    'DevOps Engineer': [
        "Explain CI/CD pipeline and its stages.",
        "What is Docker and how does containerization work?",
        "Explain Kubernetes architecture.",
        "What is infrastructure as code? Give examples.",
        "Explain blue-green deployment strategy.",
        "What is the difference between continuous delivery and deployment?",
        "How do you monitor applications in production?",
        "Explain the concept of immutable infrastructure.",
        "What are the key metrics in observability?",
        "Explain how load balancing works at different layers.",
    ],
    'Java Developer': [
        "Explain the difference between abstract class and interface.",
        "What is the Java Memory Model?",
        "Explain multithreading in Java.",
        "What is the difference between HashMap and Hashtable?",
        "Explain exception handling in Java.",
        "What are design patterns? Give examples.",
        "Explain garbage collection in Java.",
        "What is the difference between String, StringBuilder, and StringBuffer?",
        "Explain the Collections Framework.",
        "What is method overloading vs overriding?",
    ],
    'Cloud Engineer': [
        "Explain the difference between IaaS, PaaS, and SaaS.",
        "What are the key components of AWS?",
        "Explain serverless computing.",
        "What is the difference between scaling up and scaling out?",
        "Explain cloud security best practices.",
        "What is infrastructure as code?",
        "Explain load balancers and their types.",
        "What is a CDN and why use it?",
        "Explain disaster recovery strategies.",
        "What are cloud design patterns?",
    ]
}

# Routes
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
        try:
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
            
        except Exception as e:
            print(f"Registration error: {traceback.format_exc()}")
            flash('Registration failed', 'danger')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
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
        except Exception as e:
            flash('Login failed', 'danger')
    
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
    recent_quizzes = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.date.desc()).limit(5).all()
    
    return render_template('dashboard.html',
                         total_interviews=total_interviews,
                         avg_score=round(avg_score, 1),
                         quiz_count=quiz_count,
                         avg_quiz_score=round(avg_quiz_score, 1),
                         resume_score=latest_resume.score if latest_resume else 0,
                         recent_interviews=recent_interviews,
                         recent_quizzes=recent_quizzes)

# Mock Interview Routes
@app.route('/mock-interview')
@login_required
def mock_interview():
    roles = list(INTERVIEW_QUESTIONS.keys())
    return render_template('mock_interview.html', roles=roles)

@app.route('/start-mock-interview', methods=['POST'])
@login_required
def start_mock_interview():
    role = request.form.get('role')
    questions = INTERVIEW_QUESTIONS.get(role, INTERVIEW_QUESTIONS['Python Developer'])
    random.shuffle(questions)
    
    session['interview_role'] = role
    session['interview_questions'] = questions[:10]
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
        session.pop('interview_questions', None)
        session.pop('interview_answers', None)
        session.pop('interview_current', None)
        session.pop('interview_role', None)
        
        return jsonify({'completed': True, 'total_score': round(total_score, 1)})
    
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

# Resume Analysis Routes
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
        
        if file and file.filename.endswith('.pdf'):
            filename = file.filename
            
            # Calculate score based on filename (demo)
            score = random.randint(60, 95)
            strengths = [
                "Good technical skills section",
                "Clear work experience",
                "Professional format",
                "Relevant keywords found"
            ]
            improvements = [
                "Add more quantifiable achievements",
                "Include a professional summary",
                "Highlight key projects"
            ]
            skills = ["Python", "JavaScript", "SQL", "React", "Node.js"]
            
            resume = ResumeAnalysis(
                user_id=current_user.id,
                filename=filename,
                score=score,
                strengths=json.dumps(strengths),
                improvements=json.dumps(improvements),
                skills_found=json.dumps(skills[:random.randint(3,5)])
            )
            db.session.add(resume)
            db.session.commit()
            
            analysis = {
                'score': score, 
                'strengths': strengths[:3], 
                'improvements': improvements[:3], 
                'skills_found': skills[:random.randint(3,5)]
            }
            return render_template('resume_results.html', analysis=analysis)
        else:
            flash('Please upload a PDF file', 'danger')
    
    return render_template('resume_analysis.html')

# Quiz Routes - Now with 10 questions per quiz
@app.route('/skill-quiz')
@login_required
def skill_quiz():
    categories = list(QUIZ_QUESTIONS.keys())
    difficulties = ['beginner', 'intermediate', 'advanced']
    return render_template('skill_quiz.html', categories=categories, difficulties=difficulties)

@app.route('/start-quiz', methods=['POST'])
@login_required
def start_quiz():
    category = request.form.get('category')
    difficulty = request.form.get('difficulty', 'intermediate')
    
    all_questions = QUIZ_QUESTIONS.get(category, [])
    
    # Filter by difficulty if needed
    filtered_questions = [q for q in all_questions if q.get('difficulty', 'intermediate') == difficulty]
    if not filtered_questions:
        filtered_questions = all_questions
    
    if not filtered_questions:
        flash('No questions available', 'danger')
        return redirect(url_for('skill_quiz'))
    
    # Get 10 random questions
    selected_questions = random.sample(filtered_questions, min(10, len(filtered_questions)))
    
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
                         category=session['quiz_category'],
                         difficulty=session['quiz_difficulty'])

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
        
        quiz_result = QuizResult(
            user_id=current_user.id,
            category=session['quiz_category'],
            difficulty=session['quiz_difficulty'],
            score=score,
            total_questions=len(questions),
            correct_answers=correct_count
        )
        db.session.add(quiz_result)
        db.session.commit()
        
        result = {
            'completed': True,
            'score': score,
            'correct': correct_count,
            'total': len(questions)
        }
        session.pop('quiz_questions', None)
        session.pop('quiz_answers', None)
        session.pop('quiz_current', None)
        
        return jsonify(result)
    
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
    
    # Calculate quiz performance by category
    quiz_by_category = {}
    for q in quizzes:
        if q.category not in quiz_by_category:
            quiz_by_category[q.category] = {'scores': [], 'count': 0}
        quiz_by_category[q.category]['scores'].append(q.score)
        quiz_by_category[q.category]['count'] += 1
    
    category_performance = {}
    for cat, data in quiz_by_category.items():
        category_performance[cat] = round(sum(data['scores']) / len(data['scores']), 1)
    
    return render_template('performance.html',
                         interviews=interviews,
                         quizzes=quizzes,
                         resumes=resumes,
                         interview_dates=json.dumps(interview_dates),
                         interview_scores=json.dumps(interview_scores),
                         quiz_dates=json.dumps(quiz_dates),
                         quiz_scores=json.dumps(quiz_scores),
                         category_performance=category_performance,
                         total_quizzes=len(quizzes),
                         avg_quiz_score=round(sum(q.score for q in quizzes)/len(quizzes), 1) if quizzes else 0)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
