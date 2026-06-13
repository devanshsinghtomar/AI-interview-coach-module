from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime
import json
import os
import random
import PyPDF2
from werkzeug.utils import secure_filename

from utils.role_data import (
    ROLES, ROLE_INFO, ROLE_KEYWORDS, QUIZ_CATEGORY_INFO, QUIZ_CATEGORIES,
    ROLE_TO_QUIZ_CATEGORY, DIFFICULTIES,
)
from utils.interview_bank import INTERVIEW_QUESTIONS
from utils.quiz_bank import QUIZ_QUESTIONS

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

INTERVIEW_QUESTION_COUNTS = [4, 6, 8]
QUIZ_QUESTION_COUNTS = [5, 8]


# ============================================================
# DATABASE MODELS
# ============================================================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Interview(db.Model):
    """One row per individual interview question that was answered."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_role = db.Column(db.String(100))
    question = db.Column(db.Text)
    answer = db.Column(db.Text)
    score = db.Column(db.Integer)
    feedback = db.Column(db.Text)
    difficulty = db.Column(db.String(20), default='Medium')
    date = db.Column(db.DateTime, default=datetime.utcnow)


class InterviewSession(db.Model):
    """One row per completed mock-interview attempt (for progress tracking)."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_role = db.Column(db.String(100))
    difficulty = db.Column(db.String(20), default='Medium')
    mode = db.Column(db.String(10), default='text')
    num_questions = db.Column(db.Integer, default=0)
    avg_score = db.Column(db.Float, default=0)
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
    """One row per completed skill-quiz attempt."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(100))
    difficulty = db.Column(db.String(20), default='Medium')
    score = db.Column(db.Integer)
    total_questions = db.Column(db.Integer)
    correct_answers = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.context_processor
def inject_globals():
    return {'current_year': datetime.utcnow().year}


# ============================================================
# HELPERS -- INTERVIEW
# ============================================================
def find_question_meta(role, question_text):
    """Locate a question's bank entry (keywords + its actual difficulty)."""
    role_bank = INTERVIEW_QUESTIONS.get(role, {})
    for diff, questions in role_bank.items():
        for q in questions:
            if q['question'] == question_text:
                return q, diff
    return None, None


def select_interview_questions(role, difficulty, count):
    """Pick `count` question strings for a role at the chosen difficulty.

    'Mixed' draws from every difficulty. A single difficulty draws from that
    tier first and tops up from the other tiers if the tier is smaller than
    `count`, so the requested question count is always honoured.
    """
    role_bank = INTERVIEW_QUESTIONS.get(role, {})

    if difficulty == 'Mixed':
        primary = [q['question'] for d in DIFFICULTIES for q in role_bank.get(d, [])]
        others = []
    else:
        primary = [q['question'] for q in role_bank.get(difficulty, [])]
        others = [q['question'] for d in DIFFICULTIES if d != difficulty
                  for q in role_bank.get(d, [])]

    if len(primary) >= count:
        return random.sample(primary, count)

    chosen = list(primary)
    needed = count - len(chosen)
    if needed > 0 and others:
        chosen += random.sample(others, min(needed, len(others)))
    random.shuffle(chosen)
    return chosen


def evaluate_answer(question, answer, role):
    """Lightweight keyword-coverage scoring with constructive feedback."""
    answer = (answer or "").strip()
    answer_lower = answer.lower()
    word_count = len(answer_lower.split())

    if word_count == 0:
        return 0, "No answer was recorded for this question."

    if word_count < 5:
        return 10, "That answer is quite brief. Try explaining your reasoning in a full sentence or two."

    q_meta, _ = find_question_meta(role, question)
    if not q_meta:
        return 50, "Thanks for sharing your thoughts on this one."

    keywords = q_meta['keywords']
    matched = [kw for kw in keywords if kw in answer_lower]
    missing = [kw for kw in keywords if kw not in matched]

    if not matched:
        return 20, f"Consider mentioning concepts like: {', '.join(keywords[:4])}."

    score = max(35, min(95, int(round((len(matched) / len(keywords)) * 100))))

    if score >= 85:
        feedback = f"Excellent answer! You clearly covered: {', '.join(matched)}."
    elif score >= 65:
        feedback = (f"Good answer -- you covered {', '.join(matched)}. "
                     f"For an even stronger response, also mention {', '.join(missing[:2])}.")
    else:
        feedback = (f"You're on the right track with {', '.join(matched)}, "
                     f"but a complete answer should also cover {', '.join(missing)}.")

    return score, feedback


