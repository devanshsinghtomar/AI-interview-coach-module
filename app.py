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
app.config['SECRET_KEY'] = 'your-secret-key-change-this-to-something-secure'
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

# Create tables
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Question Bank
QUESTIONS_DB = {
    'Python Developer': {
        'easy': [
            "What are Python decorators and how do you use them?",
            "Explain the difference between lists and tuples in Python.",
            "What is list comprehension? Give an example.",
            "How does exception handling work in Python?",
            "What is the difference between 'is' and '==' in Python?"
        ],
        'medium': [
            "Explain the Global Interpreter Lock (GIL) in Python.",
            "What are generators and how are they memory efficient?",
            "How does garbage collection work in Python?"
        ],
        'hard': [
            "Design a thread-safe singleton pattern in Python.",
            "Explain async/await and event loops in Python.",
            "How would you optimize a slow Python application?"
        ]
    },
    'JavaScript Developer': {
        'easy': [
            "What is hoisting in JavaScript?",
            "Explain the difference between var, let, and const.",
            "What is closure in JavaScript? Give an example."
        ],
        'medium': [
            "Explain promises and async/await in JavaScript.",
            "What is the difference between == and ===?",
            "Explain event delegation in JavaScript."
        ],
        'hard': [
            "Explain the event loop and callback queue in detail.",
            "How would you implement debouncing and throttling?",
            "What are Web Workers and when to use them?"
        ]
    },
    'Data Scientist': {
        'easy': [
            "What is the difference between supervised and unsupervised learning?",
            "Explain bias-variance tradeoff.",
            "What is overfitting and how do you prevent it?"
        ],
        'medium': [
            "Explain the difference between bagging and boosting.",
            "What is feature engineering and why is it important?",
            "How do you handle imbalanced datasets?"
        ],
        'hard': [
            "Explain gradient descent and its variants.",
            "How would you build a recommendation system from scratch?",
            "What is attention mechanism in transformers?"
        ]
    },
    'Full Stack Developer': {
        'easy': [
            "What is REST and what are its principles?",
            "Explain the difference between SQL and NoSQL databases.",
            "What is CORS and how do you handle it?"
        ],
        'medium': [
            "Explain JWT tokens and how they work.",
            "What is the difference between horizontal and vertical scaling?",
            "Explain ACID properties in databases."
        ],
        'hard': [
            "Design a URL shortening service like bit.ly.",
            "How would you implement rate limiting in an API?",
            "Explain database indexing and query optimization."
        ]
    }
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
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('register'))
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose another.', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login.', 'error')
            return redirect(url_for('register'))
        
        # Create user
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
        
        if not username or not password:
            flash('Please enter both username and password', 'error')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.username}!', 'success')
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    interviews = Interview.query.filter_by(user_id=current_user.id).order_by(Interview.date.desc()).limit(5).all()
    total_interviews = Interview.query.filter_by(user_id=current_user.id).count()
    avg_score = db.session.query(db.func.avg(Interview.overall_score)).filter_by(user_id=current_user.id).scalar() or 0
    resume_count = ResumeAnalysis.query.filter_by(user_id=current_user.id).count()
    
    return render_template('dashboard.html', 
                         total_interviews=total_interviews,
                         avg_score=round(avg_score, 1),
                         resume_count=resume_count,
                         recent_interviews=interviews)

