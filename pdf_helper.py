from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from filters import format_currency
from excel_helper import query


def create_pdf(type,type_id):
    if type == 'savings':
        if type_id == 'None':
           return create_all_savings_pdf()
        else:
            person = query.get_person(type_id)
            return create_payments_pdf(person)
        
    elif type == 'loan':
        if type_id == 'None':
           return create_all_loan_pdf()
        else:
            person = query.get_person(type_id)
            return create_loan_pdf(person)
        
    elif type == 'bank':
        if type_id == 'None':
           return 
        else:
            bank = query.get_bank(type_id)
            return create_bank_pdf(bank)
        
    elif type == 'income':
        if type_id == 'None':
           return create_income_pdf()
        else:
            return 
    elif type == 'persons':
        if type_id == 'None':
           return create_persons_pdf()
    
def create_persons_pdf():
    # Create a list to hold the PDF elements
    elements = []

    # Register Arial Unicode MS font
    pdfmetrics.registerFont(TTFont('ArialUnicode', 'arialuni.ttf'))

    # Create a stylesheet for styling the PDF content
    styles = getSampleStyleSheet()

    # Add person information
    elements.append(Paragraph("<b>Coolink Cooperative Members Summary</b>", styles['Title']))
    elements.append(Paragraph("", styles['Normal']))  # Empty line
    elements.append(Paragraph("", styles['Normal']))  # Empty line

    # Create a table for the payment details
    table_data = [
        ['Employee ID', 'Name','Email', 'Phone Number', 'Savings Balance', 'Loan  Balance','Company' ]   
    ]

    for person in query.get_persons():
        table_data.append([
            person.employee_id,
            '-',
            person.name ,
            person.email ,
            person.phone_no,
            format_currency(person.total_balance),
            format_currency(person.loan_balance),
            person.company.name
        ])
    total_row = [
        'Total',
        'Total',
        '-',
        '-',
        '-',
        format_currency(sum(person.total_balance for person in query.get_persons())),
        format_currency(sum(person.loan_balance for person in query.get_persons()))
    ]
    table_data.append(total_row)

    # Set table style
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'ArialUnicode'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])

    # Create the table
    table = Table(table_data, style=table_style)

    # Add the table to the PDF elements
    elements.append(table)

    # Create the PDF file
    file_path = 'persons.pdf'
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    doc.build(elements)

    return file_path

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
        ['None', 'None', 'Balance B/FWD', format_currency(person.balance_bfd), format_currency(person.balance_bfd)]
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

def create_loan_pdf(person):
    # Create a list to hold the PDF elements
    elements = []

    # Register Arial Unicode MS font
    pdfmetrics.registerFont(TTFont('ArialUnicode', 'arialuni.ttf'))

    # Create a stylesheet for styling the PDF content
    styles = getSampleStyleSheet()

    # Add person information
    elements.append(Paragraph("<b>Coolink Cooperative Loan Account</b>", styles['Title']))
    elements.append(Paragraph(f"<b>Name:</b> {person.name}", styles['Normal']))
    elements.append(Paragraph(f"<b>Company:</b> {person.company.name}", styles['Normal']))
    elements.append(Paragraph(f"<b>Member ID:</b> {person.employee_id}", styles['Normal']))
    elements.append(Paragraph("", styles['Normal']))  # Empty line

    # Create a table for the payment details
    table_data = [
        ['Date', 'Reference Number', 'Description', 'Amount', 'Balance'],
        ['None', 'None', 'Balance B/FWD', format_currency(person.loan_balance_bfd), format_currency(person.loan_balance_bfd)]
    ]

    for payment in person.loan_payments_made:
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

def create_all_savings_pdf():
    # Create a list to hold the PDF elements
    elements = []

    # Register Arial Unicode MS font
    pdfmetrics.registerFont(TTFont('ArialUnicode', 'arialuni.ttf'))

    # Create a stylesheet for styling the PDF content
    styles = getSampleStyleSheet()

    # Add person information
    elements.append(Paragraph("<b>Coolink Cooperative Loan Account</b>", styles['Title']))
    elements.append(Paragraph("", styles['Normal']))
    elements.append(Paragraph("", styles['Normal']))  # Empty line

    # Create a table for the payment details
    table_data = [
        ['Date', 'Reference Number', 'Description', 'Amount']
    ]

    for payment in query.get_savings():
        table_data.append([
            payment.date.strftime('%Y-%m-%d'),
            payment.ref_no,
            payment.description,
            format_currency(payment.amount)
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
    file_path = 'savings.pdf'
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    doc.build(elements)

    return file_path

def create_all_loan_pdf():
    # Create a list to hold the PDF elements
    elements = []

    # Register Arial Unicode MS font
    pdfmetrics.registerFont(TTFont('ArialUnicode', 'arialuni.ttf'))

    # Create a stylesheet for styling the PDF content
    styles = getSampleStyleSheet()

    # Add person information
    elements.append(Paragraph("<b>Coolink Cooperative Loan Account</b>", styles['Title']))
    elements.append(Paragraph("", styles['Normal']))
    elements.append(Paragraph("", styles['Normal']))  # Empty line

    # Create a table for the payment details
    table_data = [
        ['Date', 'Reference Number', 'Description', 'Amount']
    ]

    for payment in query.get_loans():
        table_data.append([
            payment.date.strftime('%Y-%m-%d'),
            payment.ref_no,
            payment.description,
            format_currency(payment.amount)
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
    file_path = 'loans.pdf'
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    doc.build(elements)

    return file_path

def create_bank_pdf(bank):
    # Create a list to hold the PDF elements
    elements = []

    # Register Arial Unicode MS font
    pdfmetrics.registerFont(TTFont('ArialUnicode', 'arialuni.ttf'))

    # Create a stylesheet for styling the PDF content
    styles = getSampleStyleSheet()

    # Add person information
    elements.append(Paragraph("<b>Coolink Cooperative Loan Account</b>", styles['Title']))
    elements.append(Paragraph(f"<b>Name:</b> {bank.name}", styles['Normal']))
    elements.append(Paragraph("", styles['Normal']))
    elements.append(Paragraph("", styles['Normal']))  # Empty line

    # Create a table for the payment details
    table_data = [
        ['Date', 'Reference Number', 'Description', 'Amount']
    ]

    for payment in bank.payments:
        table_data.append([
            payment.date.strftime('%Y-%m-%d'),
            payment.ref_no,
            payment.description,
            format_currency(payment.amount),
            format_currency(payment.bank_balance)
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
    file_path = f'{bank.name} bank.pdf'
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    doc.build(elements)

    return file_path


def create_income_pdf():
    # Create a list to hold the PDF elements
    elements = []

    # Register Arial Unicode MS font
    pdfmetrics.registerFont(TTFont('ArialUnicode', 'arialuni.ttf'))

    # Create a stylesheet for styling the PDF content
    styles = getSampleStyleSheet()

    # Add person information
    elements.append(Paragraph("<b>Coolink Cooperative Income Account</b>", styles['Title']))
    elements.append(Paragraph("", styles['Normal']))
    elements.append(Paragraph("", styles['Normal']))  # Empty line

    # Create a table for the payment details
    table_data = [
        ['Date', 'Reference Number', 'Description', 'Amount']
    ]

    for payment in query.get_income():
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
    file_path = 'income.pdf'
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    doc.build(elements)

    return file_path