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

# ============ REAL INTERVIEW QUESTIONS WITH CORRECT ANSWERS ============
INTERVIEW_QUESTIONS_WITH_ANSWERS = {
    'Python Developer': [
        {
            "question": "What is the difference between a list and a tuple in Python?",
            "keywords": ["mutable", "immutable", "change", "modify", "fixed"],
            "sample_answer": "Lists are mutable (can be changed after creation) while tuples are immutable (cannot be changed). Lists use square brackets [], tuples use parentheses ()."
        },
        {
            "question": "What is a decorator in Python and how do you use it?",
            "keywords": ["function", "modify", "wrapper", "@", "syntax"],
            "sample_answer": "A decorator is a function that takes another function and extends its behavior without explicitly modifying it. It's used with @ syntax."
        },
        {
            "question": "Explain the Global Interpreter Lock (GIL) in Python.",
            "keywords": ["mutex", "thread", "execution", "bytecode", "simultaneously"],
            "sample_answer": "The GIL is a mutex that prevents multiple threads from executing Python bytecode at once, making CPython thread-safe for memory management."
        },
        {
            "question": "What is list comprehension? Give an example.",
            "keywords": ["concise", "create", "list", "loop", "condition"],
            "sample_answer": "List comprehension provides a concise way to create lists. Example: [x*2 for x in range(5)] creates [0,2,4,6,8]."
        },
        {
            "question": "How does exception handling work in Python?",
            "keywords": ["try", "except", "finally", "raise", "error"],
            "sample_answer": "Exception handling uses try-except blocks. Code that might raise an exception goes in try block, and error handling in except block."
        }
    ],
    'JavaScript Developer': [
        {
            "question": "What is closure in JavaScript?",
            "keywords": ["inner function", "outer scope", "variables", "return", "access"],
            "sample_answer": "A closure is a function that has access to its outer function's scope even after the outer function has returned."
        },
        {
            "question": "Explain the difference between == and === in JavaScript.",
            "keywords": ["value", "type", "strict", "equality", "comparison"],
            "sample_answer": "== compares only value after type coercion, while === compares both value and type without coercion."
        },
        {
            "question": "What is hoisting in JavaScript?",
            "keywords": ["declaration", "move", "top", "scope", "var"],
            "sample_answer": "Hoisting is JavaScript's behavior of moving declarations to the top of their scope during compilation."
        }
    ],
    'Data Scientist': [
        {
            "question": "What is the difference between supervised and unsupervised learning?",
            "keywords": ["labeled", "unlabeled", "output", "target", "training"],
            "sample_answer": "Supervised learning uses labeled data with known outputs, while unsupervised learning finds patterns in unlabeled data."
        },
        {
            "question": "What is overfitting and how do you prevent it?",
            "keywords": ["training", "noise", "generalization", "regularization", "validation"],
            "sample_answer": "Overfitting occurs when a model learns training data too well including noise. Prevent with cross-validation, regularization, or more data."
        }
    ]
}

