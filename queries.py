from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models import Company, Person, Payment , Loan, Expense,Investment
from datetime import datetime


class Queries():

    def __init__(self,db) -> None:
        self.db = db

    def create_new_user(self, name ,company_id, email, phone_no , balance , savings,is_admin=False):
        self.db.session.add(Person(name =name,employee_id=company_id,email=email,total_balance=balance,savings=savings,is_admin=is_admin,phone_no=phone_no))
        self.db.session.commit()

    def create_new_company(self,name):
        self.db.session.add(Company(name=name))

    def save_amount(self,employee_id,amount):
        person = Person.query.filter_by(id=employee_id).first()
        if person:
            person.total_balance += float(amount)
            self.db.session.commit()
            
            payment = Payment(amount=amount, date=datetime.utcnow(), person_id=person.id)
            self.db.session.add(payment)
            self.db.session.commit()

            company = Company.query.filter_by(id = Person.company_id).first()
            company.amount_accumulated += float(amount)
            self.db.session.add(company)
            self.db.session.commit()



    def make_loan(self,employee_id,amount,interest_rate,start_date,end_date):
        person = Person.query.filter_by(employee_id=employee_id).first()
        if person:
            person.loan_balance += float(amount)
            self.db.session.commit()

            loan = Loan(
            person_id=person.id,
            amount=amount,
            interest_rate=interest_rate,
            start_date=start_date,
            end_date=end_date
        )
            self.db.session.add(loan)
            self.db.session.commit()

    def repay_loan(self,employee_id,amount):
        person = Person.query.filter_by(employee_id=employee_id)
        if person:
            person.loan_balance -= amount
            self.db.session.commit()

            payment =Payment(amount=amount,date=datetime.utcnow(),person=person.id,loan=True)
            self.db.session.add(payment)
            self.db.session.commit()

            company = Company.query.filter_by(id = Person.company_id)
            company.amount_accumulated += amount



    def get_companies(self):
        company = Company.query.all()

        return company
    
    def get_persons(self):
        person = Person.query.all()
        return person
    
    def get_person(self,employee_id):
        person = Person.query.filter_by(employee_id=employee_id)
        return person

    def get_payments(employee_id):
        payments = Payment.query.filter_by(Person_id=employee_id)
        return payments

    def get_loans(employee_id):
        loans = Loan.query.filter_by(employee_id=employee_id)
        return loans
    
    def get_investments():
        investment = Investment.query.all
        return investment
    
    def get_expenses():
        expence = Expense.query.all
        return expence