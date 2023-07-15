from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from flask_login import UserMixin

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cooperative.db'
db = SQLAlchemy(app)


class Company(db.Model):
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False,unique=True)
    balance_bfd = db.Column(db.Float, default=0.0)
    amount_accumulated = db.Column(db.Float, default=0.0)
    payments_made = db.relationship('BankPayment', backref='company_payer', lazy=True)
    employees = db.relationship('Person', backref='company', lazy=True)

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'amount_accumulated': self.amount_accumulated,
            'employees': [employee.to_json() for employee in self.employees]
        }


class Person(db.Model,UserMixin):
    __tablename__ = 'persons'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String, nullable=True,unique=True)
    password = db.Column(db.String(255), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    employee_id = db.Column(db.String, nullable=False,unique=True)
    phone_no = db.Column(db.String,unique=True)
    balance_bfd = db.Column(db.Float, default=0.0)
    total_balance = db.Column(db.Float, default=0.0)
    loan_balance = db.Column(db.Float, default=0.0)
    loan_balance_bfd = db.Column(db.Float, default=0.0)
    loans = db.relationship('Loan', backref='person')
    payments_made = db.relationship('SavingPayment', backref='payer', lazy=True)
    loan_payments_made = db.relationship('LoanPayment', backref='payer', lazy=True)

    def to_json(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'employee_id': self.employee_id,
            'name': self.name,
            'email': self.email,
            'phone_no': self.phone_no,
            'balance_bfd': self.balance_bfd,
            'total_balance': self.total_balance,
            'loan_balance': self.loan_balance,
            'loan_balance_bfd': self.loan_balance_bfd,
            'loans': [loan.to_json() for loan in self.loans],
            'payments_made': [payment.to_json() for payment in self.payments_made],
            'loan_payments_made': [payment.to_json() for payment in self.loan_payments_made]
        }

# Define the Role data-model
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('persons.id', ondelete='CASCADE'))
    person = db.relationship('Person', backref='role')


class SavingPayment(db.Model):
    __tablename__ = 'savings_payments'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    exact_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date = db.Column(db.Date, nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id'), nullable=False, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True, index=True)
    description = db.Column(db.String, nullable=True)
    ref_no = db.Column(db.String)
    balance = db.Column(db.Float, nullable=True)
    bank_id = db.Column(db.Integer, db.ForeignKey('banks.id'), nullable=True, index=True)

    def to_json(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'exact_date': self.exact_date,
            'date': self.date,
            'person_id': self.person_id,
            'company_id': self.company_id,
            'description': self.description,
            'ref_no': self.ref_no,
            'balance': self.balance,
            'bank_id': self.bank_id
        }


class LoanPayment(db.Model):
    __tablename__ = 'loan_payments'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    exact_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String, nullable=True)
    ref_no = db.Column(db.String)
    balance = db.Column(db.Float, nullable=True)
    bank_id = db.Column(db.Integer, db.ForeignKey('banks.id'), nullable=True, index=True)
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id'), nullable=True, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True, index=True)

    def to_json(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'exact_date': self.exact_date,
            'date': self.date,
            'description': self.description,
            'ref_no': self.ref_no,
            'balance': self.balance,
            'bank_id': self.bank_id,
            'person_id': self.person_id,
            'company_id': self.company_id
        }


class BankPayment(db.Model):
    __tablename__ = 'bank_payments'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    exact_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date = db.Column(db.Date, nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id'), nullable=True, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True, index=True)
    description = db.Column(db.String, nullable=True)
    ref_no = db.Column(db.String)
    bank_balance = db.Column(db.Float, nullable=True)
    bank_id = db.Column(db.Integer, db.ForeignKey('banks.id'), nullable=True, index=True)

    def to_json(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'exact_date': self.exact_date,
            'date': self.date,
            'person_id': self.person_id,
            'company_id': self.company_id,
            'description': self.description,
            'ref_no': self.ref_no,
            'bank_balance': self.bank_balance,
            'bank_id': self.bank_id
        }


class CompanyPayment(db.Model):
    __tablename__ = 'company_payments'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    exact_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date = db.Column(db.Date, nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True, index=True)
    description = db.Column(db.String, nullable=True)
    ref_no = db.Column(db.String)
    balance = db.Column(db.Float, nullable=True)
    bank_id = db.Column(db.Integer, db.ForeignKey('banks.id'), nullable=True, index=True)

    def to_json(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'exact_date': self.exact_date,
            'date': self.date,
            'company_id': self.company_id,
            'description': self.description,
            'ref_no': self.ref_no,
            'balance': self.balance,
            'bank_id': self.bank_id
        }


class Loan(db.Model):
    __tablename__ = 'loans'

    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id'), nullable=False, index=True)
    amount = db.Column(db.Integer)
    interest_rate = db.Column(db.Integer)
    start_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.Date, nullable=False)
    is_paid = db.Column(db.Boolean, default=False)

    def to_json(self):
        return {
            'id': self.id,
            'person_id': self.person_id,
            'amount': self.amount,
            'interest_rate': self.interest_rate,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'is_paid': self.is_paid
        }


class Expense(db.Model):
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    ref_no = db.Column(db.String)
    amount = db.Column(db.Integer)
    balance = balance = db.Column(db.Float, nullable=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)

    def to_json(self):
        return {
            'id': self.id,
            'description': self.description,
            'amount': self.amount,
            'balance': self.balance,
            'date': self.date
        }


class Investment(db.Model):
    __tablename__ = 'investments'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    ref_no = db.Column(db.String)
    amount = db.Column(db.Integer)
    balance = balance = db.Column(db.Float, nullable=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)

    def to_json(self):
        return {
            'id': self.id,
            'description': self.description,
            'amount': self.amount,
            'balance': self.balance,
            'date': self.date
        }


class Bank(db.Model):
    __tablename__ = 'banks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False,unique=True)
    balance_bfd = db.Column(db.Float, default=0.0)
    new_balance = db.Column(db.Float, default=0.0)
    payments = db.relationship('BankPayment', backref='bank')

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'balance_bfd': self.balance_bfd,
            'new_balance': self.new_balance,
            'payments': [payment.to_json() for payment in self.payments]
        }


class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    ref_no = db.Column(db.String)
    amount = db.Column(db.Float, default=0.0)
    description = db.Column(db.String, nullable=False)
    balance = db.Column(db.Float, default=0.0)

    def to_json(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'description': self.description,
            'balance': self.balance
        }

with app.app_context():
    db.create_all()