# ============================================================
# HELPERS -- SKILL QUIZ
# ============================================================
def select_quiz_questions(category, difficulty, count):
    """Pick `count` quiz questions, preferring ones not seen recently by the
    user in this session, and shuffle each question's option order.
    """
    pool = QUIZ_QUESTIONS.get(category, {}).get(difficulty, [])
    if not pool:
        return []

    count = min(count, len(pool))
    key = f"{category}|{difficulty}"
    seen_map = session.get('quiz_seen', {})
    seen_ids = set(seen_map.get(key, []))

    unseen = [q for q in pool if q['id'] not in seen_ids]
    if len(unseen) >= count:
        chosen = random.sample(unseen, count)
    else:
        chosen = list(unseen)
        remaining_ids = {q['id'] for q in chosen}
        remaining_pool = [q for q in pool if q['id'] not in remaining_ids]
        needed = count - len(chosen)
        chosen += random.sample(remaining_pool, min(needed, len(remaining_pool)))

    # Update "recently seen" tracking, cycling once the whole pool is covered.
    new_seen_ids = list({q['id'] for q in chosen} | seen_ids)
    if len(new_seen_ids) >= len(pool):
        new_seen_ids = [q['id'] for q in chosen]
    seen_map[key] = new_seen_ids
    session['quiz_seen'] = seen_map

    result = []
    for q in chosen:
        q_copy = dict(q)
        opts = list(q['options'])
        random.shuffle(opts)
        q_copy['options'] = opts
        result.append(q_copy)
    random.shuffle(result)
    return result


# ============================================================
# HELPERS -- RESUME ANALYSIS
# ============================================================
def extract_text_from_file(filepath):
    """Extract text from PDF and TXT resume files."""
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
    except Exception as e:
        print(f"Extraction error: {e}")
        text = ""
    return text


def analyze_resume(text):
    """Score a resume against every role and build a feedback report."""
    text_lower = text.lower()

    scores, matched_skills = {}, {}
    for role, keywords in ROLE_KEYWORDS.items():
        matched = [kw for kw in keywords if kw in text_lower]
        scores[role] = min(len(matched) * 15, 100)
        matched_skills[role] = matched

    best_role = max(scores, key=scores.get) if scores else ROLES[0]
    best_score = scores.get(best_role, 50)

    suitable_roles = []
    for role, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        if role == best_role:
            continue
        if score >= 25:
            suitable_roles.append({
                'role': role,
                'score': score,
                'skills': matched_skills.get(role, [])[:4],
                'icon': ROLE_INFO.get(role, {}).get('icon', 'fa-solid fa-briefcase'),
                'color': ROLE_INFO.get(role, {}).get('color', '#94a3b8'),
            })

    word_count = len(text.split())

    strengths = []
    if word_count > 150:
        strengths.append("Good resume length and level of detail")
    if '@' in text:
        strengths.append("Contact information is included")
    if best_score >= 70:
        strengths.append(f"Strong keyword match for {best_role}")
    if len(suitable_roles) >= 2:
        strengths.append("Your skills span multiple roles, giving you flexibility")
    if not strengths:
        strengths.append("Resume uploaded and analyzed successfully")

    improvements = []
    if word_count < 150:
        improvements.append("Add more detail about your experience and projects")
    if best_score < 50:
        improvements.append(f"Add more {best_role}-specific keywords and tools")
    if '@' not in text:
        improvements.append("Include an email address so recruiters can reach you")
    if not any(ch.isdigit() for ch in text):
        improvements.append("Quantify your achievements with numbers and metrics")
    if not improvements:
        improvements.append("Keep tailoring your keywords to each job description")

    all_skills = []
    for skills in matched_skills.values():
        all_skills.extend(skills)
    unique_skills = sorted(set(all_skills))[:12]

    return {
        'best_role': best_role,
        'best_score': best_score,
        'suitable_roles': suitable_roles[:5],
        'strengths': strengths[:4],
        'improvements': improvements[:4],
        'skills': unique_skills,
        'word_count': word_count,
        'role_info': ROLE_INFO.get(best_role, {}),
        'quiz_category': ROLE_TO_QUIZ_CATEGORY.get(best_role, 'Python'),
    }


