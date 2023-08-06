from flask import Flask, render_template, request, redirect,send_file, render_template, redirect, url_for, flash,jsonify
from forms import *
from functools import wraps
from models import *
from excel_helper import create_excel,generate_repayment_schedule,export_repayment_schedule_to_excel,send_upload_to_loan_repayment,send_upload_to_savings,start_up
from pdf_helper import create_pdf
from queries import Queries
import pandas as pd,json,csv
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

def role_required(roles_required):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("You must be logged in to access this page.", "danger")
                return redirect(url_for("login"))

            user_role = current_user.role
            if user_role.name not in roles_required:
                flash("You don't have the required role to access this page.", "danger")
                return redirect(url_for("dashboard"))  # Change this to your desired redirect

            return view_func(*args, **kwargs)

        return wrapper

    return decorator

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
            return redirect(url_for('dashboard'))

        form.errors.append('Invalid User Credentials')

        # next = request.args.get('next')
        # # url_has_allowed_host_and_scheme should check if the url is safe
        # # for redirects, meaning it matches the request host.
        # # See Django's url_has_allowed_host_and_scheme for an example.
        # if not url_has_allowed_host_and_scheme(next, request.host):
        #     return abort(400)

        return redirect( url_for('login',form=form,error=form.errors))
    return render_template('login.html', form=form,error=form.errors)

@app.route('/dashboard')
@login_required
def dashboard():
    person = current_user 
    form = SearchForm()
    return render_template('dashboard.html',person=person,form=form)

@app.route('/forms')
@login_required
@role_required(['Admin','Secretary'])
def forms():
    return render_template('forms.html')

@app.route('/queries')

@login_required
@role_required(['Admin','Secretary','Sub-Admin'])
def queries():
    return render_template('queries.html')

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

@app.route('/search_suggestions', methods=['GET'])
def search_suggestions():
    query = request.args.get('query', '')
    # Perform the search query using Flask-SQLAlchemy
    # For example, search the Company and Person models for the given query
    companies_results = Company.query.filter(Company.name.ilike(f'%{query}%')).all()
    persons_results = Person.query.filter(Person.name.ilike(f'%{query}%')).all()

    suggestions = {
        'companies': [[company.id,company.name] for company in companies_results],
        'persons': [[person.id,person.name] for person in persons_results]
    }

    return jsonify(suggestions)

