from fpdf import FPDF


def generate_report(title, feedback, filename):

    pdf = FPDF()

    pdf.add_page()

    pdf.set_font("Arial", "B", 16)

    pdf.cell(
        200,
        10,
        txt=title,
        ln=True,
        align="C"
    )

    pdf.ln(10)

    pdf.set_font("Arial", size=12)

    pdf.multi_cell(
        0,
        10,
        feedback
    )

    pdf.output(filename)