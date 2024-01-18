from collections import defaultdict
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    send_file,
    render_template,
    redirect,
    url_for,
    flash,
    jsonify,
    g,
)
from sqlalchemy import desc
from forms import *
from functools import wraps
from models import *
from excel_helper import (
    create_excel,
    generate_repayment_schedule,
    export_repayment_schedule_to_excel,
    send_upload_to_loan_repayment,
    send_upload_to_savings,
    start_up,
    create_income_excel,
)
from pdf_helper import create_pdf,create_income_pdf
from queries import Queries
from filters import format_currency, calculate_duration_in_months
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
import os
import pandas as pd, json, csv

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")

db.init_app(app)
query = Queries(db)
login_manager = LoginManager()

login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "You must be logged in to access this page."



@login_manager.user_loader
def load_user(person_id):
    return Person.query.get(person_id)


def role_required(roles_required):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("You must be logged in to access this page.", "error")
                return redirect(url_for("login"))

            user_role = current_user.role
            if user_role.name not in roles_required:
                flash("You don't have the required role to access this page.", "error")
                return redirect(
                    url_for("dashboard")
                )  # Change this to your desired redirect

            return view_func(*args, **kwargs)

        return wrapper

    return decorator


@app.before_request
def before_request():
    g.user = current_user


# Routes for creating and submitting forms


