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
    score = db.Column(db.Integer)
    total_questions = db.Column(db.Integer)
    correct_answers = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# Create tables
def init_db():
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")

init_db()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
            
            # Validation
            if not username or not email or not password:
                flash('All fields are required', 'danger')
                return render_template('register.html')
            
            if password != confirm_password:
                flash('Passwords do not match', 'danger')
                return render_template('register.html')
            
            if len(password) < 4:
                flash('Password must be at least 4 characters', 'danger')
                return render_template('register.html')
            
            # Check existing user
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists. Please choose another.', 'danger')
                return render_template('register.html')
            
            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                flash('Email already registered. Please login.', 'danger')
                return render_template('register.html')
            
            # Create user
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(username=username, email=email, password_hash=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            print(f"Registration error: {traceback.format_exc()}")
            flash(f'Registration failed: {str(e)}', 'danger')
            return render_template('register.html')
    
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
                
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'danger')
                
        except Exception as e:
            print(f"Login error: {traceback.format_exc()}")
            flash('Login failed. Please try again.', 'danger')
    
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
    try:
        total_interviews = Interview.query.filter_by(user_id=current_user.id).count()
        avg_score = db.session.query(db.func.avg(Interview.score)).filter_by(user_id=current_user.id).scalar() or 0
        quiz_count = QuizResult.query.filter_by(user_id=current_user.id).count()
        latest_resume = ResumeAnalysis.query.filter_by(user_id=current_user.id).order_by(ResumeAnalysis.date.desc()).first()
        recent_interviews = Interview.query.filter_by(user_id=current_user.id).order_by(Interview.date.desc()).limit(5).all()
        
        return render_template('dashboard.html',
                             total_interviews=total_interviews,
                             avg_score=round(avg_score, 1),
                             quiz_count=quiz_count,
                             resume_score=latest_resume.score if latest_resume else 0,
                             recent_interviews=recent_interviews)
    except Exception as e:
        print(f"Dashboard error: {traceback.format_exc()}")
        flash('Error loading dashboard', 'danger')
        return render_template('dashboard.html', 
                             total_interviews=0, avg_score=0, quiz_count=0, 
                             resume_score=0, recent_interviews=[])

# Mock Interview Routes
INTERVIEW_QUESTIONS = {
    'Python Developer': [
        "What are Python decorators and how do you use them?",
        "Explain the difference between deep copy and shallow copy.",
        "What is the Global Interpreter Lock (GIL)?",
        "Explain list comprehension with an example.",
        "What are generators and how are they memory efficient?",
    ],
    'JavaScript Developer': [
        "Explain the event loop in JavaScript.",
        "What is closure? Give an example.",
        "Explain the difference between var, let, and const.",
        "What are promises and how do they work?",
        "Explain the concept of hoisting.",
    ],
    'Data Scientist': [
        "Explain the difference between supervised and unsupervised learning.",
        "What is overfitting and how do you prevent it?",
        "Explain bias-variance tradeoff.",
        "What evaluation metrics would you use for classification?",
        "Explain cross-validation.",
    ]
}

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
    session['interview_questions'] = questions[:5]
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
            text = f"Sample resume content from {filename}"
            
            score = 75
            strengths = ["Good resume structure", "Relevant skills mentioned"]
            improvements = ["Add more quantifiable achievements", "Include a professional summary"]
            skills = ["Python", "JavaScript", "SQL"]
            
            resume = ResumeAnalysis(
                user_id=current_user.id,
                filename=filename,
                score=score,
                strengths=json.dumps(strengths),
                improvements=json.dumps(improvements),
                skills_found=json.dumps(skills)
            )
            db.session.add(resume)
            db.session.commit()
            
            analysis = {'score': score, 'strengths': strengths, 'improvements': improvements, 'skills_found': skills}
            return render_template('resume_results.html', analysis=analysis)
        else:
            flash('Please upload a PDF file', 'danger')
    
    return render_template('resume_analysis.html')

# Quiz Routes
QUIZ_QUESTIONS = {
    'Python': [
        {"question": "What is the correct file extension for Python files?", "options": [".py", ".pyth", ".pt", ".p"], "correct": ".py"},
        {"question": "How do you create a variable with the floating number 2.8?", "options": ["x = 2.8", "x = float(2.8)", "Both", "x = 2,8"], "correct": "Both"},
        {"question": "What is the correct syntax to output 'Hello World'?", "options": ["print('Hello World')", "p('Hello World')", "echo", "printf"], "correct": "print('Hello World')"},
    ],
    'JavaScript': [
        {"question": "How do you declare a variable in JavaScript?", "options": ["let x;", "variable x;", "v x;", "declare x;"], "correct": "let x;"},
        {"question": "What does console.log() do?", "options": ["Prints to console", "Shows alert", "Returns value", "Creates log"], "correct": "Prints to console"},
    ],
    'SQL': [
        {"question": "What does SQL stand for?", "options": ["Structured Query Language", "Simple Query Language", "Standard Query", "System Query"], "correct": "Structured Query Language"},
        {"question": "Which SQL statement is used to extract data?", "options": ["SELECT", "EXTRACT", "GET", "OPEN"], "correct": "SELECT"},
    ]
}

@app.route('/skill-quiz')
@login_required
def skill_quiz():
    categories = list(QUIZ_QUESTIONS.keys())
    return render_template('skill_quiz.html', categories=categories)

@app.route('/start-quiz', methods=['POST'])
@login_required
def start_quiz():
    category = request.form.get('category')
    questions = QUIZ_QUESTIONS.get(category, [])
    
    if not questions:
        flash('No questions available', 'danger')
        return redirect(url_for('skill_quiz'))
    
    selected_questions = random.sample(questions, min(3, len(questions)))
    
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
            score=score,
            total_questions=len(questions),
            correct_answers=correct_count
        )
        db.session.add(quiz_result)
        db.session.commit()
        
        session.pop('quiz_questions', None)
        session.pop('quiz_answers', None)
        session.pop('quiz_current', None)
        
        return jsonify({'completed': True, 'score': score, 'correct': correct_count, 'total': len(questions)})
    
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