# ============================================================
# HELPERS -- ANALYTICS
# ============================================================
def _avg_by(records, key_attr, val_attr, rounding=1):
    buckets = {}
    for r in records:
        buckets.setdefault(getattr(r, key_attr), []).append(getattr(r, val_attr))
    return {k: round(sum(v) / len(v), rounding) for k, v in buckets.items()}


# ============================================================
# CORE ROUTES
# ============================================================
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        email = (request.form.get('email') or '').strip()
        password = request.form.get('password') or ''
        confirm = request.form.get('confirm_password') or ''

        if not username or not email or not password:
            flash('Please fill in every field.', 'danger')
            return redirect(url_for('register'))

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Password should be at least 6 characters long.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('That username is already taken.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('That email is already registered.', 'danger')
            return redirect(url_for('register'))

        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password_hash=hashed)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! You can now sign in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        remember = request.form.get('remember') == 'on'

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ============================================================
# DASHBOARD
# ============================================================
@app.route('/dashboard')
@login_required
def dashboard():
    sessions = InterviewSession.query.filter_by(user_id=current_user.id) \
        .order_by(InterviewSession.date.asc()).all()
    quizzes = QuizResult.query.filter_by(user_id=current_user.id) \
        .order_by(QuizResult.date.asc()).all()
    resumes = ResumeAnalysis.query.filter_by(user_id=current_user.id) \
        .order_by(ResumeAnalysis.date.asc()).all()

    total_interviews = len(sessions)
    total_quizzes = len(quizzes)
    total_resumes = len(resumes)

    avg_score = round(sum(s.avg_score for s in sessions) / total_interviews, 1) if total_interviews else 0
    avg_quiz = round(sum(q.score for q in quizzes) / total_quizzes, 1) if total_quizzes else 0
    resume_score = resumes[-1].score if resumes else 0
    resume_role = resumes[-1].suggested_role if resumes else None

    components = []
    if total_interviews:
        components.append(avg_score)
    if total_quizzes:
        components.append(avg_quiz)
    if total_resumes:
        components.append(resume_score)
    readiness = round(sum(components) / len(components)) if components else 0

    recent_sessions = sessions[-10:]
    recent_quizzes = quizzes[-10:]
    interview_dates = [s.date.strftime('%b %d') for s in recent_sessions]
    interview_scores = [s.avg_score for s in recent_sessions]
    quiz_dates = [q.date.strftime('%b %d') for q in recent_quizzes]
    quiz_scores = [q.score for q in recent_quizzes]

    role_performance = _avg_by(sessions, 'job_role', 'avg_score')
    quiz_category_performance = _avg_by(quizzes, 'category', 'score')

    activity_counts = {
        'Mock Interviews': total_interviews,
        'Skill Quizzes': total_quizzes,
        'Resume Scans': total_resumes,
    }

    recent_activity = []
    for s in sessions:
        recent_activity.append({
            'type': 'interview', 'icon': 'fa-comments',
            'title': f"{s.job_role} Interview",
            'meta': f"{s.difficulty} - {s.num_questions} questions",
            'score': round(s.avg_score, 1), 'date': s.date,
        })
    for q in quizzes:
        recent_activity.append({
            'type': 'quiz', 'icon': 'fa-square-poll-vertical',
            'title': f"{q.category} Quiz ({q.difficulty})",
            'meta': f"{q.correct_answers}/{q.total_questions} correct",
            'score': q.score, 'date': q.date,
        })
    for r in resumes:
        recent_activity.append({
            'type': 'resume', 'icon': 'fa-file-lines',
            'title': "Resume Analysis",
            'meta': f"Best match: {r.suggested_role}",
            'score': r.score, 'date': r.date,
        })
    recent_activity.sort(key=lambda x: x['date'], reverse=True)
    recent_activity = recent_activity[:6]

    return render_template(
        'dashboard.html',
        total_interviews=total_interviews, avg_score=avg_score,
        total_quizzes=total_quizzes, avg_quiz=avg_quiz,
        total_resumes=total_resumes, resume_score=resume_score, resume_role=resume_role,
        readiness=readiness,
        interview_dates=json.dumps(interview_dates), interview_scores=json.dumps(interview_scores),
        quiz_dates=json.dumps(quiz_dates), quiz_scores=json.dumps(quiz_scores),
        role_performance=role_performance, quiz_category_performance=quiz_category_performance,
        activity_counts=activity_counts, recent_activity=recent_activity,
        roles=ROLES, role_info=ROLE_INFO, quiz_categories=QUIZ_CATEGORY_INFO,
    )