# ============ REAL QUIZ QUESTIONS WITH CORRECT OPTIONS ============
QUIZ_QUESTIONS = {
    'Python': [
        {
            "question": "What is the correct way to create a function in Python?",
            "options": ["def myFunction():", "function myFunction():", "create myFunction():", "func myFunction():"],
            "correct": "def myFunction():",
            "explanation": "In Python, functions are defined using the 'def' keyword."
        },
        {
            "question": "What does the 'len()' function do in Python?",
            "options": ["Returns the length of an object", "Converts to lowercase", "Rounds a number", "Finds the maximum value"],
            "correct": "Returns the length of an object",
            "explanation": "len() returns the number of items in a container."
        },
        {
            "question": "Which operator is used for exponentiation in Python?",
            "options": ["**", "^", "exp()", "&&"],
            "correct": "**",
            "explanation": "** is the exponentiation operator (e.g., 2**3 = 8)."
        },
        {
            "question": "What is the output of print(type(10)) in Python?",
            "options": ["<class 'int'>", "<class 'float'>", "<class 'str'>", "<class 'list'>"],
            "correct": "<class 'int'>",
            "explanation": "10 is an integer, so type() returns int class."
        },
        {
            "question": "How do you create a list in Python?",
            "options": ["my_list = [1, 2, 3]", "my_list = (1, 2, 3)", "my_list = {1, 2, 3}", "my_list = <1, 2, 3>"],
            "correct": "my_list = [1, 2, 3]",
            "explanation": "Lists are created using square brackets []."
        },
        {
            "question": "What is the correct syntax for a while loop in Python?",
            "options": ["while x > y:", "while (x > y)", "x > y while {", "while x > y then:"],
            "correct": "while x > y:",
            "explanation": "while loops use the syntax 'while condition:'."
        },
        {
            "question": "What does the 'append()' method do to a list?",
            "options": ["Adds an element to the end", "Removes an element", "Inserts at beginning", "Sorts the list"],
            "correct": "Adds an element to the end",
            "explanation": "append() adds an element to the end of a list."
        },
        {
            "question": "What is the result of 10 // 3 in Python?",
            "options": ["3", "3.33", "3.0", "1"],
            "correct": "3",
            "explanation": "// is floor division, which returns the integer quotient."
        },
        {
            "question": "Which keyword is used to define a class in Python?",
            "options": ["class", "def", "object", "struct"],
            "correct": "class",
            "explanation": "Classes are defined using the 'class' keyword."
        },
        {
            "question": "What does the 'break' statement do?",
            "options": ["Exits the loop", "Skips current iteration", "Pauses the loop", "Restarts the loop"],
            "correct": "Exits the loop",
            "explanation": "break terminates the loop completely."
        }
    ],
    'JavaScript': [
        {
            "question": "How do you declare a variable in JavaScript?",
            "options": ["let x;", "variable x;", "v x;", "declare x;"],
            "correct": "let x;",
            "explanation": "let, const, and var are used to declare variables."
        },
        {
            "question": "What does 'console.log()' do?",
            "options": ["Prints to console", "Shows an alert", "Returns a value", "Creates a log file"],
            "correct": "Prints to console",
            "explanation": "console.log() outputs messages to the browser's console."
        },
        {
            "question": "What is the correct way to write a function in JavaScript?",
            "options": ["function myFunction() {}", "def myFunction() {}", "create myFunction() {}", "func myFunction() {}"],
            "correct": "function myFunction() {}",
            "explanation": "Functions are defined using the 'function' keyword."
        }
    ],
    'SQL': [
        {
            "question": "What does SQL stand for?",
            "options": ["Structured Query Language", "Simple Query Language", "Standard Query Language", "System Query Language"],
            "correct": "Structured Query Language",
            "explanation": "SQL stands for Structured Query Language."
        },
        {
            "question": "Which SQL statement is used to extract data from a database?",
            "options": ["SELECT", "EXTRACT", "GET", "OPEN"],
            "correct": "SELECT",
            "explanation": "SELECT retrieves data from database tables."
        },
        {
            "question": "What does the WHERE clause do?",
            "options": ["Filters records", "Sorts records", "Groups records", "Joins tables"],
            "correct": "Filters records",
            "explanation": "WHERE clause filters records based on conditions."
        }
    ]
}

