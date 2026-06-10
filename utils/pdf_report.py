import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER

class PDFReportGenerator:
    """Generate PDF reports for interview performance"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#6366f1'),
            alignment=TA_CENTER,
            spaceAfter=30
        )
    
    def generate_interview_report(self, interview_data, user_name, filepath):
        """Generate a PDF report for an interview session"""
        try:
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            story = []
            
            # Title
            title = Paragraph(f"Interview Performance Report", self.title_style)
            story.append(title)
            story.append(Spacer(1, 0.25*inch))
            
            # User info
            user_info = Paragraph(f"<b>Candidate:</b> {user_name}<br/>"
                                 f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}<br/>"
                                 f"<b>Job Role:</b> {interview_data.get('job_role', 'N/A')}<br/>"
                                 f"<b>Experience Level:</b> {interview_data.get('experience_level', 'N/A')}",
                                 self.styles['Normal'])
            story.append(user_info)
            story.append(Spacer(1, 0.25*inch))
            
            # Overall Score
            score = interview_data.get('overall_score', 0)
            score_text = Paragraph(f"<b>Overall Score: {score}/100</b>", self.styles['Heading2'])
            story.append(score_text)
            story.append(Spacer(1, 0.25*inch))
            
            # Questions and Answers
            questions = interview_data.get('questions', [])
            answers = interview_data.get('answers', [])
            
            for i, (q, a) in enumerate(zip(questions, answers), 1):
                story.append(Paragraph(f"<b>Question {i}:</b> {q}", self.styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(f"<b>Answer:</b> {a}", self.styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph("-" * 50, self.styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
            
            # Build PDF
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return False
    
    def generate_resume_report(self, resume_data, user_name, filepath):
        """Generate a PDF report for resume analysis"""
        try:
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            story = []
            
            # Title
            title = Paragraph(f"Resume Analysis Report", self.title_style)
            story.append(title)
            story.append(Spacer(1, 0.25*inch))
            
            # User info
            user_info = Paragraph(f"<b>Candidate:</b> {user_name}<br/>"
                                 f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                                 self.styles['Normal'])
            story.append(user_info)
            story.append(Spacer(1, 0.25*inch))
            
            # Score
            score = resume_data.get('overall_score', 0)
            score_text = Paragraph(f"<b>Resume Score: {score}/100</b>", self.styles['Heading2'])
            story.append(score_text)
            story.append(Spacer(1, 0.25*inch))
            
            # Strengths
            strengths = resume_data.get('strengths', [])
            story.append(Paragraph("<b>Strengths:</b>", self.styles['Heading3']))
            for s in strengths:
                story.append(Paragraph(f"• {s}", self.styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
            
            # Weaknesses
            weaknesses = resume_data.get('weaknesses', [])
            story.append(Paragraph("<b>Areas for Improvement:</b>", self.styles['Heading3']))
            for w in weaknesses:
                story.append(Paragraph(f"• {w}", self.styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
            
            # Recommendations
            recommendations = resume_data.get('recommendations', [])
            story.append(Paragraph("<b>Recommendations:</b>", self.styles['Heading3']))
            for r in recommendations:
                story.append(Paragraph(f"• {r}", self.styles['Normal']))
            
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return False

# Also define a simple function for backward compatibility
def generate_pdf_report(data, filename):
    """Simple function to generate PDF reports"""
    generator = PDFReportGenerator()
    return generator.generate_interview_report(data, data.get('user_name', 'User'), filename)

# For backward compatibility - export the class as pdf_report
pdf_report = PDFReportGenerator()
