from PyPDF2 import PdfReader
import os

def extract_resume_text(filepath):

    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".pdf":

        text = ""

        reader = PdfReader(filepath)

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

        return text

    elif ext == ".txt":

        with open(
            filepath,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as f:

            return f.read()

    else:

        return (
            "Unsupported file format. "
            "Please upload PDF or TXT."
        )
