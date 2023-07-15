from flask import Flask, render_template, request, redirect,send_file, render_template, redirect, url_for, flash,abort
from forms import *
from models import db,Company,Person
from excel_helper import create_excel,generate_repayment_schedule,export_repayment_schedule_to_excel,send_upload_to_loan_repayment,send_upload_to_savings
from pdf_helper import create_pdf
from queries import Queries
from sqlalchemy.orm import subqueryload
import pandas as pd ,io, openpyxl,json,pdfkit
from filters import format_currency
from flask_login import LoginManager,login_user, login_required, logout_user, current_user
login_manager = LoginManager()


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cooperative.db'  # Replace with your database URI
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with your own secret key
db.init_app(app)
query= Queries(db)
login_manager.init_app(app)

@login_manager.user_loader
def load_user(person_id):
    return Person.query.get(person_id)

def log_report(report):
    with open("report.txt", 'a', encoding='utf-8') as f:
            f.write(f'{report}\n')
# Routes for creating and submitting forms

@app.route('/', methods=['GET', 'POST'])
def login():

    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.identifier.data
        password = form.password.data
        user = query.get_user(identifier)
        
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))

        form.errors.append('Invalid User Credentials')

        # next = request.args.get('next')
        # # url_has_allowed_host_and_scheme should check if the url is safe
        # # for redirects, meaning it matches the request host.
        # # See Django's url_has_allowed_host_and_scheme for an example.
        # if not url_has_allowed_host_and_scheme(next, request.host):
        #     return abort(400)

        return redirect( url_for('login',form=form,error=form.errors))
    return render_template('login.html', form=form,error=form.errors)

@app.route('/index')
@login_required
def index():
    return render_template('index.html')

@app.template_filter('to_json')
@login_required
def to_json(obj):
    if hasattr(obj, 'to_json'):
        # Check if the object has a to_dict() method
        return json.dumps(obj.to_json())
    elif isinstance(obj, list) or isinstance(obj, dict):
        # Handle lists and dictionaries by directly serializing them to JSON
        return json.dumps(obj)
    else:
        # Raise an exception for unsupported object types
        raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

# Register the filter in the Jinja environment

@app.template_filter('currency')
@login_required
def currency(value):
    # Implement your filter logic here
    modified_value = format_currency(value)  # Modify the value as needed
    return modified_value

#creating data
@app.route('/company/create', methods=['GET', 'POST'])
@login_required
def create_company():
    form = CompanyForm()

    if form.validate_on_submit():
        company =query.create_new_company(name=form.name.data,balance_bfd=form.balance_bfd.data)#remember to add to form for admin or ask in meeting
        flash('Company created successfully.', 'success')
        return redirect(url_for('index'))
    else:
        flash(form.errors)

    return render_template('forms/company_form.html', form=form)

@app.route('/bank/create', methods=['GET', 'POST'])
@login_required
def create_bank():
    form = BankForm()
    if form.validate_on_submit():
        query.create_bank(form.name.data,form.balance.data)#remember to add to form for admin or ask in meeting
        
        flash('Company created successfully.', 'success')
        return redirect(url_for('index'))
    else:
        flash(form.errors)
    
    return render_template('forms/bank_form.html', form=form)

@app.route('/person/create', methods=['GET', 'POST'])
@login_required
def create_person():
    form = PersonForm()
    form.company_id.choices = [(company.id, company.name) for company in Company.query.all()]
    if form.validate_on_submit():
        file = query.create_new_user(employee_id=form.employee_id.data,
            name=form.name.data,
            email=form.email.data,
            phone_no=form.phone_no.data,
            balance=form.total_balance.data,
            loan_balance=form.loan_balance.data,
            company_id=form.company_id.data
        )
        return redirect(f'/download/{file}')
        
    else:
        
                flash(f'Error in field {form.errors}')
    return render_template('forms/person_form.html', form=form, companies=Company.query.all())

@app.route('/payment', methods=['GET', 'POST'])
@login_required
def make_payment():
    form = PaymentForm()
    form.person_id.choices = [(person.id, (f'{person.name} ({person.employee_id})')) for person in query.get_persons()]
    form.bank.choices=[(bank.id,bank.name) for bank in query.get_banks()]
    
    if form.validate_on_submit():
       
        amount = form.amount.data
        payment_type = form.payment_type.data
        description = form.description.data
        selected_person_id = form.person_id.data
        selected_person = Person.query.get(selected_person_id)
        date = form.date.data
        bank_id = form.bank.data
        ref_no=form.ref_no.data
        if selected_person:
            
            if payment_type == 'savings':
                query.save_amount(employee_id=selected_person_id,amount=amount,date=date,description=description,bank_id=bank_id,ref_no=ref_no)
                
            elif payment_type == 'loan':
                

                query.repay_loan(selected_person.id,amount,date,bank_id,ref_no,description)
   
            flash('Payment submitted successfully.')
            return redirect(url_for('index'))
        else:
        
           flash('Invalid person selection.')

        return redirect(url_for('get_person', person_id=selected_person_id))
    

    return render_template('forms/payment.html', form=form)

