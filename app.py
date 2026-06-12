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
import zipfile
from io import BytesIO

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

# ============ INTERVIEW QUESTIONS (15+ ROLES) ============
INTERVIEW_QUESTIONS = {
    'Python Developer': [
        {"question": "What is the difference between a list and a tuple?", "keywords": ["mutable", "immutable", "change"]},
        {"question": "What is a decorator in Python?", "keywords": ["function", "modify", "wrapper"]},
        {"question": "Explain the Global Interpreter Lock (GIL).", "keywords": ["thread", "execution", "mutex"]},
    ],
    'JavaScript Developer': [
        {"question": "What is closure in JavaScript?", "keywords": ["inner function", "outer scope", "variables"]},
        {"question": "Difference between == and ===?", "keywords": ["value", "type", "strict"]},
        {"question": "What is hoisting?", "keywords": ["declaration", "move", "top"]},
    ],
    'Data Scientist': [
        {"question": "Difference between supervised and unsupervised learning?", "keywords": ["labeled", "unlabeled", "output"]},
        {"question": "What is overfitting?", "keywords": ["training", "noise", "generalization"]},
        {"question": "Explain bias-variance tradeoff.", "keywords": ["error", "complexity", "balance"]},
    ],
    'Full Stack Developer': [
        {"question": "What is REST API?", "keywords": ["representational", "state", "http"]},
        {"question": "Difference between SQL and NoSQL?", "keywords": ["structured", "schema", "scalability"]},
    ],
    'DevOps Engineer': [
        {"question": "What is Docker?", "keywords": ["container", "image", "isolate"]},
        {"question": "Explain CI/CD.", "keywords": ["continuous", "integration", "automation"]},
    ],
    'Java Developer': [
        {"question": "Difference between abstract class and interface?", "keywords": ["implementation", "multiple", "inheritance"]},
        {"question": "What is multithreading?", "keywords": ["concurrent", "threads", "parallel"]},
    ],
    'Cloud Engineer': [
        {"question": "What are cloud service models?", "keywords": ["iaas", "paas", "saas"]},
        {"question": "Explain serverless computing.", "keywords": ["functions", "event-driven", "scale"]},
    ],
    'Machine Learning Engineer': [
        {"question": "Explain AI vs ML vs DL.", "keywords": ["artificial", "intelligence", "deep"]},
        {"question": "What is transfer learning?", "keywords": ["pretrained", "fine-tune", "adapt"]},
    ],
}

# ============ QUIZ QUESTIONS ============
QUIZ_QUESTIONS = {
    'Python': [
        {"question": "What is the correct way to create a function?", "options": ["def myFunc():", "function myFunc():", "create myFunc():", "func myFunc():"], "correct": "def myFunc():", "explanation": "def keyword is used to define functions"},
        {"question": "What does len() function do?", "options": ["Returns length", "Converts to string", "Finds maximum", "Rounds number"], "correct": "Returns length", "explanation": "len() returns number of items"},
        {"question": "Which operator is used for exponentiation?", "options": ["**", "^", "exp()", "&&"], "correct": "**", "explanation": "** is exponentiation operator"},
        {"question": "What is the output of print(type(10))?", "options": ["<class 'int'>", "<class 'float'>", "<class 'str'>", "<class 'list'>"], "correct": "<class 'int'>", "explanation": "10 is an integer"},
        {"question": "How do you create a list?", "options": ["[1, 2, 3]", "(1, 2, 3)", "{1, 2, 3}", "<1, 2, 3>"], "correct": "[1, 2, 3]", "explanation": "Square brackets create lists"},
        {"question": "What is the correct while loop syntax?", "options": ["while x > y:", "while (x > y)", "x > y while {", "while x > y then:"], "correct": "while x > y:", "explanation": "Colon required after condition"},
        {"question": "What does append() do?", "options": ["Adds to end", "Removes item", "Inserts at start", "Sorts list"], "correct": "Adds to end", "explanation": "append() adds element to end"},
        {"question": "What is 10 // 3?", "options": ["3", "3.33", "3.0", "1"], "correct": "3", "explanation": "// is floor division"},
    ],
    'JavaScript': [
        {"question": "How to declare a variable?", "options": ["let x;", "variable x;", "v x;", "declare x;"], "correct": "let x;", "explanation": "let, const, var declare variables"},
        {"question": "What does console.log() do?", "options": ["Prints to console", "Shows alert", "Returns value", "Creates file"], "correct": "Prints to console", "explanation": "Outputs to browser console"},
        {"question": "How to write a function?", "options": ["function myFunc() {}", "def myFunc() {}", "create myFunc() {}", "func myFunc() {}"], "correct": "function myFunc() {}", "explanation": "function keyword defines functions"},
        {"question": "What does === do?", "options": ["Compares value and type", "Compares only value", "Compares only type", "Assigns value"], "correct": "Compares value and type", "explanation": "Strict equality operator"},
    ],
    'SQL': [
        {"question": "What does SQL stand for?", "options": ["Structured Query Language", "Simple Query Language", "Standard Query", "System Query"], "correct": "Structured Query Language", "explanation": "SQL = Structured Query Language"},
        {"question": "Which statement extracts data?", "options": ["SELECT", "EXTRACT", "GET", "OPEN"], "correct": "SELECT", "explanation": "SELECT retrieves data"},
        {"question": "What does WHERE do?", "options": ["Filters records", "Sorts records", "Groups records", "Joins tables"], "correct": "Filters records", "explanation": "WHERE filters based on conditions"},
    ],
    'Data Science': [
        {"question": "Supervised vs Unsupervised?", "options": ["Labeled vs Unlabeled", "Fast vs Slow", "New vs Old", "Big vs Small"], "correct": "Labeled vs Unlabeled", "explanation": "Supervised uses labeled data"},
        {"question": "What is overfitting?", "options": ["Model too complex", "Model too simple", "Model perfect", "No model"], "correct": "Model too complex", "explanation": "Overfitting learns noise"},
        {"question": "What is cross-validation?", "options": ["Validating on different data", "Same data", "No validation", "Random"], "correct": "Validating on different data", "explanation": "Tests model generalization"},
    ],
}

