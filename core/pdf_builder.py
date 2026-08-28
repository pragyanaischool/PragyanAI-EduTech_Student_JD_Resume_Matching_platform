import io
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
    KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def generate_pdf_report(markdown_text: str, title: str = "Curriculum Vitae") -> bytes:
    """
    Converts Markdown formatted text into a publication-grade, ATS-compliant PDF.
    Uses ReportLab Flowables with clean visual hierarchies, rules, and typography.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=4
    )
    
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=10,
        spaceAfter=4
    )

    h3_style = ParagraphStyle(
        'SubSectionH3',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor("#2D3748"),
        spaceBefore=6,
        spaceAfter=2
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=3
    )

    bullet_style = ParagraphStyle(
        'BulletText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        leftIndent=14,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=2
    )

    story = []

    # Render Document Title
    story.append(Paragraph(title, title_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=8))

    lines = markdown_text.split('\n')
    for line in lines:
        raw_line = line.strip()
        if not raw_line:
            story.append(Spacer(1, 4))
            continue

        # Clean Markdown inline bold/italic for ReportLab XML tags
        formatted_line = raw_line
        formatted_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', formatted_line)
        formatted_line = re.sub(r'\*(.*?)\*', r'<i>\1</i>', formatted_line)
        formatted_line = re.sub(r'`(.*?)`', r'<font face="Courier">\1</font>', formatted_line)

        if raw_line.startswith('# '):
            main_header = formatted_line[2:].strip()
            story.append(Paragraph(main_header, title_style))
            story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=6))
        elif raw_line.startswith('## '):
            section_header = formatted_line[3:].strip()
            story.append(Spacer(1, 4))
            story.append(Paragraph(section_header, h2_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E0"), spaceAfter=4))
        elif raw_line.startswith('### '):
            sub_header = formatted_line[4:].strip()
            story.append(Paragraph(sub_header, h3_style))
        elif raw_line.startswith('- ') or raw_line.startswith('* '):
            bullet_content = formatted_line[2:].strip()
            story.append(Paragraph(f"&bull; {bullet_content}", bullet_style))
        elif re.match(r'^\d+\.\s', raw_line):
            num_match = re.match(r'^(\d+\.)\s(.*)', formatted_line)
            if num_match:
                story.append(Paragraph(f"<b>{num_match.group(1)}</b> {num_match.group(2)}", bullet_style))
            else:
                story.append(Paragraph(formatted_line, body_style))
        else:
            story.append(Paragraph(formatted_line, body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
