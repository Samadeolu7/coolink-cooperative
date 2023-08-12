from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from filters import format_currency
from excel_helper import query

def create_pdf(type, type_id):
    if type == 'savings':
        if type_id == 'None':
            return create_list_pdf('Coolink Cooperative Savings Account', 'savings.pdf', query.get_savings())
        else:
            person = query.get_person(type_id)
            return create_payments_pdf(person, 'Coolink Cooperative Savings Account', f'{person.name} payments.pdf', person.payments_made)

    elif type == 'loan':
        if type_id == 'None':
            return create_list_pdf('Coolink Cooperative Loan Account', 'loans.pdf', query.get_loans())
        else:
            person = query.get_person(type_id)
            return create_payments_pdf(person, 'Coolink Cooperative Loan Account', f'{person.name} loan payments.pdf', person.loan_payments_made)

    elif type == 'bank':
        if type_id == 'None':
            return create_list_pdf('', '', [])
        else:
            bank = query.get_bank(type_id)
            return create_payments_pdf(bank, 'Coolink Cooperative Bank Account', f'{bank.name} bank payments.pdf', bank.payments)

    elif type == 'income':
        if type_id == 'None':
            return create_list_pdf('Coolink Cooperative Income Account', 'income.pdf', query.get_income())
        else:
            return

    elif type == 'persons':
        if type_id == 'None':
            return create_persons_pdf()

def create_list_pdf(title, file_name, data):
    elements = prepare_common_elements(title)

    table_data = [
        ['Date', 'Reference Number', 'Description', 'Amount']
    ]

    for item in data:
        table_data.append([
            item.date.strftime('%Y-%m-%d'),
            item.ref_no,
            item.description,
            format_currency(item.amount)
        ])

    table_style = prepare_common_table_style()

    table = Table(table_data, style=table_style)
    elements.append(table)

    create_and_save_pdf(file_name, elements)

    return file_name

def create_payments_pdf(person_or_bank, title, file_name, payments_data):
    elements = prepare_common_elements(title)
    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"<b>Name:</b> {person_or_bank.name}", styles['Normal']))
    elements.append(Paragraph("", styles['Normal']))  # Empty line

    table_data = [
        ['Date', 'Reference Number', 'Description', 'Amount', 'Balance'],
        ['None', 'None', 'Balance B/FWD', format_currency(person_or_bank.balance_bfd), format_currency(person_or_bank.balance_bfd)]
    ]

    for payment in payments_data:
        table_data.append([
            payment.date.strftime('%Y-%m-%d'),
            payment.ref_no,
            payment.description,
            format_currency(payment.amount),
            format_currency(payment.balance)
        ])

    table_style = prepare_common_table_style()

    table = Table(table_data, style=table_style)
    elements.append(table)

    create_and_save_pdf(file_name, elements)

    return file_name

def create_persons_pdf():
    elements = prepare_common_elements('Coolink Cooperative Members Summary')
    
    table_data = [
        ['Employee ID', 'Name', 'Email', 'Phone Number', 'Savings Balance', 'Loan Balance', 'Company']
    ]

    for person in query.get_persons():
        table_data.append([
            person.employee_id,
            '-',
            person.name,
            person.email,
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

    table_style = prepare_common_table_style()

    table = Table(table_data, style=table_style)
    elements.append(table)

    create_and_save_pdf('persons.pdf', elements)

    return 'persons.pdf'

def prepare_common_elements(title):
    elements = []

    pdfmetrics.registerFont(TTFont('ArialUnicode', 'Arial Unicode MS Font.ttf'))

    styles = getSampleStyleSheet()

    elements.append(Paragraph(f"<b>{title}</b>", styles['Title']))
    elements.append(Paragraph("", styles['Normal']))  # Empty line
    elements.append(Paragraph("", styles['Normal']))  # Empty line

    return elements

def prepare_common_table_style():
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'ArialUnicode'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])

def create_and_save_pdf(file_name, elements):
    doc = SimpleDocTemplate(file_name, pagesize=letter)
    doc.build(elements)
