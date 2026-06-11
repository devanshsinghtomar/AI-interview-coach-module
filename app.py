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

# ============ INTERVIEW QUESTIONS ============
INTERVIEW_QUESTIONS = {
    'Python Developer': [
        "What is the difference between a list and a tuple in Python?",
        "What is a decorator in Python?",
        "Explain the Global Interpreter Lock (GIL).",
        "What is list comprehension? Give an example.",
        "How does exception handling work in Python?"
    ],
    'JavaScript Developer': [
        "What is closure in JavaScript?",
        "Explain the difference between == and ===.",
        "What is hoisting in JavaScript?",
        "What are promises in JavaScript?",
        "Explain the event loop in JavaScript."
    ],
    'Data Scientist': [
        "What is the difference between supervised and unsupervised learning?",
        "What is overfitting and how do you prevent it?",
        "Explain bias-variance tradeoff.",
        "What evaluation metrics would you use for classification?",
        "Explain cross-validation."
    ],
    'Full Stack Developer': [
        "What is REST API?",
        "Difference between SQL and NoSQL?",
        "What is JWT authentication?",
        "Explain CORS.",
        "What is the difference between authentication and authorization?"
    ],
    'DevOps Engineer': [
        "What is Docker?",
        "Explain CI/CD pipeline.",
        "What is Kubernetes?",
        "What is infrastructure as code?",
        "Explain blue-green deployment."
    ],
    'Java Developer': [
        "Difference between abstract class and interface?",
        "What is multithreading in Java?",
        "Explain garbage collection in Java.",
        "What is Spring Boot?",
        "Difference between HashMap and Hashtable?"
    ],
    'Cloud Engineer': [
        "What are the cloud service models?",
        "Explain serverless computing.",
        "What is the difference between scaling up and scaling out?",
        "What is Infrastructure as Code?",
        "Explain load balancer types."
    ],
    'Machine Learning Engineer': [
        "Explain the difference between AI, ML, and DL.",
        "What is the difference between classification and regression?",
        "Explain neural networks.",
        "What is transfer learning?",
        "Explain the confusion matrix."
    ]
}

# ============ QUIZ QUESTIONS ============
QUIZ_DATA = {
    'Python': {
        'questions': [
            {"q": "What is the correct way to create a function in Python?", "options": ["def myFunction():", "function myFunction():", "create myFunction():", "func myFunction():"], "correct": "def myFunction():", "exp": "Functions use the 'def' keyword."},
            {"q": "What does the 'len()' function do?", "options": ["Returns length", "Converts to lowercase", "Rounds a number", "Finds maximum"], "correct": "Returns length", "exp": "len() returns the number of items."},
            {"q": "Which operator is used for exponentiation?", "options": ["**", "^", "exp()", "&&"], "correct": "**", "exp": "** is exponentiation (2**3=8)."}
        ]
    },
    'JavaScript': {
        'questions': [
            {"q": "How to declare a variable in JavaScript?", "options": ["let x;", "variable x;", "v x;", "declare x;"], "correct": "let x;", "exp": "let, const, var are used."},
            {"q": "What does 'console.log()' do?", "options": ["Prints to console", "Shows alert", "Returns value", "Creates log"], "correct": "Prints to console", "exp": "Outputs to browser console."}
        ]
    },
    'SQL': {
        'questions': [
            {"q": "What does SQL stand for?", "options": ["Structured Query Language", "Simple Query Language", "Standard Query Language", "System Query Language"], "correct": "Structured Query Language", "exp": "SQL = Structured Query Language."},
            {"q": "Which SQL statement extracts data?", "options": ["SELECT", "EXTRACT", "GET", "OPEN"], "correct": "SELECT", "exp": "SELECT retrieves data."}
        ]
    }
}

