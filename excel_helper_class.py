import pandas as pd
from flask import Flask
from models import db
from queries import Queries

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cooperative.db'
db.init_app(app)

class CooperativeProcessor:
    def __init__(self, filename):
        self.filename = filename
        self.dataframe = None
        self.query = Queries(db)

    def process_excel(self):
        self.dataframe = pd.read_excel(self.filename)
        rows_to_update = self.dataframe.iloc[0:]
        return rows_to_update

    def start_up(self, rows_to_update):
        new_users = []
        for index, row in rows_to_update.iterrows():
            user_data = {
                'name': row['Name'],
                'coy': row['COY'],
                'email': f'samade{row["S/N"]}@gmail.com',
                'phone': row['Phone'],
                'balance': row['BAL B/FWD'],
                'month': row['Month-January']
            }
            new_users.append(user_data)

        # Create new records in the database in batch
        self.query.create_new_users(new_users)

    def create_loan(self, rows_to_update):
        loans = []
        for index, row in rows_to_update.iterrows():
            loan_data = {
                'coy': row['COY'],
                'amount': row['Amount']
            }
            loans.append(loan_data)

        # Make loans in the database in batch
        self.query.make_loans(loans)

    def create_repayment_schedule(self, rows_to_update):
        repayment_schedules = []
        for index, row in rows_to_update.iterrows():
            person_id = self.query.get_person_id(row['COY'])
            loan_amount = row['Amount']
            interest_rate = row['Interest Rate'] / 100
            start_date = row['Start Date']
            end_date = row['End Date']

            repayment_schedule = self.generate_repayment_schedule(loan_amount, interest_rate, start_date, end_date)
            repayment_schedules.append((person_id, repayment_schedule))

        # Save the repayment schedules to the database in batch or perform any other required actions
        self.query.save_repayment_schedules(repayment_schedules)

    def generate_repayment_schedule(self, loan_amount, interest_rate, start_date, end_date):
        num_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
        monthly_interest_rate = interest_rate / 12
        monthly_repayment = loan_amount * monthly_interest_rate / (1 - (1 + monthly_interest_rate) ** -num_months)

        repayment_schedule = []
        for i in range(num_months):
            installment_number = i + 1
            due_date = start_date + pd.DateOffset(months=i)
            repayment_amount = monthly_repayment
            repayment_schedule.append({
                'Installment Number': installment_number,
                'Due Date': due_date,
                'Repayment Amount': repayment_amount
            })

        return repayment_schedule

    def export_repayment_schedule_to_excel(self, repayment_schedule, filename):
        df_repayment_schedule = pd.DataFrame(repayment_schedule)
        writer = pd.ExcelWriter(filename, engine='xlsxwriter')
        df_repayment_schedule.to_excel(writer, sheet_name='Repayment Schedule', index=False)
        writer.save()

    def save(self, rows_to_update):
        amounts = []
        for index, row in rows_to_update.iterrows():
            amount_data = {
                'coy': row['COY'],
                'amount': row['Amount']
            }
            amounts.append(amount_data)

        # Save amounts to the database in batch
        self.query.save_amounts(amounts)

    def process_input(self):
        rows_to_update = self.process_excel()
        self.start_up(rows_to_update)
        self.create_loan(rows_to_update)
        self.create_repayment_schedule(rows_to_update)
        self.save(rows_to_update)

    def create_individual_report(self, employee_id):
        person = self.query.get_person(employee_id)
        df_person = pd.DataFrame([(person.id, person.is_admin, person.employee_id, person.name, person.email,
                                   person.phone_no, person.savings, person.total_balance, person.loan_balance,
                                   person.monthly_payment_amount, person.company_id) for person in person],
                                 columns=['ID', 'Is Admin', 'Employee ID', 'Name', 'Email', 'Phone No', 'Savings',
                                          'Total Balance', 'Loan Balance', 'Monthly Payment Amount', 'Company ID'])

        writer = pd.ExcelWriter('cooperative_data.xlsx', engine='xlsxwriter')
        df_person.to_excel(writer, sheet_name='Persons', index=False)
        writer.save()

    def create_full_report(self):
        companies = self.query.get_companies()
        persons = self.query.get_persons()
        payments = self.query.get_payments()
        loans = self.query.get_loans()
        investments = self.query.get_investments()
        expenses = self.query.get_expenses()

        df_companies = pd.DataFrame([(company.id, company.name) for company in companies], columns=['ID', 'Name'])
        df_persons = pd.DataFrame([(person.id, person.is_admin, person.employee_id, person.name, person.email,
                                    person.phone_no, person.savings, person.total_balance, person.loan_balance,
                                    person.monthly_payment_amount, person.company_id) for person in persons],
                                  columns=['ID', 'Is Admin', 'Employee ID', 'Name', 'Email', 'Phone No', 'Savings',
                                           'Total Balance', 'Loan Balance', 'Monthly Payment Amount', 'Company ID'])
        df_payments = pd.DataFrame([(payment.id, payment.amount, payment.loan, payment.date, payment.person_id)
                                    for payment in payments],
                                   columns=['ID', 'Amount', 'Loan', 'Date', 'Person ID'])
        df_loans = pd.DataFrame([(loan.id, loan.person_id, loan.amount, loan.interest_rate, loan.start_date, loan.end_date,
                                  loan.is_paid) for loan in loans],
                                columns=['ID', 'Person ID', 'Amount', 'Interest Rate', 'Start Date', 'End Date', 'Is Paid'])
        df_expenses = pd.DataFrame([(expense.id, expense.description, expense.amount, expense.date)
                                    for expense in expenses],
                                   columns=['ID', 'Description', 'Amount', 'Date'])
        df_investments = pd.DataFrame([(investment.id, investment.description, investment.amount, investment.date)
                                       for investment in investments],
                                      columns=['ID', 'Description', 'Amount', 'Date'])

        writer = pd.ExcelWriter('cooperative_data.xlsx', engine='xlsxwriter')
        df_companies.to_excel(writer, sheet_name='Companies', index=False)
        df_persons.to_excel(writer, sheet_name='Persons', index=False)
        df_payments.to_excel(writer, sheet_name='Payments', index=False)
        df_loans.to_excel(writer, sheet_name='Loans', index=False)
        df_expenses.to_excel(writer, sheet_name='Expenses', index=False)
        df_investments.to_excel(writer, sheet_name='Investments', index=False)
        writer.save()

# Example usage:
processor = CooperativeProcessor('./Cooperative 2022 Financial.xlsx')
processor.process_input()
processor.create_individual_report(123)
processor.create_full_report()
