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
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        analysis_data TEXT,
        score INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS skill_quiz_results(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        skill TEXT,
        score INTEGER,
        total_questions INTEGER,
        percentage REAL,
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

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM interviews WHERE user_id=?",
        (session["user_id"],)
    )
    total_interviews = cur.fetchone()[0]

    cur.execute(
        """
        SELECT AVG(score)
        FROM interviews
        WHERE user_id=?
        """,
        (session["user_id"],)
    )

    avg = cur.fetchone()[0]
    average_score = round(avg or 0)

    cur.execute(
        """
        SELECT COUNT(*)
        FROM skill_quiz_results
        WHERE user_id=?
        """,
        (session["user_id"],)
    )

    quiz_count = cur.fetchone()[0]

    cur.execute(
        """
        SELECT score
        FROM resume_analyses
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 1
        """,
        (session["user_id"],)
    )

    row = cur.fetchone()
    resume_score = row["score"] if row else 0

    conn.close()

    return render_template(
        "dashboard.html",
        name=session.get("name", "User"),
        total_interviews=total_interviews,
        average_score=average_score,
        resume_score=resume_score,
        quiz_count=quiz_count
    )
# ==================================================
# INTERVIEW PAGE
# ==================================================

@app.route("/interview")
def interview():

    if "user_id" not in session:
        flash("Please login first")
        return redirect("/")

   return render_template("interview.html")

# ==================================================
# GENERATE QUESTIONS ROUTE
# ==================================================

@app.route("/generate_questions", methods=["POST"])
def generate_questions_route():

    if "user_id" not in session:
        flash("Please login first")
        return redirect("/")

    role = request.form.get("role")
    level = request.form.get("level")

    questions = generate_questions(role, level)

    return render_template(
        "interview.html",
        questions=questions
    )


# ==================================================
# GENERATE QUESTIONS
# ==================================================

def generate_questions(role, level):
    """
    Safe AI question generator (fixed crash-proof version)
    """

    try:
        # -------------------------
        # Normalize inputs safely
        # -------------------------
        role_key = (role or "").lower().strip().replace(" ", "_")
        level = (level or "Beginner").capitalize()

        role_mapping = {
    "python": "python_developer",
    "python_developer": "python_developer",

    "java": "java_developer",
    "java_developer": "java_developer",

    "javascript": "javascript_developer",
    "javascript_developer": "javascript_developer",

    "data_science": "data_scientist",
    "data_scientist": "data_scientist",

    "full_stack": "full_stack_developer",
    "full_stack_developer": "full_stack_developer",

    "devops": "devops_engineer",
    "devops_engineer": "devops_engineer"
}

        role_key = role_mapping.get(role_key, "python_developer")

        # -------------------------
        # safe bank fetch
        # -------------------------
        bank = QUESTION_BANK.get(role_key, QUESTION_BANK["python_developer"])

        # -------------------------
        # level safe mapping
        # -------------------------
        if level == "Beginner":
            g, t, b = 3, 3, 2
        elif level == "Intermediate":
            g, t, b = 2, 4, 3
        else:
            g, t, b = 2, 5, 3

        # -------------------------
        # SAFE sampling
        # -------------------------
        questions = []

        questions += random.sample(
            bank["general"],
            min(g, len(bank["general"]))
        )

        questions += random.sample(
            bank["technical"],
            min(t, len(bank["technical"]))
        )

        questions += random.sample(
            bank["behavioral"],
            min(b, len(bank["behavioral"]))
        )

        formatted = "\n\n".join(
            f"{i+1}. {q}" for i, q in enumerate(questions)
        )

        display_role = role.replace("_", " ").title()

        return f"""
🎯 AI Interview Questions for {display_role} ({level})

{formatted}

💡 Tip: Use STAR method for behavioral answers
"""

    except Exception as e:
        return f"""
❌ Question generation failed safely recovered

Error: {str(e)}

👉 Please check role/level input from frontend
"""
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
        return redirect("/resume-analysis")

    file = request.files["resume"]

    if file.filename == "":
        flash("Please select a file")
        return redirect("/resume-analysis")

    filepath = os.path.join(
        UPLOAD_FOLDER,
        file.filename
    )

    file.save(filepath)

    try:

        resume_text = extract_resume_text(filepath)

        ai_result = analyze_resume_ai(resume_text)

        analysis = {
            "ats_score": ai_result.get("score", 75),
            "keyword_match": ai_result.get("score", 75),
            "readability": 90,

            "skills": ai_result.get(
                "skills",
                ["Python", "Flask"]
            ),

            "matched_keywords": ai_result.get(
                "strengths",
                []
            ),

            "missing_keywords": ai_result.get(
                "weaknesses",
                []
            ),

            "recommendations": ai_result.get(
                "recommendations",
                []
            ),

            "summary": ai_result.get(
                "summary",
                "Resume analyzed successfully."
            ),

            "report_url": "/download_report"
        }

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO resume_analyses
            (
                user_id,
                analysis_data,
                score
            )
            VALUES (?,?,?)
            """,
            (
                session["user_id"],
                str(analysis),
                analysis["ats_score"]
            )
        )

        conn.commit()
        conn.close()

        return render_template(
            "resume_analysis.html",
            analysis=analysis
        )

    except Exception as e:

        flash(str(e))

        return render_template(
            "resume_analysis.html",
            analysis=None
        )

@app.route("/resume-analysis")
def resume_analysis():

    if "user_id" not in session:
        flash("Please login first")
        return redirect("/")

    return render_template(
        "resume_analysis.html",
        analysis=None
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
        cur.execute("""
            SELECT *
            FROM interviews
            WHERE user_id=?
            ORDER BY id DESC
        """, (session["user_id"],))
        records = cur.fetchall()

        cur.execute("""
            SELECT *
            FROM skill_quiz_results
            WHERE user_id=?
            ORDER BY id DESC
        """, (session["user_id"],))
        quiz_results = cur.fetchall()

        average_score = 0

        if records:
            average_score = round(
                sum(r["score"] for r in records) / len(records)
            )

        cur.execute("""
            SELECT score
            FROM resume_analyses
            WHERE user_id=?
            ORDER BY id DESC
            LIMIT 1
        """, (session["user_id"],))

        row = cur.fetchone()
        resume_score = row["score"] if row else 0

    except Exception as e:
        records = []
        quiz_results = []
        average_score = 0
        resume_score = 0
        flash(f"Error loading performance: {str(e)}")

    finally:
        conn.close()

    return render_template(
        "performance.html",
        records=records,
        quiz_results=quiz_results,
        total_interviews=len(records),
        total_quizzes=len(quiz_results),
        average_score=average_score,
        resume_score=resume_score
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


@app.route("/submit_skill_quiz", methods=["POST"])
def submit_skill_quiz():

    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()

    skill = data.get("skill")
    score = data.get("score")
    total = data.get("total")

    percentage = round((score / total) * 100, 2)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO skill_quiz_results
        (user_id, skill, score, total_questions, percentage)
        VALUES (?, ?, ?, ?, ?)
    """, (
        session["user_id"],
        skill,
        score,
        total,
        percentage
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "percentage": percentage
    })
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