# ============================================================
# MOCK INTERVIEW
# ============================================================
@app.route('/mock-interview')
@login_required
def mock_interview():
    return render_template(
        'mock_interview.html',
        roles=ROLES, role_info=ROLE_INFO,
        difficulties=DIFFICULTIES, question_counts=INTERVIEW_QUESTION_COUNTS,
    )


@app.route('/start-mock-interview', methods=['POST'])
@login_required
def start_mock_interview():
    role = request.form.get('role')
    difficulty = request.form.get('difficulty', 'Medium')
    mode = request.form.get('mode', 'text')
    try:
        count = int(request.form.get('count', 5))
    except (TypeError, ValueError):
        count = 5

    if role not in INTERVIEW_QUESTIONS:
        flash('Please select a valid role.', 'danger')
        return redirect(url_for('mock_interview'))

    if difficulty not in DIFFICULTIES + ['Mixed']:
        difficulty = 'Medium'
    if mode not in ('text', 'voice'):
        mode = 'text'
    if count not in INTERVIEW_QUESTION_COUNTS:
        count = INTERVIEW_QUESTION_COUNTS[0]

    questions = select_interview_questions(role, difficulty, count)

    session['interview_role'] = role
    session['interview_difficulty'] = difficulty
    session['interview_mode'] = mode
    session['interview_questions'] = questions
    session['interview_items'] = []
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

    role = session.get('interview_role', '')
    question = questions[current]
    _, q_difficulty = find_question_meta(role, question)

    return render_template(
        'take_interview.html',
        question=question,
        question_difficulty=q_difficulty or session.get('interview_difficulty', 'Medium'),
        num=current + 1,
        total=len(questions),
        role=role,
        difficulty=session.get('interview_difficulty', 'Medium'),
        mode=session.get('interview_mode', 'text'),
        role_info=ROLE_INFO.get(role, {}),
    )