# ============ RESUME PARSER FUNCTIONS ============
def extract_text_from_pdf(filepath):
    try:
        with open(filepath, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
            return text
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return ""

def analyze_resume_content(text):
    text_lower = text.lower()
    
    # Role matching
    role_keywords = {
        'Python Developer': ['python', 'django', 'flask', 'pandas', 'numpy'],
        'JavaScript Developer': ['javascript', 'react', 'angular', 'vue', 'node'],
        'Data Scientist': ['data science', 'machine learning', 'python', 'analytics', 'statistics'],
        'Full Stack Developer': ['react', 'node', 'html', 'css', 'javascript', 'mongodb'],
        'DevOps Engineer': ['docker', 'kubernetes', 'aws', 'jenkins', 'ci/cd'],
        'Java Developer': ['java', 'spring', 'hibernate', 'maven', 'j2ee']
    }
    
    # Score each role
    role_scores = {}
    for role, keywords in role_keywords.items():
        score = 0
        for keyword in keywords:
            if keyword in text_lower:
                score += 15
        role_scores[role] = min(score, 100)
    
    # Get best match
    best_role = max(role_scores, key=role_scores.get) if role_scores else "Python Developer"
    best_score = role_scores.get(best_role, 50)
    
    # Get other suggestions
    suggested_roles = []
    for role, score in sorted(role_scores.items(), key=lambda x: x[1], reverse=True)[:3]:
        if score >= 30 and role != best_role:
            suggested_roles.append({
                'role': role,
                'match_percentage': score,
                'matched_skills': [k for k in role_keywords[role] if k in text_lower][:3]
            })
    
    # Generate strengths
    strengths = []
    if len(text) > 500:
        strengths.append("Resume has good length and detail")
    if '@' in text:
        strengths.append("Contact information included")
    if 'github' in text_lower or 'linkedin' in text_lower:
        strengths.append("Professional links included")
    
    # Generate improvements
    improvements = []
    if len(text) < 300:
        improvements.append("Add more details about your experience and skills")
    if best_score < 50:
        improvements.append(f"Add more {best_role}-specific keywords to your resume")
    
    return {
        'overall_score': best_score,
        'best_role': best_role,
        'suggested_roles': suggested_roles,
        'strengths': strengths if strengths else ["Resume uploaded successfully"],
        'improvements': improvements if improvements else ["Consider adding more quantifiable achievements"],
        'skills_found': list(set([k for keywords in role_keywords.values() for k in keywords if k in text_lower]))[:8],
        'word_count': len(text.split())
    }

# ============ ANSWER EVALUATION FUNCTION ============
def evaluate_answer(question_text, user_answer, job_role):
    """Evaluate answer based on keywords presence"""
    user_answer_lower = user_answer.lower()
    
    # Find the question in database
    question_data = None
    for q in INTERVIEW_QUESTIONS_WITH_ANSWERS.get(job_role, []):
        if q["question"] == question_text:
            question_data = q
            break
    
    if not question_data:
        # Default scoring if question not found
        word_count = len(user_answer.split())
        if word_count > 50:
            return 75, "Good length, but could be more specific to the question."
        elif word_count > 20:
            return 55, "Answer is brief. Add more details."
        else:
            return 35, "Answer is too short. Please provide more detailed response."
    
    # Evaluate based on keywords
    keywords = question_data["keywords"]
    matched_keywords = sum(1 for kw in keywords if kw.lower() in user_answer_lower)
    score = int((matched_keywords / len(keywords)) * 100)
    
    # Adjust score based on answer length
    word_count = len(user_answer.split())
    if word_count < 10:
        score = max(20, score - 20)
    elif word_count > 100:
        score = min(95, score + 10)
    
    # Generate feedback
    if score >= 80:
        feedback = f"Excellent! You covered key points including: {', '.join(keywords[:2])}. Great understanding!"
    elif score >= 60:
        missing = [kw for kw in keywords if kw.lower() not in user_answer_lower][:2]
        feedback = f"Good answer. Consider mentioning: {', '.join(missing)} to improve."
    elif score >= 40:
        feedback = f"Fair answer. Key concepts missing. Focus on: {', '.join(keywords[:3])}"
    else:
        feedback = f"Answer needs improvement. The question expects discussion of: {', '.join(keywords)}"
    
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
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
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
    
    return render_template('dashboard.html',
                         total_interviews=total_interviews,
                         avg_score=round(avg_score, 1),
                         quiz_count=quiz_count,
                         avg_quiz_score=round(avg_quiz_score, 1),
                         resume_score=latest_resume.score if latest_resume else 0,
                         recent_interviews=recent_interviews)

# ============ MOCK INTERVIEW ROUTES ============
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
        flash('Please select a role', 'danger')
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
    
    # Evaluate answer
    score, feedback = evaluate_answer(question, answer, role)
    
    session['interview_answers'].append({'question': question, 'answer': answer, 'score': score})
    session['interview_scores'].append(score)
    session['interview_feedbacks'].append(feedback)
    session['interview_current'] = session.get('interview_current', 0) + 1
    session.modified = True
    
    questions = session.get('interview_questions', [])
    current_idx = session.get('interview_current', 0)
    
    if current_idx >= len(questions):
        # Save to database
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
        
        # Clear session
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
        
        if not file.filename.endswith('.pdf'):
            flash('Please upload a PDF file', 'danger')
            return redirect(url_for('resume_analysis'))
        
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Extract text from PDF
            extracted_text = extract_text_from_pdf(filepath)
            
            if not extracted_text or len(extracted_text.strip()) < 50:
                flash('Could not extract text from PDF. Please ensure it\'s a valid text-based PDF.', 'danger')
                os.remove(filepath)
                return redirect(url_for('resume_analysis'))
            
            # Analyze resume
            analysis = analyze_resume_content(extracted_text)
            
            # Save to database
            resume_record = ResumeAnalysis(
                user_id=current_user.id,
                filename=filename,
                extracted_text=extracted_text[:1000],
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
            
        except Exception as e:
            print(f"Resume analysis error: {str(e)}")
            flash('Error analyzing resume. Please try again.', 'danger')
            return redirect(url_for('resume_analysis'))
    
    return render_template('resume_analysis.html')

# ============ HELPER ROUTES ============
@app.route('/start-mock-interview-direct', methods=['POST'])
@login_required
def start_mock_interview_direct():
    role = request.form.get('role')
    if not role:
        flash('No role specified', 'danger')
        return redirect(url_for('resume_analysis'))
    
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
    if not category:
        flash('No category specified', 'danger')
        return redirect(url_for('resume_analysis'))
    
    all_questions = QUIZ_QUESTIONS.get(category, [])
    if not all_questions:
        flash('No questions available', 'danger')
        return redirect(url_for('skill_quiz'))
    
    selected_questions = random.sample(all_questions, min(5, len(all_questions)))
    
    session['quiz_category'] = category
    session['quiz_questions'] = selected_questions
    session['quiz_answers'] = []
    session['quiz_current'] = 0
    
    return redirect(url_for('take_quiz'))

# ============ QUIZ ROUTES ============
@app.route('/skill-quiz')
@login_required
def skill_quiz():
    categories = list(QUIZ_QUESTIONS.keys())
    return render_template('skill_quiz.html', categories=categories)

@app.route('/start-quiz', methods=['POST'])
@login_required
def start_quiz():
    category = request.form.get('category')
    all_questions = QUIZ_QUESTIONS.get(category, [])
    
    if not all_questions:
        flash('No questions available', 'danger')
        return redirect(url_for('skill_quiz'))
    
    selected_questions = random.sample(all_questions, min(5, len(all_questions)))
    
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
            difficulty='intermediate',
            score=score,
            total_questions=len(questions),
            correct_answers=correct_count
        )
        db.session.add(quiz_result)
        db.session.commit()
        
        result = {'completed': True, 'score': score, 'correct': correct_count, 'total': len(questions)}
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
