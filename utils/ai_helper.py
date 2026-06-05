import os
from dotenv import load_dotenv
import google.generativeai as genai

# ---------------- GEMINI CONFIG ---------------- #

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise Exception(
        "GEMINI_API_KEY not found. Add it to your .env file."
    )

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-1.5-flash")

# ---------------- QUESTION GENERATION ---------------- #

def generate_questions(role, level):

    prompt = f"""
You are a Senior Technical Interviewer.

Create role-specific interview questions.

Job Role: {role}
Experience Level: {level}

Requirements:
- Questions must be specific to the given role.
- Different roles must get different questions.
- Include:
  * Technical Questions
  * Scenario-Based Questions
  * Project Questions
  * Problem-Solving Questions
  * Advanced Questions
  * HR Questions

Generate as many high-quality questions as possible.
Return only the questions in a structured format.
"""

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.9,
                "max_output_tokens": 8192
            }
        )

        return response.text

    except Exception as e:
        return f"Error Generating Questions: {str(e)}"


# ---------------- ANSWER EVALUATION ---------------- #

def evaluate_answer(role, question, answer):

    prompt = f"""
You are a Senior Interview Evaluator.

ROLE:
{role}

QUESTION:
{question}

ANSWER:
{answer}

Evaluate the answer and provide:

1. Score (/10)
2. Strengths
3. Weaknesses
4. Technical Feedback
5. Improvement Suggestions
6. Ideal Answer
7. Hiring Recommendation
"""

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 4096
            }
        )

        return response.text

    except Exception as e:
        return f"Evaluation Error: {str(e)}"