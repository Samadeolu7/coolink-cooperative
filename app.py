from flask import Flask, render_template, request, redirect,send_file, render_template, redirect, url_for, flash , get_flashed_messages
from forms import CompanyForm, PersonForm, PaymentForm, LoanForm, ExpenseForm, InvestmentForm,BankForm
from models import db,Company, Person, Payment, Loan, Expense, Investment,Bank
from excel_helper import process_excel,generate_repayment_schedule,export_repayment_schedule_to_excel
from queries import Queries
from sqlalchemy.orm import subqueryload
import pandas as pd

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cooperative.db'  # Replace with your database URI
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with your own secret key
db.init_app(app)
query= Queries(db)

def log_report(report):
    with open("report.txt", 'a', encoding='utf-8') as f:
            f.write(f'{report}\n')

# Routes for creating and submitting forms

@app.route('/')
def index():
    return 'Welcome to the Cooperative App!'

#creating data

@app.route('/company/create', methods=['GET', 'POST'])
def create_company():
    form = CompanyForm()

    if form.validate_on_submit():
        company = Company(name=form.name.data, amount_accumulated=0.0)#remember to add to form for admin or ask in meeting
        db.session.add(company)
        db.session.commit()
        flash('Company created successfully.', 'success')
        return redirect(url_for('index'))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error in field "{getattr(form, field).label.text}": {error}', 'error')

    return render_template('company_form.html', form=form)

@app.route('/bank/create', methods=['GET', 'POST'])
def create_bank():
    form = BankForm()
    if form.validate_on_submit():
        bank = Bank(name=form.name.data, balance=form.balance.data)#remember to add to form for admin or ask in meeting
        db.session.add(bank)
        db.session.commit()
        flash('Company created successfully.', 'success')
        return redirect(url_for('index'))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error in field "{getattr(form, field).label.text}": {error}', 'error')
    if form.errors:
        log_report(form.errors)
    return render_template('bank_form.html', form=form)


@app.route('/person/create', methods=['GET', 'POST'])
def create_person():
    form = PersonForm()
    form.company_id.choices = [(company.id, company.name) for company in Company.query.all()]
    if form.validate_on_submit():
        person = Person(
            is_admin=form.is_admin.data,
            employee_id=form.employee_id.data,
            name=form.name.data,
            email=form.email.data,
            phone_no=form.phone_no.data,
            
            total_balance=form.total_balance.data,
            loan_balance=form.loan_balance.data,
            company_id=form.company_id.data
        )
        db.session.add(person)
        db.session.commit()
        flash('Person created successfully.', 'success')
        return redirect(url_for('index'))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error in field "{getattr(form, field).label.text}": {error}', 'error')
    return render_template('person_form.html', form=form, companies=Company.query.all())

@app.route('/payment', methods=['GET', 'POST'])
def make_payment():
    form = PaymentForm()
    form.person_id.choices = [(person.id, person.name) for person in Person.query.all()]
    log_report('IT did not VALIDATE')
    if form.validate_on_submit():
        log_report('IT VALIDATED')
        amount = form.amount.data
        payment_type = form.payment_type.data
        description = form.description.data
        selected_person_id = form.person_id.data
        selected_person = Person.query.get(selected_person_id)
        date = form.date.data
        if selected_person:
            log_report('IT VALIDATED selected person')
            if payment_type == 'savings':
                query.save_amount(selected_person_id,amount,date,description)
                
            elif payment_type == 'loan':
                log_report('IT entered loan')

                query.repay_loan(selected_person.id,amount,date,description)
   
            flash('Payment submitted successfully.')
            return redirect(url_for('index'))
        else:
        
           flash('Invalid person selection.')

        return redirect(url_for('get_person', person_id=selected_person_id))
    if form.errors:
        log_report(form.errors)

    return render_template('payment.html', form=form, persons=Person.query.all())

#making queries

@app.route('/persons', methods=['GET'])
def get_person():
    persons = Person.query.all()
    return render_template('person.html', persons=persons)

@app.route('/savings_payments', methods=['GET'])
def get_payments():
    payments = Payment.query.filter_by(loan=0).all()
    persons = Person.query.all()
    return render_template('savings_payment.html', payments=payments, persons=persons)




@app.route('/savings/<person_id>', methods=['GET', 'POST'])
def savings_acccount(person_id):
    payments = query.get_payments(person_id)
    person = query.get_person(person_id)
    company = Company.query.get(person.company_id)
    return render_template('savings_account.html', payments= payments,person=person,company = company)

@app.route('/loans/<person_id>', methods=['GET', 'POST'])
def loan_acccount(person_id):
    payments = query.get_payments(person_id)
    person = query.get_person(person_id)
    company = query.get_company(person.company_id)
    return render_template('loan_account.html', payments= payments,person=person,company = company)

#create loan 

@app.route('/loan/create', methods=['GET', 'POST'])
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
        return redirect(f'/download_repayment_schedule/{file_path}')

    return render_template('loan_form.html', form = form)

# Route to download the repayment schedule
@app.route('/download_repayment_schedule/<path:file_path>', methods=['GET'])
def download_repayment_schedule(file_path):
    # Send the file back to the user as a response
    return send_file(file_path, as_attachment=True)

@app.route('/expense/create', methods=['GET', 'POST'])
def create_expense():
    form = ExpenseForm()
    if form.validate_on_submit():
        expense = Expense(
            description=form.description.data,
            amount=form.amount.data,
            date=form.date.data
        )
        db.session.add(expense)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('expense_form.html', form=form)

@app.route('/investment/create', methods=['GET', 'POST'])
def create_investment():
    form = InvestmentForm()
    if form.validate_on_submit():
        investment = Investment(
            description=form.description.data,
            amount=form.amount.data,
            date=form.date.data
        )
        db.session.add(investment)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('investment_form.html', form=form)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.xlsx'):
            # Save the uploaded file
            file.save(file.filename)
            # Process the uploaded file
            process_excel(file.filename)

            return redirect('/download')
    return render_template('upload.html')


@app.route('/download')
def download_file():
    # Generate the Excel file for download
    # ...
    return send_file('output.xlsx', as_attachment=True)