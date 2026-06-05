# utils/resume_parser.py

import PyPDF2


def extract_resume_text(filepath):

    if filepath.endswith(".txt"):

        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    elif filepath.endswith(".pdf"):

        text = ""

        with open(filepath, "rb") as pdf_file:

            pdf = PyPDF2.PdfReader(pdf_file)

            for page in pdf.pages:
                extracted = page.extract_text()

                if extracted:
                    text += extracted + "\n"

        return text

    return "Unsupported file format"
