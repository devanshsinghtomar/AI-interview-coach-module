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
import io
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///interview.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

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

# Interview Questions (15+ ROLES)
INTERVIEW_QUESTIONS = {
    'Python Developer': [
        {"question": "What is the difference between a list and a tuple?", "keywords": ["mutable", "immutable", "change", "modify"]},
        {"question": "What is a decorator in Python?", "keywords": ["function", "modify", "wrapper", "@"]},
        {"question": "Explain the Global Interpreter Lock (GIL).", "keywords": ["thread", "execution", "mutex", "concurrency"]},
        {"question": "What are list comprehensions?", "keywords": ["syntax", "loop", "expression", "list"]},
        {"question": "Explain the difference between deep and shallow copy.", "keywords": ["nested", "reference", "recursive", "copy"]},
    ],
    'JavaScript Developer': [
        {"question": "What is closure in JavaScript?", "keywords": ["inner function", "outer scope", "variables", "return"]},
        {"question": "Difference between == and ===?", "keywords": ["value", "type", "strict", "coercion"]},
        {"question": "What is hoisting?", "keywords": ["declaration", "move", "top", "var", "function"]},
        {"question": "Explain event delegation.", "keywords": ["bubbling", "parent", "child", "listener"]},
        {"question": "What is the difference between let, const, and var?", "keywords": ["scope", "block", "reassign", "temporal"]},
    ],
    'Data Scientist': [
        {"question": "Difference between supervised and unsupervised learning?", "keywords": ["labeled", "unlabeled", "output", "target"]},
        {"question": "What is overfitting?", "keywords": ["training", "noise", "generalization", "variance"]},
        {"question": "Explain bias-variance tradeoff.", "keywords": ["error", "complexity", "balance", "underfitting"]},
        {"question": "What is cross-validation?", "keywords": ["fold", "holdout", "validation", "testing"]},
        {"question": "Explain the difference between bagging and boosting.", "keywords": ["ensemble", "sequential", "parallel", "weight"]},
    ],
    'Full Stack Developer': [
        {"question": "What is REST API?", "keywords": ["representational", "state", "http", "endpoint"]},
        {"question": "Difference between SQL and NoSQL?", "keywords": ["structured", "schema", "scalability", "document"]},
        {"question": "Explain CORS.", "keywords": ["cross-origin", "resource", "sharing", "headers"]},
        {"question": "What is JWT?", "keywords": ["json", "token", "authentication", "claim"]},
        {"question": "Explain MVC architecture.", "keywords": ["model", "view", "controller", "pattern"]},
    ],
    'DevOps Engineer': [
        {"question": "What is Docker?", "keywords": ["container", "image", "isolate", "orchestration"]},
        {"question": "Explain CI/CD.", "keywords": ["continuous", "integration", "automation", "delivery"]},
        {"question": "What is Kubernetes?", "keywords": ["container", "orchestration", "pod", "cluster"]},
        {"question": "Explain Infrastructure as Code.", "keywords": ["terraform", "cloudformation", "automation", "version"]},
        {"question": "What is the difference between continuous delivery and deployment?", "keywords": ["automated", "manual", "release", "production"]},
    ],
    'Java Developer': [
        {"question": "Difference between abstract class and interface?", "keywords": ["implementation", "multiple", "inheritance", "abstract"]},
        {"question": "What is multithreading?", "keywords": ["concurrent", "threads", "parallel", "runnable"]},
        {"question": "Explain garbage collection.", "keywords": ["memory", "heap", "collector", "gc"]},
        {"question": "What is polymorphism?", "keywords": ["many", "forms", "override", "overload"]},
        {"question": "Explain the difference between ArrayList and LinkedList.", "keywords": ["array", "node", "index", "performance"]},
    ],
    'Cloud Engineer': [
        {"question": "What are cloud service models?", "keywords": ["iaas", "paas", "saas", "serverless"]},
        {"question": "Explain serverless computing.", "keywords": ["functions", "event-driven", "scale", "lambda"]},
        {"question": "What is the difference between scalability and elasticity?", "keywords": ["capacity", "automated", "demand", "resources"]},
        {"question": "Explain load balancer.", "keywords": ["traffic", "distribute", "server", "health"]},
        {"question": "What is a CDN?", "keywords": ["content", "delivery", "network", "cache"]},
    ],
    'Machine Learning Engineer': [
        {"question": "Explain AI vs ML vs DL.", "keywords": ["artificial", "intelligence", "deep", "learning"]},
        {"question": "What is transfer learning?", "keywords": ["pretrained", "fine-tune", "adapt", "weights"]},
        {"question": "Explain gradient descent.", "keywords": ["optimization", "minimize", "loss", "function"]},
        {"question": "What is regularization?", "keywords": ["overfitting", "penalty", "lasso", "ridge"]},
        {"question": "Explain the difference between precision and recall.", "keywords": ["accuracy", "false", "positive", "negative"]},
    ],
    'Frontend Developer': [
        {"question": "What is the DOM?", "keywords": ["document", "object", "model", "tree"]},
        {"question": "Explain flexbox.", "keywords": ["layout", "flexible", "container", "items"]},
        {"question": "What is responsive design?", "keywords": ["mobile", "screen", "viewport", "media"]},
        {"question": "Explain CSS specificity.", "keywords": ["id", "class", "element", "inline"]},
        {"question": "What is a virtual DOM?", "keywords": ["react", "render", "performance", "update"]},
    ],
    'Backend Developer': [
        {"question": "What is API rate limiting?", "keywords": ["throttle", "request", "limit", "429"]},
        {"question": "Explain database indexing.", "keywords": ["performance", "search", "b-tree", "optimize"]},
        {"question": "What is message queue?", "keywords": ["rabbitmq", "kafka", "async", "broker"]},
        {"question": "Explain ACID properties.", "keywords": ["atomicity", "consistency", "isolation", "durability"]},
        {"question": "What is a microservice?", "keywords": ["architecture", "independent", "deploy", "scalable"]},
    ],
    'Cybersecurity Analyst': [
        {"question": "What is a DDoS attack?", "keywords": ["distributed", "denial", "service", "traffic"]},
        {"question": "Explain encryption vs hashing.", "keywords": ["reversible", "one-way", "key", "salt"]},
        {"question": "What is XSS?", "keywords": ["cross-site", "scripting", "injection", "browser"]},
        {"question": "Explain SQL injection.", "keywords": ["query", "parameter", "sanitize", "prepared"]},
        {"question": "What is a firewall?", "keywords": ["network", "security", "filter", "traffic"]},
    ],
    'Product Manager': [
        {"question": "What is Agile methodology?", "keywords": ["sprint", "scrum", "iterative", "backlog"]},
        {"question": "Explain MVP.", "keywords": ["minimum", "viable", "product", "features"]},
        {"question": "What is a user story?", "keywords": ["feature", "requirement", "agile", "customer"]},
        {"question": "Explain KPI.", "keywords": ["performance", "metric", "measure", "goal"]},
        {"question": "What is market research?", "keywords": ["customer", "competition", "demand", "analysis"]},
    ],
}

