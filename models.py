from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from dotenv import load_dotenv
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates
from sqlalchemy import desc
import os

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")  # Replace with your database URI
db = SQLAlchemy(app)


class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    balance_bfd = db.Column(db.Float, default=0.0)
    amount_accumulated = db.Column(db.Float, default=0.0)
    payments_made = db.relationship("BankPayment", backref="company_payer", lazy=True)
    employees = db.relationship("Person", backref="company", lazy=True)

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "amount_accumulated": self.amount_accumulated,
            "employees": [employee.to_json() for employee in self.employees],
        }


class CompanyPayment(db.Model):
    __tablename__ = "company_payments"

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    exact_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date = db.Column(db.Date, nullable=False)
    company_id = db.Column(
        db.Integer, db.ForeignKey("companies.id"), nullable=True, index=True
    )
    description = db.Column(db.String, nullable=True)
    ref_no = db.Column(db.String)
    balance = db.Column(db.Float, nullable=True)
    bank_id = db.Column(
        db.Integer, db.ForeignKey("banks.id"), nullable=True, index=True
    )
    year = db.Column(db.Integer, nullable=False)

    def to_json(self):
        return {
            "id": self.id,
            "amount": self.amount,
            "exact_date": self.exact_date,
            "date": self.date,
            "company_id": self.company_id,
            "description": self.description,
            "ref_no": self.ref_no,
            "balance": self.balance,
            "bank_id": self.bank_id,
        }


class Person(db.Model, UserMixin):
    __tablename__ = "persons"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))
    email = db.Column(db.String, nullable=True, unique=True)
    password = db.Column(db.String(255), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))
    employee_id = db.Column(db.String, nullable=False, unique=True)
    phone_no = db.Column(db.String, unique=True)
    balance_bfd = db.Column(db.Float, default=0.0)
    balance_withheld = db.Column(db.Float, default=0.0) 
    available_balance = db.Column(db.Float, default=0.0)
    loan_balance = db.Column(db.Float, default=0.0)
    loan_balance_bfd = db.Column(db.Float, default=0.0)
    loans = db.relationship("Loan", backref="person",foreign_keys="[Loan.person_id]")
    bank_payments_made = db.relationship("BankPayment", backref="payer", lazy=True)
    payments_made = db.relationship("SavingPayment", backref="payer", lazy=True)
    loan_payments_made = db.relationship("LoanPayment", backref="payer", lazy=True)

    def to_json(self):
        return {
            "id": self.id,
            "company_id": self.company_id,
            "employee_id": self.employee_id,
            "name": self.name,
            "email": self.email,
            "phone_no": self.phone_no,
            "balance_bfd": self.balance_bfd,
            "available_balance": self.available_balance,
            "loan_balance": self.loan_balance,
            "loan_balance_bfd": self.loan_balance_bfd,
            "loans": [loan.to_json() for loan in self.loans],
            "payments_made": [payment.to_json() for payment in self.payments_made],
            "loan_payments_made": [
                payment.to_json() for payment in self.loan_payments_made
            ],
        }
    
    def get_guaranteed_payments(self):
        # Query LoanFormPayment instances where this Person is a guarantor
        loan = LoanFormPayment.query.filter(LoanFormPayment.guarantors.any(id=self.id)).all()
        ret = [l for l in loan if not l.loan]
        return ret
    
    def last_loan(self):
        # Query the loans associated with this person, ordered by the loan's start_date in descending order
        last_loan = Loan.query.filter_by(person_id=self.id).order_by(desc(Loan.start_date)).first()
        return last_loan
    
    @validates("balance_bfd", "balance_withheld", "available_balance", "loan_balance", "loan_balance_bfd")
    def validate_non_negative(self, key, value):
        if value < 0:
            raise ValueError(f"{key} cannot be negative")
        return value
    
    @hybrid_property
    def total_balance(self):
        return self.available_balance + self.balance_withheld


# Define the Role data-model
class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)
    person = db.relationship("Person", backref="role")

class WithdrawalRequest(db.Model):
    __tablename__ = "withdrawal_requests"

    id = db.Column(db.Integer, primary_key=True)
    person = db.relationship("Person", backref="withdrawal_requests")
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String, nullable=True)
    ref_no = db.Column(db.String)
    bank_id = db.Column(
        db.Integer, db.ForeignKey("banks.id"), nullable=False, index=True
    )
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=False)
    approved_by = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=True)
    year = db.Column(db.Integer, nullable=False)

    def to_json(self):
        return {
            "id": self.id,
            "person_id": self.person_id,
            "amount": self.amount,
            "description": self.description,
            "ref_no": self.ref_no,
            "bank_id": self.bank_id,
            "date": self.date,
            "is_approved": self.is_approved,
        }

