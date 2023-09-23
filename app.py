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
import pandas as pd, json, csv
from filters import format_currency, calculate_duration_in_months
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")


db.init_app(app)
query = Queries(db)
login_manager = LoginManager()

login_manager.init_app(app)


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


def log_report(report):
    with open("report.txt", "a", encoding="utf-8") as f:
        f.write(f"{report}\n")


# Routes for creating and submitting forms


@app.route("/", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.identifier.data
        password = form.password.data
        user = query.get_user(identifier)

        if user and user.password == password:
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
    
    return render_template("dashboard.html", person=person, form=form,consents=pre_guarantor)


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
                balance=form.total_balance.data,
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
            query.create_new_ledger(int(ledger), form.name.data, form.description.data)
            flash("Succesfully created Ledger", "success")

            return redirect(url_for("dashboard"))
        flash(f"Error in field {form.errors}", "error")

    return render_template("admin/ledger.html", form=form)


@app.route("/role_assignment", methods=["GET", "POST"])
@role_required(["Admin"])
def role_assignment():
    form = RoleAssignmentForm()

    # Populate the choices for the person and role select fields
    form.person.choices = [(person.id, person.name) for person in Person.query.all()]
    form.role.choices = [(role.id, role.name) for role in Role.query.all()]
    if request.method == "POST":
        if form.validate_on_submit():
            person_id = form.person.data
            role_id = form.role.data

            person = Person.query.get(person_id)
            role = Role.query.get(role_id)

            if person and role:
                person.role = role
                db.session.commit()
                flash("Succesfully changed Role", "success")

                return redirect(url_for("dashboard"))
        flash(f"Error in field {form.errors}", "error")

    return render_template("admin/role_assignment.html", form=form)


@app.route("/reset_password", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Secretary"])
def reset_password():
    form = ResetPasswordForm()
    if current_user.role.name == "Admin":
        form.person.choices = [
            (person.id, f"{person.name}({person.employee_id})")
            for person in query.get_persons()
        ]
    else:
        form.person.choices = [
            (person.id, f"{person.name}({person.employee_id})")
            for person in query.get_persons()
            if person.role.name == "User"
        ]

    if form.validate_on_submit():
        person_id = form.person.data
        password = query.generate_password()
        person = query.get_person(person_id)
        person.password = password
        db.session.commit()
        with open(
            f"credentials/{person.employee_id}_credentials.csv", "w", newline=""
        ) as file:
            writer = csv.writer(file)
            writer.writerow(["Username", "Password"])
            writer.writerow([f"{person.employee_id} or {person.email}", password])

        flash(f"Succesfully reset {person.name}'s password", "success")

        return redirect(url_for("download", file_path=file.name))
    return render_template("admin/reset_password.html", form=form)


@app.route("/make_payment", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Secretary"])
def make_payment():
    form = MakePaymentForm()
    form.person_id.choices = [
        (person.id, (f"{person.name} ({person.employee_id})"))
        for person in query.get_persons()
    ]
    form.date.data = pd.to_datetime("today")
    form.bank.choices = [(bank.id, bank.name) for bank in query.get_banks()]
    if request.method == "POST":
        if form.validate_on_submit():
            amount = form.amount.data
            payment_type = form.payment_type.data
            description = form.description.data
            selected_person_id = form.person_id.data
            selected_person = Person.query.get(selected_person_id)
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
                    query.repay_loan(
                        selected_person.id, amount, date, bank_id, ref_no, description
                    )

                flash("Payment submitted successfully.", "success")
                return redirect(url_for("dashboard"))
            else:
                flash(f"Error in field {form.errors}", "error")

        return redirect(url_for("get_person", person_id=selected_person_id))

    return render_template("forms/payment.html", form=form)


@app.route("/forms/register", methods=["GET", "POST"])
@login_required
def register_loan():
    form = RegisterLoanForm()
    if current_user.role.name == "User":
        form.name.choices = [ (current_user.id, (f"{current_user.name} ({current_user.employee_id})"))]
        form.description.data = f"Loan Application for {current_user.employee_id}"
    else:
        form.name.choices = [
            (person.id, (f"{person.name} ({person.employee_id})"))
            for person in query.get_persons()
        ]
    form.guarantor.choices = [(None,None)] + [(person.id, f'{person.name},{person.employee_id}') for person in query.get_persons() ]
    form.guarantor_2.choices =[(None,None)] + [(person.id,f'{person.name},{person.employee_id}') for person in query.get_persons() ]

    form.date.data = pd.to_datetime("today")
    form.bank.choices = [(bank.id, bank.name) for bank in query.get_banks()]
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
            if guarantor!="None" :
                guarantor = query.get_person(guarantor)
                guarantors.append(guarantor)
            guarantor_2 = form.guarantor_2.data   
            if guarantor_2 !="None":   
                guarantor_2 = query.get_person(guarantor_2)
                guarantors.append(guarantor_2)
            log_report(guarantors)
            test = query.registeration_payment(
                id, amount, date, ref_no, bank_id, description, loan=True, guarantors=guarantors
            )
            if test == True:
                flash("Registration submitted successfully.", "success")
            
            else:
                log_report(test)
                flash(f"something went wrong.{test}", "error")
                return redirect(url_for("register_loan"))
            return redirect(url_for("dashboard"))
        flash(form.errors, "error")

    return render_template("forms/register_loan.html", form=form)



@app.route("/make_income", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Secretary"])
def make_income():
    form = IncomeForm()
    form.name.choices = [(income.id, income.name) for income in query.get_income()]
    form.bank.choices = [(bank.id, bank.name) for bank in query.get_banks()]
    form.date.data = pd.to_datetime("today")
    if request.method == "POST":
        if form.validate_on_submit():
            id = form.name.data
            amount = form.amount.data
            description = form.description.data
            date = form.date.data
            bank_id = form.bank.data
            ref_no = form.ref_no.data

            query.add_income(
                id,
                amount,
                date,
                ref_no,
                bank_id,
                description,
            )
            flash("Income submitted successfully.", "success")
            return redirect(url_for("dashboard"))
        flash(form.errors, "error")

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
    form.date.data = pd.to_datetime("today")
    if request.method == "POST":
        if form.validate_on_submit():
            # Handle existing expense selection
            query.add_transaction(
                form.main_account.data,
                form.sub_account.data,
                form.amount.data,
                form.date.data,
                form.ref_no.data,
                form.bank.data,
                form.description.data,
            )
            flash("Transaction submitted successfully.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash(form.errors, "error")

    return render_template("forms/expense_form.html", form=form)


# @app.route("/withdraw", methods=["GET", "POST"])
# @login_required
# @role_required(["Admin", "Secretary"])
# def withdraw():
#     # Add logic to retrieve the list of persons from the database
#     # Replace `get_all_persons()` with an appropriate function that retrieves the list of persons.
#     persons = query.get_persons()
#     form = WithdrawalForm()
#     form.person.choices = [(person.id, person.name) for person in query.get_persons()]
#     form.bank_id.choices = [(bank.id, bank.name) for bank in query.get_banks()]
#     form.date.data = pd.to_datetime("today")
#     if request.method == "POST":
        
#         if form.validate_on_submit():
#             person_id = form.person.data
#             amount = form.amount.data
#             description = form.description.data
#             ref_no = form.ref_no.data
#             bank_id = form.bank_id.data
#             date = form.date.data
#             # Retrieve the selected person from the database
#             selected_person = query.get_person(person_id)
#             test = query.withdraw(person_id, amount, description, ref_no, bank_id, date)
#             if test == True:
#                 flash(
#                     f"Withdrawal of {amount} successful for {selected_person.name}. Updated balance: {selected_person.balance_bfd}"
#                 )
#                 return redirect("dashboard")
            
#             elif test :
#                 flash(test, "error")
#                 return render_template(
#                     "forms/withdraw.html", form=form, persons=persons
#                 )
#             else:
#                 flash(
#                     f"Insufficient balance for {selected_person.name} to withdraw {amount}."
#                 )
#                 return render_template(
#                     "forms/withdraw.html", form=form, persons=persons
#                 )
#         else:
#             flash(form.errors, "error")
#     return render_template("forms/withdraw.html", form=form, persons=persons)
@app.route("/withdraw", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Secretary"])
def request_withdrawal():
    form = WithdrawalForm()
    form.person.choices = [(person.id, person.name) for person in query.get_persons()]
    form.bank_id.choices = [(bank.id, bank.name) for bank in query.get_banks()]
    form.date.data = pd.to_datetime("today")

    if request.method == "POST":
        if form.validate_on_submit():
            person_id = form.person.data
            amount = form.amount.data
            description = form.description.data
            ref_no = form.ref_no.data
            bank_id = form.bank_id.data
            date = form.date.data

            person = query.get_person(person_id)

            withdrawal_request = WithdrawalRequest(
                person=person,
                amount=amount,
                description=description,
                ref_no=ref_no,
                bank_id=bank_id,
                date=date,
            )

            db.session.add(withdrawal_request)
            db.session.commit()

            flash("Withdrawal sent for approval.", "success")

            return redirect(url_for("dashboard"))

        else:
            flash(form.errors, "error")

    return render_template("forms/withdraw.html", form=form)

@app.route("/withdraw/approve/<int:request_id>", methods=["GET"])
@login_required
@role_required(["Admin"])
def approve_withdrawal(request_id):

    wr= WithdrawalRequest.query.get(request_id)

    if not wr:
        flash("Withdrawal request not found.", "error")
    elif not wr.is_approved:
        test = query.withdraw(wr.person.id, wr.amount, wr.description, wr.ref_no, wr.bank_id, wr.date)
        if test == True:
            flash(
                f"Withdrawal of {wr.amount} successful for {wr.person.name}. Updated balance: {wr.person.total_balance}"
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
        (person.id, (f"{person.name} ({person.employee_id})"))
        for person in query.get_registered()
    ]
    form.start_date.data = pd.to_datetime("today")
    form.bank.choices = [(bank.id, bank.name) for bank in query.get_banks()]

    from dateutil.relativedelta import relativedelta

    if request.method == "POST":
        if form.validate_on_submit():
            employee = query.get_registered_person(form.name.data)
            employee_id = employee.employee_id
            person = Person.query.filter_by(employee_id=employee_id).first()
            duration = int(form.duration.data)
            end_date = form.start_date.data + relativedelta(months=duration)
            test = query.make_loan_request(
                bank_id=form.bank.data,
                employee_id=person.employee_id,
                amount=form.amount.data,
                interest_rate=form.interest_rate.data,
                start_date=form.start_date.data,
                end_date=end_date,
                description=form.description.data,
                ref_no=form.ref_no.data,
            )
            if test == True:
                flash("Loan sent for approval.", "success")
                return redirect(url_for("dashboard"))
            else:
                flash(test, "error")
                log_report(test)

    return render_template("forms/loan_form.html", form=form)


@app.route("/approval", methods=["GET", "POST"])
@login_required
@role_required(["Admin"])
def approval():
    loans = query.get_loans()
    
    withdrawals = WithdrawalRequest.query.filter_by(is_approved=False).all()

    return render_template("admin/approval.html", loans=loans, withdrawals=withdrawals)

     

@app.route("/loan/approve/<int:loan_id>", methods=["GET"])
@login_required
@role_required(["Admin"])
def approve_loan(loan_id):

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
        log_report(test)

    return render_template("admin/approval.html")



@app.route("/change_password", methods=["GET", "POST"])
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
        if query.edit_profile(
            form.person.data, form.email.data, form.phone_no.data, form.company_id.data
        ):
            flash("Profile updated successfully!", "success")
        else:
            flash("An error occurred while updating the profile.", "error")

    return render_template("forms/edit_profile.html", form=form)


# upload


@app.route("/upload_savings", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Secretary"])
def upload_savings():
    form = UploadForm()
    form.date.data = pd.to_datetime("today")
    if request.method == "POST" and form.validate_on_submit():
        file = request.files["file"]
        if file:
            log_report("found_file")
            # Save the uploaded file
            file.save(f'upload/{file.filename}')
            # Process the uploaded file
            test = send_upload_to_savings(file,form.ref_no.data, form.description.data, form.date.data)
            if test==True:
                flash("Savings updated successfully!", "success")
            else:
                flash(test, "error")

            return redirect(url_for("get_payments"))
    else:
        flash(form.errors, "error")
        log_report(form.errors)
    return render_template("forms/upload.html", form=form, route_type="savings")


@app.route("/upload_loan_repayment", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Secretary"])
def upload_loan():
    form = UploadForm()
    form.date.data = pd.to_datetime("today")
    if request.method == "POST" and form.validate_on_submit():
        file = request.files["file"]
        if file:
            # Save the uploaded file
            file.save(f'upload/{file.filename}')
            # Process the uploaded file
            send_upload_to_loan_repayment(
                file.filename,form.ref_no.data , form.description.data, form.date.data
            )
            flash("Savings updated successfully!", "success")

            return redirect("/dashboard")
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


@app.route("/income", methods=["GET"])
@login_required
@role_required(["Admin", "Secretary", "Sub-Admin"])
def income_statement():
    incomes = query.get_income()
    expenses = query.get_expenses()

    net_income = query.get_net_income()

    return render_template("query/income.html", incomes=incomes, expenses=expenses, net_income=net_income)



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
        loans = query.get_person_loans(person_id)
        person = query.get_person(person_id)
        payments = person.loan_payments_made
        form = DateFilterForm(request.args)
        # Filter payments based on date range
        start_date = form.start_date.data
        end_date = form.end_date.data
        filtered_payments = filter_payments(start_date, end_date, payments)
        return render_template(
            "query/loan_account.html",
            payments=filtered_payments,
            person=person,
            loans=loans,
            form=form,
        )
    else:
        return redirect(url_for("loan_account", person_id=user.id))


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


# @app.route("/trial_balance")
# @login_required
# @role_required(["Admin", "Secretary", "Sub-Admin"])
# def trial_balance():
#     # Retrieve data from the database
#     companies = Company.query.all()
#     banks = Bank.query.all()
#     persons = Person.query.all()
#     assets = Asset.query.all()
#     liabilities = Liability.query.all()
#     incomes = Income.query.all()
#     expenses = Expense.query.all()
#     investments = Investment.query.all()
#     # Calculate total cash and equivalents
#     total_company_receivable = sum(company.amount_accumulated for company in companies)
#     total_cash_and_equivalents = total_company_receivable + sum(
#         bank.new_balance for bank in banks
#     )

#     # Calculate total accounts receivable
#     total_accounts_receivable = sum(person.loan_balance for person in persons)

#     total_investments = sum(
#         investment.balance for investment in investments if investment.balance
#     )
#     # Calculate total income
#     total_incomes = sum(income.balance for income in incomes if income.balance)

#     # Calculate total expenses
#     total_expenses = sum(expense.balance for expense in expenses if expense.balance)

#     # Calculate total assets
#     total_assets = (
#         total_cash_and_equivalents
#         + total_accounts_receivable
#         + sum(asset.balance for asset in assets if asset.balance)
#         + total_incomes
#         + total_investments
#     )

#     # Calculate total accounts payable
#     total_accounts_payable = sum(person.total_balance for person in persons)

#     # Calculate total liabilities
#     total_liabilities = (
#         total_accounts_payable
#         + sum(liability.balance for liability in liabilities if liability.balance)
#         + total_expenses
#     )

#     # Calculate total equity and liabilities & equity
#     total_equity = total_assets - total_liabilities
#     total_liabilities_and_equity = total_liabilities + total_equity

#     return render_template(
#         "query/trial_balance.html",
#         assets=assets,
#         total_expenses=total_expenses,
#         expenses=expenses,
#         incomes=incomes,
#         banks=banks,
#         total_cash_and_equivalents=total_cash_and_equivalents,
#         company=total_company_receivable,
#         total_accounts_receivable=total_accounts_receivable,
#         total_incomes=total_incomes,
#         total_assets=total_assets,
#         investments=investments,
#         liabilities=liabilities,
#         total_accounts_payable=total_accounts_payable,
#         total_liabilities=total_liabilities,
#         total_equity=total_equity,
#         total_liabilities_and_equity=total_liabilities_and_equity,
#     )

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
    accounts_payable = query.get_accounts_payable()

    fixed_assets = Asset.query.all()
    liabilities = Liability.query.all()
    incomes = Income.query.all()
    expenses = Expense.query.all()
    investments = Investment.query.all()

    total_fixed_assets = sum(a.balance for a in fixed_assets)
    total_assets = cash_and_bank + accounts_receivable+ company_receivable+ total_investments+ total_fixed_assets

    total_dr = total_assets
    total_cr = net_income+ accounts_payable+ total_liabilities
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
    total_fixed_assets = sum(a.balance for a in fixed_assets)

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
    }
    return render_template("query/balance-sheet.html", **context)



# @app.route("/balance_sheet")
# @login_required
# @role_required(["Admin", "Secretary", "Sub-Admin"])
# def balance_sheet():
#     # Retrieve data from the database
#     companies = Company.query.all()
#     banks = Bank.query.all()
#     assets = Asset.query.all()
#     investments = Investment.query.all()
#     expenses = Expense.query.all()
#     liabilities = Liability.query.all()

#     total_cash_and_equivalents = sum(
#         company.amount_accumulated for company in companies
#     ) + sum(bank.new_balance for bank in banks)

#     persons = Person.query.all()
#     total_accounts_receivable = sum(person.loan_balance for person in persons)
#     # Calculate the total assets
#     total_assets = total_cash_and_equivalents + total_accounts_receivable

#     total_accounts_payable = sum(person.total_balance for person in persons)

#     # Calculate the total liabilities
#     total_liabilities = total_accounts_payable

#     # Calculate the total equity and liabilities & equity
#     total_equity = total_assets - total_liabilities
#     total_liabilities_and_equity = total_liabilities + total_equity
#     balance_sheet_data = {
#         "total_cash_and_equivalents": total_cash_and_equivalents,
#         "total_accounts_receivable": total_accounts_receivable,
#         "total_assets": total_assets,
#         "total_accounts_payable": total_accounts_payable,
#         "total_liabilities": total_liabilities,
#         "total_equity": total_equity,
#         "total_liabilities_and_equity": total_liabilities_and_equity,
#         "assets": assets,
#         "expenses": expenses,
#         "investments": investments,
#         "liabilities": liabilities,
#     }

#     return render_template(
#         "query/balance_sheet.html",
#         balance_sheet_data=balance_sheet_data,
#     )


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


# dynamic lookup


@app.route("/forgot_password")
def forgot_password():
    pass


# API endpoints
@app.route("/get_person_info/<person_id>")
def get_person_info(person_id):
    person = query.get_person(person_id)
    return person.to_json()

# @app.route("/get_person_balance/<person_id>")
# def get_person_info(person_id):
#     person = query.get_person(person_id)

#     return person.to_json()


@app.route("/search_suggestions", methods=["GET"])
def search_suggestions():
    query = request.args.get("query", "")
    # Perform the search query using Flask-SQLAlchemy
    # For example, search the Company and Person models for the given query
    companies_results = Company.query.filter(Company.name.ilike(f"%{query}%")).all()
    persons_results = Person.query.filter(Person.name.ilike(f"%{query}%")).all()

    suggestions = {
        "companies": [[company.id, company.name] for company in companies_results],
        "persons": [[person.id, person.name] for person in persons_results],
    }

    return jsonify(suggestions)


@app.route("/get_sub_accounts/<int:main_account_id>")
def get_sub_accounts(main_account_id):
    # Fetch sub-account options based on the selected main_account
    # You need to implement this logic based on your database structure
    sub_accounts = query.sub_accounts(main_account_id)

    # Create a list of dictionaries with 'id' and 'name' keys
    sub_account_options = [
        {"id": sub_account.id, "name": sub_account.name} for sub_account in sub_accounts
    ]

    return jsonify(sub_account_options)


@app.route("/get_balance/<int:person_id>")
def get_balance(person_id):
    selected_person = Person.query.get(person_id)
    if selected_person:
        return format_currency(selected_person.total_balance)
    else:
        return jsonify(error="Person not found"), 404


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