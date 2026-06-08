from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    flash,
    send_file,
    jsonify
)

import sqlite3
import os

from utils.ai_helper import (
    generate_questions,
    evaluate_answer,
    analyze_resume_ai,
    get_ai_suggestions
)

from utils.resume_parser import extract_resume_text
from utils.pdf_report import generate_report

# ==================================================
# APP CONFIG
# ==================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "interviewcoach-secret-key"
)

app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours

UPLOAD_FOLDER = "static/uploads"
REPORT_FOLDER = "reports"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

# ==================================================
# DATABASE
# ==================================================

def get_db():
    conn = sqlite3.connect("interview.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS interviews(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        role TEXT,
        question TEXT,
        answer TEXT,
        feedback TEXT,
        score INTEGER,
        communication_level TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS resume_analyses(
    cur.execute("""
CREATE TABLE IF NOT EXISTS skill_assessments(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    skill TEXT,
    score INTEGER,
    total_questions INTEGER,
    percentage INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        analysis_data TEXT,
        score INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


init_db()

# ==================================================
# HOME
# ==================================================

@app.route("/")
def home():
    return render_template("login.html")


# ==================================================
# REGISTER
# ==================================================

@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/register_user", methods=["POST"])
def register_user():

    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            INSERT INTO users(name,email,password)
            VALUES (?,?,?)
            """,
            (name, email, password)
        )

        conn.commit()

        flash("Account created successfully! Please login.")

    except sqlite3.IntegrityError:

        flash("Email already exists. Please use a different email.")
        return redirect("/register")

    finally:
        conn.close()

    return redirect("/")


# ==================================================
# LOGIN
# ==================================================

@app.route("/login", methods=["POST"])
def login():

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()

    if not email or not password:
        flash("Please enter both email and password")
        return redirect("/")

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT * FROM users
            WHERE email=? AND password=?
            """,
            (email, password)
        )

        user = cur.fetchone()

        if user:
            session.permanent = True
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["email"] = user["email"]
            return redirect("/dashboard")
        else:
            flash("Invalid Email or Password. Please try again.")
            return redirect("/")

    except Exception as e:
        flash(f"Login error: {str(e)}")
        return redirect("/")

    finally:
        conn.close()


# ==================================================
# LOGOUT
# ==================================================

@app.route("/logout")
def logout():

    session.clear()
    flash("Logged out successfully!")
    return redirect("/")


# ==================================================
# DASHBOARD
# ==================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        flash("Please login first")
        return redirect("/")

    return render_template(
        "dashboard.html",
        name=session.get("name", "User")
    )


# ==================================================
# INTERVIEW PAGE
# ==================================================

@app.route("/interview")
def interview():

    if "user_id" not in session:
        flash("Please login first")
        return redirect("/")

    return render_template("index.html")


# ==================================================
# GENERATE QUESTIONS
# ==================================================

@app.route("/generate_questions", methods=["POST"])
def generate():

    if "user_id" not in session:
        flash("Please login first")
        return redirect("/")

    role = request.form.get("role", "").strip()
    level = request.form.get("level", "Beginner")

    if role == "":
        flash("Please enter a job role")
        return redirect("/interview")

    try:

        questions = generate_questions(
            role,
            level
        )
        
        # Get AI suggestions
        suggestions = get_ai_suggestions(role, level)

    except Exception as e:

        questions = f"""
❌ Question Generation Failed

Error:
{str(e)}
"""
        suggestions = {}

    return render_template(
        "interview.html",
        role=role,
        questions=questions,
        suggestions=suggestions
    )


# ==================================================
# EVALUATE ANSWER
# ==================================================

@app.route("/evaluate", methods=["POST"])
def evaluate():

    if "user_id" not in session:
        flash("Please login first")
        return redirect("/")

    role = request.form.get("role")
    question = request.form.get("question")
    answer = request.form.get("answer")

    try:

        feedback, score, communication = evaluate_answer(
            role,
            question,
            answer
        )

        session["feedback"] = feedback
        session["score"] = score

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO interviews
            (
                user_id,
                role,
                question,
                answer,
                feedback,
                score,
                communication_level
            )
            VALUES (?,?,?,?,?,?,?)
            """,
            (
                session["user_id"],
                role,
                question,
                answer,
                feedback,
                score,
                communication
            )
        )

        conn.commit()
        conn.close()

        return render_template(
            "result.html",
            feedback=feedback,
            score=score
        )

    except Exception as e:

        return render_template(
            "result.html",
            feedback=f"❌ Evaluation Error: {str(e)}",
            score=0
        )


# ==================================================
# RESUME PAGE
# ==================================================

@app.route("/resume")
def resume():

    if "user_id" not in session:
        flash("Please login first")
        return redirect("/")

    return render_template("resume_upload.html")


# ==================================================
# RESUME UPLOAD
# ==================================================

@app.route("/upload_resume", methods=["POST"])
def upload_resume():

    if "user_id" not in session:
        flash("Please login first")
        return redirect("/")

    if "resume" not in request.files:
        flash("No file selected")
        return redirect("/resume")

    resume = request.files["resume"]

    if resume.filename == "":
        flash("Please select a resume file")
        return redirect("/resume")

    filepath = os.path.join(
        UPLOAD_FOLDER,
        resume.filename
    )

    resume.save(filepath)

    try:

        resume_text = extract_resume_text(filepath)

        analysis = analyze_resume_ai(resume_text)

        if not analysis.get("valid", True):

            flash(analysis["message"])

            return render_template(
                "resume_result.html",
                resume_text="",
                analysis={
                    "score": 0,
                    "strengths": [],
                    "weaknesses": [],
                    "recommendations": [analysis["message"]]
                },
                recommendations=None
            )

        recommendations = analysis["recommendations"]

    except Exception as e:

        return render_template(
            "resume_result.html",
            resume_text="",
            analysis={
                "score": 0,
                "strengths": [],
                "weaknesses": [str(e)],
                "recommendations": [str(e)]
            },
            recommendations=None
        )

    return render_template(
        "resume_result.html",
        resume_text=resume_text,
        analysis=analysis,
        recommendations=recommendations
    )
# ==================================================
# PERFORMANCE
# ==================================================

@app.route("/performance")
def performance():

    if "user_id" not in session:
        flash("Please login first")
        return redirect("/")

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT *
            FROM interviews
            WHERE user_id=?
            ORDER BY id DESC
            """,
            (session["user_id"],)
        )

        records = cur.fetchall()

    except Exception as e:
        records = []
        flash(f"Error loading performance: {str(e)}")

    finally:
        conn.close()

    return render_template(
        "performance.html",
        records=records
    )


# ==================================================
# SKILL ASSESSMENT
# ==================================================

@app.route("/skill-assessment")
def skill_assessment():

    if "user_id" not in session:
        flash("Please login first")
        return redirect("/")

    return render_template("skill_assessment.html")


# ==================================================
# DOWNLOAD REPORT
# ==================================================

@app.route("/download_report")
def download_report():

    if "user_id" not in session:
        flash("Please login first")
        return redirect("/")

    feedback = session.get(
        "feedback",
        "No feedback available"
    )

    filepath = os.path.join(
        REPORT_FOLDER,
        f"report_{session.get('user_id',0)}.pdf"
    )

    try:
        generate_report(
            "AI Interview Report",
            feedback,
            filepath
        )

        return send_file(
            filepath,
            as_attachment=True
        )
    except Exception as e:
        flash(f"Error generating report: {str(e)}")
        return redirect("/dashboard")


# ==================================================
# FEEDBACK PAGE (Optional)
# ==================================================

@app.route("/feedback")
def feedback():

    if "user_id" not in session:
        flash("Please login first")
        return redirect("/")

    return redirect("/performance")


# ==================================================
# ERROR HANDLER
# ==================================================

@app.errorhandler(404)
def not_found(error):
    if "user_id" in session:
        return render_template(
            "dashboard.html",
            name=session.get("name", "User")
        )
    return redirect("/")


# ==================================================
# RUN APP
# ==================================================

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 5000)
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
