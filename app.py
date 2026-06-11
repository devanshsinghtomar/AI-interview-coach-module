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
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max

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
    extracted_text = db.Column(db.Text)
    score = db.Column(db.Integer)
    suggested_role = db.Column(db.String(100))
    suggested_roles = db.Column(db.Text)  # JSON array
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

# ============ SKILLS DATABASE FOR RESUME PARSING ============
SKILLS_DATABASE = {
    'Python Developer': {
        'keywords': ['python', 'django', 'flask', 'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'fastapi', 'celery'],
        'required_skills': ['Python', 'SQL', 'Git', 'REST APIs', 'Problem Solving']
    },
    'JavaScript Developer': {
        'keywords': ['javascript', 'react', 'angular', 'vue', 'node.js', 'express', 'typescript', 'jquery', 'redux', 'next.js'],
        'required_skills': ['JavaScript', 'HTML/CSS', 'React/Angular', 'Node.js', 'REST APIs']
    },
    'Data Scientist': {
        'keywords': ['python', 'data science', 'machine learning', 'statistics', 'pandas', 'scikit-learn', 'tensorflow', 'analytics', 'visualization', 'sql'],
        'required_skills': ['Python', 'Statistics', 'Machine Learning', 'SQL', 'Data Visualization']
    },
    'Full Stack Developer': {
        'keywords': ['react', 'angular', 'node.js', 'express', 'mongodb', 'postgresql', 'html', 'css', 'javascript', 'typescript', 'rest api', 'graphql'],
        'required_skills': ['Frontend Framework', 'Backend Development', 'Databases', 'REST APIs', 'Git']
    },
    'DevOps Engineer': {
        'keywords': ['docker', 'kubernetes', 'jenkins', 'aws', 'azure', 'gcp', 'terraform', 'ansible', 'ci/cd', 'linux', 'bash'],
        'required_skills': ['Docker', 'Kubernetes', 'CI/CD', 'Cloud Platforms', 'Linux']
    },
    'Java Developer': {
        'keywords': ['java', 'spring', 'hibernate', 'maven', 'gradle', 'junit', 'microservices', 'rest api', 'jpa', 'thymeleaf'],
        'required_skills': ['Java', 'Spring Boot', 'Hibernate', 'SQL', 'Maven/Gradle']
    },
    'Cloud Engineer': {
        'keywords': ['aws', 'azure', 'gcp', 'cloud', 'terraform', 'cloudformation', 'serverless', 'lambda', 'ec2', 's3', 'vpc'],
        'required_skills': ['Cloud Platform', 'Infrastructure as Code', 'Networking', 'Security', 'Scripting']
    },
    'Frontend Developer': {
        'keywords': ['react', 'angular', 'vue', 'html5', 'css3', 'javascript', 'typescript', 'webpack', 'bootstrap', 'tailwind', 'sass'],
        'required_skills': ['HTML/CSS', 'JavaScript', 'React/Angular/Vue', 'Responsive Design', 'Web Performance']
    },
    'Backend Developer': {
        'keywords': ['python', 'java', 'node.js', 'go', 'ruby', 'php', 'rest api', 'microservices', 'sql', 'nosql', 'graphql', 'redis'],
        'required_skills': ['Backend Language', 'Database Management', 'API Design', 'Security', 'System Design']
    },
    'Mobile Developer': {
        'keywords': ['android', 'ios', 'swift', 'kotlin', 'react native', 'flutter', 'mobile', 'app development', 'xcode', 'android studio'],
        'required_skills': ['Mobile Platform', 'Programming Language', 'UI/UX', 'API Integration', 'App Deployment']
    }
}

# Generate Quiz Questions
def generate_quiz_questions():
    questions_db = {}
    for role in SKILLS_DATABASE.keys():
        role_questions = []
        for i in range(1, 101):
            skill = random.choice(SKILLS_DATABASE[role]['required_skills'])
            question = {
                "question": f"{role} Quiz: What is the best practice for {skill} in {role} development?",
                "options": [
                    f"Best practice 1 for {skill}",
                    f"Best practice 2 for {skill}",
                    f"Best practice 3 for {skill}",
                    f"Best practice 4 for {skill}"
                ],
                "correct": f"Best practice 1 for {skill}",
                "explanation": f"{skill} is crucial for {role} role.",
                "difficulty": random.choice(["beginner", "intermediate", "advanced"])
            }
            role_questions.append(question)
        questions_db[role] = role_questions
    return questions_db

QUIZ_QUESTIONS = generate_quiz_questions()

# Interview Questions Database
INTERVIEW_QUESTIONS = {}
for role in SKILLS_DATABASE.keys():
    INTERVIEW_QUESTIONS[role] = [
        f"What are the key responsibilities of a {role}?",
        f"What technologies are essential for {role} role?",
        f"Explain a challenging {role} project you worked on.",
        f"How do you stay updated with {role} technologies?",
        f"What is your approach to debugging in {role} development?",
        f"Describe your experience with {random.choice(SKILLS_DATABASE[role]['required_skills'])}.",
        f"How do you handle code reviews as a {role}?",
        f"What's your preferred development methodology for {role} projects?",
        f"How would you optimize performance in a {role} application?",
        f"What security considerations are important for {role} development?"
    ]

# ============ RESUME PARSER FUNCTIONS ============
def extract_text_from_pdf(filepath):
    try:
        with open(filepath, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return ""

def is_valid_resume(text):
    text_lower = text.lower()
    resume_indicators = ['experience', 'education', 'skills', 'work', 'employment', 'project', 'certification', 'summary', 'objective', 'profile']
    contact_indicators = [r'\b\d{10}\b', r'\b[\w\.-]+@[\w\.-]+\.\w+\b']
    has_resume_words = sum(1 for word in resume_indicators if word in text_lower) >= 2
    has_contact = any(re.search(pattern, text) for pattern in contact_indicators)
    return has_resume_words or has_contact or len(text) > 200

def analyze_resume_content(text):
    text_lower = text.lower()
    role_scores = {}
    role_matched_keywords = {}
    
    for role, data in SKILLS_DATABASE.items():
        score = 0
        matched = []
        for keyword in data['keywords']:
            if keyword in text_lower:
                score += 10
                matched.append(keyword)
        role_scores[role] = score
        role_matched_keywords[role] = matched
    
    sorted_roles = sorted(role_scores.items(), key=lambda x: x[1], reverse=True)
    best_role = sorted_roles[0][0] if sorted_roles else "Python Developer"
    best_score = sorted_roles[0][1] if sorted_roles else 0
    
    overall_score = min(100, 40 + best_score)
    
    strengths = []
    if best_score >= 50:
        strengths.append(f"Strong match for {best_role} role")
        strengths.append(f"Good keyword density with {len(role_matched_keywords[best_role])} relevant terms")
    if len(text) > 500:
        strengths.append("Detailed resume with substantial content")
    if re.search(r'\b\d{4}\b', text):
        strengths.append("Includes dates and timeline information")
    
    improvements = []
    if best_score < 40:
        improvements.append(f"Add more {best_role}-specific keywords to your resume")
    if 'github' not in text_lower and 'portfolio' not in text_lower:
        improvements.append("Include links to your GitHub or portfolio")
    if 'achievement' not in text_lower:
        improvements.append("Quantify your achievements with numbers and metrics")
    
    suggested_roles = []
    for role, score in sorted_roles[:3]:
        if score >= 20:
            suggested_roles.append({
                'role': role,
                'match_percentage': min(95, score + 20),
                'matched_skills': role_matched_keywords[role][:5]
            })
    
    if not suggested_roles:
        suggested_roles = [{'role': 'Python Developer', 'match_percentage': 60, 'matched_skills': ['General skills']}]
    
    return {
        'overall_score': overall_score,
        'best_role': best_role,
        'suggested_roles': suggested_roles,
        'strengths': strengths if strengths else ["Resume uploaded successfully"],
        'improvements': improvements if improvements else ["Add more specific technical skills"],
        'skills_found': list(set([skill for skills in role_matched_keywords.values() for skill in skills]))[:10],
        'word_count': len(text.split())
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
        
        allowed_extensions = {'.pdf', '.doc', '.docx', '.txt'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            flash('Please upload a PDF, DOC, DOCX, or TXT file', 'danger')
            return redirect(url_for('resume_analysis'))
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract text
        extracted_text = ""
        if file_ext == '.pdf':
            extracted_text = extract_text_from_pdf(filepath)
        else:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    extracted_text = f.read()
            except:
                extracted_text = ""
        
        # Validate resume
        if not is_valid_resume(extracted_text):
            flash('⚠️ The uploaded file does not appear to be a resume. Please upload a proper resume document.', 'danger')
            os.remove(filepath)
            return redirect(url_for('resume_analysis'))
        
        # Analyze
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
    
    return render_template('resume_analysis.html')

# ============ HELPER ROUTES FOR DIRECT INTERVIEW/QUIZ FROM RESUME ============
@app.route('/start-mock-interview-direct', methods=['POST', 'GET'])
@login_required
def start_mock_interview_direct():
    """Start mock interview directly from resume suggestion"""
    if request.method == 'POST':
        role = request.form.get('role')
    else:
        role = request.args.get('role')
    
    if not role:
        flash('No role specified', 'danger')
        return redirect(url_for('resume_analysis'))
    
    questions = INTERVIEW_QUESTIONS.get(role, INTERVIEW_QUESTIONS['Python Developer'])
    random.shuffle(questions)
    
    session['interview_role'] = role
    session['interview_questions'] = questions[:10]
    session['interview_answers'] = []
    session['interview_current'] = 0
    
    flash(f'Starting {role} mock interview!', 'success')
    return redirect(url_for('take_mock_interview'))

@app.route('/start-quiz-direct', methods=['POST', 'GET'])
@login_required
def start_quiz_direct():
    """Start quiz directly from resume suggestion"""
    if request.method == 'POST':
        category = request.form.get('category')
    else:
        category = request.args.get('category')
    
    if not category:
        flash('No category specified', 'danger')
        return redirect(url_for('resume_analysis'))
    
    all_questions = QUIZ_QUESTIONS.get(category, [])
    if not all_questions:
        flash('No questions available for this category', 'danger')
        return redirect(url_for('resume_analysis'))
    
    selected_questions = random.sample(all_questions, min(10, len(all_questions)))
    
    session['quiz_category'] = category
    session['quiz_difficulty'] = 'intermediate'
    session['quiz_questions'] = selected_questions
    session['quiz_answers'] = []
    session['quiz_current'] = 0
    
    flash(f'Starting {category} quiz!', 'success')
    return redirect(url_for('take_quiz'))

# ============ MOCK INTERVIEW ROUTES ============
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

# ============ QUIZ ROUTES ============
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
    
    if not all_questions:
        flash('No questions available', 'danger')
        return redirect(url_for('skill_quiz'))
    
    selected_questions = random.sample(all_questions, min(10, len(all_questions)))
    
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

# ============ PERFORMANCE ROUTES ============
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
