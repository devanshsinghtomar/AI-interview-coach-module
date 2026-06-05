# utils/pdf_report.py

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet


def generate_report(title, content, filepath):

    doc = SimpleDocTemplate(filepath)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(title, styles["Title"])
    )

    elements.append(
        Spacer(1, 20)
    )

    elements.append(
        Paragraph(content.replace("\n", "<br/>"),
                  styles["BodyText"])
    )

    doc.build(elements)