# ============ RESUME ANALYSIS (NO PDF REQUIRED - MANUAL INPUT) ============
def analyze_resume_text(text):
    """Analyze resume text and return results"""
    text_lower = text.lower()
    
    # Role keywords
    role_keywords = {
        'Python Developer': ['python', 'django', 'flask', 'pandas', 'numpy'],
        'JavaScript Developer': ['javascript', 'react', 'angular', 'vue', 'node'],
        'Data Scientist': ['data science', 'machine learning', 'statistics', 'analytics'],
        'Full Stack Developer': ['react', 'angular', 'node', 'html', 'css', 'mongodb'],
        'DevOps Engineer': ['docker', 'kubernetes', 'aws', 'jenkins', 'ci/cd'],
        'Java Developer': ['java', 'spring', 'hibernate', 'maven'],
        'Cloud Engineer': ['aws', 'azure', 'gcp', 'cloud', 'terraform'],
        'Machine Learning Engineer': ['machine learning', 'tensorflow', 'pytorch', 'keras']
    }
    
    # Calculate scores
    scores = {}
    matched_skills = {}
    for role, keywords in role_keywords.items():
        score = 0
        matched = []
        for kw in keywords:
            if kw in text_lower:
                score += 15
                matched.append(kw)
        scores[role] = min(score, 100)
        matched_skills[role] = matched
    
    # Get best role
    best_role = max(scores, key=scores.get)
    best_score = scores[best_role]
    
    # Get other roles
    other_roles = []
    for role, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        if score >= 25 and role != best_role:
            other_roles.append({
                'role': role,
                'match': score,
                'skills': matched_skills[role][:3]
            })
    
    # Calculate quality
    words = len(text.split())
    if words > 200 and best_score >= 60:
        quality = "Excellent"
        color = "#48bb78"
    elif words > 100 and best_score >= 40:
        quality = "Good"
        color = "#48bb78"
    elif words > 50:
        quality = "Average"
        color = "#f59e0b"
    else:
        quality = "Needs Improvement"
        color = "#ef4444"
    
    return {
        'score': best_score,
        'best_role': best_role,
        'suggested_roles': other_roles[:5],
        'quality': quality,
        'quality_color': color,
        'word_count': words,
        'has_email': '@' in text,
        'full_text': text[:2000],
        'matched_skills': matched_skills[best_role][:5]
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
        confirm = request.form.get('confirm_password')
        
        if not username or not email or not password:
            flash('All fields required', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username exists', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email registered', 'danger')
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
    total = Interview.query.filter_by(user_id=current_user.id).count()
    avg = db.session.query(db.func.avg(Interview.score)).filter_by(user_id=current_user.id).scalar() or 0
    quiz_count = QuizResult.query.filter_by(user_id=current_user.id).count()
    latest = ResumeAnalysis.query.filter_by(user_id=current_user.id).order_by(ResumeAnalysis.date.desc()).first()
    recent = Interview.query.filter_by(user_id=current_user.id).order_by(Interview.date.desc()).limit(5).all()
    
    return render_template('dashboard.html',
                         total_interviews=total,
                         avg_score=round(avg, 1),
                         quiz_count=quiz_count,
                         avg_quiz_score=0,
                         resume_score=latest.score if latest else 0,
                         recent_interviews=recent)

# ============ MOCK INTERVIEW ============
@app.route('/mock-interview')
@login_required
def mock_interview():
    return render_template('mock_interview.html', roles=list(INTERVIEW_QUESTIONS.keys()))

@app.route('/start-mock-interview', methods=['POST'])
@login_required
def start_mock_interview():
    role = request.form.get('role')
    questions = INTERVIEW_QUESTIONS.get(role, INTERVIEW_QUESTIONS['Python Developer'])
    random.shuffle(questions)
    
    session['interview_role'] = role
    session['interview_questions'] = questions[:5]
    session['interview_answers'] = []
    session['interview_scores'] = []
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
                         role=session.get('interview_role'))

@app.route('/submit-mock-answer', methods=['POST'])
@login_required
def submit_mock_answer():
    answer = request.form.get('answer')
    question = request.form.get('question')
    
    # Score based on answer length
    words = len(answer.split())
    if words > 80:
        score = random.randint(75, 95)
    elif words > 40:
        score = random.randint(55, 80)
    elif words > 15:
        score = random.randint(40, 65)
    else:
        score = random.randint(25, 50)
    
    session['interview_answers'].append(answer)
    session['interview_scores'].append(score)
    session['interview_current'] = session.get('interview_current', 0) + 1
    
    questions = session.get('interview_questions', [])
    current_idx = session.get('interview_current', 0)
    
    if current_idx >= len(questions):
        for i, q in enumerate(questions):
            interview = Interview(
                user_id=current_user.id,
                job_role=session.get('interview_role'),
                question=q,
                answer=session['interview_answers'][i][:500],
                score=session['interview_scores'][i],
                feedback="Good attempt!"
            )
            db.session.add(interview)
        db.session.commit()
        
        total_score = sum(session['interview_scores']) / len(session['interview_scores'])
        session.clear()
        
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

