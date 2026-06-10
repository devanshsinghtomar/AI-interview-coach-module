from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime
import json
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# Fixed imports - using correct class names
from utils.ai_helper import AIHelper
from utils.resume_parser import ResumeParser  # This now works
from utils.job_recommendation import JobRecommender
from utils.pdf_report import PDFReportGenerator
from utils.quiz_data import QuizData

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-this-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///interview.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please login to access this page.'

# Initialize helpers
ai_helper = AIHelper()
resume_parser = ResumeParser()
job_recommender = JobRecommender()
quiz_data = QuizData()

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    interviews = db.relationship('Interview', backref='user', lazy=True)
    resumes = db.relationship('ResumeAnalysis', backref='user', lazy=True)
    quiz_results = db.relationship('QuizResult', backref='user', lazy=True)

class Interview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_role = db.Column(db.String(100))
    experience_level = db.Column(db.String(50))
    questions_asked = db.Column(db.Text)
    answers_given = db.Column(db.Text)
    feedback = db.Column(db.Text)
    overall_score = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class ResumeAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(200))
    extracted_text = db.Column(db.Text)
    analysis_result = db.Column(db.Text)
    recommended_roles = db.Column(db.Text)
    score = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_role = db.Column(db.String(100))
    difficulty = db.Column(db.String(50))
    score = db.Column(db.Float)
    total_questions = db.Column(db.Integer)
    correct_answers = db.Column(db.Integer)
    answers_detail = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# Create tables
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password_hash=hashed_password)
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
        remember = request.form.get('remember', False)
        
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
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    total_interviews = Interview.query.filter_by(user_id=current_user.id).count()
    avg_score = db.session.query(db.func.avg(Interview.overall_score)).filter_by(user_id=current_user.id).scalar() or 0
    recent_interviews = Interview.query.filter_by(user_id=current_user.id).order_by(Interview.date.desc()).limit(5).all()
    resume_count = ResumeAnalysis.query.filter_by(user_id=current_user.id).count()
    quiz_count = QuizResult.query.filter_by(user_id=current_user.id).count()
    
    return render_template('dashboard.html', 
                         total_interviews=total_interviews,
                         avg_score=round(avg_score, 1),
                         recent_interviews=recent_interviews,
                         resume_count=resume_count,
                         quiz_count=quiz_count)

@app.route('/interview', methods=['GET', 'POST'])
@login_required
def interview():
    if request.method == 'POST':
        job_role = request.form['job_role']
        experience_level = request.form['experience_level']
        
        session['current_job_role'] = job_role
        session['current_experience'] = experience_level
        session['questions_asked'] = []
        session['answers'] = []
        session['current_question_index'] = 0
        
        question = ai_helper.generate_question(job_role, experience_level, session['questions_asked'])
        session['questions_asked'].append(question)
        session.modified = True
        
        return render_template('interview.html', 
                             question=question,
                             question_num=1,
                             job_role=job_role,
                             experience_level=experience_level)
    
    return render_template('interview.html', show_setup=True)

@app.route('/next_question', methods=['POST'])
@login_required
def next_question():
    data = request.json
    answer = data.get('answer')
    question = data.get('question')
    
    session['answers'].append(answer)
    
    feedback = ai_helper.evaluate_answer(question, answer, session['current_job_role'])
    
    if len(session['answers']) >= 5:
        total_score = sum(f.get('overall_score', 70) for f in [feedback])
        avg_score = total_score / len(session['answers'])
        
        interview_record = Interview(
            user_id=current_user.id,
            job_role=session['current_job_role'],
            experience_level=session['current_experience'],
            questions_asked=json.dumps(session['questions_asked']),
            answers_given=json.dumps(session['answers']),
            feedback=json.dumps(feedback),
            overall_score=avg_score
        )
        db.session.add(interview_record)
        db.session.commit()
        
        session.pop('questions_asked', None)
        session.pop('answers', None)
        
        return jsonify({
            'completed': True,
            'feedback': feedback,
            'overall_score': avg_score
        })
    
    next_q = ai_helper.generate_question(
        session['current_job_role'], 
        session['current_experience'],
        session['questions_asked']
    )
    session['questions_asked'].append(next_q)
    session.modified = True
    
    return jsonify({
        'completed': False,
        'next_question': next_q,
        'feedback': feedback
    })

