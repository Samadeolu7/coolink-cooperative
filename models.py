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
    payments_made = db.relationship('Payment', backref='company_payer', lazy=True)
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
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    is_admin = db.Column(db.Boolean, default=False)
    employee_id = db.Column(db.String, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String)
    phone_no = db.Column(db.String)
    total_balance = db.Column(db.Float, default=0.0)
    loan_balance = db.Column(db.Float, default=0.0)
    loans = db.relationship('Loan', backref='person')
    payments_made = db.relationship('Payment', backref='payer', lazy=True)

    def to_json(self):
        return {
            'id': self.id,
            'is_admin': self.is_admin,
            'employee_id': self.employee_id,
            'name': self.name,
            'email': self.email,
            'phone_no': self.phone_no,
            'total_balance': self.total_balance,
            'loan_balance': self.loan_balance,
            'loans': [loan.to_json() for loan in self.loans],
            'payments_made': [payment.to_json() for payment in self.payments_made]
        }


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    exact_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date = db.Column(db.Date, nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id'), nullable=False, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True, index=True)
    description = db.Column(db.String, nullable=True)
    balance = db.Column(db.Float, nullable=True)
    bank_balance = db.Column(db.Float, nullable=True)
    loan = db.Column(db.Boolean, default=False)
    bank_id = db.Column(db.Integer, db.ForeignKey('banks.id'), nullable=True, index=True)

    def to_json(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'loan': self.loan,
            'date': self.date.isoformat(),
            'person_id': self.person_id
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
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'is_paid': self.is_paid
        }


class Expense(db.Model):
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    amount = db.Column(db.Integer)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)

    def to_json(self):
        return {
            'id': self.id,
            'description': self.description,
            'amount': self.amount,
            'date': self.date.isoformat()
        }


class Investment(db.Model):
    __tablename__ = 'investments'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    amount = db.Column(db.Integer)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)

    def to_json(self):
        return {
            'id': self.id,
            'description': self.description,
            'amount': self.amount,
            'date': self.date.isoformat()
        }


class Bank(db.Model):
    __tablename__ = 'banks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    balance_bfd = db.Column(db.Float, default=0.0)
    new_balance = db.Column(db.Float, default=0.0)
    payments = db.relationship('Payment', backref='bank')

    

    def to_json(self):
        return {
            'id': self.id,
            'description': self.name,
            'amount': self.balance,
        }


class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, default = 0.0)
    description = db.Column(db.String, nullable = False)
    balance = db.Column(db.Float, default = 0.0)


with app.app_context():
    db.create_all()