class SavingPayment(db.Model):
    __tablename__ = "savings_payments"

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    exact_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date = db.Column(db.Date, nullable=False)
    person_id = db.Column(
        db.Integer, db.ForeignKey("persons.id"), nullable=False, index=True
    )
    company_id = db.Column(
        db.Integer, db.ForeignKey("companies.id"), nullable=True, index=True
    )
    description = db.Column(db.String, nullable=True)
    ref_no = db.Column(db.String)
    balance = db.Column(db.Float, nullable=True)
    bank_id = db.Column(
        db.Integer, db.ForeignKey("banks.id"), nullable=True, index=True
    )
    year = db.Column(db.Integer, nullable=False)

    def to_json(self):
        return {
            "id": self.id,
            "amount": self.amount,
            "exact_date": self.exact_date,
            "date": self.date,
            "person_id": self.person_id,
            "company_id": self.company_id,
            "description": self.description,
            "ref_no": self.ref_no,
            "balance": self.balance,
            "bank_id": self.bank_id,
        }


class Loan(db.Model):
    __tablename__ = "loans"

    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(
        db.Integer, db.ForeignKey("persons.id"), nullable=False, index=True
    )
    description = db.Column(db.String, nullable=True)
    bank_id = db.Column(
        db.Integer, db.ForeignKey("banks.id"), nullable=True, index=True
    )
    ref_no = db.Column(db.String)
    amount = db.Column(db.Integer)
    interest_rate = db.Column(db.Integer)
    start_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.Date, nullable=False)
    guarantor = db.relationship("Person", backref="guarantor",foreign_keys="[Loan.guarantor_id]", lazy=True)
    guarantor_id = db.Column(
        db.Integer, db.ForeignKey("persons.id"), nullable=True, index=True
    )
    is_paid = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=False)
    admin_approved = db.Column(db.Boolean, default=False)
    approved_by = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=True)


    def to_json(self):
        return {
            "id": self.id,
            "person_id": self.person_id,
            "amount": self.amount,
            "interest_rate": self.interest_rate,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "is_paid": self.is_paid,
        }
    
    
    
    def payment_complete(self):
        log_report("loan balance")
        if self.person.loan_balance == 0:
            log_report("loan balance is 0")
            self.is_paid = True
            for guarantor in self.guarantor:
                log_report("payment complete")
                guarantor.available_balance += guarantor.loan_form_payment.contribution_amount
                guarantor.balance_withheld -= guarantor.loan_form_payment.contribution_amount
                
            db.session.commit()
            return True

class LoanPayment(db.Model):
    __tablename__ = "loan_payments"

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    exact_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String, nullable=True)
    ref_no = db.Column(db.String)
    balance = db.Column(db.Float, nullable=True)
    bank_id = db.Column(
        db.Integer, db.ForeignKey("banks.id"), nullable=True, index=True
    )
    person_id = db.Column(
        db.Integer, db.ForeignKey("persons.id"), nullable=True, index=True
    )
    company_id = db.Column(
        db.Integer, db.ForeignKey("companies.id"), nullable=True, index=True
    )
    year = db.Column(db.Integer, nullable=False)

    def to_json(self):
        return {
            "id": self.id,
            "amount": self.amount,
            "exact_date": self.exact_date,
            "date": self.date,
            "description": self.description,
            "ref_no": self.ref_no,
            "balance": self.balance,
            "bank_id": self.bank_id,
            "person_id": self.person_id,
            "company_id": self.company_id,
        }


class Bank(db.Model):
    __tablename__ = "banks"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    balance_bfd = db.Column(db.Float, default=0.0)
    new_balance = db.Column(db.Float, default=0.0)
    payments = db.relationship("BankPayment", backref="bank")

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "balance_bfd": self.balance_bfd,
            "new_balance": self.new_balance,
            "payments": [payment.to_json() for payment in self.payments],
        }


