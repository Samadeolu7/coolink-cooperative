from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models import Company, Person, Payment , Loan, Expense,Investment,Bank,Income
from datetime import datetime

def log_report(report):
    with open("report.txt", 'a', encoding='utf-8') as f:
            f.write(f'{report}\n')
class Queries():

    def __init__(self,db) -> None:
        self.db = db

    def create_new_user(self, name ,company_id, email, phone_no , balance , savings,is_admin=False):
        self.db.session.add(Person(name =name,employee_id=company_id,email=email,total_balance=balance,savings=savings,is_admin=is_admin,phone_no=phone_no))
        self.db.session.commit()

    def create_new_company(self,name):
        self.db.session.add(Company(name=name))

    def save_amount(self,employee_id,amount,date,description=None):
        person = Person.query.filter_by(id=employee_id).first()
        bank = Bank.query.first()
        if person:
            person.total_balance += float(amount)

            bank.new_balance +=  float(amount)
            
            payment = Payment(amount=amount, date=date, person_id=person.id,
                              exact_date=datetime.utcnow(),description=description,
                              balance =person.total_balance,bank_balance=bank.new_balance,
                              bank_id=bank.id)
            

            self.db.session.add(payment)
            self.db.session.commit()

            

    def make_loan(self,employee_id,amount,interest_rate,start_date,end_date):
        person = Person.query.filter_by(employee_id=employee_id).first()
        if person:
            loan_repay = float(amount) +( float(amount) * (float(interest_rate)/100))
            person.loan_balance += loan_repay 
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

            amount=loan_repay-float(amount)
            last_entry = Income.query.order_by(Income.id.desc()).first()
            if last_entry:
                balance = last_entry.balance + amount
                income = Income(amount=amount,description=f'loan intrest on {person.name}',balance=balance )
                self.db.session.add(income)
                self.db.session.commit()
            else:
                income = Income(amount=amount,description=f'loan intrest on {person.name}',balance=amount )
                self.db.session.add(income)
                self.db.session.commit()

        bank = Bank.query.filter_by(id=1).first()

        if bank:
            bank.balance -= float(amount)
            self.db.session.commit()

    def repay_loan(self,id,amount,date,description=None):
        person = Person.query.filter_by(id=id).first()
        if person:
            log_report('what is going on')
            person.loan_balance -= float(amount)
            self.db.session.commit()

            payment =Payment(amount=amount,exact_date=datetime.utcnow(),date=date,person_id=person.id,loan=True,description=description,balance =person.loan_balance)
            self.db.session.add(payment)
            self.db.session.commit()

            company = Company.query.filter_by(id = Person.company_id).first()
            company.amount_accumulated += float(amount)
            self.db.session.commit()


    def company_payment(self,company_id,amount):
        company = Company.query.filter_by(id=company_id).first()
        if company:
            company.amount_acumulated -= float(amount)
            self.db.session.commit()
        bank =Bank.query.filter_by(id=1).first()
        if bank:
            bank.balance += float(amount)
            self.db.session.commit()

    def get_companies(self):
        company = Company.query.all()

        return company
    
    def get_persons(self):
        person = Person.query.all()
        return person
    
    def get_person(self,person_id):
        person = Person.query.filter_by(id=person_id).first()
        return person

    def get_payments(self,employee_id):
        payments = Payment.query.filter_by(person_id=employee_id)
        return payments

    def get_loans(employee_id):
        loans = Loan.query.filter_by(employee_id=employee_id).first()
        return loans
    
    def get_investments():
        investment = Investment.query.all
        return investment
    
    def get_expenses():
        expence = Expense.query.all
        return expence