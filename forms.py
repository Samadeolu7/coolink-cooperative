from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, BooleanField, IntegerField, DateField, SubmitField
from wtforms.validators import DataRequired, Email
from flask import Flask
from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)


class CompanyForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Submit')


class BankForm(FlaskForm):
    name = StringField('Name',validators=[DataRequired()] )
    balance = FloatField('Bank Balance')


class PersonForm(FlaskForm):
    is_admin = BooleanField('Is Admin')
    employee_id = StringField('Employee ID', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_no = StringField('Phone No')
    total_balance = FloatField('Total Balance')
    loan_balance = FloatField('Loan Balance')
    company_id = IntegerField('Company ID', validators=[DataRequired()])
    submit = SubmitField('Submit')


class PaymentForm(FlaskForm):
    amount = DecimalField('Amount', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    payment_type = SelectField('Payment Type', choices=[('savings', 'Savings'), ('loan', 'Loan')], validators=[DataRequired()])
    person_id = SelectField('Person', coerce=int, validators=[DataRequired()])
    description = StringField('Description')
    submit = SubmitField('Submit')


class LoanForm(FlaskForm):
    employee_id = StringField('Employee ID', validators=[DataRequired()])
    amount = IntegerField('Amount', validators=[DataRequired()])
    interest_rate = SelectField('Interest Rate', choices=[(5, '5%'), (10, '10%'), (15, '15%')], validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    submit = SubmitField('Submit')


class ExpenseForm(FlaskForm):
    description = StringField('Description', validators=[DataRequired()])
    amount = IntegerField('Amount', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    submit = SubmitField('Submit')


class InvestmentForm(FlaskForm):
    description = StringField('Description', validators=[DataRequired()])
    amount = IntegerField('Amount', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    submit = SubmitField('Submit')