#creating data
@app.route('/company/create', methods=['GET', 'POST'])
@login_required
@role_required(['Admin','Secretary'])
def create_company():
    form = CompanyForm()

    if form.validate_on_submit():
        company =query.create_new_company(name=form.name.data,balance_bfd=form.balance_bfd.data)#remember to add to form for admin or ask in meeting
        flash('Company created successfully.', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash(form.errors)

    return render_template('forms/company_form.html', form=form)

@app.route('/bank/create', methods=['GET', 'POST'])
@login_required
@role_required(['Admin','Secretary'])
def create_bank():
    form = BankForm()
    if form.validate_on_submit():
        query.create_bank(form.name.data,form.balance.data)#remember to add to form for admin or ask in meeting
        
        flash('Company created successfully.', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash(form.errors)
    
    return render_template('forms/bank_form.html', form=form)

@app.route('/person/create', methods=['GET', 'POST'])
@login_required
@role_required(['Admin','Secretary'])
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

@app.route('/ledger_admin', methods=['GET', 'POST'])
@role_required(['Admin'])
def ledger_admin():
    form = LedgerAdminForm()
    if form.validate_on_submit():
        return redirect(url_for('new_ledger',ledger=form.ledger.data))
    return render_template('admin/ledger_admin.html',form=form)

@app.route('/ledger/<ledger>', methods=['GET', 'POST'])
@role_required(['Admin'])
def new_ledger(ledger):
    form = LedgerForm()
    if form.validate_on_submit():
        query.create_new_ledger(int(ledger),form.name.data,form.description.data)
        return redirect(url_for('dashboard'))
    return render_template('admin/ledger.html',form=form)

@app.route('/role_assignment', methods=['GET', 'POST'])
@role_required(['Admin'])
def role_assignment():
    form = RoleAssignmentForm()

    # Populate the choices for the person and role select fields
    form.person.choices = [(person.id, person.name) for person in Person.query.all()]
    form.role.choices = [(role.id, role.name) for role in Role.query.all()]

    if form.validate_on_submit():
        person_id = form.person.data
        role_id = form.role.data

        person = Person.query.get(person_id)
        role = Role.query.get(role_id)

        if person and role:
            person.role = role
            db.session.commit()
            return redirect(url_for('dashboard'))

    return render_template('admin/role_assignment.html', form=form)

@app.route('/make_payment', methods=['GET', 'POST'])
@login_required
@role_required(['Admin','Secretary'])
def make_payment():
    form = MakePaymentForm()
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
            return redirect(url_for('dashboard'))
        else:
        
           flash('Invalid person selection.')

        return redirect(url_for('get_person', person_id=selected_person_id))
    

    return render_template('forms/payment.html', form=form)

@app.route('/payment', methods=['GET', 'POST'])
@login_required
@role_required(['Admin','Secretary'])
def payment():
    form = PaymentForm()
    form.person_id.choices = [(person.id, (f'{person.name} ({person.employee_id})')) for person in query.get_persons()]
    form.bank.choices=[(bank.id,bank.name) for bank in query.get_banks()]
    
    if form.validate_on_submit():
       
        amount = form.amount.data
        payment_type = form.payment_type.data
        description = form.description.data
        date = form.date.data
        bank_id = form.bank.data
        ref_no=form.ref_no.data
        
        query.make_payment(amount,payment_type,description,date=date,bank_id= bank_id,ref_no=ref_no)
    
        return redirect(url_for('get_person'))

    return render_template('forms/payment.html', form=form)

@app.route('/make_income', methods=['GET', 'POST'])
@login_required
@role_required(['Admin','Secretary'])
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
@role_required(['Admin','Secretary','Sub-Admin'])
def get_persons():
    persons = query.get_persons()
    total_loan = sum(person.loan_balance for person in persons)
    total_savings = sum(person.total_balance for person in persons)
    return render_template('query/person.html', persons=persons,total_loan=total_loan,total_savings=total_savings)


def filter_payments(start_date,end_date,payments):

    filtered_payments = payments
    if start_date and end_date:
        filtered_payments = [payment for payment in payments if start_date <= payment.date <= end_date]
    elif start_date:
        filtered_payments = [payment for payment in payments if payment.date >= start_date]
    elif end_date:
        filtered_payments = [payment for payment in payments if payment.date <= end_date]

    return filtered_payments

@app.route('/savings_account', methods=['GET'])
@login_required
def get_payments():
    
    payments = query.get_savings()
    persons = query.get_persons()
    form = DateFilterForm(request.args)
    # Filter payments based on date range
    start_date = form.start_date.data
    end_date = form.end_date.data
    filtered_payments =filter_payments(start_date,end_date,payments)

    return render_template('query/savings_payment.html', form=form, payments=filtered_payments, persons=persons)


@app.route('/loans', methods=['GET', 'POST'])
@login_required
@role_required(['Admin','Secretary','Sub-Admin'])
def get_loan():
    loans = query.get_loans()
    form = DateFilterForm(request.args)
    # Filter payments based on date range
    start_date = form.start_date.data
    end_date = form.end_date.data
    filtered_payments =filter_payments(start_date,end_date,loans)
    return render_template('query/loans.html',loans=filtered_payments)

@app.route('/income', methods=['GET'])
@login_required
@role_required(['Admin','Secretary','Sub-Admin'])
def get_income():
    incomes = query.get_income()
    form = DateFilterForm(request.args)
    # Filter payments based on date range
    start_date = form.start_date.data
    end_date = form.end_date.data
    filtered_payments =filter_payments(start_date,end_date,incomes)
    return render_template('query/income.html', incomes=filtered_payments)

@app.route('/savings_account/<person_id>', methods=['GET', 'POST'])
@login_required
@role_required(['Admin','Secretary','Sub-Admin'])
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
@role_required(['Admin','Secretary','Sub-Admin'])
def bank_report():
    banks = query.get_banks()
    return render_template('query/banks.html', banks=banks)
    
@app.route('/companies_report')
@login_required
@role_required(['Admin','Secretary','Sub-Admin'])
def companies_report():
    companies = query.get_companies()
    return render_template('query/companies.html', companies=companies)

@app.route('/company/<company_id>')
@login_required
@role_required(['Admin','Secretary','Sub-Admin'])
def individual_company_report(company_id):
    # Query the bank and its associated payments
    company = query.get_company(company_id)
    payments = company.payments_made

    # Calculate the total amount received by the bank
    total_amount = sum(payment.amount for payment in payments)
    # Render the bank report template with the data
    return render_template('query/company_report.html', company=company, payments=payments, total_amount=total_amount)

@app.route('/debtors_report')
@login_required
@role_required(['Admin','Secretary','Sub-Admin'])
def debtors_report():
    # Query the bank and its associated payments
    company = query.get_companies()
    loans = query.get_loans()

    # Render the bank report template with the data
    return render_template('query/debtors_report.html', company=company, loans = loans)

@app.route('/bank_report/<bank_id>')
@login_required
@role_required(['Admin','Secretary','Sub-Admin'])
def individual_bank_report(bank_id):
    # Query the bank and its associated payments
    bank = query.get_bank(bank_id)
    payments = bank.payments

    # Calculate the total amount received by the bank
    total_amount = sum(payment.amount for payment in payments)
    # Render the bank report template with the data
    return render_template('query/bank_report.html', bank=bank, payments=payments, total_amount=total_amount)

@app.route('/ledger_report')
@login_required
@role_required(['Admin','Secretary','Sub-Admin'])
def ledger_report():
    # Retrieve data from the database
    companies = Company.query.all()
    banks = Bank.query.all()
    persons = Person.query.all()
    assets = Asset.query.all()
    liabilities = Liability.query.all()
    incomes = Income.query.all()
    expenses = Expense.query.all()
    investments = Investment.query.all()
    # Calculate total cash and equivalents
    total_company_receivable =sum(company.amount_accumulated for company in companies)
    total_cash_and_equivalents = total_company_receivable + sum(bank.new_balance for bank in banks)

    # Calculate total accounts receivable
    total_accounts_receivable = sum(person.loan_balance for person in persons)

    total_investments= sum(investment.balance for investment in investments if investment.balance)
    # Calculate total income
    total_incomes = sum(income.balance for income in incomes if income.balance)

    # Calculate total expenses
    total_expenses = sum(expense.balance for expense in expenses if expense.balance )

    # Calculate total assets
    total_assets = total_cash_and_equivalents + total_accounts_receivable + sum(asset.balance for asset in assets if asset.balance) + total_incomes + total_investments

    # Calculate total accounts payable
    total_accounts_payable = sum(person.total_balance for person in persons)

    # Calculate total liabilities
    total_liabilities = total_accounts_payable + sum(liability.balance for liability in liabilities if liability.balance) + total_expenses

    # Calculate total equity and liabilities & equity
    total_equity = total_assets - total_liabilities
    total_liabilities_and_equity = total_liabilities + total_equity

    return render_template('query/ledger_report.html', assets=assets, total_expenses=total_expenses, expenses = expenses,incomes=incomes,
                           banks=banks, total_cash_and_equivalents=total_cash_and_equivalents,company =total_company_receivable,
                           total_accounts_receivable=total_accounts_receivable, total_incomes=total_incomes,
                           total_assets=total_assets, investments=investments,liabilities=liabilities,
                           total_accounts_payable=total_accounts_payable, total_liabilities=total_liabilities,
                           total_equity=total_equity, total_liabilities_and_equity=total_liabilities_and_equity)

@app.route('/balance_sheet')
@login_required
@role_required(['Admin','Secretary','Sub-Admin'])
def balance_sheet():
    # Retrieve data from the database
    companies = Company.query.all()
    banks = Bank.query.all()
    total_cash_and_equivalents = sum(company.amount_accumulated for company in companies) +sum(bank.new_balance for bank in banks)

    persons = Person.query.all()
    total_accounts_receivable = sum(person.loan_balance for person in persons)
    # Calculate the total assets
    total_assets = total_cash_and_equivalents + total_accounts_receivable

    total_accounts_payable = sum(person.total_balance for person in persons)

    # Calculate the total liabilities
    total_liabilities = total_accounts_payable 

    # Calculate the total equity and liabilities & equity
    total_equity = total_assets - total_liabilities
    total_liabilities_and_equity = total_liabilities + total_equity
    balance_sheet_data = { 'total_cash_and_equivalents': total_cash_and_equivalents,
                           'total_accounts_receivable':total_accounts_receivable,
                           'total_assets':total_assets,
                           'total_accounts_payable':total_accounts_payable,
                           'total_liabilities':total_liabilities,
                           'total_equity':total_equity,
                           'total_liabilities_and_equity':total_liabilities_and_equity
    }

    return render_template('query/balance_sheet.html',balance_sheet_data=balance_sheet_data,
                           total_cash_and_equivalents=total_cash_and_equivalents,
                           total_accounts_receivable=total_accounts_receivable,
                           total_assets=total_assets,
                           total_accounts_payable=total_accounts_payable,
                           total_liabilities=total_liabilities,
                           total_equity=total_equity,
                           total_liabilities_and_equity=total_liabilities_and_equity)

@app.route('/loan/create', methods=['GET', 'POST'])
@login_required
@role_required(['Admin','Secretary'])
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
        if form.existing_expense.data:
            # Handle existing expense selection
            query.update_expense(id=form.existing_expense.data,amount=form.amount.data,date=form.date.data,
                                    ref_no=form.ref_no.data,bank_id=form.bank_id.data,
                                    description=form.description.data)
        else:
            query.add_expense(name=form.name.data,amount=form.amount.data,date=form.date.data,
                                    ref_no=form.ref_no.data,bank_id=form.bank_id.data,
                                    description=form.description.data)
        return redirect(url_for('dashboard'))
    return render_template('forms/expense_form.html', form=form)

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    # Add logic to retrieve the list of persons from the database
    # Replace `get_all_persons()` with an appropriate function that retrieves the list of persons.
    persons = query.get_persons()

    form = WithdrawalForm()
    form.person.choices = [(person.id, person.name) for person in query.get_persons()]
    if form.validate_on_submit():
        person_id = form.person.data
        amount = form.amount.data
        
        # Retrieve the selected person from the database
        selected_person = query.get_person(person_id)

        if selected_person:
            # Perform validation to ensure the withdrawal amount does not exceed the available balance
            if amount <= selected_person.total_balance:
                # Update the balance in the database (subtract the withdrawal amount)
                selected_person.total_balance -= amount

                # Save the changes to the database
                # (You'll need to commit the session if using SQLAlchemy)
                # db.session.commit()

                # You may want to add additional logic for transaction history, etc.

                return f"Withdrawal of {amount} successful for {selected_person.name}. Updated balance: {selected_person.balance_bfd}"
            else:
                return f"Insufficient balance for {selected_person.name} to withdraw {amount}."
        else:
            return "Invalid person selected."

    return render_template('forms/withdraw.html', form=form, persons=persons)


#uploads 

@app.route('/upload_savings', methods=['GET', 'POST'])
@login_required
@role_required(['Admin','Secretary'])
def upload_savings():
    form = UploadForm()
    if request.method == 'POST' and form.validate_on_submit():
        file = request.files['file']
        log_report('validated_file')
        if file :
            log_report('found_file')
            # Save the uploaded file
            file.save(file.filename)
            # Process the uploaded file
            send_upload_to_savings(file,form.description.data,form.date.data)

            return redirect(url_for('get_payments'))
    else:
        log_report(form.errors)
    return render_template('forms/upload.html', form = form)

@app.route('/upload_loan_repayment', methods=['GET', 'POST'])
@login_required
@role_required(['Admin','Secretary'])
def upload_loan():
    form = UploadForm()
    if request.method == 'POST':
        file = request.files['file']
        if file :
            # Save the uploaded file
            file.save(file.filename)
            # Process the uploaded file
            send_upload_to_loan_repayment(file.filename)

            return redirect('/dashboard')
    return render_template('forms/upload.html',form=form)

@app.route('/startup', methods=['GET', 'POST'])
@login_required
@role_required(['Admin','Secretary'])
def startup():
    
    if request.method == 'POST' :
        file = request.files['file']
        log_report('validated_file')
        if file :
            log_report('found_file')
            # Save the uploaded file
            file.save(file.filename)
            # Process the uploaded file
            file=start_up(file)
            return redirect(url_for('download',file_path=file))

    return render_template('forms/startup.html')

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

@app.route("/logout", methods=['GET', 'POST'])
@login_required
def logout():
  logout_user()
  current_user = None
  return redirect(url_for('dashboard'))

#dynamic lookup
@app.route('/get_balance/<int:person_id>')
def get_balance(person_id):
    selected_person = Person.query.get(person_id)
    if selected_person:
        return format_currency(selected_person.total_balance)
    else:
        return jsonify(error='Person not found'), 404
    
@app.route('/forgot_password')
def forgot_password():
    pass

@app.route('/reset_password',methods=['GET', 'POST'])
@login_required
@role_required(['Admin','Secretary'])
def reset_password():
    form = ResetPasswordForm()
    if current_user.role.name == 'Admin':
        form.person.choices = [(person.id,f'{person.name}({person.employee_id})') for person in query.get_persons()]
    else:
        form.person.choices = [(person.id,f'{person.name}({person.employee_id})') for person in query.get_persons() if person.role.name =='User' ]


    if form.validate_on_submit():
        person_id = form.person.data
        password = query.generate_password()
        person = query.get_person(person_id)
        person.password = password 
        db.session.commit()
        with open (f'credentials/{person.employee_id}_credentials.csv','w',newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Username','Password'])
            writer.writerow([f'{person.employee_id} or {person.email}',password])

        return redirect(url_for('download',file_path=file.name))
    return render_template('admin/reset_password.html',form = form)
        
@app.route('/get_sub_accounts/<int:main_account_id>')
def get_sub_accounts(main_account_id):
    # Fetch sub-account options based on the selected main_account
    # You need to implement this logic based on your database structure
    sub_accounts = query.sub_accounts(main_account_id)

    # Create a list of dictionaries with 'id' and 'name' keys
    sub_account_options = [{'id': sub_account.id, 'name': sub_account.name} for sub_account in sub_accounts]

    return jsonify(sub_account_options)