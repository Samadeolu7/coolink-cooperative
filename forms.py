from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, PasswordField, IntegerField, DateField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp
from flask import Flask
from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional

app = Flask(__name__)


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8),
        EqualTo('confirm_new_password', message='Passwords must match'),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$', message='Password must include capital letters, numbers, and symbols')
    ])
    confirm_new_password = PasswordField('Confirm New Password', validators=[DataRequired()])
    submit = SubmitField('Change Password')


class LoginForm(FlaskForm):
    identifier = StringField('Email', validators=[ DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


class CompanyForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Submit')
    balance_bfd = FloatField('Balance B/FWD')


class BankForm(FlaskForm):
    name = StringField('Name',validators=[DataRequired()] )
    balance = FloatField('Balance B/FWD')


class PersonForm(FlaskForm):
    
    employee_id = StringField('Employee ID', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[ Email()])
    phone_no = StringField('Phone No',validators=[DataRequired()])
    total_balance = FloatField('Balance B/FWD')
    loan_balance = FloatField('Loan Balance')
    company_id = IntegerField('Company ID', validators=[DataRequired()])
    submit = SubmitField('Submit')


class MakePaymentForm(FlaskForm):
    amount = DecimalField('Amount', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    payment_type = SelectField('Payment Type', choices=[('savings', 'Savings'), ('loan', 'Loan')], validators=[DataRequired()])
    bank = SelectField('Bank',coerce=int, validators=[DataRequired()])
    person_id = SelectField('Person', coerce=int, validators=[DataRequired()])
    description = StringField('Description')
    ref_no = StringField('Ref Number', validators=[DataRequired()])
    submit = SubmitField('Submit')

class PaymentForm(FlaskForm):
    amount = DecimalField('Amount', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    payment_type = SelectField('Payment Type', choices=[], validators=[DataRequired()])
    bank = SelectField('Bank',coerce=int, validators=[DataRequired()])
    description = StringField('Description')
    ref_no = StringField('Ref Number', validators=[DataRequired()])
    submit = SubmitField('Submit')

class LoanForm(FlaskForm):
    employee_id = StringField('Employee ID', validators=[DataRequired()])
    amount = IntegerField('Amount', validators=[DataRequired()])
    interest_rate = SelectField('Interest Rate', choices=[(5, '5%'), (10, '10%'), (15, '15%')], validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    description = StringField('Description')
    submit = SubmitField('Submit')


class ExpenseForm(FlaskForm):
    sub_account = SelectField('Sub-Select Account', choices=[], coerce=int) #change name to main account
    amount = FloatField('Amount', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    description = StringField('Description')
    main_account = SelectField('Select Account', choices=[(1,'Expense'),(2,'Asset'),(3,'Investment'),(4,'Liability')], coerce=int) #change name to sub-account
    bank = SelectField('Bank', choices=[], coerce=int)
    ref_no = StringField('Reference Number')


# class InvestmentForm(FlaskForm):
#     name = StringField('Name', validators=[DataRequired()])
#     amount = FloatField('Amount', validators=[DataRequired()])
#     date = DateField('Date', validators=[DataRequired()])
#     description = StringField('Description')
#     existing_investment = SelectField('Existing Expense', choices=[], coerce=int)
#     bank = StringField('Bank')
#     ref_no = StringField('Reference Number')


class UploadForm(FlaskForm):
    description = StringField('Description', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    submit = SubmitField('Submit')


class IncomeForm(FlaskForm):
    name = SelectField('Sub-Account', choices=[('loan','Loan Application Form'),('form','Registration Form')], validators=[DataRequired()])
    amount = DecimalField('Amount', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    bank = SelectField('Bank',coerce=int, validators=[DataRequired()])
    description = StringField('Description')
    ref_no = StringField('Ref Number', validators=[DataRequired()])
    submit = SubmitField('Submit')

class WithdrawalForm(FlaskForm):
    person = SelectField('Select Person', coerce=int, validators=[DataRequired()])
    balance = FloatField('Available Balance', render_kw={'readonly': True})
    description = StringField('Description')
    ref_no = StringField('Ref Number', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    amount = FloatField('Withdraw Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Withdraw')

class RoleAssignmentForm(FlaskForm):
    person = SelectField('Select Person', choices=[], validators=[DataRequired()])
    role = SelectField('Role', choices=[], validators=[DataRequired()])
    submit = SubmitField('Assign Role')

class DateFilterForm(FlaskForm):
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[Optional()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Apply Filter')

class SearchForm(FlaskForm):
    search_query = StringField('Search')
    submit = SubmitField('Search')

class LedgerAdminForm(FlaskForm):
    ledger = SelectField('Select Ledger',choices=[(1,'Asset'),(2,'Expenses'),(3,'Income'),(4,'Liabilities'),(5,'Investments')],validators=[DataRequired()])
    submit = SubmitField('Create New Ledger')

class LedgerForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    submit = SubmitField('Create')

class ResetPasswordForm(FlaskForm):
    person = SelectField('Select Person', choices=[], validators=[DataRequired()])
    submit = SubmitField('Reset Password')