@app.route('/submit-answer', methods=['POST'])
@login_required
def submit_answer():
    if 'interview_questions' not in session:
        return jsonify({'error': 'No active interview.'}), 400

    answer = request.form.get('answer', '')
    question = request.form.get('question', '')
    role = session.get('interview_role', '')

    score, feedback = evaluate_answer(question, answer, role)
    _, q_difficulty = find_question_meta(role, question)
    q_difficulty = q_difficulty or session.get('interview_difficulty', 'Medium')

    display_answer = answer.strip()
    if len(display_answer) > 300:
        display_answer = display_answer[:300].rstrip() + '...'

    session['interview_items'].append({
        'question': question,
        'answer': display_answer,
        'score': score,
        'feedback': feedback,
        'difficulty': q_difficulty,
    })
    session['interview_current'] = session.get('interview_current', 0) + 1
    session.modified = True

    questions = session['interview_questions']
    current = session['interview_current']

    if current >= len(questions):
        items = session['interview_items']
        scores = [it['score'] for it in items]
        total = round(sum(scores) / len(scores), 1) if scores else 0
        role_name = session.get('interview_role', '')
        difficulty_choice = session.get('interview_difficulty', 'Medium')
        mode = session.get('interview_mode', 'text')

        for it in items:
            db.session.add(Interview(
                user_id=current_user.id, job_role=role_name, question=it['question'],
                answer=it['answer'], score=it['score'], feedback=it['feedback'],
                difficulty=it['difficulty'],
            ))
        db.session.add(InterviewSession(
            user_id=current_user.id, job_role=role_name, difficulty=difficulty_choice,
            mode=mode, num_questions=len(items), avg_score=total,
        ))
        db.session.commit()

        summary = {
            'role': role_name, 'difficulty': difficulty_choice, 'mode': mode,
            'total': total, 'items': items,
        }
        session['last_interview_summary'] = summary

        for key in ('interview_role', 'interview_difficulty', 'interview_mode',
                    'interview_questions', 'interview_items', 'interview_current'):
            session.pop(key, None)

        return jsonify({'completed': True, 'total': total, 'redirect': url_for('interview_complete')})

    next_question = questions[current]
    _, next_difficulty = find_question_meta(role, next_question)

    return jsonify({
        'completed': False,
        'next': next_question,
        'next_difficulty': next_difficulty or session.get('interview_difficulty', 'Medium'),
        'num': current + 1,
        'total': len(questions),
        'score': score,
        'feedback': feedback,
    })


@app.route('/interview-complete')
@login_required
def interview_complete():
    summary = session.pop('last_interview_summary', None)
    if not summary:
        return redirect(url_for('mock_interview'))
    return render_template('interview_complete.html', summary=summary,
                            role_info=ROLE_INFO.get(summary.get('role'), {}))


# ============================================================
# RESUME ANALYSIS
# ============================================================
@app.route('/resume-analysis', methods=['GET', 'POST'])
@login_required
def resume_analysis():
    if request.method == 'POST':
        if 'resume' not in request.files or request.files['resume'].filename == '':
            flash('Please choose a resume file to upload.', 'danger')
            return redirect(url_for('resume_analysis'))

        file = request.files['resume']
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ('.pdf', '.txt'):
            flash('Please upload a PDF or TXT file (DOCX is not fully supported yet).', 'danger')
            return redirect(url_for('resume_analysis'))

        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            text = extract_text_from_file(filepath)

            if os.path.exists(filepath):
                os.remove(filepath)

            if not text or len(text.strip()) < 50:
                flash('Could not extract enough text from that file. Try a different PDF or a .txt file.', 'danger')
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
                skills_found=json.dumps(analysis['skills']),
            )
            db.session.add(resume)
            db.session.commit()

            flash(f"Best match: {analysis['best_role']} ({analysis['best_score']}% match)", 'success')
            return render_template('resume_result.html', analysis=analysis, difficulties=DIFFICULTIES)

        except Exception as e:
            print(f"Resume analysis error: {e}")
            flash('Something went wrong while analyzing that resume. Please try again.', 'danger')
            return redirect(url_for('resume_analysis'))

    return render_template('resume_analysis.html')