# Quiz Questions
QUIZ_QUESTIONS = {
    'Python': [
        {"question": "What is the correct way to create a function?", "options": ["def myFunc():", "function myFunc():", "create myFunc():", "func myFunc():"], "correct": "def myFunc():", "explanation": "def keyword is used to define functions"},
        {"question": "What does len() function do?", "options": ["Returns length", "Converts to string", "Finds maximum", "Rounds number"], "correct": "Returns length", "explanation": "len() returns number of items in an object"},
        {"question": "Which operator is used for exponentiation?", "options": ["**", "^", "exp()", "&&"], "correct": "**", "explanation": "** is the exponentiation operator"},
        {"question": "What is the output of print(type(10))?", "options": ["<class 'int'>", "<class 'float'>", "<class 'str'>", "<class 'list'>"], "correct": "<class 'int'>", "explanation": "10 is an integer"},
        {"question": "How do you create a list?", "options": ["[1, 2, 3]", "(1, 2, 3)", "{1, 2, 3}", "<1, 2, 3>"], "correct": "[1, 2, 3]", "explanation": "Square brackets create lists"},
        {"question": "What is the correct while loop syntax?", "options": ["while x > y:", "while (x > y)", "x > y while {", "while x > y then:"], "correct": "while x > y:", "explanation": "Colon required after condition"},
        {"question": "What does append() do?", "options": ["Adds to end", "Removes item", "Inserts at start", "Sorts list"], "correct": "Adds to end", "explanation": "append() adds element to end of list"},
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

def extract_text_from_file(filepath):
    """Extract text from PDF and TXT files with better error handling"""
    text = ""
    try:
        if filepath.lower().endswith('.pdf'):
            with open(filepath, 'rb') as f:
                # Create PDF reader with error handling
                try:
                    reader = PyPDF2.PdfReader(f)
                    for page_num, page in enumerate(reader.pages):
                        try:
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + "\n"
                        except Exception as e:
                            print(f"Error extracting page {page_num}: {e}")
                            continue
                except Exception as e:
                    print(f"Error reading PDF: {e}")
                    return ""
        elif filepath.lower().endswith('.txt'):
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(filepath, 'r', encoding=encoding, errors='ignore') as f:
                        text = f.read()
                    break
                except:
                    continue
        else:
            return ""
        
        # Clean up text
        text = re.sub(r'\s+', ' ', text)  # Replace multiple whitespace with single space
        text = text.strip()
        
        return text
    except Exception as e:
        print(f"Extraction error: {e}")
        return ""

def analyze_resume(text):
    """Analyze resume content with improved scoring"""
    if not text or len(text.strip()) < 50:
        return {
            'best_role': 'General Professional',
            'best_score': 30,
            'suitable_roles': [],
            'strengths': ['📄 Resume uploaded successfully'],
            'improvements': ['📈 Add more content to your resume (minimum 50 characters)', '📈 Include technical skills and keywords'],
            'skills': [],
            'word_count': len(text.split()) if text else 0
        }
    
    text_lower = text.lower()
    
    role_keywords = {
        'Python Developer': ['python', 'django', 'flask', 'pandas', 'numpy', 'fastapi', 'pytest', 'scipy'],
        'JavaScript Developer': ['javascript', 'react', 'angular', 'vue', 'node', 'express', 'typescript', 'jquery'],
        'Data Scientist': ['data science', 'machine learning', 'python', 'analytics', 'sql', 'statistics', 'pandas', 'scikit-learn'],
        'Full Stack Developer': ['react', 'angular', 'node', 'html', 'css', 'mongodb', 'express', 'api', 'frontend', 'backend'],
        'DevOps Engineer': ['docker', 'kubernetes', 'jenkins', 'aws', 'ci/cd', 'terraform', 'linux', 'ansible'],
        'Java Developer': ['java', 'spring', 'hibernate', 'maven', 'gradle', 'junit', 'eclipse', 'intellij'],
        'Cloud Engineer': ['aws', 'azure', 'gcp', 'cloud', 'terraform', 'lambda', 'ec2', 's3', 'cloudformation'],
        'Machine Learning Engineer': ['machine learning', 'deep learning', 'tensorflow', 'keras', 'pytorch', 'nlp', 'cv'],
        'Frontend Developer': ['react', 'vue', 'angular', 'css', 'html', 'javascript', 'bootstrap', 'tailwind'],
        'Backend Developer': ['node', 'python', 'java', 'api', 'database', 'sql', 'redis', 'microservices', 'rest'],
        'Cybersecurity Analyst': ['security', 'firewall', 'encryption', 'vulnerability', 'penetration', 'cissp', 'network'],
        'Product Manager': ['product', 'agile', 'scrum', 'roadmap', 'user story', 'jira', 'market', 'product management'],
    }
    
    # Calculate scores
    scores = {}
    matched_skills = {}
    for role, keywords in role_keywords.items():
        score = 0
        matched = []
        for kw in keywords:
            # Count occurrences (more occurrences = better match)
            count = text_lower.count(kw)
            if count > 0:
                score += min(20, count * 8)  # Max 20 points per keyword
                matched.append(kw)
        scores[role] = min(100, score)
        matched_skills[role] = matched
    
    # Find best match (if all scores are 0, return default)
    if max(scores.values()) == 0:
        best_role = "General Professional"
        best_score = 30
    else:
        best_role = max(scores, key=scores.get)
        best_score = scores.get(best_role, 30)
    
    # Get suitable roles (score >= 20)
    suitable_roles = []
    for role, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        if score >= 20 and role != best_role:
            suitable_roles.append({
                'role': role,
                'score': score,
                'skills': matched_skills.get(role, [])[:3]
            })
    
    # Generate strengths
    strengths = []
    word_count = len(text.split())
    
    if word_count > 300:
        strengths.append("✅ Good resume length and detail")
    elif word_count > 150:
        strengths.append("✅ Adequate resume content")
    else:
        strengths.append("📄 Resume uploaded - consider adding more detail")
    
    if '@' in text and '.' in text:
        strengths.append("✅ Contact information included")
    
    if best_score >= 60:
        strengths.append(f"✅ Good match for {best_role}")
    elif best_score >= 40:
        strengths.append(f"✅ Potential fit for {best_role}")
    
    # Generate improvements
    improvements = []
    
    if word_count < 200:
        improvements.append("📈 Add more details about your experience and skills")
    
    if best_score < 40:
        improvements.append(f"📈 Add more keywords related to {best_role}")
    
    # Check for missing common sections
    if 'experience' not in text_lower and 'work' not in text_lower:
        improvements.append("📈 Add work experience section")
    
    if 'education' not in text_lower and 'degree' not in text_lower and 'university' not in text_lower:
        improvements.append("📈 Add education qualifications")
    
    # Ensure we have at least one improvement
    if not improvements:
        improvements = ["📈 Consider adding more technical skills and quantifiable achievements"]
    
    if not strengths:
        strengths = ["✅ Resume uploaded successfully"]
    
    # Get unique skills found
    all_skills = []
    for skills in matched_skills.values():
        all_skills.extend(skills)
    unique_skills = list(set(all_skills))[:12]
    
    return {
        'best_role': best_role,
        'best_score': best_score,
        'suitable_roles': suitable_roles[:5],
        'strengths': strengths[:5],
        'improvements': improvements[:5],
        'skills': unique_skills if unique_skills else ['General Skills', 'Communication', 'Problem Solving'],
        'word_count': word_count
    }

def evaluate_answer(question, answer, role):
    """Evaluate answer"""
    answer_lower = answer.lower().strip()
    
    if len(answer_lower.split()) < 5:
        return 15, "❌ Answer too short. Please provide more details."
    
    # Find the question in INTERVIEW_QUESTIONS
    for q in INTERVIEW_QUESTIONS.get(role, []):
        if q['question'] == question:
            keywords = q['keywords']
            matched = [kw for kw in keywords if kw in answer_lower]
            
            if not matched:
                return 25, f"❌ Needs improvement. Key concepts to mention: {', '.join(keywords[:3])}"
            
            # Calculate score based on keyword matches
            score = int((len(matched) / len(keywords)) * 90) + 10
            score = min(95, score)
            
            if score >= 85:
                feedback = f"✅ Excellent! You covered: {', '.join(matched)}"
            elif score >= 70:
                missing = [kw for kw in keywords if kw not in answer_lower][:2]
                feedback = f"👍 Good! Consider mentioning: {', '.join(missing)}"
            elif score >= 50:
                feedback = f"📝 Fair answer. Missing key concepts like: {', '.join(keywords[:2])}"
            else:
                feedback = f"⚠️ Needs improvement. Expected keywords: {', '.join(keywords)}"
            
            return score, feedback
    
    return 50, "Good attempt! Keep practicing."

# Routes
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
        
        if not all([username, email, password]):
            flash('All fields are required', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
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
    interviews = Interview.query.filter_by(user_id=current_user.id).all()
    quizzes = QuizResult.query.filter_by(user_id=current_user.id).all()
    resumes = ResumeAnalysis.query.filter_by(user_id=current_user.id).all()
    
    total_interviews = len(interviews)
    avg_score = sum(i.score for i in interviews) / total_interviews if total_interviews > 0 else 0
    total_quizzes = len(quizzes)
    avg_quiz = sum(q.score for q in quizzes) / total_quizzes if total_quizzes > 0 else 0
    latest_resume = resumes[-1].score if resumes else 0
    
    recent_interviews = interviews[-5:] if interviews else []
    recent_quizzes = quizzes[-5:] if quizzes else []
    
    return render_template('dashboard.html',
                         total_interviews=total_interviews,
                         avg_score=round(avg_score, 1),
                         total_quizzes=total_quizzes,
                         avg_quiz=round(avg_quiz, 1),
                         resume_score=latest_resume,
                         recent_interviews=recent_interviews,
                         recent_quizzes=recent_quizzes)

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
        flash('Please select a role', 'danger')
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
            # Get score for this specific answer
            q_score, q_feedback = evaluate_answer(item['question'], item['answer'], role)
            interview = Interview(
                user_id=current_user.id,
                job_role=role,
                question=item['question'],
                answer=item['answer'][:1000],
                score=q_score,
                feedback=q_feedback
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
        
        # Check file extension
        allowed_extensions = {'.pdf', '.txt'}
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_extensions:
            flash('Please upload PDF or TXT file only', 'danger')
            return redirect(url_for('resume_analysis'))
        
        try:
            # Save file temporarily
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Extract text
            text = extract_text_from_file(filepath)
            
            # Clean up - remove temp file
            try:
                os.remove(filepath)
            except:
                pass
            
            # Check if text extraction was successful
            if not text or len(text.strip()) < 30:
                flash('Could not extract text from file. Please ensure the file is not corrupted or try a different file.', 'warning')
                return redirect(url_for('resume_analysis'))
            
            # Analyze resume
            analysis = analyze_resume(text)
            
            # Save to database
            resume = ResumeAnalysis(
                user_id=current_user.id,
                filename=filename,
                extracted_text=text[:3000],
                score=analysis['best_score'],
                suggested_role=analysis['best_role'],
                suggested_roles=json.dumps(analysis['suitable_roles']),
                strengths=json.dumps(analysis['strengths']),
                improvements=json.dumps(analysis['improvements']),
                skills_found=json.dumps(analysis['skills'])
            )
            db.session.add(resume)
            db.session.commit()
            
            flash(f'✅ Resume analyzed! Best match: {analysis["best_role"]} ({analysis["best_score"]}%)', 'success')
            return render_template('resume_results.html', analysis=analysis)
            
        except Exception as e:
            print(f"Error in resume analysis: {str(e)}")
            flash(f'Error analyzing resume: {str(e)[:100]}', 'danger')
            return redirect(url_for('resume_analysis'))
    
    return render_template('resume_analysis.html')

@app.route('/start-from-resume', methods=['POST'])
@login_required
def start_from_resume():
    role = request.form.get('role')
    action = request.form.get('action')
    
    if not role:
        flash('Role not specified', 'danger')
        return redirect(url_for('resume_analysis'))
    
    if action == 'interview':
        # Get questions for the role
        questions = [q['question'] for q in INTERVIEW_QUESTIONS.get(role, [])]
        if not questions:
            flash(f'No interview questions available for {role}', 'warning')
            return redirect(url_for('resume_analysis'))
        
        random.shuffle(questions)
        session['interview_role'] = role
        session['interview_questions'] = questions[:4]
        session['interview_answers'] = []
        session['interview_scores'] = []
        session['interview_current'] = 0
        return redirect(url_for('take_interview'))
    
    elif action == 'quiz':
        # Find matching quiz category
        quiz_cat = 'Python'  # default
        for cat in QUIZ_QUESTIONS.keys():
            if cat.lower() in role.lower() or role.lower() in cat.lower():
                quiz_cat = cat
                break
        
        questions = QUIZ_QUESTIONS.get(quiz_cat, QUIZ_QUESTIONS['Python'])[:8]
        random.shuffle(questions)
        session['quiz_category'] = f"{role} Quiz"
        session['quiz_questions'] = questions
        session['quiz_answers'] = []
        session['quiz_current'] = 0
        return redirect(url_for('take_quiz'))
    
    flash('Invalid action', 'danger')
    return redirect(url_for('resume_analysis'))

@app.route('/skill-quiz')
@login_required
def skill_quiz():
    categories = list(QUIZ_QUESTIONS.keys())
    return render_template('skill_quiz.html', categories=categories)

@app.route('/start-quiz', methods=['POST'])
@login_required
def start_quiz():
    category = request.form.get('category')
    if not category or category not in QUIZ_QUESTIONS:
        flash('Invalid quiz category', 'danger')
        return redirect(url_for('skill_quiz'))
    
    questions = QUIZ_QUESTIONS[category][:8]
    random.shuffle(questions)
    
    session['quiz_category'] = category
    session['quiz_questions'] = questions
    session['quiz_answers'] = []
    session['quiz_current'] = 0
    
