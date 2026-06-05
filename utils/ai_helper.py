# utils/ai_helper.py

def generate_questions(role, level):

    questions = f"""
1. Tell me about yourself.

2. Why do you want to work as a {role}?

3. What are your strengths?

4. What are your weaknesses?

5. Explain a challenging project you worked on.

6. How do you handle deadlines?

7. Why should we hire you?

8. Where do you see yourself in 5 years?

9. Describe a difficult situation and how you handled it.

10. Do you have any questions for us?
"""

    return questions


def evaluate_answer(role, question, answer):

    score = min(len(answer.split()) * 2, 100)

    feedback = f"""
Role: {role}

Question:
{question}

Your Answer:
{answer}

Evaluation:

✔ Communication: Good

✔ Relevance: Good

✔ Confidence: Moderate

Estimated Score: {score}/100

Suggestions:

• Add more technical details
• Use real project examples
• Structure answers using STAR method
"""

    return feedback