@app.route("/", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.identifier.data
        password = form.password.data
        user = query.get_user(identifier)

        if user and user.password == query.hash_password(password):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Invalid User Credentials", "error")

        return redirect(url_for("login", form=form))
    return render_template("login.html", form=form, error=form.errors)


@app.route("/dashboard")
@login_required
def dashboard():
    person = current_user
    form = SearchForm()
    pre_guarantor = person.get_guaranteed_payments()
    failed_loan = None
    message = None
    for payment in person.loan_form_payment:
        if payment.failed:
            failed_loan = payment
            if failed_loan.guarantor_amount not in [0, None]:
                if failed_loan.loan_amount > failed_loan.guarantor_amount:
                    message = "Guaranteed amount insuffficient"
                else:
                    message = "Consent not given"

                break  # Exit the loop if a failed loan is found
 
    return render_template("dashboard.html", person=person, form=form,consents=pre_guarantor,failed_loan=failed_loan,message=message)


@app.route("/forms")
@login_required
@role_required(["Admin", "Secretary"])
def forms():
    person = current_user
    return render_template("forms.html", person=person)


@app.route("/queries")
@login_required
@role_required(["Admin", "Secretary", "Sub-Admin"])
def queries():
    person = current_user
    return render_template("queries.html", person=person)


@app.template_filter("to_json")
@login_required
def to_json(obj):
    if hasattr(obj, "to_json"):
        # Check if the object has a to_dict() method
        return json.dumps(obj.to_json())
    elif isinstance(obj, list) or isinstance(obj, dict):
        # Handle lists and dictionaries by directly serializing them to JSON
        return json.dumps(obj)
    else:
        # Raise an exception for unsupported object types
        raise TypeError(
            f"Object of type {obj.__class__.__name__} is not JSON serializable"
        )


# Register the filter in the Jinja environment


@app.template_filter("currency")
@login_required
def currency(value):
    # Implement your filter logic here
    modified_value = format_currency(value)  # Modify the value as needed
    return modified_value

@app.template_filter("calculate_duration")
def calculate_duration(start_date, end_date):
    return calculate_duration_in_months(start_date, end_date)

# creating data
@app.route("/company/create", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Secretary"])
def create_company():
    form = CompanyForm()
    if request.method == "POST":
        if form.validate_on_submit():
            company = query.create_new_company(
                name=form.name.data, balance_bfd=form.balance_bfd.data
            )
            if company == True:
                flash("Company created successfully.", "success")
                return redirect(url_for("dashboard"))
            else:
                flash(company, "error")
        else:
            flash(f"{form.errors}", "error")

    return render_template("forms/company_form.html", form=form)


@app.route("/bank/create", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Secretary"])
def create_bank():
    form = BankForm()
    if request.method == "POST":
        if form.validate_on_submit():
            query.create_bank(
                form.name.data, form.balance.data
            )  # remember to add to form for admin or ask in meeting

            flash("Company created successfully.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash(f"{form.errors}", "error")

    return render_template("forms/bank_form.html", form=form)


@app.route("/person/create", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Secretary"])
def create_person():
    form = PersonForm()
    form.company_id.choices = [
        (company.id, company.name) for company in Company.query.all()
    ]

    if request.method == "POST":
        if form.validate_on_submit():
            file = query.create_new_user(
                employee_id=form.employee_id.data,
                name=form.name.data,
                email=form.email.data,
                phone_no=form.phone_no.data,
                balance=form.available_balance.data,
                loan_balance=form.loan_balance.data,
                company_id=form.company_id.data,
            )
            if file:
                flash("Succesfully created Member", "success")
                return redirect(f"/download/{file}")
            else:
                flash(file, "error")

        else:
            flash(f"Error in field {form.errors}", "error")
    return render_template(
        "forms/person_form.html", form=form, companies=Company.query.all()
    )


@app.route("/ledger_admin", methods=["GET", "POST"])
@role_required(["Admin"])
def ledger_admin():
    form = LedgerAdminForm()
    if request.method == "POST":
        if form.validate_on_submit():
            flash("Succesfully created Member", "success")
            return redirect(url_for("new_ledger", ledger=form.ledger.data))
        flash(f"Error in field {form.errors}", "error")

    return render_template("admin/ledger_admin.html", form=form)


@app.route("/ledger/<ledger>", methods=["GET", "POST"])
@role_required(["Admin"])
def new_ledger(ledger):
    form = LedgerForm()
    if request.method == "POST":
        if form.validate_on_submit():
            query.create_new_ledger(int(ledger), form.name.data,form.description.data,form.balance_bfd.data)
            flash("Succesfully created Ledger", "success")

            return redirect(url_for("dashboard"))
        flash(f"Error in field {form.errors}", "error")

    return render_template("admin/ledger.html", form=form)


@app.route("/role_assignment", methods=["GET", "POST"])
@role_required(["Admin"])
def role_assignment():
    form = RoleAssignmentForm()

    # Populate the choices for the person and role select fields
    people = [person for person in Person.query.all()]
    form.role.choices = [(role.id, role.name) for role in Role.query.all()]
    if request.method == "POST":
        if form.validate_on_submit():
            person_id = form.person.data
            role_id = form.role.data

            person = query.get_person_by_name(person_id)
            role = Role.query.get(role_id)

            if person and role:
                person.role = role
                db.session.commit()
                flash("Succesfully changed Role", "success")

                return redirect(url_for("dashboard"))
        flash(f"Error in field {form.errors}", "error")

    return render_template("admin/role_assignment.html", form=form,people=people)


@app.route("/reset_password", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Secretary"])
def reset_password():
    form = ResetPasswordForm()
    people = query.get_persons()
    if current_user.role.name == "Admin":
        people = [
            person
            for person in people
        ]
    else:
        people = [
            person
            for person in people
            if person.role.name == "User"
        ]

    if form.validate_on_submit():
        try:
            person_id = form.person.data
            password = query.generate_password()
            person = query.get_person_by_name(person_id)
            person.password = query.hash_password(password)
            db.session.commit()
            from csv_helper import write_credentials_to_file
            file = write_credentials_to_file(person.employee_id, person.email, password)
        except Exception as e:
            flash(f"Something went wrong. {e}", "error")
            return redirect(url_for("reset_password"))

        flash(f"Succesfully reset {person.name}'s password", "success")

        return redirect(url_for("download", file_path=file.name))
    return render_template("admin/reset_password.html", form=form, people=people)


@app.route("/make_payment", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Secretary"])
def make_payment():
    form = MakePaymentForm()
    people = query.get_persons()
    form.bank.choices = [(bank.id, bank.name) for bank in query.get_banks()]
    if request.method == "POST":
        if form.validate_on_submit():
            
            amount = form.amount.data
            payment_type = form.payment_type.data
            description = form.description.data
            selected_person = form.person_id.data
            selected_person = query.get_person_by_name(selected_person)
            selected_person_id = selected_person.id
            date = form.date.data
            bank_id = form.bank.data
            ref_no = form.ref_no.data
            if selected_person:
                
                if payment_type == "savings":
                    query.save_amount(
                        employee_id=selected_person_id,
                        amount=amount,
                        date=date,
                        description=description,
                        bank_id=bank_id,
                        ref_no=ref_no,
                    )

                elif payment_type == "loan":
                    
                    test = query.repay_loan(
                        selected_person.id, amount, date, bank_id, ref_no, description
                    )
                    if test == True:
                        flash("Payment submitted successfully.", "success")
                        return redirect(url_for("dashboard"))
                    else:
                        flash(test, "error")
                        
                        return redirect(url_for("make_payment"))

                flash("Payment submitted successfully.", "success")
                return redirect(url_for("dashboard"))
            else:
                flash(f"Error in field {form.errors}", "error")
        form.date.data = pd.to_datetime("today")

        return redirect(url_for("get_person", person_id=selected_person_id))

    return render_template("forms/payment.html", form=form,people=people)

#repay loan with savings
@app.route("/repay_loan", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Secretary"])
def repay_loan():
    form = RepayLoanForm()
    form.person.choices = [
        (person.id, (f"{person.name} ({person.employee_id})"))
        for person in query.get_persons()
    ]
    
    form.bank.choices = [(bank.id, bank.name) for bank in query.get_banks()]
    if request.method == "POST":
        if form.validate_on_submit():
            amount = form.amount.data
            selected_person_id = form.person.data
            selected_person = Person.query.get(selected_person_id)
            date = form.date.data
            bank_id = form.bank.data
            ref_no = form.ref_no.data
            description = form.description.data
            if selected_person:
                test = query.repay_loan_with_savings(
                    selected_person.id, amount, date, bank_id, ref_no, description
                )
                if test == True:
                    flash("Payment submitted successfully.", "success")
                    return redirect(url_for("dashboard"))
                else:
                    flash(test, "error")
                    
                    return redirect(url_for("repay_loan"))

            else:
                flash(f"Error in field {form.errors}", "error")

        return redirect(url_for("get_person", person_id=selected_person_id))
    form.date.data = pd.to_datetime("today")
    
    return render_template("forms/repay_loan.html", form=form)


@app.route("/forms/register", methods=["GET", "POST"])
@login_required
def register_loan():
    form = RegisterLoanForm()
    if current_user.role.name == "User" or current_user.role.name == "Sub-Admin":
        form.name.choices = [ (current_user.id, (f"{current_user.name} ({current_user.employee_id})"))]
        form.description.data = f"Loan Application for {current_user.employee_id}"
    else:
        form.name.choices = [
            (person.id, (f"{person.name} ({person.employee_id})"))
            for person in query.get_persons()
        ]
    form.guarantor.choices = [(None,None)] + [(person.id, f'{person.name},{person.employee_id}') for person in query.get_persons() ]
    form.guarantor_2.choices =[(None,None)] + [(person.id,f'{person.name},{person.employee_id}') for person in query.get_persons() ]


    form.bank.choices = [(bank.id, bank.name) for bank in query.get_banks()]
    form.fee.data = int(query.loan_application_fee)
    form.fee.render_kw = {'readonly': True}
    if request.method == "POST":

 
        if form.validate_on_submit():

            id = form.name.data
            amount = form.amount.data
            description = form.description.data
            date = form.date.data
            bank_id = form.bank.data
            ref_no = form.ref_no.data
            guarantors= []
            guarantor = form.guarantor.data
            loan_unpaid = Loan.query.filter_by(person_id=id,is_paid=False).first()
            if loan_unpaid:
                flash("You have an unpaid loan","error")
                return redirect(url_for("register_loan"))
            
            if guarantor!="None" :
                guarantor = query.get_person(guarantor)
                guarantors.append(guarantor)

            guarantor_2 = form.guarantor_2.data   
            if guarantor_2 !="None":   
                guarantor_2 = query.get_person(guarantor_2)
                guarantors.append(guarantor_2)

            if guarantor=='None' and guarantor_2 == 'None':
                guarantor = query.get_person(int(form.name.data))
                guarantors.append(guarantor)

            elif guarantor == guarantor_2:
                flash('You cant pick the same person twice')
                return redirect(url_for("register_loan")) 

            test = query.registeration_payment(
                id, amount, date, ref_no, bank_id, description, loan=True, guarantors=guarantors
            )
            if test == True:
                flash("Registration submitted successfully.", "success")
                name='Loan Application Form'
                income_id= Income.query.filter_by(name=name).first()
                test_2 = query.add_income(income_id,query.loan_application_fee,date,ref_no,bank_id,description)
                if test_2 == True:
                    flash("Income submitted successfully.", "success")
                    return redirect(url_for("dashboard"))
                else:
                    flash(test, "error")
            
            elif "UniqueViolation" in test:
                flash("You have an already registed for loan","error")
                return redirect(url_for("register_loan"))
            
            else:
                flash(f"something went wrong.{test}", "error")
                return redirect(url_for("register_loan"))
            return redirect(url_for("dashboard"))
        flash(form.errors, "error")
    form.date.data = pd.to_datetime("today")
    return render_template("forms/register_loan.html", form=form)


@app.route("/forms/update_loan/<int:loan_id>", methods=["GET", "POST"])
@login_required
def update_loan(loan_id):
    form = RegisterLoanForm()
    loan = LoanFormPayment.query.get(loan_id)  # Replace with your logic to fetch the existing loan data
    
    if current_user.role.name == "User":
        form.name.choices = [(current_user.id, f"{current_user.name} ({current_user.employee_id}))")]
    else:
        form.name.choices = [
            (person.id, f"{person.name} ({person.employee_id})")
            for person in query.get_persons()
        ]
    form.bank.choices = [(bank.id, bank.name) for bank in query.get_banks()]

    form.guarantor.choices = [(None, None)] + [(person.id, f'{person.name}, {person.employee_id}') for person in query.get_persons()]
    form.guarantor_2.choices = [(None, None)] + [(person.id, f'{person.name}, {person.employee_id}') for person in query.get_persons()]

    if request.method == "POST":
        if form.validate_on_submit():
            # Update the loan data
            loan.amount = form.amount.data
            loan.description = form.description.data
            loan.date = form.date.data
            loan.bank_id = form.bank.data
            loan.ref_no = form.ref_no.data
            guarantors = []
            
            guarantor = form.guarantor.data
            if guarantor != "None":
                guarantor = query.get_person(guarantor)
                guarantors.append(guarantor)
            
            guarantor_2 = form.guarantor_2.data
            if guarantor_2 != "None":
                guarantor_2 = query.get_person(guarantor_2)
                guarantors.append(guarantor_2)

            if guarantor=='None' and guarantor_2 == 'None':
                guarantor = query.get_person(int(form.name.data))
                guarantors.append(guarantor)

            if guarantor == guarantor_2:
                flash('You cant pick the same person twice')
                return render_template("forms/register_loan.html", form=form) 


            # Update the loan record in the database
            test = query.update_loan(loan.id,loan.amount,guarantors=guarantors)  # Replace with your logic to update the loan
            if test:
                flash("Loan updated successfully.", "success")
                return redirect(url_for("dashboard"))
            else:
                flash("Something went wrong during the update.", "error")
        
        else:
            flash(form.errors, "error")
    
    # Prepopulate the form fields with existing loan data
    form.name.data = loan.person  # Replace with your logic to retrieve user_id
    form.amount.data = loan.loan_amount
    if loan.guarantors:

        form.guarantor.data = loan.guarantors[0] # Replace with your logic to retrieve guarantor_id
        if len(loan.guarantors) == 2:
            form.guarantor_2.data = loan.guarantor[1] # Replace with your logic to retrieve guarantor_2_id

    form.ref_no.render_kw = {'readonly': True}
    form.fee.render_kw = {'readonly': True}
    form.fee.data = int(query.loan_application_fee)

    
    return render_template("forms/register_loan.html", form=form)


@app.route("/give_consent/<loan_id>", methods=["GET", "POST"])
@login_required
def give_consent(loan_id):
    form = ConsentForm()
    loan = LoanFormPayment.query.get(loan_id)
    form.consent.choices = [(3, "None"), (1, "Yes"), (2, "No")]
    if loan:
        if current_user in loan.guarantors:
            if request.method == "POST":
                if form.validate_on_submit():
                    if form.amount.data > loan.loan_amount:
                        flash("Amount cannot be greater than loan amount.", "error")
                        return redirect(url_for("give_consent", loan_id=loan_id))
                    elif form.amount.data < 0:
                        flash("Amount cannot be less than zero.", "error")
                        return redirect(url_for("give_consent", loan_id=loan_id))
                    elif form.amount.data == 0:
                        flash("Amount cannot be zero.", "error")
                        return redirect(url_for("give_consent", loan_id=loan_id))
                    elif form.amount.data > current_user.available_balance:
                        flash("Amount cannot be greater than your available balance.", "error")
                        return redirect(url_for("give_consent", loan_id=loan_id))
                    consent = form.consent.data
                    if consent == "1" :
                        test = query.give_consent(loan, current_user,form.amount.data)
                        if test == True:
                            flash("Consent submitted successfully.", "success")
                            return redirect(url_for("dashboard"))
                        else:
                            flash(test, "error")
                    else:
                        try:
                            loan.loan_failed()
                            db.session.commit()
                        except Exception as e:
                            db.session.rollback()
                            flash(f"Something went wrong. {e}", "error")
                            return redirect(url_for("dashboard"))
                        flash("Consent not given.", "error")
                        return redirect(url_for("dashboard"))
                else:
                    flash(form.errors, "error")
            return render_template("forms/consent.html", form=form, loan=loan)
        else:
            flash("You are not a guarantor for this loan.", "error")
            return redirect(url_for("dashboard"))
    else:
        flash("Loan not found.", "error")
        return redirect(url_for("dashboard"))    


@app.route("/make_income", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Secretary"])
def make_income():
    form = IncomeForm()
    form.name.choices = [(income.id, income.name) for income in query.get_income()]
    form.bank.choices = [(bank.id, bank.name) for bank in query.get_banks()]

    if request.method == "POST":
        if form.validate_on_submit():
            id = form.name.data
            amount = form.amount.data
            description = form.description.data
            date = form.date.data
            bank_id = form.bank.data
            ref_no = form.ref_no.data

            income = Income.query.get(id)

            query.add_income(
                income,
                amount,
                date,
                ref_no,
                bank_id,
                description,
            )
            flash("Income submitted successfully.", "success")
            return redirect(url_for("dashboard"))
        flash(form.errors, "error")

    form.date.data = pd.to_datetime("today")
    return render_template("forms/income_form.html", form=form)


@app.route("/expense/create", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Secretary"])
def create_expense():
    form = ExpenseForm()
    form.bank.choices = [(bank.id, bank.name) for bank in query.get_banks()]
    assets = [(asset.id, asset.name) for asset in Asset.query.all()]
    
    expenses = [(expense.id, expense.name) for expense in Expense.query.all()]
    liabilities = [
        (liability.id, liability.name) for liability in Liability.query.all()
    ]
    investments = [
        (investment.id, investment.name) for investment in Investment.query.all()
    ]
    form.sub_account.choices = assets + expenses + investments + liabilities

    if request.method == "POST":
        if form.validate_on_submit():
            # Handle existing expense selection
            test = query.add_transaction(
                form.main_account.data,
                form.sub_account.data,
                form.amount.data,
                form.date.data,
                form.ref_no.data,
                form.bank.data,
                form.description.data,
            )
            if test == True:

                flash("Transaction submitted successfully.", "success")
                return redirect(url_for("dashboard"))
            else:
                flash(f'somthing went wrong {test}','error')
                return redirect(url_for('create_expense'))
        else:
            flash(form.errors, "error")

    form.date.data = pd.to_datetime("today")
    return render_template("forms/expense_form.html", form=form)

@app.route("/ledger_payment", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Secretary"])
def ledger_payment():
    form = LedgerPaymentForm()
    assets = [(asset.id, asset.name) for asset in Asset.query.all()]
    
    expenses = [(expense.id, expense.name) for expense in Expense.query.all()]
    liabilities = [
        (liability.id, liability.name) for liability in Liability.query.all()
    ]
    investments = [
        (investment.id, investment.name) for investment in Investment.query.all()
    ]
    savings = [(person.id,f'{person.name}, {person.employee_id}') for person in query.get_persons()]
    loans = [(loan.id, f'{loan.person.name}, {loan.person.employee_id}') for loan in query.get_loans()]
    companies = [
        (company.id, company.name) for company in query.get_companies()
    ]
    income = [(income.id, income.name) for income in query.get_income()]
    form.sub_account.choices = assets + expenses + investments + liabilities + savings + loans + companies + income
    form.sub_account_2.choices = assets + expenses + investments + liabilities + savings + loans + companies + income

    if request.method == "POST":
        if form.validate_on_submit():
            # Handle existing expense selection
            test = query.journal_voucher(
                form.main_account.data,
                form.main_account_2.data,
                form.sub_account.data,
                form.sub_account_2.data,
                form.amount.data,
                form.date.data,
                form.ref_no.data,
                form.description.data,
                current_user.id
            )
            if test == True:
                flash("Transaction submitted successfully.", "success")
                return redirect(url_for("dashboard"))
            else:
                flash(f'error{test}','error')
                log_report(f'error{test}')
                return redirect(url_for('ledger_payment'))
        else:
            flash(form.errors, "error")

    form.date.data = pd.to_datetime("today")
    return render_template("forms/ledger_payment.html", form=form)

@app.route("/journal", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Secretary"])
def journal():
    form = JournalForm()
    form.bank.choices = [(bank.id, bank.name) for bank in query.get_banks()]
    companies = [
        (company.id, company.name) for company in query.get_companies()
    ]
   
    form.sub_account.choices = companies
    form.date.data = pd.to_datetime("today")
    if request.method == "POST":
        if form.validate_on_submit():
            # Handle existing expense selection
            test = query.add_journal_transaction(
                form.main_account.data,
                form.sub_account.data,
                form.amount.data,
                form.date.data,
                form.ref_no.data,
                form.bank.data,
                form.description.data,
            )
            if test == True:
                flash("Transaction submitted successfully.", "success")
                return redirect(url_for("dashboard"))
            else:
                flash(f'error{test}','error')
                return redirect(url_for('journal'))
        else:
            flash(form.errors, "error")

    return render_template("forms/journal.html", form=form)


@app.route("/withdraw", methods=["GET", "POST"])
@login_required
def request_withdrawal():
    form = WithdrawalForm()
    if current_user.role.name == "User" or current_user.role.name == "Sub-Admin":
        people = [current_user]
    else:
        people = [person for person in query.get_persons()]
    form.bank_id.choices = [(bank.id, bank.name) for bank in query.get_banks()]


    if request.method == "POST":
        if form.validate_on_submit():
            person_id = form.person.data
            amount = form.amount.data
            description = form.description.data
            ref_no = form.ref_no.data
            bank_id = form.bank_id.data
            date = form.date.data

            person = query.get_person_by_name(person_id)

            if amount > person.available_balance:
                flash("Amount cannot be greater than available balance.", "error")
                return redirect(url_for("request_withdrawal"))
            
            withdrawal_request = WithdrawalRequest(
                person=person,
                amount=amount,
                description=description,
                ref_no=ref_no,
                bank_id=bank_id,
                date=date,
                year=query.year,
            )

            db.session.add(withdrawal_request)
            db.session.commit()

            flash("Withdrawal sent for approval.", "success")

            return redirect(url_for("dashboard"))

        else:
            flash(form.errors, "error")

    form.date.data = pd.to_datetime("today")
    return render_template("forms/withdraw.html", form=form,people=people)

@app.route("/withdraw/reject/<int:request_id>")
@login_required
@role_required(["Admin"])
def reject_withdrawal(request_id):
    wr= WithdrawalRequest.query.get(request_id)
    if not wr:
        flash("Withdrawal request not found.", "error")
    elif wr.is_approved:
        flash("Withdrawal request is already approved.", "error")
    else:
        #delete the withdrawal request
        db.session.delete(wr)
        db.session.commit()
        flash("Withdrawal request rejected successfully.", "success")
        return redirect(url_for("approval"))

@app.route("/withdraw/approve/<int:request_id>", methods=["GET"])
@login_required
@role_required(["Admin","Sub-Admin"])
def approve_withdrawal(request_id):

    if current_user.role.name == "Sub-Admin":
        wr= WithdrawalRequest.query.get(request_id)

        if not wr:
            flash("Withdrawal request not found.", "error")
        elif not wr.is_sub_approved:   
            wr.is_sub_approved = True
            wr.sub_approved_by = current_user.id

            db.session.commit()
            flash("Withdrawal request approved successfully.", "success")
        else:
            flash("Withdrawal request is already approved.", "error")
    else:
        wr= WithdrawalRequest.query.get(request_id)
        if not wr:
            flash("Withdrawal request not found.", "error")
        elif not wr.is_approved:
            test = query.withdraw(wr.person.id, wr.amount, wr.description, wr.ref_no, wr.bank_id, wr.date)
            if test == True:
                flash(
                    f"Withdrawal of {wr.amount} successful for {wr.person.name}. Updated balance: {wr.person.available_balance}"
                )
            
            elif test :
                flash(test, "error")
                
            wr.is_approved = True
            wr.approved_by = current_user.id

            db.session.commit()
            flash("Withdrawal request approved successfully.", "success")
        else:
            flash("Withdrawal request is already approved.", "error")

    return redirect(url_for("approval"))


@app.route("/loan/request", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Secretary"])
def request_loan():
    form = LoanForm()
    form.name.choices = [
        (person.person.id, (f"{person.name} ({person.person.employee_id})"))
        for person in query.get_registered() if person.loan == True and person.is_approved==False
    ]

    form.bank.choices = [(bank.id, bank.name) for bank in query.get_banks()]
    form.amount.render_kw = {'readonly': True}

    if request.method == "POST":
        if form.validate_on_submit():
            employee = query.get_registered_person(form.name.data)
            employee_id = employee.person_id
            person = Person.query.filter_by(id=employee_id).first()
            pre_loan = person.loan_form_payment[0]
            duration = int(form.duration.data)
            end_date = form.start_date.data + relativedelta(months=duration)
            test = query.make_loan_request(
                pre_loan=pre_loan,
                bank_id=form.bank.data,
                id=person.id,
                interest_rate=form.interest_rate.data,
                start_date=form.start_date.data,
                end_date=end_date,
                description=form.description.data,
                ref_no=form.ref_no.data,
            )
            if test == True:
                flash("Loan sent for approval.", "success")
                return redirect(url_for("get_loan_details", person_id=person.id))
            else:
                flash(test, "error")

    form.start_date.data = pd.to_datetime("today")
    return render_template("forms/loan_form.html", form=form)


@app.route("/approval", methods=["GET", "POST"])
@login_required
@role_required(["Admin","Sub-Admin"])
def approval():
    if current_user.role.name == "Sub-Admin":
        loans = query.get_loans()
        withdrawals = WithdrawalRequest.query.filter_by(is_sub_approved=False).all()
        loans= [loan for loan in loans if loan.is_approved==True and loan.sub_admin_approved==False]
    
    else:
        loans = query.get_loans()
        withdrawals = WithdrawalRequest.query.filter_by(is_sub_approved=True,is_approved=False).all()
        loans= [loan for loan in loans if loan.sub_admin_approved==True and loan.admin_approved==False]      

    return render_template("admin/approval.html", loans=loans, withdrawals=withdrawals)


@app.route("/loan/reject/<int:loan_id>")     
@login_required
@role_required(["Admin","Sub-Admin"])
def reject_loan(loan_id):
    if current_user.role.name == "Sub-Admin":
        test = query.sub_reject_loan(loan_id, current_user.id)
        if test == True:
            flash("Loan rejected successfully.", "success")
        else:
            flash(test, "error")
    test = query.reject_loan(loan_id)
    if test == True:
        flash("Loan rejected successfully.", "success")
    else:
        flash(test, "error")        

    return redirect(url_for("approval"))

@app.route("/loan/approve/<int:loan_id>", methods=["GET"])
@login_required
@role_required(["Admin","Sub-Admin"])
def approve_loan(loan_id):
    if current_user.role.name == "Sub-Admin":
        test = query.sub_approve_loan(loan_id)
        if test == True:
            flash("Loan approved successfully.", "success")
            loan = Loan.query.get(loan_id)
            loan.sub_admin_approved = True
            loan.sub_approved_by = current_user.id
            db.session.commit()
        else:
            flash(test, "error")
            
        return redirect("/dashboard")
    else:
        test = query.approve_loan(loan_id)
        if test == True:
            flash("Loan approved successfully.", "success")

            # Generate the repayment schedule
            loan = Loan.query.get(loan_id)
            loan.approved_by = current_user.id
            db.session.commit()
            repayment_schedule = generate_repayment_schedule(
                loan.person_id, loan.amount, loan.interest_rate, loan.start_date, loan.end_date
            )

            # Export the repayment schedule to Excel
            file_path = export_repayment_schedule_to_excel(
                repayment_schedule, loan.person_id
            )

            # Return the file path for download
            flash("Loan created successfully.", "success")

            return redirect(f"/download/{file_path}")
        else:
            flash(test, "error")
            

        return render_template("admin/approval.html")



@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        user = current_user  # Replace with actual user retrieval
        if query.change_password(
            user, form.current_password.data, form.new_password.data
        ):
            # Redirect to a success page or profile page
            flash("Password Changed successfully.", "success")

            return redirect(url_for("dashboard"))
        else:
            flash("Invalid current password", "error")
            return redirect(url_for("change_password"))

    return render_template("forms/change_password.html", form=form)


@app.route("/edit_profile", methods=["GET", "POST"])
@role_required(["Admin", "Secretary"])
def edit_profile():
    form = EditProfileForm()
    form.person.choices = [
        (person.id, f"{person.name}({person.employee_id})")
        for person in query.get_persons()
    ]
    form.company_id.choices = [
        (company.id, company.name) for company in query.get_companies()
    ]
    if form.validate_on_submit():
        user = current_user
        test= query.edit_profile(
            form.person.data, form.employee_id.data, form.email.data, form.phone_no.data, form.company_id.data
        )
        if test == True:
            flash("Profile updated successfully!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash(test, "error")
            return redirect(url_for("edit_profile"))

    return render_template("forms/edit_profile.html", form=form)


@app.route("/get_person_role/<person_id>", methods=["GET", "POST"])
@login_required
def get_person_role(person_id):
    person = query.get_person(person_id)
    
    return jsonify(
        {
            "name": person.name,
            "role": person.role.name,
        }
    )
# upload


@app.route("/upload_savings", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Secretary"])
def upload_savings():
    form = UploadForm()

    if request.method == "POST" and form.validate_on_submit():
        file = request.files["file"]
        if file:
            # Save the uploaded file
            file.save(f'upload/{file.filename}')
            # Process the uploaded file
            report = send_upload_to_savings(file,form.ref_no.data, form.description.data, form.date.data)
            
            return redirect(url_for("download", file_path=report))

    else:
        flash(form.errors, "error")

    form.date.data = pd.to_datetime("today")
    return render_template("forms/upload.html", form=form, route_type="savings")


@app.route("/upload_loan_repayment", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Secretary"])
def upload_loan():
    form = UploadForm()

    if request.method == "POST" and form.validate_on_submit():
        file = request.files["file"]
        if file:
            # Save the uploaded file
            file.save(f'upload/{file.filename}')
            # Process the uploaded file
            report = send_upload_to_loan_repayment(
                file,form.ref_no.data , form.description.data, form.date.data
            )
            return redirect(url_for("download", file_path=report))
        else:
            flash("No file selected.", "error")
    else:
        flash(form.errors, "error")

    form.date.data = pd.to_datetime("today")
    return render_template("forms/upload.html", form=form, route_type="loan")


@app.route("/startup", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Secretary"])
def startup():
    if request.method == "POST":
        file = request.files["file"]

        if file:

            # Save the uploaded file
            file.save(f'upload/{file.filename}')
            # Process the uploaded file
            file = start_up(file)
            flash("Savings updated successfully!", "success")
            return redirect(url_for("download", file_path=file))

    return render_template("forms/startup.html")


# making queries


@app.route("/persons", methods=["GET"])
@login_required
@role_required(["Admin", "Secretary", "Sub-Admin"])
def get_persons():
    persons = query.get_persons()
    total_loan = sum(person.loan_balance for person in persons)
    total_savings = sum(person.total_balance for person in persons)
    return render_template(
        "query/person.html",
        persons=persons,
        total_loan=total_loan,
        total_savings=total_savings,
    )


def filter_payments(start_date, end_date, payments):
    filtered_payments = payments
    if start_date and end_date:
        filtered_payments = [
            payment for payment in payments if start_date <= payment.date <= end_date
        ]
    elif start_date:
        filtered_payments = [
            payment for payment in payments if payment.date >= start_date
        ]
    elif end_date:
        filtered_payments = [
            payment for payment in payments if payment.date <= end_date
        ]

    return filtered_payments


@app.route("/savings_account", methods=["GET"])
@login_required
def get_payments():
    payments = query.get_savings()
    persons = query.get_persons()
    form = DateFilterForm(request.args)
    # Filter payments based on date range
    start_date = form.start_date.data
    end_date = form.end_date.data
    filtered_payments = filter_payments(start_date, end_date, payments)

    return render_template(
        "query/savings_payment.html",
        form=form,
        payments=filtered_payments,
        persons=persons,
    )


@app.route("/loans", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Secretary", "Sub-Admin"])
def get_loan():
    loans = query.get_loans()
    form = DateFilterForm(request.args)
    # Filter payments based on date range
    start_date = form.start_date.data
    end_date = form.end_date.data
    
    filtered_payments = filter_payments(start_date, end_date, loans)
    return render_template("query/loans.html", loans=filtered_payments, form=form)


@app.route("/loan_status/<loan_id>", methods=["GET", "POST"])
@login_required
@role_required(["Admin"])
def loan_status(loan_id):
    loan = Loan.query.get(loan_id)
    if loan.is_paid == False:
        loan.is_paid = True
        db.session.commit()
        flash("Loan status updated successfully.", "success")
    else:
        loan.is_paid = False
        db.session.commit()
        flash("Loan status updated successfully.", "success")

    return redirect(url_for("get_loan"))


@app.route("/loan_details/<person_id>", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Secretary", "Sub-Admin"])
def get_loan_details(person_id):
    loans = query.get_loan(person_id)
    form = DateFilterForm(request.args)
    # Filter payments based on date range
    start_date = form.start_date.data
    end_date = form.end_date.data
    guarantors = [p.guarantor.name for p in loans.guarantor_contributions if p.guarantor != None]
    admin = query.get_person(loans.approved_by)
    sub_admin = query.get_person(loans.sub_approved_by)
    
    filtered_payments = filter_payments(start_date, end_date, loans)
    return render_template("query/loan_details.html", loan=filtered_payments, form=form,guarantors=guarantors,admin=admin,sub_admin=sub_admin)


@app.route("/savings_details/<person_id>", methods=["GET", "POST"])
@login_required
def savings_account_details(person_id):
    
    person = query.get_person(person_id)
    
    return render_template("query/savings_account_details.html", person=person)


@app.route("/income", methods=["GET"])
@login_required
@role_required(["Admin", "Secretary", "Sub-Admin"])
def income_statement():
    incomes = query.get_income()
    expenses = query.get_expenses()
    total_income = sum(income.balance for income in incomes)
    total_expenses = sum(expense.balance for expense in expenses)

    net_income = query.get_net_income()
    current_year = os.getenv("CURRENT_YEAR")
    query_year = query.year
    year_range = [year for year in range(int(current_year), int(query_year))]
    context = {
        "incomes": incomes,
        "expenses": expenses,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_income": net_income,
        "year": None,
        "years": year_range
    }

    return render_template("query/income.html", **context)


@app.route("/income-yearly/<year>", methods=["GET"])
@login_required
@role_required(["Admin", "Secretary", "Sub-Admin"])
def income_statement_yearly(year):
    all_incomes = IncomePerYear.query.filter_by(year=year).order_by(IncomePerYear.id.desc()).all()
    net_income = all_incomes.pop(-1)
    incomes = [income for income in all_incomes if income.debit >0]
    expenses = [expense for expense in all_incomes if expense.credit >0]
    total_income = sum(income.debit for income in incomes)
    total_expenses = sum(expense.credit for expense in expenses)

    current_year = os.getenv("CURRENT_YEAR")
    query_year = query.year
    year_range = [year for year in range(int(current_year), int(query_year))]

    context = {
        "incomes": incomes,
        "expenses": expenses,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_income": net_income,
        "year": year,
        "years": year_range
    }
    return render_template("query/income.html", **context)


@app.route("/savings_account/<person_id>", methods=["GET", "POST"])
@login_required
def savings_account(person_id):
    user = current_user
    if user.role.id != 4 or user.id == int(person_id):
        person = query.get_person(person_id)
        payments = person.payments_made
        form = DateFilterForm(request.args)
        # Filter payments based on date range
        start_date = form.start_date.data
        end_date = form.end_date.data
        filtered_payments = filter_payments(start_date, end_date, payments)

        return render_template(
            "query/savings_account.html",
            payments=filtered_payments,
            person=person,
            form=form,
        )
    else:
        return redirect(url_for("savings_account", person_id=user.id))


@app.route("/loan/<person_id>", methods=["GET", "POST"])
@login_required
def loan_account(person_id):
    user = current_user
    if user.role.id != 4 or user.id == int(person_id):
        person = query.get_person(person_id)
        loan = person.last_loan()
        payments = person.loan_payments_made
        form = DateFilterForm(request.args)
        # Filter payments based on date range
        start_date = form.start_date.data
        end_date = form.end_date.data
        filtered_payments = filter_payments(start_date, end_date, payments)
        approved = query.get_person(loan.approved_by)
        guarantors = [p.guarantor.name for p in loan.guarantor_contributions if p.guarantor != None]
        return render_template(
            "query/loan_account.html",
            payments=filtered_payments,
            person=person,
            loan=loan,
            form=form,
            approved=approved,
            guarantors=guarantors
        )
    else:
        return redirect(url_for("loan_account", person_id=user.id))
    


@app.route('/admin-search', methods=['GET'])
@login_required
@role_required(["Admin"])
def admin_search():
    ref_no = request.args.get('ref_no')
    savings, loans, companies, banks, incomes, expenses, assets, liabilities, investments = query.search_all_payment_tables(ref_no)
    all_payments = savings + loans + companies + banks + incomes + expenses + assets + liabilities + investments

    # Sort the list by ref_no
    all_payments.sort(key=lambda payment: payment['ref_no'])
    payments_dict = defaultdict(list)

    # Loop over all payments
    for payment in all_payments:
        # Append the payment to the list of payments with the same ref_no
        payments_dict[payment['ref_no']].append(payment)

    result = {
        'savings': savings,
        'loans': loans,
        'companies': companies,
        'banks': banks,
        'incomes': incomes,
        'expenses': expenses,
        'assets': assets,
        'liabilities': liabilities,
        'investments': investments,

    }

    return render_template('query/search.html', data = result,by_ref_no=payments_dict)


@app.route("/banks_report")
@login_required
@role_required(["Admin", "Secretary", "Sub-Admin"])
def bank_report():
    banks = query.get_banks()
    return render_template("query/banks.html", banks=banks)


@app.route("/ledger_report/<ledger>/<ledger_id>")
@login_required
@role_required(["Admin", "Secretary", "Sub-Admin"])
def ledger_report(ledger, ledger_id):
    ledger_report = query.get_ledger_report(ledger, ledger_id)
    form = DateFilterForm(request.args)
    # Filter payments based on date range
    start_date = form.start_date.data
    end_date = form.end_date.data
    filtered_payments = filter_payments(start_date, end_date, ledger_report.payments)
    return render_template(
        "query/ledger_report.html",
        form=form,
        ledger_report=ledger_report,
        payments=filtered_payments,
    )


@app.route("/companies_report")
@login_required
@role_required(["Admin", "Secretary", "Sub-Admin"])
def companies_report():
    companies = query.get_companies()
    return render_template("query/companies.html", companies=companies)


@app.route("/company/<company_id>")
@login_required
@role_required(["Admin", "Secretary", "Sub-Admin"])
def individual_company_report(company_id):
    # Query the bank and its associated payments
    company = query.get_company(company_id)
    payments = company.payments_made

    # Calculate the total amount received by the bank
    total_amount = sum(payment.amount for payment in payments)
    # Render the bank report template with the data
    return render_template(
        "query/company_report.html",
        company=company,
        payments=payments,
        total_amount=total_amount,
    )


@app.route("/debtors_report")
@login_required
@role_required(["Admin", "Secretary", "Sub-Admin"])
def debtors_report():
    # Query the bank and its associated payments
    company = query.get_companies()
    loans = query.get_loans()

    # Render the bank report template with the data
    return render_template("query/debtors_report.html", company=company, loans=loans)


@app.route("/bank_report/<bank_id>")
@login_required
@role_required(["Admin", "Secretary", "Sub-Admin"])
def individual_bank_report(bank_id):
    # Query the bank and its associated payments
    bank = query.get_bank(bank_id)
    payments = bank.payments

    # Calculate the total amount received by the bank
    total_amount = sum(payment.amount for payment in payments)
    # Render the bank report template with the data
    return render_template(
        "query/bank_report.html",
        bank=bank,
        payments=payments,
        total_amount=total_amount,
    )



@app.route("/trial_balance")
@login_required
@role_required(["Admin", "Secretary", "Sub-Admin"])
def trial_balance():

    cash_and_bank = query.get_cash_and_banks()
    accounts_receivable = query.get_accounts_receivable()
    company_receivable = query.get_company_receivables()
    total_investments = query.get_total_investment()
    total_liabilities = query.get_total_liabilities()
    net_income = query.get_net_income()
    accounts_payable = query.get_accounts_payable()

    fixed_assets = Asset.query.all()
    liabilities = Liability.query.all()
    incomes = Income.query.all()
    expenses = Expense.query.all()
    investments = Investment.query.all()

    incomes = [income for income in incomes ]
    expenses = [expense for expense in expenses ]
    total_income = sum(income.balance for income in incomes)
    total_expenses = sum(expense.balance for expense in expenses)
    total_fixed_assets = sum(a.balance for a in fixed_assets)
    total_assets = cash_and_bank + accounts_receivable+ company_receivable+ total_investments+ total_fixed_assets

    total_dr = total_assets + total_expenses
    total_cr = accounts_payable+ total_liabilities + total_income
    context = {
        "assets": fixed_assets,
        "incomes": incomes,
        "expenses": expenses,
        "liabilities": liabilities,
        "investments": investments,
        "cash_and_bank": cash_and_bank,
        "accounts_receivable": accounts_receivable,
        "company_receivable": company_receivable,
        "net_income": net_income,
        "accounts_payable": accounts_payable,
        "accounts_payable": accounts_payable,
        "total_dr": total_dr,
        "total_cr": total_cr,
    }
    return render_template("query/trial-balance.html", **context)


@app.route("/balance_sheet")
@login_required
@role_required(["Admin", "Secretary", "Sub-Admin"])
def balance_sheet():
    fixed_assets = Asset.query.all()
    expenses = Expense.query.all()
    total_fixed_assets = sum(a.balance for a in fixed_assets)
    total_expense = sum(e.balance for e in expenses)

    cash_and_bank = query.get_cash_and_banks()
    accounts_receivable = query.get_accounts_receivable()
    company_receivable = query.get_company_receivables()
    investments = query.get_total_investment()
    total_current_assets = cash_and_bank + accounts_receivable+ company_receivable+ investments
    
    total_assets = total_current_assets + total_fixed_assets

    net_income = query.get_net_income()
    accounts_payable = query.get_accounts_payable()
    liabilities = Liability.query.all()
    total_liabilities = query.get_total_liabilities()
    
    accounts_payable = query.get_accounts_payable()
    total_equity = accounts_payable + net_income
    total_liabilities_and_equity = total_liabilities + total_equity
    current_year = os.getenv("CURRENT_YEAR")
    query_year = query.year
    year_range = [year for year in range(int(current_year),int(query_year)-1)]

    context = {
        "assets": fixed_assets,
        "cash_and_bank": cash_and_bank,
        "accounts_receivable": accounts_receivable,
        "company_receivable": company_receivable,
        "investments": investments,
        "total_assets": total_assets,
        "net_income": net_income,
        "accounts_payable": accounts_payable,
        "liabilities": liabilities,
        "accounts_payable": accounts_payable,
        "total_liabilities": total_liabilities,
        "total_equity": total_equity,
        "total_liabilities_and_equity": total_liabilities_and_equity,
        "year_range": year_range,
    }
    return render_template("query/balance-sheet.html", **context)

@app.route("/balance_sheet_year/<year>")
@login_required
@role_required(["Admin", "Secretary", "Sub-Admin"])
def balance_sheet_by_year(year):
    bs = BalanceSheet.query.filter_by(year=year).first()
    liabilities = query.get_liabilities_per_year(year)
    current_year = os.getenv("CURRENT_YEAR")
    query_year = query.year
    year_range = [year for year in range(int(current_year), int(query_year))]

    context = {
        "assets": bs.total_fixed_assets,
        "cash_and_bank": bs.cash_and_bank,
        "accounts_receivable": bs.accounts_receivable,
        "company_receivable": bs.company_receivable,
        "investments": bs.investments,
        "total_assets": bs.total_assets,
        "net_income": bs.net_income,
        "accounts_payable": bs.accounts_payable,
        "liabilities": liabilities,
        "total_liabilities": bs.total_liabilities,
        "total_equity": bs.total_equity,
        "total_liabilities_and_equity": bs.total_liabilities_and_equity,
        "year_range": year_range,
    }

    return render_template("query/balance-sheet.html", **context)
# uploads


# DOWNLOADS
@app.route("/download/<path:file_path>", methods=["GET"])
@login_required
def download(file_path):
    # Send the file back to the user as a response
    return send_file(file_path, as_attachment=True)


@app.route("/download_pdf/<type>/<type_id>")
@login_required
def download_pdf(type, type_id):
    file_path = create_pdf(type, type_id)

    return redirect(f"/download/{file_path}")


@app.route("/download_excel/<type>/<type_id>")
@login_required
def download_excel(type, type_id):
    file_path = create_excel(type, type_id)

    return redirect(f"/download/{file_path}")

@app.route("/download_excel_income")
@login_required
def download_excel_income():

    file_path = create_income_excel()
    return redirect(url_for("download", file_path=file_path))


@app.route("/download_pdf_income")
@login_required
def download_pdf_income():

    file_path = create_income_pdf()
    return redirect(url_for("download", file_path=file_path))


@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/close_year", methods=["GET", "POST"])
@login_required
@role_required(["Admin"])
def close_year():
    form = CloseYearForm()
    form.current_year.data = query.year
    form.current_loan_application_fee.data =int(query.loan_application_fee)

    if form.validate_on_submit():
        test = query.close_year(form.current_year.data, form.new_loan_application_fee.data)
        if test ==True:
            flash("Year closed successfully!", "success")
            return redirect(url_for("dashboard"))

        else:
            flash("An error occurred while closing the year.", "error")
            
            return redirect(url_for("close_year"))
    else:
        flash(form.errors, "error")
  
    return render_template("forms/close_year.html", form=form)


# dynamic lookup


@app.route("/forgot_password")
def forgot_password():
    pass


# API endpoints

from flask import jsonify

@app.route("/get_loan_data/<int:person_id>")
@login_required
@role_required(["Admin", "Secretary"])
def get_loan_data(person_id):
    
    person = query.get_person(person_id)
    payment = person.loan_form_payment
    amount = payment[0].loan_amount
    return format_currency(amount)

@app.route("/get_balance/<int:person_id>")
@login_required
def get_balance(person_id):
    person = query.get_person(person_id)
    balance = query.get_person_balance(person_id)
    return jsonify({"balance": format_currency(balance), "loan_balance": format_currency(person.loan_balance)})
    


@app.route("/get_person_info/<person_id>")
@login_required
def get_person_info(person_id):
    person = query.get_person(person_id)
    return person.to_json()


@app.route("/search", methods=["POST"])
@login_required
@role_required(["Admin", "Secretary", "Sub-Admin"])
def search():
    ref_no = request.form.get("ref_no")
    transactions = query.get_transactions_with_ref_no(ref_no)
    #check if SavingsPayment is in transactions
    
    if ref_no[0]=='J':
        account_key = {'assets':1,'expenses':2,'investments':3,'liabilities':4}
        form = LedgerPaymentForm()
        form.ref_no.render_kw = {"readonly": True}
        form.ref_no.data = ref_no
        form.main_account.render_kw = {"readonly": True}
        form.main_account.data = account_key[transactions[0].main]if transactions[0].amount >0 else account_key[transactions[1].main]
        form.main_account_2.render_kw = {"readonly": True}
        form.main_account_2.data = account_key[transactions[1].main]if transactions[0].amount < 0 else account_key[transactions[1].main]
        form.sub_account.render_kw = {"readonly": True}
        form.sub_account.data = transactions[0].main.name if transactions[0].amount >0 else transactions[1].main.name
        form.sub_account_2.render_kw = {"readonly": True}
        form.sub_account_2.data = transactions[1].main.name if transactions[0].amount < 0 else transactions[1].main.name
        form.amount.render_kw = {"readonly": True}
        form.amount.data = abs(transactions[0].amount)
        form.date.render_kw = {"readonly": True}
        form.date.data = transactions[0].date
        form.description.render_kw = {"readonly": True}
        form.description.data = transactions[0].description
        
        
        return render_template("forms/ledger_payment.html", form=form)
    elif 'SA-LO' in ref_no:
        form = RepayLoanForm()
        form.ref_no.render_kw = {"readonly": True}
        form.ref_no.data = ref_no
        form.person.render_kw = {"readonly": True}
        form.person.data = transactions[0].payer.name
        form.amount.render_kw = {"readonly": True}
        form.amount.data = abs(transactions[0].amount)
        form.date.render_kw = {"readonly": True}
        form.date.data = transactions[0].date
        form.description.render_kw = {"readonly": True}
        form.description.data = transactions[0].description
        form.loan_balance.render_kw = {"readonly": True}
        form.loan_balance.data = transactions[1].balance
        return render_template("forms/repay_loan.html", form=form)

    elif 'BR' in ref_no:
        form = MakePaymentForm()
        form.ref_no.render_kw = {"readonly": True}
        form.ref_no.data = ref_no
        form.person_id.render_kw = {"readonly": True}
        form.person_id.data = transactions[0].payer.name
        form.amount.render_kw = {"readonly": True}
        form.amount.data = abs(transactions[0].amount)
        form.date.render_kw = {"readonly": True}
        form.date.data = transactions[0].date
        form.description.render_kw = {"readonly": True}
        form.description.data = transactions[0].description
        form.bank.render_kw = {"readonly": True}
        form.bank.choices = [(1,transactions[1].main.name)]
        form.payment_type.render_kw = {"readonly": True}
        form.payment_type.data = 'Savings' if transactions[0].payer else 'Loan'  
        return render_template("forms/make_payment.html", form=form)
    
    elif 'LA' in ref_no:
        flash("No Support for this transaction", "error")
        return redirect(url_for("dashboard"))

    elif 'IN' in ref_no:
        flash("No Support for this transaction", "error")
        return redirect(url_for("dashboard"))

    elif 'EX' in ref_no:
        form = ExpenseForm()
        form.ref_no.render_kw = {"readonly": True}
        form.ref_no.data = ref_no
        form.amount.render_kw = {"readonly": True}
        form.amount.data = abs(transactions[0].amount)
        form.date.render_kw = {"readonly": True}
        form.date.data = transactions[0].date
        form.description.render_kw = {"readonly": True}
        form.description.data = transactions[0].description
        form.sub_account.render_kw = {"readonly": True}
        form.sub_account.data = transactions[0].main.name
        form.main_account.render_kw = {"readonly": True}
        form.main_account.data = 'Expense'
        form.bank.render_kw = {"readonly": True}
        form.bank.choices = [(1,transactions[1].main.name)]

        return render_template("forms/expense.html", form=form)
    
    elif 'AS' in ref_no:
        form = ExpenseForm()
        form.ref_no.render_kw = {"readonly": True}
        form.ref_no.data = ref_no
        form.amount.render_kw = {"readonly": True}
        form.amount.data = abs(transactions[0].amount)
        form.date.render_kw = {"readonly": True}
        form.date.data = transactions[0].date
        form.description.render_kw = {"readonly": True}
        form.description.data = transactions[0].description
        form.sub_account.render_kw = {"readonly": True}
        form.sub_account.data = transactions[0].main.name
        form.main_account.render_kw = {"readonly": True}
        form.main_account.data = 'Asset'
        form.bank.render_kw = {"readonly": True}
        form.bank.choices = [(1,transactions[1].main.name)]
        return render_template("forms/expense.html", form=form)
    
    elif 'LI' in ref_no:
        form = ExpenseForm()
        form.ref_no.render_kw = {"readonly": True}
        form.ref_no.data = ref_no
        form.amount.render_kw = {"readonly": True}
        form.amount.data = abs(transactions[0].amount)
        form.date.render_kw = {"readonly": True}
        form.date.data = transactions[0].date
        form.description.render_kw = {"readonly": True}
        form.description.data = transactions[0].description
        form.sub_account.render_kw = {"readonly": True}
        form.sub_account.data = transactions[0].main.name
        form.main_account.render_kw = {"readonly": True}
        form.main_account.data = 'Liability'
        form.bank.render_kw = {"readonly": True}
        form.bank.choices = [(1,transactions[1].main.name)]
        return render_template("forms/expense.html", form=form)
    
    elif 'IV' in ref_no:
        form = ExpenseForm()
        form.ref_no.render_kw = {"readonly": True}
        form.ref_no.data = ref_no
        form.amount.render_kw = {"readonly": True}
        form.amount.data = abs(transactions[0].amount)
        form.date.render_kw = {"readonly": True}
        form.date.data = transactions[0].date
        form.description.render_kw = {"readonly": True}
        form.description.data = transactions[0].description
        form.sub_account.render_kw = {"readonly": True}
        form.sub_account.data = transactions[0].main.name
        form.main_account.render_kw = {"readonly": True}
        form.main_account.data = 'Investment'
        form.bank.render_kw = {"readonly": True}
        form.bank.choices = [(1,transactions[1].main.name)]

        return render_template("forms/expense.html", form=form)

    elif 'WD' in ref_no:
        form = WithdrawalForm()
        form.ref_no.render_kw = {"readonly": True}
        form.ref_no.data = ref_no
        form.amount.render_kw = {"readonly": True}
        form.amount.data = abs(transactions[0].amount)
        form.date.render_kw = {"readonly": True}
        form.date.data = transactions[0].date
        form.description.render_kw = {"readonly": True}
        form.description.data = transactions[0].description
        form.bank_id.render_kw = {"readonly": True}
        form.bank_id.choices = [(1,transactions[1].main.name)]
        form.person.render_kw = {"readonly": True}
        form.person.data = transactions[0].payer.name
        return render_template("forms/withdrawal.html", form=form)
    
    elif 'CO-SA' in ref_no:
        flash("No Support for this transaction", "error")
        return redirect(url_for("dashboard"))

    elif 'CO-LO' in ref_no:
        flash("No Support for this transaction", "error")
        return redirect(url_for("dashboard"))

    elif 'CO' in ref_no:
        form = JournalForm()
        form.ref_no.render_kw = {"readonly": True}
        form.ref_no.data = ref_no
        form.amount.render_kw = {"readonly": True}
        form.amount.data = abs(transactions[0].amount)
        form.date.render_kw = {"readonly": True}
        form.date.data = transactions[0].date
        form.description.render_kw = {"readonly": True}
        form.description.data = transactions[0].description
        form.main_account.render_kw = {"readonly": True}
        form.main_account.data = 'Company'
        form.sub_account.render_kw = {"readonly": True}
        form.sub_account.data = transactions[0].main.name
        form.bank.render_kw = {"readonly": True}
        form.bank.choices = [(1,transactions[1].main.name)]
        return render_template("forms/journal.html", form=form)

    else:
        flash("No results found", "error")
        return redirect(url_for("dashboard"))


@app.route("/get_sub_accounts/<int:main_account_id>")
def get_sub_accounts(main_account_id):
    # Fetch sub-account options based on the selected main_account
    # You need to implement this logic based on your database structure
    sub_accounts = query.sub_accounts(main_account_id)

    # Create a list of dictionaries with 'id' and 'name' keys
    if main_account_id == 5:
        sub_account_options = [
            {"id": sub_account.id, "name": f'{sub_account.name}, {sub_account.employee_id}',"balance":sub_account.available_balance} for sub_account in sub_accounts
        ]
    elif main_account_id == 7:
        sub_account_options = [
            {"id": sub_account.id, "name":f'{sub_account.name}',"balance":sub_account.amount_accumulated} for sub_account in sub_accounts
        ]
    elif main_account_id == 6:
        sub_account_options = [
            {"id": sub_account.id, "name":f'{sub_account.person.name}, {sub_account.person.employee_id}',"balance":sub_account.person.loan_balance} for sub_account in sub_accounts
        ]
    else:
        sub_account_options = [
            {"id": sub_account.id, "name": sub_account.name,"balance":sub_account.balance} for sub_account in sub_accounts
        ]

    return jsonify(sub_account_options)
@app.route("/get_sub_journals/<journal>/")
def get_sub_journals(journal):
    # Fetch sub-account options based on the selected main_account
    # You need to implement this logic based on your database structure
    sub_accounts = query.sub_journal(journal)

    # Create a list of dictionaries with 'id' and 'name' keys
    sub_account_options = [
        {"id": sub_account.id, "name": sub_account.name} for sub_account in sub_accounts
    ]

    return jsonify(sub_account_options)



# errorhandlers


@app.errorhandler(404)
def page_not_found(eror):

    return render_template('errorpage/errorbase.html'), 404


@app.errorhandler(500)
def internal_server_error(error):

    return render_template('errorpage/error500.html'), 500


@app.route('/error')
def error():
    return render_template('errorpage/errorbase.html')

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080)