@app.route('/start-from-resume', methods=['POST'])
@login_required
def start_from_resume():
    role = request.form.get('role')
    action = request.form.get('action')
    difficulty = request.form.get('difficulty', 'Medium')
    if difficulty not in DIFFICULTIES + ['Mixed']:
        difficulty = 'Medium'

    if action == 'interview':
        if role not in INTERVIEW_QUESTIONS:
            flash('That role is not available for mock interviews yet.', 'danger')
            return redirect(url_for('resume_analysis'))

        questions = select_interview_questions(role, difficulty, 5)
        session['interview_role'] = role
        session['interview_difficulty'] = difficulty
        session['interview_mode'] = 'text'
        session['interview_questions'] = questions
        session['interview_items'] = []
        session['interview_current'] = 0
        return redirect(url_for('take_interview'))

    elif action == 'quiz':
        quiz_difficulty = difficulty if difficulty in DIFFICULTIES else 'Medium'
        quiz_cat = ROLE_TO_QUIZ_CATEGORY.get(role, QUIZ_CATEGORIES[0])
        questions = select_quiz_questions(quiz_cat, quiz_difficulty, 5)

        session['quiz_category'] = quiz_cat
        session['quiz_difficulty'] = quiz_difficulty
        session['quiz_questions'] = questions
        session['quiz_answers'] = []
        session['quiz_current'] = 0
        return redirect(url_for('take_quiz'))

    return redirect(url_for('resume_analysis'))


# ============================================================
# SKILL QUIZ
# ============================================================
@app.route('/skill-quiz')
@login_required
def skill_quiz():
    return render_template(
        'skill_quiz.html',
        categories=QUIZ_CATEGORY_INFO, difficulties=DIFFICULTIES,
        question_counts=QUIZ_QUESTION_COUNTS,
    )


@app.route('/start-quiz', methods=['POST'])
@login_required
def start_quiz():
    category = request.form.get('category')
    difficulty = request.form.get('difficulty', 'Medium')
    try:
        count = int(request.form.get('count', 5))
    except (TypeError, ValueError):
        count = 5

    if category not in QUIZ_QUESTIONS:
        flash('Please choose a valid quiz category.', 'danger')
        return redirect(url_for('skill_quiz'))
    if difficulty not in DIFFICULTIES:
        difficulty = 'Medium'
    if count not in QUIZ_QUESTION_COUNTS:
        count = QUIZ_QUESTION_COUNTS[0]

    questions = select_quiz_questions(category, difficulty, count)
    if not questions:
        flash('No questions are available for that combination yet.', 'danger')
        return redirect(url_for('skill_quiz'))

    session['quiz_category'] = category
    session['quiz_difficulty'] = difficulty
    session['quiz_questions'] = questions
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

    category = session['quiz_category']
    return render_template(
        'take_quiz.html',
        question=questions[current],
        num=current + 1,
        total=len(questions),
        category=category,
        difficulty=session.get('quiz_difficulty', 'Medium'),
        category_info=QUIZ_CATEGORY_INFO.get(category, {}),
    )


@app.route('/submit-quiz', methods=['POST'])
@login_required
def submit_quiz():
    if 'quiz_questions' not in session:
        return jsonify({'error': 'No active quiz.'}), 400

    data = request.get_json(silent=True) or {}
    answer = data.get('answer')
    correct = data.get('correct')
    is_correct = (answer == correct)

    session['quiz_answers'].append({
        'question': data.get('question'),
        'answer': answer,
        'correct': correct,
        'is_correct': is_correct,
        'explanation': data.get('explanation', ''),
    })
    session['quiz_current'] = session.get('quiz_current', 0) + 1
    session.modified = True

    questions = session['quiz_questions']
    current = session['quiz_current']

    if current >= len(questions):
        answers = session['quiz_answers']
        correct_count = sum(1 for a in answers if a['is_correct'])
        score = int(round((correct_count / len(questions)) * 100))
        category = session['quiz_category']
        difficulty = session.get('quiz_difficulty', 'Medium')

        result = QuizResult(
            user_id=current_user.id, category=category, difficulty=difficulty,
            score=score, total_questions=len(questions), correct_answers=correct_count,
        )
        db.session.add(result)
        db.session.commit()

        summary = {
            'category': category, 'difficulty': difficulty, 'score': score,
            'correct': correct_count, 'total': len(questions), 'items': answers,
        }
        session['last_quiz_summary'] = summary

        for key in ('quiz_category', 'quiz_difficulty', 'quiz_questions', 'quiz_answers', 'quiz_current'):
            session.pop(key, None)

        return jsonify({
            'completed': True, 'score': score, 'correct': correct_count,
            'total': len(questions), 'redirect': url_for('quiz_complete'),
        })

    return jsonify({
        'completed': False,
        'next': questions[current],
        'num': current + 1,
        'total': len(questions),
    })