@app.route('/start-interview', methods=['GET', 'POST'])
@login_required
def start_interview():
    if request.method == 'POST':
        job_role = request.form.get('job_role')
        difficulty = request.form.get('difficulty', 'medium')
        
        role_questions = QUESTIONS_DB.get(job_role, QUESTIONS_DB['Python Developer'])
        questions = role_questions.get(difficulty, role_questions['medium'])
        
        session['interview_questions'] = questions
        session['interview_role'] = job_role
        session['interview_difficulty'] = difficulty
        session['interview_answers'] = []
        session['interview_scores'] = []
        session['interview_current'] = 0
        
        return redirect(url_for('take_interview'))
    
    return render_template('start_interview.html', roles=list(QUESTIONS_DB.keys()))

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
    
    # Score based on answer length and quality
    clarity_score = min(100, max(40, len(answer) // 10 + 40))
    relevance_score = min(100, max(40, len(answer.split()) // 15 + 40))
    confidence_score = min(100, max(40, len(answer) // 50 + 50))
    overall_score = (clarity_score + relevance_score + confidence_score) // 3
    
    session['interview_answers'].append(answer)
    session['interview_scores'].append({
        'clarity': clarity_score,
        'relevance': relevance_score,
        'confidence': confidence_score,
        'overall': overall_score
    })
    session['interview_current'] = session.get('interview_current', 0) + 1
    session.modified = True
    
    questions = session['interview_questions']
    current_idx = session['interview_current']
    
    if current_idx >= len(questions):
        return jsonify({
            'completed': True,
            'next_url': url_for('interview_complete')
        })
    
    return jsonify({
        'completed': False,
        'next_question': questions[current_idx],
        'question_num': current_idx + 1,
        'total': len(questions),
        'scores': {
            'clarity': clarity_score,
            'relevance': relevance_score,
            'confidence': confidence_score,
            'overall': overall_score
        }
    })

@app.route('/interview-complete')
@login_required
def interview_complete():
    if 'interview_answers' not in session:
        return redirect(url_for('start_interview'))
    
    total_overall = sum(s['overall'] for s in session['interview_scores']) / len(session['interview_scores'])
    
    for q, a, s in zip(session['interview_questions'], session['interview_answers'], session['interview_scores']):
        interview = Interview(
            user_id=current_user.id,
            job_role=session['interview_role'],
            question=q,
            answer=a[:500],
            clarity_score=s['clarity'],
            relevance_score=s['relevance'],
            confidence_score=s['confidence'],
            overall_score=s['overall']
        )
        db.session.add(interview)
    db.session.commit()
    
    result = {
        'total_questions': len(session['interview_answers']),
        'avg_overall': round(total_overall, 1),
        'job_role': session['interview_role']
    }
    
    session.pop('interview_questions', None)
    session.pop('interview_answers', None)
    session.pop('interview_scores', None)
    session.pop('interview_current', None)
    session.pop('interview_role', None)
    
    return render_template('interview_complete.html', result=result)

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
            
            # Extract text from PDF
            text = ""
            try:
                import PyPDF2
                with open(filepath, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text += page.extract_text()
            except:
                text = file.filename
            
            word_count = len(text.split())
            
            # Score calculation
            score = 50
            if word_count > 100:
                score += 15
            if word_count > 300:
                score += 10
            if '@' in text:
                score += 10
            if any(skill in text.lower() for skill in ['python', 'java', 'javascript', 'react', 'sql']):
                score += 15
            
            strengths = []
            weaknesses = []
            recommendations = []
            
            if word_count > 200:
                strengths.append("Good length and detail")
            else:
                weaknesses.append("Resume is too short")
                recommendations.append("Add more details about your experience")
            
            if '@' in text:
                strengths.append("Contact information included")
            else:
                weaknesses.append("Missing contact email")
                recommendations.append("Add your email address")
            
            if any(skill in text.lower() for skill in ['python', 'java', 'javascript']):
                strengths.append("Technical skills mentioned")
            else:
                weaknesses.append("Missing technical skills section")
                recommendations.append("Add a technical skills section")
            
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
                                 recommendations=recommendations,
                                 word_count=word_count)
    
    return render_template('resume_upload.html')

@app.route('/performance')
@login_required
def performance():
    interviews = Interview.query.filter_by(user_id=current_user.id).order_by(Interview.date).all()
    resumes = ResumeAnalysis.query.filter_by(user_id=current_user.id).order_by(ResumeAnalysis.date.desc()).all()
    
    interview_dates = [i.date.strftime('%Y-%m-%d') for i in interviews]
    interview_scores = [i.overall_score for i in interviews]
    
    roles_scores = {}
    for i in interviews:
        if i.job_role not in roles_scores:
            roles_scores[i.job_role] = []
        roles_scores[i.job_role].append(i.overall_score)
    
    role_performance = {role: round(sum(scores)/len(scores), 1) for role, scores in roles_scores.items()}
    
    return render_template('performance.html',
                         interviews=interviews,
                         resumes=resumes,
                         interview_dates=json.dumps(interview_dates),
                         interview_scores=json.dumps(interview_scores),
                         role_performance=role_performance)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