class BankPayment(db.Model):
    __tablename__ = "bank_payments"

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    exact_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date = db.Column(db.Date, nullable=False)
    person_id = db.Column(
        db.Integer, db.ForeignKey("persons.id"), nullable=True, index=True
    )
    company_id = db.Column(
        db.Integer, db.ForeignKey("companies.id"), nullable=True, index=True
    )
    description = db.Column(db.String, nullable=True)
    ref_no = db.Column(db.String)
    bank_balance = db.Column(db.Float, nullable=True)
    bank_id = db.Column(
        db.Integer, db.ForeignKey("banks.id"), nullable=True, index=True
    )
    year = db.Column(db.Integer, nullable=False)

    def to_json(self):
        return {
            "id": self.id,
            "amount": self.amount,
            "exact_date": self.exact_date,
            "date": self.date,
            "person_id": self.person_id,
            "company_id": self.company_id,
            "description": self.description,
            "ref_no": self.ref_no,
            "bank_balance": self.bank_balance,
            "bank_id": self.bank_id,
        }


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String, nullable=True)
    balance_bfd = db.Column(db.Float, default=0.0)
    balance = db.Column(db.Float, default=0.0)
    payments = db.relationship("ExpensePayment", backref="expense")

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "balance": self.balance,
        }


class ExpensePayment(db.Model):
    __tablename__ = "expense_payments"

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    exact_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date = db.Column(db.Date, nullable=False)
    expense_id = db.Column(
        db.Integer, db.ForeignKey("expenses.id"), nullable=True, index=True
    )
    description = db.Column(db.String, nullable=True)
    ref_no = db.Column(db.String)
    balance = db.Column(db.Float, nullable=True)
    bank_id = db.Column(
        db.Integer, db.ForeignKey("banks.id"), nullable=True, index=True
    )
    year = db.Column(db.Integer, nullable=False)

    def to_json(self):
        return {
            "id": self.id,
            "amount": self.amount,
            "exact_date": self.exact_date,
            "date": self.date,
            "expense_id": self.expense_id,
            "description": self.description,
            "ref_no": self.ref_no,
            "balance": self.balance,
            "bank_id": self.bank_id,
        }


class Asset(db.Model):
    __tablename__ = "assets"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    balance_bfd = db.Column(db.Float, default=0.0)
    description = db.Column(db.String, nullable=True)
    balance = db.Column(db.Float, default=0.0)
    payments = db.relationship("AssetPayment", backref="asset")

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "balance": self.balance,
        }


class AssetPayment(db.Model):
    __tablename__ = "asset_payments"

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    exact_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date = db.Column(db.Date, nullable=False)
    asset_id = db.Column(
        db.Integer, db.ForeignKey("assets.id"), nullable=True, index=True
    )
    description = db.Column(db.String, nullable=True)
    ref_no = db.Column(db.String)
    balance = db.Column(db.Float, nullable=True)
    bank_id = db.Column(
        db.Integer, db.ForeignKey("banks.id"), nullable=True, index=True
    )
    year = db.Column(db.Integer, nullable=False)

    def to_json(self):
        return {
            "id": self.id,
            "amount": self.amount,
            "exact_date": self.exact_date,
            "date": self.date,
            "expense_id": self.expense_id,
            "description": self.description,
            "ref_no": self.ref_no,
            "balance": self.balance,
            "bank_id": self.bank_id,
        }


class Income(db.Model):
    __tablename__ = "incomes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String, nullable=True)
    balance_bfd = db.Column(db.Float, default=0.0)
    balance = db.Column(db.Float, default=0.0)
    payments = db.relationship("IncomePayment", backref="income")

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "balance": self.balance,
        }


class IncomePayment(db.Model):
    __tablename__ = "income_payments"

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    exact_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date = db.Column(db.Date, nullable=False)
    income_id = db.Column(
        db.Integer, db.ForeignKey("incomes.id"), nullable=True, index=True
    )
    description = db.Column(db.String, nullable=True)
    ref_no = db.Column(db.String)
    balance = db.Column(db.Float, nullable=True)
    bank_id = db.Column(
        db.Integer, db.ForeignKey("banks.id"), nullable=True, index=True
    )
    year = db.Column(db.Integer, nullable=False)

    def to_json(self):
        return {
            "id": self.id,
            "amount": self.amount,
            "exact_date": self.exact_date,
            "date": self.date,
            "expense_id": self.expense_id,
            "description": self.description,
            "ref_no": self.ref_no,
            "balance": self.balance,
            "bank_id": self.bank_id,
        }