@app.route('/quiz-complete')
@login_required
def quiz_complete():
    summary = session.pop('last_quiz_summary', None)
    if not summary:
        return redirect(url_for('skill_quiz'))
    return render_template('quiz_complete.html', summary=summary,
                            category_info=QUIZ_CATEGORY_INFO.get(summary.get('category'), {}))


# ============================================================
# PERFORMANCE
# ============================================================
@app.route('/performance')
@login_required
def performance():
    questions = Interview.query.filter_by(user_id=current_user.id) \
        .order_by(Interview.date.asc()).all()
    sessions = InterviewSession.query.filter_by(user_id=current_user.id) \
        .order_by(InterviewSession.date.asc()).all()
    quizzes = QuizResult.query.filter_by(user_id=current_user.id) \
        .order_by(QuizResult.date.asc()).all()
    resumes = ResumeAnalysis.query.filter_by(user_id=current_user.id) \
        .order_by(ResumeAnalysis.date.asc()).all()

    interview_dates = [s.date.strftime('%b %d') for s in sessions]
    interview_scores = [s.avg_score for s in sessions]
    quiz_dates = [q.date.strftime('%b %d') for q in quizzes]
    quiz_scores = [q.score for q in quizzes]

    role_performance = _avg_by(sessions, 'job_role', 'avg_score')
    quiz_category_performance = _avg_by(quizzes, 'category', 'score')
    quiz_difficulty_performance = _avg_by(quizzes, 'difficulty', 'score')
    interview_difficulty_performance = _avg_by(questions, 'difficulty', 'score')

    activity_counts = {
        'Mock Interviews': len(sessions),
        'Skill Quizzes': len(quizzes),
        'Resume Scans': len(resumes),
    }

    total_interviews = len(sessions)
    total_quizzes = len(quizzes)
    avg_score = round(sum(s.avg_score for s in sessions) / total_interviews, 1) if total_interviews else 0
    avg_quiz = round(sum(q.score for q in quizzes) / total_quizzes, 1) if total_quizzes else 0
    best_quiz = max((q.score for q in quizzes), default=0)
    best_interview = max((s.avg_score for s in sessions), default=0)

    history = []
    for s in sessions:
        history.append({'type': 'Mock Interview', 'detail': f"{s.job_role} ({s.difficulty}, {s.mode})",
                         'score': round(s.avg_score, 1), 'date': s.date})
    for q in quizzes:
        history.append({'type': 'Skill Quiz', 'detail': f"{q.category} ({q.difficulty}) - {q.correct_answers}/{q.total_questions}",
                         'score': q.score, 'date': q.date})
    for r in resumes:
        history.append({'type': 'Resume Analysis', 'detail': f"Best match: {r.suggested_role}",
                         'score': r.score, 'date': r.date})
    history.sort(key=lambda x: x['date'], reverse=True)

    return render_template(
        'performance.html',
        total_interviews=total_interviews, total_quizzes=total_quizzes, total_resumes=len(resumes),
        avg_score=avg_score, avg_quiz=avg_quiz, best_quiz=best_quiz, best_interview=round(best_interview, 1),
        interview_dates=json.dumps(interview_dates), interview_scores=json.dumps(interview_scores),
        quiz_dates=json.dumps(quiz_dates), quiz_scores=json.dumps(quiz_scores),
        role_performance=role_performance,
        quiz_category_performance=quiz_category_performance,
        quiz_difficulty_performance=quiz_difficulty_performance,
        interview_difficulty_performance=interview_difficulty_performance,
        activity_counts=activity_counts,
        history=history[:25],
    )


# ============================================================
# ERROR HANDLERS
# ============================================================
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