# ============ FILE EXTRACTION FUNCTION (No external dependencies) ============
def extract_text_from_file(filepath):
    """Extract text from PDF and TXT files (no docx2txt dependency)"""
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
        elif filepath.endswith('.docx'):
            # Simple fallback - inform user to use PDF or TXT
            text = "DOCX files are not fully supported. Please convert to PDF or TXT for best results."
    except Exception as e:
        print(f"Extraction error: {e}")
        text = ""
    return text

def analyze_resume(text):
    """Analyze resume content and return job role suggestions"""
    text_lower = text.lower()
    
    role_keywords = {
        'Python Developer': ['python', 'django', 'flask', 'pandas', 'numpy'],
        'JavaScript Developer': ['javascript', 'react', 'angular', 'vue', 'node'],
        'Data Scientist': ['data science', 'machine learning', 'python', 'analytics'],
        'Full Stack Developer': ['react', 'angular', 'node', 'html', 'css'],
        'DevOps Engineer': ['docker', 'kubernetes', 'jenkins', 'aws', 'ci/cd'],
        'Java Developer': ['java', 'spring', 'hibernate', 'maven'],
        'Cloud Engineer': ['aws', 'azure', 'gcp', 'cloud', 'terraform'],
        'Machine Learning Engineer': ['machine learning', 'deep learning', 'tensorflow', 'keras'],
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
    
    # Find best match
    best_role = max(scores, key=scores.get) if scores else "Python Developer"
    best_score = scores.get(best_role, 50)
    
    # Get suitable roles (score >= 25)
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
    if len(text) > 500:
        strengths.append("✅ Good resume length and detail")
    if '@' in text:
        strengths.append("✅ Contact information included")
    if best_score >= 70:
        strengths.append(f"✅ Strong match for {best_role}")
    
    improvements = []
    if len(text) < 300:
        improvements.append("📈 Add more details about your experience")
    if best_score < 50:
        improvements.append(f"📈 Add more {best_role} keywords")
    
    if not strengths:
        strengths = ["✅ Resume uploaded successfully"]
    if not improvements:
        improvements = ["📈 Consider adding more technical skills"]
    
    # Get unique skills found
    all_skills = []
    for skills in matched_skills.values():
        all_skills.extend(skills)
    unique_skills = list(set(all_skills))[:10]
    
    return {
        'best_role': best_role,
        'best_score': best_score,
        'suitable_roles': suitable_roles[:6],
        'strengths': strengths,
        'improvements': improvements,
        'skills': unique_skills,
        'word_count': len(text.split())
    }

def evaluate_answer(question, answer, role):
    """Evaluate answer - gives low scores for wrong answers"""
    answer_lower = answer.lower().strip()
    
    if len(answer_lower.split()) < 5:
        return 10, "❌ Answer too short. Please provide more details."
    
    for q in INTERVIEW_QUESTIONS.get(role, []):
        if q['question'] == question:
            keywords = q['keywords']
            matched = [kw for kw in keywords if kw in answer_lower]
            
            if not matched:
                return 5, f"❌ Incorrect. Should mention: {', '.join(keywords)}"
            
            score = min(95, int((len(matched) / len(keywords)) * 100))
            
            if score >= 85:
                feedback = f"✅ Excellent! You covered: {', '.join(matched)}"
            elif score >= 70:
                feedback = f"👍 Good! Also mention key concepts"
            elif score >= 50:
                feedback = f"📝 Fair. Missing key concepts"
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
        for item in session['interview_answers']:
            interview = Interview(
                user_id=current_user.id,
                job_role=role,
                question=item['question'],
                answer=item['answer'][:500],
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
        
        allowed = ['.pdf', '.txt']
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed:
            flash('Please upload PDF or TXT file (DOCX not fully supported)', 'danger')
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
                extracted_text=text[:2000],
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
        session['interview_questions'] = questions[:4]
        session['interview_answers'] = []
        session['interview_scores'] = []
        session['interview_current'] = 0
        return redirect(url_for('take_interview'))
    
    elif action == 'quiz':
        quiz_cat = 'Python'
        for cat in QUIZ_QUESTIONS:
            if cat.lower() in role.lower():
                quiz_cat = cat
                break
        questions = QUIZ_QUESTIONS[quiz_cat][:8]
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
    session['quiz_questions'] = questions[:8]
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
