# from reportlab.lib.pagesizes import letter
# from reportlab.lib import colors
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
# from reportlab.lib.styles import getSampleStyleSheet
# from filters import format_currency

# def create_payments_pdf(person):
#     # Create a list to hold the PDF elements
#     elements = []

#     # Create a stylesheet for styling the PDF content
#     styles = getSampleStyleSheet()

#     # Add person information
#     elements.append(Paragraph("<b>Coolink Cooperative Savings Account</b>", styles['Title']))
#     elements.append(Paragraph(f"<b>Name:</b> {person.name}", styles['Normal']))
#     elements.append(Paragraph(f"<b>Company:</b> {person.company.name}", styles['Normal']))
#     elements.append(Paragraph(f"<b>Member ID:</b> {person.employee_id}", styles['Normal']))
#     elements.append(Paragraph("", styles['Normal']))  # Empty line

#     # Create a table for the payment details
#     table_data = [
#         ['Date', 'Reference Number', 'Description', 'Amount', 'Balance'],
#         [None, None, 'Balance B/FWD', format_currency(person.balance_bfd), format_currency(person.balance_bfd)]
#     ]

#     for payment in person.payments_made:
#         table_data.append([
#             payment.date.strftime('%Y-%m-%d'),
#             payment.ref_no,
#             payment.description,
#             format_currency(payment.amount),
#             format_currency(payment.balance)
#         ])

#     # Set table style
#     table_style = TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
#         ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#         ('FONTSIZE', (0, 0), (-1, 0), 12),
#         ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#         ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#         ('GRID', (0, 0), (-1, -1), 1, colors.black)
#     ])

#     # Create the table
#     table = Table(table_data, style=table_style)

#     # Add the table to the PDF elements
#     elements.append(table)

#     # Create the PDF file
#     file_path = 'person_payments.pdf'
#     doc = SimpleDocTemplate(file_path, pagesize=letter)
#     doc.build(elements)

#     return file_path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from filters import format_currency

def create_payments_pdf(person):
    # Create a list to hold the PDF elements
    elements = []

    # Register Arial Unicode MS font
    pdfmetrics.registerFont(TTFont('ArialUnicode', 'arialuni.ttf'))

    # Create a stylesheet for styling the PDF content
    styles = getSampleStyleSheet()

    # Add person information
    elements.append(Paragraph("<b>Coolink Cooperative Savings Account</b>", styles['Title']))
    elements.append(Paragraph(f"<b>Name:</b> {person.name}", styles['Normal']))
    elements.append(Paragraph(f"<b>Company:</b> {person.company.name}", styles['Normal']))
    elements.append(Paragraph(f"<b>Member ID:</b> {person.employee_id}", styles['Normal']))
    elements.append(Paragraph("", styles['Normal']))  # Empty line

    # Create a table for the payment details
    table_data = [
        ['Date', 'Reference Number', 'Description', 'Amount', 'Balance'],
        [None, None, 'Balance B/FWD', format_currency(person.balance_bfd), format_currency(person.balance_bfd)]
    ]

    for payment in person.payments_made:
        table_data.append([
            payment.date.strftime('%Y-%m-%d'),
            payment.ref_no,
            payment.description,
            format_currency(payment.amount),
            format_currency(payment.balance)
        ])

    # Set table style
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'ArialUnicode'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])

    # Create the table
    table = Table(table_data, style=table_style)

    # Add the table to the PDF elements
    elements.append(table)

    # Create the PDF file
    file_path = 'person_payments.pdf'
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    doc.build(elements)

    return file_path
