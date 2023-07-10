from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cooperative.db'
db = SQLAlchemy(app)


class Company(db.Model):
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount_accumulated = db.Column(db.Float, default=0.0)
    payments_made = db.relationship('BankPayment', backref='company_payer', lazy=True)
    employees = db.relationship('Person', backref='company', lazy=True)
    
    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'employees': [employee.to_json() for employee in self.employees]
        }
    

class Person(db.Model):
    __tablename__ = 'persons'

    id = db.Column(db.Integer, primary_key=True)
    # password = db.Column(db.String, nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    # group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    employee_id = db.Column(db.String, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String,nullable=True)
    phone_no = db.Column(db.String)
    balance_bfd = db.Column(db.Float, default=0.0)
    total_balance = db.Column(db.Float, default=0.0)
    loan_balance = db.Column(db.Float, default=0.0)
    loan_balance_bfd = db.Column(db.Float, default=0.0)
    loans = db.relationship('Loan', backref='person')
    payments_made = db.relationship('SavingPayment', backref='payer', lazy=True)
    loan_payments_made = db.relationship('LoanPayment', backref='payer', lazy=True)



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


class Loan(db.Model):
    __tablename__ = 'loans'

    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id'), nullable=False, index=True)
    amount = db.Column(db.Integer)
    interest_rate = db.Column(db.Integer)
    start_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.Date, nullable=False)
    is_paid = db.Column(db.Boolean, default=False)



class Expense(db.Model):
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    amount = db.Column(db.Integer)
    balance = balance = db.Column(db.Float, nullable=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)


class Investment(db.Model):
    __tablename__ = 'investments'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    amount = db.Column(db.Integer)
    balance = balance = db.Column(db.Float, nullable=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)


class Bank(db.Model):
    __tablename__ = 'banks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    balance_bfd = db.Column(db.Float, default=0.0)
    new_balance = db.Column(db.Float, default=0.0)
    payments = db.relationship('BankPayment', backref='bank')


class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, default = 0.0)
    description = db.Column(db.String, nullable = False)
    balance = db.Column(db.Float, default = 0.0)


with app.app_context():
    db.create_all()