# ============ RESUME ANALYSIS - TEXT INPUT (NO PDF REQUIRED) ============
@app.route('/resume-analysis', methods=['GET', 'POST'])
@login_required
def resume_analysis():
    if request.method == 'POST':
        resume_text = request.form.get('resume_text', '').strip()
        
        if not resume_text:
            flash('Please paste your resume text', 'danger')
            return redirect(url_for('resume_analysis'))
        
        if len(resume_text) < 50:
            flash('Please paste more content (at least 50 characters)', 'danger')
            return redirect(url_for('resume_analysis'))
        
        # Analyze the resume
        analysis = analyze_resume_text(resume_text)
        
        # Save to database
        resume = ResumeAnalysis(
            user_id=current_user.id,
            filename="pasted_resume.txt",
            extracted_text=resume_text[:2000],
            score=analysis['score'],
            suggested_role=analysis['best_role'],
            suggested_roles=json.dumps(analysis['suggested_roles']),
            strengths=json.dumps(["Resume analyzed successfully"]),
            improvements=json.dumps(["Add more keywords for better matching"]),
            skills_found=json.dumps(analysis['matched_skills'])
        )
        db.session.add(resume)
        db.session.commit()
        
        flash(f'✅ Resume analyzed! Best match: {analysis["best_role"]} ({analysis["score"]}%)', 'success')
        return render_template('resume_results.html', analysis=analysis)
    
    return render_template('resume_analysis.html')

@app.route('/start-mock-interview-direct', methods=['POST'])
@login_required
def start_mock_interview_direct():
    role = request.form.get('role')
    questions = INTERVIEW_QUESTIONS.get(role, INTERVIEW_QUESTIONS['Python Developer'])
    random.shuffle(questions)
    
    session['interview_role'] = role
    session['interview_questions'] = questions[:5]
    session['interview_answers'] = []
    session['interview_scores'] = []
    session['interview_current'] = 0
    
    return redirect(url_for('take_mock_interview'))

@app.route('/start-quiz-direct', methods=['POST'])
@login_required
def start_quiz_direct():
    category = request.form.get('category')
    
    # Map role to quiz category
    quiz_cat = 'Python'
    if 'JavaScript' in category:
        quiz_cat = 'JavaScript'
    elif 'Data' in category or 'Machine' in category:
        quiz_cat = 'Python'
    elif 'SQL' in category:
        quiz_cat = 'SQL'
    
    questions = QUIZ_DATA.get(quiz_cat, QUIZ_DATA['Python'])['questions']
    selected = random.sample(questions, min(3, len(questions)))
    
    session['quiz_category'] = f"{category} Quiz"
    session['quiz_questions'] = selected
    session['quiz_answers'] = []
    session['quiz_current'] = 0
    
    return redirect(url_for('take_quiz'))

# ============ SKILL QUIZ ============
@app.route('/skill-quiz')
@login_required
def skill_quiz():
    return render_template('skill_quiz.html', categories=['Python', 'JavaScript', 'SQL'])

@app.route('/start-quiz', methods=['POST'])
@login_required
def start_quiz():
    category = request.form.get('category')
    questions = QUIZ_DATA.get(category, QUIZ_DATA['Python'])['questions']
    selected = random.sample(questions, min(3, len(questions)))
    
    session['quiz_category'] = category
    session['quiz_questions'] = selected
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
    is_correct = (data.get('answer') == data.get('correct'))
    
    session['quiz_answers'].append({
        'question': data.get('question'),
        'user_answer': data.get('answer'),
        'correct_answer': data.get('correct'),
        'is_correct': is_correct,
        'explanation': data.get('exp', '')
    })
    session['quiz_current'] = session.get('quiz_current', 0) + 1
    
    questions = session['quiz_questions']
    current_idx = session['quiz_current']
    
    if current_idx >= len(questions):
        correct = sum(1 for a in session['quiz_answers'] if a['is_correct'])
        score = int((correct / len(questions)) * 100)
        
        quiz = QuizResult(
            user_id=current_user.id,
            category=session['quiz_category'],
            difficulty='beginner',
            score=score,
            total_questions=len(questions),
            correct_answers=correct
        )
        db.session.add(quiz)
        db.session.commit()
        
        return jsonify({'completed': True, 'score': score, 'correct': correct, 'total': len(questions)})
    
    return jsonify({
        'completed': False,
        'next_question': questions[current_idx],
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
    interviews = Interview.query.filter_by(user_id=current_user.id).all()
    quizzes = QuizResult.query.filter_by(user_id=current_user.id).all()
    
    return render_template('performance.html',
                         interviews=interviews,
                         quizzes=quizzes,
                         interview_dates=json.dumps([i.date.strftime('%Y-%m-%d') for i in interviews]),
                         interview_scores=json.dumps([i.score for i in interviews]))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