class Investment(db.Model):
    __tablename__ = "investments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String, nullable=True)
    balance = db.Column(db.Float, default=0.0)
    balance_bfd = db.Column(db.Float, default=0.0)
    payments = db.relationship("InvestmentPayment", backref="investment")

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "balance": self.balance,
        }


class InvestmentPayment(db.Model):
    __tablename__ = "investment_payments"

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    exact_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date = db.Column(db.Date, nullable=False)
    investment_id = db.Column(
        db.Integer, db.ForeignKey("investments.id"), nullable=True, index=True
    )
    description = db.Column(db.String, nullable=True)
    ref_no = db.Column(db.String)
    balance = db.Column(db.Float, nullable=True)
    bank_id = db.Column(
        db.Integer, db.ForeignKey("banks.id"), nullable=True, index=True
    )
    year = db.Column(db.Integer, nullable=False)

    def to_json(self):
        return {
            "id": self.id,
            "amount": self.amount,
            "exact_date": self.exact_date,
            "date": self.date,
            "expense_id": self.expense_id,
            "description": self.description,
            "ref_no": self.ref_no,
            "balance": self.balance,
            "bank_id": self.bank_id,
        }


class Liability(db.Model):
    __tablename__ = "liabilities"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String, nullable=True)
    balance = db.Column(db.Float, default=0.0)
    balance_bfd = db.Column(db.Float, default=0.0)
    payments = db.relationship("LiabilityPayment", backref="liability")

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "balance": self.balance,
        }


class LiabilityPayment(db.Model):
    __tablename__ = "liability_payments"

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    exact_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date = db.Column(db.Date, nullable=False)
    liability_id = db.Column(
        db.Integer, db.ForeignKey("liabilities.id"), nullable=True, index=True
    )
    description = db.Column(db.String, nullable=True)
    ref_no = db.Column(db.String)
    balance = db.Column(db.Float, nullable=True)
    bank_id = db.Column(
        db.Integer, db.ForeignKey("banks.id"), nullable=True, index=True
    )
    year = db.Column(db.Integer, nullable=False)

    def to_json(self):
        return {
            "id": self.id,
            "amount": self.amount,
            "exact_date": self.exact_date,
            "date": self.date,
            "expense_id": self.expense_id,
            "description": self.description,
            "ref_no": self.ref_no,
            "balance": self.balance,
            "bank_id": self.bank_id,
        }


class Equity(db.Model):
    __tablename__ = "equities"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String, nullable=True)
    balance = db.Column(db.Float, default=0.0)
    balance_bfd = db.Column(db.Float, default=0.0)
    payments = db.relationship("EquityPayment", backref="equity")

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "balance": self.balance,
        }


class EquityPayment(db.Model):
    __tablename__ = "equity_payments"

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    exact_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date = db.Column(db.Date, nullable=False)
    equity_id = db.Column(
        db.Integer, db.ForeignKey("equities.id"), nullable=True, index=True
    )
    description = db.Column(db.String, nullable=True)
    ref_no = db.Column(db.String)
    balance = db.Column(db.Float, nullable=True)
    bank_id = db.Column(
        db.Integer, db.ForeignKey("banks.id"), nullable=True, index=True
    )
    year = db.Column(db.Integer, nullable=False)

    def to_json(self):
        return {
            "id": self.id,
            "amount": self.amount,
            "exact_date": self.exact_date,
            "date": self.date,
            "expense_id": self.expense_id,
            "description": self.description,
            "ref_no": self.ref_no,
            "balance": self.balance,
            "bank_id": self.bank_id,
        }

loan_payment_guarantor_association = db.Table(
    'loan_payment_guarantor_association',
    db.Column('loan_payment_id', db.Integer, db.ForeignKey('loan_form_payment.id')),
    db.Column('guarantor_id', db.Integer, db.ForeignKey('persons.id')))
class GuarantorContribution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_form_payment_id = db.Column(db.Integer, db.ForeignKey('loan_form_payment.id', ondelete='SET NULL'))
    guarantor_id = db.Column(db.Integer, db.ForeignKey('persons.id'))
    contribution_amount = db.Column(db.Float, default=0.0)
    
    # Make the loan_id relationship nullable
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=True)
    
    # Define a relationship with Person to access the guarantor
    guarantor = db.relationship("Person", foreign_keys=[guarantor_id], backref="guarantor_contributions")
    
    # Define a relationship with Loan, making it nullable
    loan = db.relationship("Loan", backref="guarantor_contributions")

class LoanFormPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id'), unique=True)
    loan = db.Column(db.Boolean, default=False)
    failed = db.Column(db.Boolean, default=False)
    loan_amount = db.Column(db.Float, default=0.0)
    
    # Define a relationship with Person to access the person associated with this loan
    person = db.relationship("Person", backref="loan_form_payment")
    
    guarantors = db.relationship("Person", secondary=loan_payment_guarantor_association)
    guarantor_amount = db.Column(db.Float, default=0.0)
    is_approved = db.Column(db.Boolean, default=False)
    consent = db.Column(db.Integer, nullable=True, default=0)
    
    # Define a relationship with GuarantorContribution to access contributions for this loan
    guarantor_contributions = db.relationship("GuarantorContribution", backref="loan_form_payment")


    def move_to_loan(self):
        if self.consent==len(self.guarantors):

            if self.guarantor_amount+self.person.available_balance >= self.loan_amount:
                self.loan = True
                return True
            else:
                self.loan_failed()
                return False
        else:
            return False
        
    def loan_failed(self):
        self.consent = 0
        self.guarantor_amount = 0
        self.is_approved = False

        log_report("guarantor contributions")

        log_report(self.guarantor_contributions)
        log_report(GuarantorContribution.query.all())

        # Delete associated GuarantorContribution records
        for contribution in GuarantorContribution.query.filter_by(loan_form_payment_id=self.id).all():
            contribution.guarantor.available_balance += contribution.contribution_amount
            log_report("available balance")
            log_report(contribution.guarantor.available_balance)
            contribution.guarantor.balance_withheld -= contribution.contribution_amount
            id = contribution.id
            log_report('id')
            log_report(id)
            contribution=GuarantorContribution.query.get(id)
            db.session.delete(contribution)

        self.guarantor_contributions = []
        self.guarantors = []

        self.failed = True
        db.session.commit()

class Constants(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    current_year = db.Column(db.Integer, nullable=False)
    loan_application_fee = db.Column(db.Float, nullable=False)

class BalanceSheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fixed_assets = db.Column(db.Float)
    total_fixed_assets = db.Column(db.Float)
    cash_and_bank = db.Column(db.Float)
    accounts_receivable = db.Column(db.Float)
    company_receivable = db.Column(db.Float)
    investments = db.Column(db.Float)
    total_current_assets = db.Column(db.Float)
    total_assets = db.Column(db.Float)
    net_income = db.Column(db.Float)
    accounts_payable = db.Column(db.Float)
    total_liabilities = db.Column(db.Float)
    total_equity = db.Column(db.Float)
    total_liabilities_and_equity = db.Column(db.Float)
    year = db.Column(db.Integer, nullable=False)


from sqlalchemy import event

def log_report(target):
    with open('report.txt', 'a') as f:
        f.write(f'{target}\n')

with app.app_context():
    db.create_all()

    if Role.query.count() == 0:
        db.session.add_all(
            [
                Role(name="Admin"),
                Role(name="Sub-Admin"),
                Role(name="Secretary"),
                Role(name="User"),
            ]
        )
        db.session.commit()

    if Income.query.count() == 0:
        db.session.add_all(
            [
                Income(name="Loan Application Form", description="Loan application fee", balance_bfd=0, balance=0),
                Income(name="Interest", description="Interest on loans", balance_bfd=0, balance=0),
            ]
        )
        db.session.commit()

    if Bank.query.count() == 0:
        db.session.add(Bank(name="Zenith", balance_bfd=0, new_balance=0))
        db.session.commit()

    if Company.query.count() == 0:
        db.session.add(
            Company(name="Nigerian Info", balance_bfd=0, amount_accumulated=0)
        )
        db.session.commit()

    if Person.query.count() == 0:
        db.session.add(
            Person(
                name="Samuel",
                employee_id="ASA123",
                email="samore@gmail.com",
                password="password",
                available_balance=0,
                loan_balance=0,
                loan_balance_bfd=0,
                phone_no=9020920855,
                balance_bfd=0,
                company_id=1,
                role_id=1,
            )
        )
        db.session.commit()

    if Constants.query.count() == 0:
        db.session.add(Constants(current_year=datetime.utcnow().year, loan_application_fee=1000))
        db.session.commit()

    log_report(GuarantorContribution.query.all())