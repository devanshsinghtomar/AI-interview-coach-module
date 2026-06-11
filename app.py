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

# ============ INTERVIEW QUESTIONS ============
INTERVIEW_QUESTIONS_WITH_ANSWERS = {
    'Python Developer': [
        {"question": "What is the difference between a list and a tuple in Python?", "keywords": ["mutable", "immutable", "change"]},
        {"question": "What is a decorator in Python?", "keywords": ["function", "modify", "wrapper"]},
        {"question": "Explain the Global Interpreter Lock (GIL).", "keywords": ["mutex", "thread", "execution"]},
    ],
    'JavaScript Developer': [
        {"question": "What is closure in JavaScript?", "keywords": ["inner function", "outer scope", "variables"]},
        {"question": "Explain the difference between == and ===.", "keywords": ["value", "type", "strict"]},
    ],
    'Data Scientist': [
        {"question": "Difference between supervised and unsupervised learning?", "keywords": ["labeled", "unlabeled", "output"]},
        {"question": "What is overfitting?", "keywords": ["training", "noise", "generalization"]},
    ],
    'Full Stack Developer': [
        {"question": "What is REST API?", "keywords": ["representational", "state", "transfer"]},
        {"question": "Difference between SQL and NoSQL?", "keywords": ["structured", "unstructured", "schema"]},
    ],
    'DevOps Engineer': [
        {"question": "What is Docker?", "keywords": ["container", "image", "isolate"]},
        {"question": "Explain CI/CD pipeline.", "keywords": ["continuous", "integration", "delivery"]},
    ],
    'Java Developer': [
        {"question": "Difference between abstract class and interface?", "keywords": ["implementation", "multiple", "inheritance"]},
        {"question": "What is multithreading in Java?", "keywords": ["concurrent", "threads", "parallel"]},
    ],
    'Cloud Engineer': [
        {"question": "What are the cloud service models?", "keywords": ["iaas", "paas", "saas"]},
        {"question": "Explain serverless computing.", "keywords": ["functions", "event-driven", "scale"]},
    ],
    'Machine Learning Engineer': [
        {"question": "Explain the difference between AI, ML, and DL.", "keywords": ["artificial", "intelligence", "machine"]},
        {"question": "What is the difference between classification and regression?", "keywords": ["categorical", "continuous", "predict"]},
    ]
}

# ============ QUIZ QUESTIONS ============
QUIZ_QUESTIONS = {
    'Python': [
        {"question": "What is the correct way to create a function in Python?", "options": ["def myFunction():", "function myFunction():", "create myFunction():", "func myFunction():"], "correct": "def myFunction():", "explanation": "Functions are defined using the 'def' keyword."},
        {"question": "What does the 'len()' function do?", "options": ["Returns length", "Converts to lowercase", "Rounds a number", "Finds maximum"], "correct": "Returns length", "explanation": "len() returns the number of items."},
        {"question": "Which operator is used for exponentiation?", "options": ["**", "^", "exp()", "&&"], "correct": "**", "explanation": "** is exponentiation operator."},
    ],
    'JavaScript': [
        {"question": "How do you declare a variable in JavaScript?", "options": ["let x;", "variable x;", "v x;", "declare x;"], "correct": "let x;", "explanation": "let, const, and var declare variables."},
        {"question": "What does 'console.log()' do?", "options": ["Prints to console", "Shows alert", "Returns value", "Creates log"], "correct": "Prints to console", "explanation": "console.log() outputs to browser console."},
    ],
    'SQL': [
        {"question": "What does SQL stand for?", "options": ["Structured Query Language", "Simple Query Language", "Standard Query Language", "System Query Language"], "correct": "Structured Query Language", "explanation": "SQL stands for Structured Query Language."},
        {"question": "Which SQL statement extracts data?", "options": ["SELECT", "EXTRACT", "GET", "OPEN"], "correct": "SELECT", "explanation": "SELECT retrieves data from database."},
    ]
}