@app.route('/make_income', methods=['GET', 'POST'])
@login_required
def make_income():
    form = IncomeForm()
    form.bank.choices=[(bank.id,bank.name) for bank in query.get_banks()]
    
    if form.validate_on_submit():
       
        amount = form.amount.data
        description = form.description.data
        date = form.date.data
        bank_id = form.bank.data
        ref_no=form.ref_no.data

        query.make_income(amount,date,ref_no,bank_id,description)

    return render_template('forms/income_form.html', form=form)

#making queries

@app.route('/persons', methods=['GET'])
@login_required
def get_persons():
    persons = query.get_persons()
    return render_template('query/person.html', persons=persons)

@app.route('/savings_account', methods=['GET'])
@login_required
def get_payments():
    payments = query.get_savings()
    persons = query.get_persons()
    return render_template('query/savings_payment.html', payments=payments, persons=persons)

@app.route('/loans', methods=['GET', 'POST'])
@login_required
def get_loan():
    loans = query.get_loans()
    return render_template('query/loans.html',loans=loans)

@app.route('/income', methods=['GET'])
@login_required
def get_income():
    incomes = query.get_income()
    return render_template('query/income.html', incomes=incomes)

@app.route('/savings_account/<person_id>', methods=['GET', 'POST'])
@login_required
def savings_account(person_id):
    person = query.get_person(person_id)
    payments = person.payments_made
    return render_template('query/savings_account.html', payments= payments,person=person)

@app.route('/loan/<person_id>', methods=['GET', 'POST'])
@login_required
def loan_account(person_id):
    loans = query.get_person_loans(person_id)
    person = query.get_person(person_id)
    payments = [payment for payment in person.loan_payments_made ]
    return render_template('query/loan_account.html',payments=payments, person=person, loans=loans)

@app.route('/banks_report')
@login_required
def bank_report():
    bank = query.get_banks()
    return render_template('query/banks.html', banks=bank)
    
@app.route('/bank_report/<bank_id>')
@login_required
def individual_bank_report(bank_id):
    # Query the bank and its associated payments
    bank = query.get_bank(bank_id)
    payments = bank.payments

    # Calculate the total amount received by the bank
    total_amount = sum(payment.amount for payment in payments)
    # Render the bank report template with the data
    return render_template('query/bank_report.html', bank=bank, payments=payments, total_amount=total_amount)

#create loan 

@app.route('/loan/create', methods=['GET', 'POST'])
@login_required
def create_loan():
    form = LoanForm()
    if form.validate_on_submit():
        query.make_loan(employee_id=form.employee_id.data,
            amount=form.amount.data,
            interest_rate=form.interest_rate.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data)
        
        person_id=form.employee_id.data
        amount=form.amount.data
        interest_rate=form.interest_rate.data
        start_date=pd.to_datetime(form.start_date.data)
        end_date=pd.to_datetime(form.end_date.data)
        
        # Generate the repayment schedule
        repayment_schedule = generate_repayment_schedule(person_id, amount, interest_rate, start_date, end_date)

        # Export the repayment schedule to Excel
        file_path = export_repayment_schedule_to_excel(repayment_schedule, person_id)

        # Return the file path for download
        return redirect(f'/download/{file_path}')

    return render_template('forms/loan_form.html', form = form)



@app.route('/expense/create', methods=['GET', 'POST'])
def create_expense():
    form = ExpenseForm()
    if form.validate_on_submit():
        expense = query.add_expense(amount=form.amount.data,date=form.date.data,
                                    ref_no=form.ref_no.data,bank_id=form.bank_id.data,
                                    description=form.description.data)

        return redirect(url_for('index'))
    return render_template('forms/expense_form.html', form=form)

# @app.route('/investment/create', methods=['GET', 'POST'])
# def create_investment():
#     form = InvestmentForm()
#     if form.validate_on_submit():
#         investment = Investment(
#             description=form.description.data,
#             amount=form.amount.data,
#             date=form.date.data
#         )
#         db.session.add(investment)
#         db.session.commit()
#         return redirect(url_for('index'))
#     return render_template('forms/investment_form.html', form=form)


#uploads 

@app.route('/upload_savings', methods=['GET', 'POST'])
@login_required
def upload_savings():
    if request.method == 'POST':
        file = request.files['file']
        if file :
            # Save the uploaded file
            file.save(file.filename)
            # Process the uploaded file
            send_upload_to_savings(file.filename)

            return redirect('/download')
    return render_template('forms/upload.html')

@app.route('/upload_loan_repayment', methods=['GET', 'POST'])
@login_required
def upload_loan():
    if request.method == 'POST':
        file = request.files['file']
        if file :
            # Save the uploaded file
            file.save(file.filename)
            # Process the uploaded file
            send_upload_to_loan_repayment(file.filename)

            return redirect('/index')
    return render_template('forms/upload.html')

#DOWNLOADS
@app.route('/download/<path:file_path>', methods=['GET'])
@login_required
def download(file_path):
    # Send the file back to the user as a response
    return send_file(file_path, as_attachment=True)

@app.route('/download_pdf/<type>/<type_id>')
@login_required
def download_pdf(type,type_id):

    file_path = create_pdf(type,type_id)

    return redirect(f'/download/{file_path}')

@app.route('/download_excel/<type>/<type_id>')
@login_required
def download_excel(type,type_id):

    file_path = create_excel(type,type_id)

    return redirect(f'/download/{file_path}')