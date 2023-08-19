from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from flask_login import UserMixin

app = Flask(__name__)
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "sqlite:///cooperative.db"  # Replace with your database URI
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
    total_balance = db.Column(db.Float, default=0.0)
    loan_balance = db.Column(db.Float, default=0.0)
    loan_balance_bfd = db.Column(db.Float, default=0.0)
    loans = db.relationship("Loan", backref="person")
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
            "total_balance": self.total_balance,
            "loan_balance": self.loan_balance,
            "loan_balance_bfd": self.loan_balance_bfd,
            "loans": [loan.to_json() for loan in self.loans],
            "payments_made": [payment.to_json() for payment in self.payments_made],
            "loan_payments_made": [
                payment.to_json() for payment in self.loan_payments_made
            ],
        }


# Define the Role data-model
class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)
    person = db.relationship("Person", backref="role")


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
    amount = db.Column(db.Integer)
    interest_rate = db.Column(db.Integer)
    start_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.Date, nullable=False)
    is_paid = db.Column(db.Boolean, default=False)

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
    balance = balance = db.Column(db.Float, default=0.0)
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
    expense_id = db.Column(
        db.Integer, db.ForeignKey("incomes.id"), nullable=True, index=True
    )
    description = db.Column(db.String, nullable=True)
    ref_no = db.Column(db.String)
    balance = db.Column(db.Float, nullable=True)
    bank_id = db.Column(
        db.Integer, db.ForeignKey("banks.id"), nullable=True, index=True
    )

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
    balance = balance = db.Column(db.Float, default=0.0)
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
    balance = balance = db.Column(db.Float, default=0.0)
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
    balance = balance = db.Column(db.Float, default=0.0)
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

    if Bank.query.count() == 0:
        db.session.add(Bank(name="Zenith", balance_bfd=2000000, new_balance=2000000))
        db.session.commit()

    if Company.query.count() == 0:
        db.session.add(
            Company(name="Nigerian Info", balance_bfd=200000, amount_accumulated=200000)
        )
        db.session.commit()

    if Person.query.count() == 0:
        db.session.add(
            Person(
                name="Samuel",
                employee_id="ASA123",
                email="samore@gmail.com",
                password="password",
                total_balance=220000,
                loan_balance=20000,
                loan_balance_bfd=20000,
                phone_no=9020920855,
                balance_bfd=220000,
                company_id=1,
                role_id=1,
            )
        )
        db.session.commit()
