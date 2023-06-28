import pandas as pd,os
from flask import Flask
from models import db
from queries import Queries


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cooperative.db'
db.init_app(app)

query= Queries(db)

def log_report(report):
    with open("report.txt", 'a', encoding='utf-8') as f:
            f.write(f'{report}\n')

# processing input functions

def process_excel(filename):

    dataframe = pd.read_excel(filename)
    rows_to_update = dataframe.iloc[0:]
    return rows_to_update

def start_up(rows_to_update):
    for index, row in rows_to_update.iterrows():
        # Create a new record in the database for each row
        query.create_new_user(row['Name'],row['COY'],f'samade{row["S/N"]}@gmail.com',row['Phone'],row['BAL B/FWD'],row['Month-January'])

def create_loan(rows_to_update):
    for index, row in rows_to_update.iterrows():
         query.make_loan(row['COY'],row['Amount'])


# Function to generate the repayment schedule
def generate_repayment_schedule(person_id, loan_amount, interest_rate, start_date, end_date):
    # Calculate the number of months between the start date and end date
    num_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1

    # Calculate the total interest amount
    total_interest = (loan_amount * (int(interest_rate) / 100))

    # Calculate the monthly repayment amount
    monthly_repayment = (loan_amount + total_interest) / num_months

    # Generate the repayment schedule as a list of dictionaries
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


# Function to export the repayment schedule to Excel
def export_repayment_schedule_to_excel(repayment_schedule, person_id):
    # Create a DataFrame from the repayment schedule
    df_repayment_schedule = pd.DataFrame(repayment_schedule)

    # Generate a unique file name based on the person ID
    file_name = f"repayment_schedule_{person_id}.xlsx"
    file_path = os.path.join("./excel", file_name)

    # Create an Excel writer object
    writer = pd.ExcelWriter(file_path, engine='xlsxwriter')

    # Write the repayment schedule DataFrame to the Excel file
    df_repayment_schedule.to_excel(writer, sheet_name='Repayment Schedule', index=False)

    # Save the Excel file
    writer.close()

    return file_path

def save(rows_to_update):
    for index, row in rows_to_update.iterrows():
         query.save_amount(row['COY'],row['Amount'])


# processing ouputs functions

def create_individual_report(employee_id):

    person = query.get_person(employee_id) 
    df_person = pd.DataFrame([(person.id, person.is_admin, person.employee_id, person.name, person.email,
                                person.phone_no, person.savings, person.total_balance, person.loan_balance,
                                person.monthly_payment_amount, person.company_id) for person in person],
                              columns=['ID', 'Is Admin', 'Employee ID', 'Name', 'Email', 'Phone No', 'Savings',
                                       'Total Balance', 'Loan Balance', 'Monthly Payment Amount', 'Company ID'])
    
    writer = pd.ExcelWriter('cooperative_data.xlsx', engine='xlsxwriter')

    df_person.to_excel(writer, sheet_name='Persons', index=False)
    writer.close()
     

def create_full_report():
    # Fetch data from the database
    companies = query.get_companies()
    persons = query.get_persons()
    payments = query.get_payments()
    loans = query.get_loans()
    payments = query.get_payments()
    investments = query.get_investments()
    expenses = query.get_expenses()

    # Create dataframes from the fetched data
    # remember to add amount accumulated to the company

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

    # Create an Excel writer object
    writer = pd.ExcelWriter('cooperative_data.xlsx', engine='xlsxwriter')

    # Write dataframes to separate sheets in the Excel file
    df_companies.to_excel(writer, sheet_name='Companies', index=False)
    df_persons.to_excel(writer, sheet_name='Persons', index=False)
    df_payments.to_excel(writer, sheet_name='Payments', index=False)
    df_loans.to_excel(writer, sheet_name='Loans', index=False)
    df_expenses.to_excel(writer, sheet_name='Expenses', index=False)
    df_investments.to_excel(writer, sheet_name='Investments', index=False)

    # Save the Excel file
    writer.close()



with app.app_context():
    process_excel('./Cooperative 2022 Financial.xlsx')