@app.route('/resume', methods=['GET', 'POST'])
@login_required
def resume():
    if request.method == 'POST':
        if 'resume' not in request.files:
            flash('No file uploaded', 'danger')
            return redirect(url_for('resume'))
        
        file = request.files['resume']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(url_for('resume'))
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            extracted_text = resume_parser.parse_pdf(filepath)
            
            analysis = ai_helper.analyze_resume(extracted_text)
            
            recommendations = job_recommender.recommend_jobs(extracted_text, analysis)
            
            resume_record = ResumeAnalysis(
                user_id=current_user.id,
                filename=filename,
                extracted_text=extracted_text[:1000],
                analysis_result=json.dumps(analysis),
                recommended_roles=json.dumps(recommendations),
                score=analysis.get('overall_score', 0)
            )
            db.session.add(resume_record)
            db.session.commit()
            
            return render_template('resume_result.html', 
                                 analysis=analysis, 
                                 recommendations=recommendations)
    
    return render_template('resume_upload.html')

@app.route('/skill-assessment', methods=['GET', 'POST'])
@login_required
def skill_assessment():
    if request.method == 'POST':
        job_role = request.form['job_role']
        difficulty = request.form['difficulty']
        
        questions = quiz_data.get_questions(job_role, difficulty, limit=20)
        
        if not questions:
            flash('No questions available for this selection', 'warning')
            return redirect(url_for('skill_assessment'))
        
        session['quiz_questions'] = questions
        session['quiz_job_role'] = job_role
        session['quiz_difficulty'] = difficulty
        session['quiz_answers'] = []
        session['quiz_current'] = 0
        
        return render_template('quiz_take.html', 
                             question=questions[0],
                             question_num=1,
                             total=len(questions),
                             job_role=job_role,
                             difficulty=difficulty)
    
    job_roles = quiz_data.get_available_roles()
    return render_template('skill_assessment.html', job_roles=job_roles)

@app.route('/submit_answer', methods=['POST'])
@login_required
def submit_answer():
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
    
    if len(session['quiz_answers']) >= len(session['quiz_questions']):
        total_questions = len(session['quiz_answers'])
        correct_count = sum(1 for a in session['quiz_answers'] if a['is_correct'])
        score = (correct_count / total_questions) * 100
        
        quiz_result = QuizResult(
            user_id=current_user.id,
            job_role=session['quiz_job_role'],
            difficulty=session['quiz_difficulty'],
            score=score,
            total_questions=total_questions,
            correct_answers=correct_count,
            answers_detail=json.dumps(session['quiz_answers'])
        )
        db.session.add(quiz_result)
        db.session.commit()
        
        session.pop('quiz_questions', None)
        session.pop('quiz_answers', None)
        
        return jsonify({
            'completed': True,
            'score': score,
            'correct': correct_count,
            'total': total_questions
        })
    
    next_index = len(session['quiz_answers'])
    next_question = session['quiz_questions'][next_index]
    
    return jsonify({
        'completed': False,
        'next_question': next_question,
        'question_num': next_index + 1,
        'total': len(session['quiz_questions'])
    })

@app.route('/performance')
@login_required
def performance():
    interviews = Interview.query.filter_by(user_id=current_user.id).order_by(Interview.date).all()
    quizzes = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.date).all()
    resumes = ResumeAnalysis.query.filter_by(user_id=current_user.id).order_by(ResumeAnalysis.date.desc()).first()
    
    interview_dates = [i.date.strftime('%Y-%m-%d') for i in interviews]
    interview_scores = [i.overall_score for i in interviews]
    
    quiz_dates = [q.date.strftime('%Y-%m-%d') for q in quizzes]
    quiz_scores = [q.score for q in quizzes]
    
    return render_template('performance.html',
                         interviews=interviews,
                         quizzes=quizzes,
                         latest_resume=resumes,
                         interview_dates=json.dumps(interview_dates),
                         interview_scores=json.dumps(interview_scores),
                         quiz_dates=json.dumps(quiz_dates),
                         quiz_scores=json.dumps(quiz_scores))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
