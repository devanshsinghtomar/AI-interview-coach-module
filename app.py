from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    flash,
    send_file
)

import sqlite3
import os

from utils.ai_helper import (
    generate_questions,
    evaluate_answer
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
        feedback TEXT
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
            INSERT INTO users
            (name,email,password)
            VALUES (?,?,?)
            """,
            (name, email, password)
        )

        conn.commit()

        flash("Account created successfully.")

    except sqlite3.IntegrityError:

        flash("Email already registered.")

        return redirect("/register")

    finally:
        conn.close()

    return redirect("/")


# ==================================================
# LOGIN
# ==================================================

@app.route("/login", methods=["POST"])
def login():

    email = request.form.get("email")
    password = request.form.get("password")

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT * FROM users
        WHERE email=? AND password=?
        """,
        (email, password)
    )

    user = cur.fetchone()

    conn.close()

    if user:

        session["user_id"] = user["id"]
        session["name"] = user["name"]

        return redirect("/dashboard")

    flash("Invalid email or password.")

    return redirect("/")


# ==================================================
# LOGOUT
# ==================================================

@app.route("/logout")
def logout():

    session.clear()

    flash("Logged out successfully.")

    return redirect("/")


# ==================================================
# DASHBOARD
# ==================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/")

    return render_template(
        "dashboard.html",
        name=session["name"]
    )


# ==================================================
# INTERVIEW PAGE
# ==================================================

@app.route("/interview")
def interview():

    if "user_id" not in session:
        return redirect("/")

    return render_template("index.html")


# ==================================================
# GENERATE QUESTIONS
# ==================================================

@app.route("/generate_questions", methods=["POST"])
def generate():

    if "user_id" not in session:
        return redirect("/")

    role = request.form.get(
        "role",
        ""
    ).strip()

    level = request.form.get(
        "level",
        ""
    ).strip()

    if not role:

        flash("Please enter a job role.")

        return redirect("/interview")

    try:

        questions = generate_questions(
            role,
            level
        )

        return render_template(
            "interview.html",
            role=role,
            questions=questions
        )

    except Exception as e:

        return render_template(
            "interview.html",
            role=role,
            questions=f"Error generating questions: {str(e)}"
        )


# ==================================================
# EVALUATE ANSWER
# ==================================================

@app.route("/evaluate", methods=["POST"])
def evaluate():

    if "user_id" not in session:
        return redirect("/")

    role = request.form.get("role")
    question = request.form.get("question")
    answer = request.form.get("answer")

    try:

        feedback = evaluate_answer(
            role,
            question,
            answer
        )

        session["feedback"] = feedback

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
                feedback
            )
            VALUES (?,?,?,?,?)
            """,
            (
                session["user_id"],
                role,
                question,
                answer,
                feedback
            )
        )

        conn.commit()
        conn.close()

        return render_template(
            "result.html",
            feedback=feedback
        )

    except Exception as e:

        return render_template(
            "result.html",
            feedback=f"Evaluation Error: {str(e)}"
        )


# ==================================================
# RESUME UPLOAD
# ==================================================

@app.route("/upload_resume", methods=["POST"])
def upload_resume():

    if "user_id" not in session:
        return redirect("/")

    if "resume" not in request.files:

        flash("No file selected.")

        return redirect("/dashboard")

    resume = request.files["resume"]

    if resume.filename == "":

        flash("Please select a resume.")

        return redirect("/dashboard")

    filepath = os.path.join(
        UPLOAD_FOLDER,
        resume.filename
    )

    resume.save(filepath)

    try:

        resume_text = extract_resume_text(
            filepath
        )

        return render_template(
            "resume_result.html",
            resume_text=resume_text
        )

    except Exception as e:

        return render_template(
            "resume_result.html",
            resume_text=f"Error: {str(e)}"
        )


# ==================================================
# PDF REPORT
# ==================================================

@app.route("/download_report")
def download_report():

    feedback = session.get(
        "feedback",
        "No interview feedback available."
    )

    filepath = os.path.join(
        REPORT_FOLDER,
        "report.pdf"
    )

    generate_report(
        "AI Interview Report",
        feedback,
        filepath
    )

    return send_file(
        filepath,
        as_attachment=True
    )


# ==================================================
# RUN APP
# ==================================================

if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )