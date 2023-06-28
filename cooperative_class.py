from datetime import datetime


class Cooperative:
    def __init__(self, name):
        self.name = name
        self.companies = []
        self.persons = []
        self.payments = []
        self.loans = []
        self.expenses = []
        self.investments = []

    class Company:
        def __init__(self, name):
            self.id = None
            self.name = name
            self.employees = []

    class Person:
        def __init__(self, is_admin, employee_id, name, email, phone_no):
            self.id = None
            self.is_admin = is_admin
            self.employee_id = employee_id
            self.name = name
            self.email = email
            self.phone_no = phone_no
            self.savings = 0.0
            self.total_balance = 0.0
            self.loan_balance = 0.0
            self.monthly_payment_amount = 0.0
            self.payment_history = []
            self.company_id = None

    class Payment:
        def __init__(self, amount, loan):
            self.id = None
            self.amount = amount
            self.loan = loan
            self.date = datetime.utcnow()
            self.person_id = None

    class Loan:
        def __init__(self, amount, interest_rate, start_date, end_date):
            self.id = None
            self.amount = amount
            self.interest_rate = interest_rate
            self.start_date = start_date
            self.end_date = end_date
            self.is_paid = False
            self.person_id = None

    class Expense:
        def __init__(self, description, amount):
            self.id = None
            self.description = description
            self.amount = amount
            self.date = datetime.utcnow()

    class Investment:
        def __init__(self, description, amount):
            self.id = None
            self.description = description
            self.amount = amount
            self.date = datetime.utcnow()

    # Company operations
    def add_company(self, name):
        company = self.Company(name)
        self.companies.append(company)
        return company

    def get_companies(self):
        return self.companies

    # Person operations
    def add_person(self, is_admin, employee_id, name, email, phone_no):
        person = self.Person(is_admin, employee_id, name, email, phone_no)
        self.persons.append(person)
        return person

    def get_persons(self):
        return self.persons

    # Payment operations
    def add_payment(self, amount, loan, person_id):
        payment = self.Payment(amount, loan)
        payment.person_id = person_id
        self.payments.append(payment)
        return payment

    def get_payments(self):
        return self.payments

    # Loan operations
    def add_loan(self, amount, interest_rate, start_date, end_date, person_id):
        loan = self.Loan(amount, interest_rate, start_date, end_date)
        loan.person_id = person_id
        self.loans.append(loan)
        return loan

    def get_loans(self):
        return self.loans

    # Expense operations
    def add_expense(self, description, amount):
        expense = self.Expense(description, amount)
        self.expenses.append(expense)
        return expense

    def get_expenses(self):
        return self.expenses

    # Investment operations
    def add_investment(self, description, amount):
        investment = self.Investment(description, amount)
        self.investments.append(investment)
        return investment

    def get_investments(self):
        return self.investments

    # Other utility methods
    def get_person_by_id(self, person_id):
        for person in self.persons:
            if person.id == person_id:
                return person
        return None

    def calculate_total_savings(self):
        total_savings = sum(person.savings for person in self.persons)
        return total_savings

    def calculate_total_loan_balance(self):
        total_loan_balance = sum(person.loan_balance for person in self.persons)
        return total_loan_balance

    def calculate_total_expenses(self):
        total_expenses = sum(expense.amount for expense in self.expenses)
        return total_expenses

    def calculate_total_investments(self):
        total_investments = sum(investment.amount for investment in self.investments)
        return total_investments


# Example usage:
coop = Cooperative("My Cooperative")

company1 = coop.add_company("Company A")
company2 = coop.add_company("Company B")

person1 = coop.add_person(False, 12345, "John Doe", "john@example.com", "1234567890")
person1.company_id = company1.id

person2 = coop.add_person(False, 54321, "Jane Smith", "jane@example.com", "9876543210")
person2.company_id = company2.id

payment1 = coop.add_payment(100.0, False, person1.id)
payment2 = coop.add_payment(200.0, False, person2.id)

loan1 = coop.add_loan(1000, 5, datetime(2023, 1, 1), datetime(2023, 6, 30), person1.id)
loan2 = coop.add_loan(2000, 7, datetime(2023, 2, 1), datetime(2023, 7, 31), person2.id)

expense1 = coop.add_expense("Office Supplies", 500)
expense2 = coop.add_expense("Rent", 1000)

investment1 = coop.add_investment("Stocks", 5000)
investment2 = coop.add_investment("Bonds", 3000)

# Retrieving data
companies = coop.get_companies()
persons = coop.get_persons()
payments = coop.get_payments()
loans = coop.get_loans()
expenses = coop.get_expenses()
investments = coop.get_investments()

# Perform calculations
total_savings = coop.calculate_total_savings()
total_loan_balance = coop.calculate_total_loan_balance()
total_expenses = coop.calculate_total_expenses()
total_investments = coop.calculate_total_investments()

print("Total Savings:", total_savings)
print("Total Loan Balance:", total_loan_balance)
print("Total Expenses:", total_expenses)
print("Total Investments:", total_investments)
