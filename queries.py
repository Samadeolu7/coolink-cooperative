from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models import *
from datetime import datetime

def log_report(report):
    with open("report.txt", 'a', encoding='utf-8') as f:
            f.write(f'{report}\n')
class Queries():

    def __init__(self,db) -> None:
        self.db = db

    def create_new_user(self, name ,employee_id,phone_no , balance , loan_balance, email,company_id ):
        self.db.session.add(Person(name =name,employee_id=employee_id,email=email,
                                   total_balance=balance,loan_balance=loan_balance,
                                   phone_no=phone_no,balance_bfd =balance,company_id=company_id))
        self.db.session.commit()

    def create_new_company(self,name):
        self.db.session.add(Company(name=name))
        db.session.commit()

    def create_bank(self,name,balance):
        bank = Bank(name=name, balance_bfd=balance,new_balance=balance)#remember to add to form for admin or ask in meeting
        db.session.add(bank)
        db.session.commit()

    def save_amount(self,employee_id,amount,date,ref_no,bank_id,description=None):
        person = Person.query.filter_by(id=employee_id).first()
        bank = Bank.query.filter_by(id=bank_id).first()
        if person:
            person.total_balance += float(amount)

            saving_payment = SavingPayment(amount=amount, date=date, person_id=person.id,
                              exact_date=datetime.utcnow(),description=description,ref_no = ref_no,
                              balance =person.total_balance,
                              bank_id=bank.id)
            
            self.db.session.add(saving_payment)

            bank.new_balance +=  float(amount)
            bank_payment = BankPayment(amount=amount, date=date, person_id=person.id,
                              exact_date=datetime.utcnow(),description=description, ref_no=ref_no,
                                bank_balance=bank.new_balance,bank_id=bank.id)
            
            self.db.session.add(bank_payment)
     
            self.db.session.commit()

    def save_amount_company(self,employee_id,amount,date,ref_no,bank_id,description=None):
        person = Person.query.filter_by(id=employee_id).first()
        company = person.company
        
        if person:
            person.total_balance += float(amount)
            
            saving_payment = SavingPayment(amount=amount, date=date, person_id=person.id,
                              exact_date=datetime.utcnow(),description=description,ref_no = ref_no,
                              company_id=company.id,balance =person.total_balance)
            
            self.db.session.add(saving_payment)

            company.amount_accumulated +=  float(amount)
            company_payment = CompanyPayment(amount=amount,date=date,exact_date=datetime.utcnow(),
                                              description=description, ref_no=ref_no, company_id=company.id,
                                              balance=company.amount_accumulated)
            
            self.db.session.add(company_payment)

            self.db.session.commit()
          
    def make_loan(self,employee_id,amount,interest_rate,start_date,end_date,description,ref_no):
        person = Person.query.filter_by(employee_id=employee_id).first()
        if person:
            
            person.loan_balance += float(amount)
        
            loan = Loan(person_id=person.id,amount=amount,interest_rate=interest_rate,
                        start_date=start_date,end_date=end_date)
            self.db.session.add(loan)

            loan_payment = LoanPayment(amount=amount,exact_date=datetime.utc(),date= start_date,
                                       description = description,ref_no=ref_no,balance=person.loan_balance,
                                       person_id = person.id)
            self.db.session.add(loan_payment)

            
            interest_amount=float(amount) * (float(interest_rate)/100)
            person.loan_balance += interest_amount 
            interest_payment = LoanPayment(amount=interest_amount,exact_date=datetime.utc(),date= start_date,
                                       description = description,ref_no=ref_no,balance=person.loan_balance,
                                       person_id = person.id)
            
            self.db.session.add(interest_payment)

            
            last_entry = Income.query.order_by(Income.id.desc()).first()
            if last_entry:
                balance = last_entry.balance + interest_amount
                income = Income(amount=interest_amount,description=f'loan interest on {person.name}',balance=balance )
                self.db.session.add(income)
                
            else:
                income = Income(amount=interest_amount,description=f'loan interest on {person.name}',balance=interest_amount )
                self.db.session.add(income)
            

            bank = Bank.query.filter_by(id=1).first()

            if bank:
                bank.new_balance -= float(amount)
                bank_payment = BankPayment(amount=-1*amount, date=start_date, person_id=person.id,loan=True,
                              exact_date=datetime.utcnow(),description=f'loan given to {person.name}',
                              balance =person.loan_balance,bank_balance=bank.new_balance,
                              bank_id=bank.id)
            
                self.db.session.add(bank_payment)
                self.db.session.commit()

    def repay_loan(self,id,amount,date,bank_id,ref_no,description=None):
        person = Person.query.filter_by(id=id).first()
        if person:
            
            person.loan_balance -= float(amount)
            loan_payment = LoanPayment(amount=amount, date=date, person_id=person.id,
                              exact_date=datetime.utcnow(),description=description ,ref_no=ref_no,
                              balance =person.loan_balance, bank_id=bank.id)
            self.db.session.add(loan_payment)     

            bank = Bank.query.filter_by(id=bank_id).first()
            bank.new_balance +=  float(amount)
            
            bank_payment = BankPayment(amount=amount, date=date, person_id=person.id,exact_date=datetime.utcnow(),
                                       description=description,ref_no=ref_no, bank_balance=bank.new_balance,
                                        bank_id=bank.id)

            self.db.session.add(bank_payment)
            self.db.session.commit()

    def repay_loan_company(self,id,amount,date,ref_no,description=None):

        person = Person.query.filter_by(id=id).first()
        company = person.company
        if person:
            
            person.loan_balance -= float(amount)
            loan_payment = LoanPayment(amount=amount, date=date, person_id=person.id,
                              exact_date=datetime.utcnow(),description=description ,ref_no=ref_no,
                              balance =person.loan_balance,company_id=company.id)
            self.db.session.add(loan_payment)

            company.amount_accumulated +=  float(amount)            
            company_payment = CompanyPayment(amount=amount,date=date,exact_date=datetime.utcnow(),
                                              description=description, ref_no=ref_no, company_id=company.id,
                                              balance=company.amount_accumulated)

            self.db.session.add(company_payment)

            self.db.session.commit()

    def company_payment(self,company_id,amount,description,ref_no,bank_id):
        company = Company.query.filter_by(id=company_id).first()
        if company:
            company.amount_acumulated -= float(amount)
            company_payment = CompanyPayment(amount=-amount,date=date,exact_date=datetime.utcnow(),
                                              description=description, ref_no=ref_no,company_id=company.id,
                                              balance=company.amount_accumulated)
            self.db.session.add(company_payment)

        bank =Bank.query.filter_by(id=bank_id).first()
        if bank:
            bank.balance += float(amount)
            bank_payment = BankPayment(amount=amount, date=date,exact_date=datetime.utcnow(),
                                       description=description,ref_no=ref_no, bank_balance=bank.new_balance,
                                        bank_id=bank.id)
            self.db.session.add(bank_payment)

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

    def get_savings(self):
        payments = SavingPayment.query.all()
        return payments

    def get_individual_savings(self,person_id):
        payments = SavingPayment.query.filter_by(id=person_id).all()
        return payments
    
    def get_loans(self):
        loans = Loan.query.all()
        return loans
    
    def get_bank(self,bank_id):
        bank = Bank.query.get(bank_id=bank_id)
        return bank
    
    def get_banks(self):
        bank = Bank.query.all()
        return bank
    
    def get_income(self):
        loans = Income.query.all()
        return loans
    
    def get_person_loans(self,person_id):
        loans = Loan.query.filter_by(person_id=person_id).first()
        return loans
    
    def get_investments(self):
        investment = Investment.query.all
        return investment
    
    def get_expenses(self):
        expence = Expense.query.all
        return expence