# ============ SIMPLIFIED RESUME ANALYSIS ============
def extract_text_from_pdf(filepath):
    """Extract text from PDF file"""
    try:
        with open(filepath, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + " "
            return text.strip() if text.strip() else "Sample resume text for analysis"
    except Exception as e:
        print(f"PDF error: {e}")
        return "Sample resume text for analysis"

def analyze_resume_content(text):
    """Analyze resume content"""
    text_lower = text.lower()
    
    # Role matching
    roles = {
        'Python Developer': ['python', 'django', 'flask', 'pandas', 'numpy'],
        'JavaScript Developer': ['javascript', 'react', 'angular', 'vue', 'node'],
        'Data Scientist': ['data science', 'machine learning', 'analytics', 'statistics'],
        'Full Stack Developer': ['react', 'angular', 'node', 'mongodb', 'html', 'css'],
        'DevOps Engineer': ['docker', 'kubernetes', 'aws', 'jenkins', 'ci/cd'],
        'Java Developer': ['java', 'spring', 'hibernate', 'maven'],
        'Cloud Engineer': ['aws', 'azure', 'gcp', 'cloud', 'terraform'],
        'Machine Learning Engineer': ['machine learning', 'deep learning', 'tensorflow', 'pytorch']
    }
    
    # Calculate scores
    scores = {}
    matched_skills = {}
    for role, keywords in roles.items():
        score = 0
        matched = []
        for kw in keywords:
            if kw in text_lower:
                score += 20
                matched.append(kw)
        scores[role] = min(score, 100)
        matched_skills[role] = matched
    
    # Get best role
    best_role = max(scores, key=scores.get)
    best_score = scores[best_role]
    
    # Get other roles
    other_roles = []
    for role, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        if score >= 30 and role != best_role:
            other_roles.append({
                'role': role,
                'match_percentage': score,
                'matched_skills': matched_skills[role][:3]
            })
    
    # Calculate quality
    word_count = len(text.split())
    has_email = '@' in text
    has_phone = bool(re.search(r'\d{10}', text))
    
    if word_count > 300 and best_score >= 60:
        quality = "Excellent"
        quality_color = "#48bb78"
    elif word_count > 150 and best_score >= 40:
        quality = "Good"
        quality_color = "#48bb78"
    elif word_count > 80:
        quality = "Average"
        quality_color = "#f59e0b"
    else:
        quality = "Needs Improvement"
        quality_color = "#ef4444"
    
    # Strengths
    strengths = []
    if word_count > 200:
        strengths.append(f"✅ Resume has {word_count} words - good detail")
    if has_email and has_phone:
        strengths.append("✅ Complete contact information")
    if best_score >= 60:
        strengths.append(f"✅ Strong match for {best_role}")
    if not strengths:
        strengths = ["✅ Resume uploaded successfully"]
    
    # Improvements
    improvements = []
    if word_count < 150:
        improvements.append("📈 Add more details to your resume")
    if not has_email:
        improvements.append("📈 Add your email address")
    if best_score < 50:
        improvements.append(f"📈 Add more {best_role} keywords")
    if not improvements:
        improvements = ["📈 Keep up the good work!"]
    
    # Skills found
    all_skills = []
    for skills in matched_skills.values():
        all_skills.extend(skills)
    unique_skills = list(set(all_skills))[:8]
    
    return {
        'overall_score': best_score,
        'best_role': best_role,
        'suggested_roles': other_roles[:5],
        'quality_rating': quality,
        'quality_color': quality_color,
        'strengths': strengths[:4],
        'improvements': improvements[:4],
        'skills_found': unique_skills,
        'word_count': word_count,
        'has_email': has_email,
        'has_phone': has_phone,
        'full_text': text[:2000]
    }

def evaluate_answer(question_text, user_answer, job_role):
    """Evaluate answer"""
    user_lower = user_answer.lower()
    words = len(user_answer.split())
    
    # Simple scoring
    if words > 100:
        score = 85
        feedback = "Excellent answer! Great detail."
    elif words > 50:
        score = 70
        feedback = "Good answer! Consider adding more specific examples."
    elif words > 20:
        score = 50
        feedback = "Fair answer. Try to elaborate more."
    else:
        score = 35
        feedback = "Answer too brief. Please provide more details."
    
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
        confirm = request.form.get('confirm_password', '')
        
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
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            flash(f'Welcome back!', 'success')
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
    roles = list(INTERVIEW_QUESTIONS_WITH_ANSWERS.keys())
    return render_template('mock_interview.html', roles=roles)

@app.route('/start-mock-interview', methods=['POST'])
@login_required
def start_mock_interview():
    role = request.form.get('role')
    if not role:
        flash('Select a role', 'danger')
        return redirect(url_for('mock_interview'))
    
    questions = [q["question"] for q in INTERVIEW_QUESTIONS_WITH_ANSWERS.get(role, [])]
    random.shuffle(questions)
    
    session['interview_role'] = role
    session['interview_questions'] = questions[:5]
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
    
    score, feedback = evaluate_answer(question, answer, role)
    
    session['interview_answers'].append({'question': question, 'answer': answer, 'score': score})
    session['interview_scores'].append(score)
    session['interview_feedbacks'].append(feedback)
    session['interview_current'] = session.get('interview_current', 0) + 1
    session.modified = True
    
    questions = session.get('interview_questions', [])
    current_idx = session.get('interview_current', 0)
    
    if current_idx >= len(questions):
        for i, item in enumerate(session['interview_answers']):
            interview = Interview(
                user_id=current_user.id,
                job_role=role,
                question=item['question'],
                answer=item['answer'][:500],
                score=item['score'],
                feedback=session['interview_feedbacks'][i]
            )
            db.session.add(interview)
        db.session.commit()
        
        total_score = sum(session['interview_scores']) / len(session['interview_scores'])
        
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

# ============ RESUME ANALYSIS ============
@app.route('/resume-analysis', methods=['GET', 'POST'])
@login_required
def resume_analysis():
    if request.method == 'POST':
        try:
            if 'resume' not in request.files:
                flash('No file uploaded', 'danger')
                return redirect(url_for('resume_analysis'))
            
            file = request.files['resume']
            if file.filename == '':
                flash('No file selected', 'danger')
                return redirect(url_for('resume_analysis'))
            
            if not file.filename.lower().endswith('.pdf'):
                flash('Please upload a PDF file', 'danger')
                return redirect(url_for('resume_analysis'))
            
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Extract text
            extracted_text = extract_text_from_pdf(filepath)
            
            # Clean up
            if os.path.exists(filepath):
                os.remove(filepath)
            
            # Analyze
            analysis = analyze_resume_content(extracted_text)
            
            # Save to database
            resume = ResumeAnalysis(
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
            db.session.add(resume)
            db.session.commit()
            
            flash(f'Resume analyzed! Best match: {analysis["best_role"]} ({analysis["overall_score"]}%)', 'success')
            return render_template('resume_results.html', analysis=analysis)
            
        except Exception as e:
            print(f"Error: {e}")
            flash('Error analyzing resume. Please try again.', 'danger')
            return redirect(url_for('resume_analysis'))
    
    return render_template('resume_analysis.html')

# ============ HELPER ROUTES ============
@app.route('/start-mock-interview-direct', methods=['POST'])
@login_required
def start_mock_interview_direct():
    role = request.form.get('role')
    questions = [q["question"] for q in INTERVIEW_QUESTIONS_WITH_ANSWERS.get(role, [])]
    random.shuffle(questions)
    
    session['interview_role'] = role
    session['interview_questions'] = questions[:5]
    session['interview_answers'] = []
    session['interview_scores'] = []
    session['interview_feedbacks'] = []
    session['interview_current'] = 0
    
    return redirect(url_for('take_mock_interview'))

@app.route('/start-quiz-direct', methods=['POST'])
@login_required
def start_quiz_direct():
    category = request.form.get('category')
    quiz_cat = 'Python'
    if 'JavaScript' in category:
        quiz_cat = 'JavaScript'
    elif 'SQL' in category:
        quiz_cat = 'SQL'
    
    questions = QUIZ_QUESTIONS.get(quiz_cat, QUIZ_QUESTIONS['Python'])
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
    questions = QUIZ_QUESTIONS.get(category, [])
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
    
    questions = session['quiz_questions']
    current_idx = session['quiz_current']
    
    if current_idx >= len(questions):
        correct_count = sum(1 for a in session['quiz_answers'] if a['is_correct'])
        score = int((correct_count / len(questions)) * 100)
        
        quiz = QuizResult(
            user_id=current_user.id,
            category=session['quiz_category'],
            difficulty='beginner',
            score=score,
            total_questions=len(questions),
            correct_answers=correct_count
        )
        db.session.add(quiz)
        db.session.commit()
        
        results = {'completed': True, 'score': score, 'correct': correct_count, 'total': len(questions)}
        session.pop('quiz_questions', None)
        session.pop('quiz_answers', None)
        session.pop('quiz_current', None)
        
        return jsonify(results)
    
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
