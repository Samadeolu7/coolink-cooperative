from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from models import *
from datetime import datetime
import string
import random
import bcrypt
import csv


def log_report(report):
    with open("report.txt", "a", encoding="utf-8") as f:
        f.write(f"{report}\n")


class Queries:
    def __init__(self, db) -> None:
        self.db = db
        self.salt = bcrypt.gensalt()

    # create data
    def generate_password(self, length=12):
        characters = string.ascii_letters + string.digits + string.punctuation
        password = "".join(random.choice(characters) for _ in range(length))
        return password

    def hash_password(self, password):
        salt = self.salt
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed_password.decode("utf-8")

    def create_new_user(
        self,
        name,
        employee_id,
        phone_no,
        balance,
        loan_balance,
        email,
        company_id,
        role_id=4,
    ):
        try:
            password = self.generate_password()
            hashed_password = self.hash_password(password)
            self.db.session.add(
                Person(
                    name=name,
                    employee_id=employee_id,
                    email=email,
                    password=hashed_password,
                    available_balance=balance,
                    loan_balance=loan_balance,
                    loan_balance_bfd=loan_balance,
                    phone_no=phone_no,
                    balance_bfd=balance,
                    company_id=company_id,
                    role_id=role_id,
                )
            )
            self.db.session.commit()
            # create .csv file
            with open(
                f"credentials/{employee_id}_credentials.csv", "w", newline=""
            ) as file:
                writer = csv.writer(file)
                writer.writerow(["Username", "Password"])
                writer.writerow([f"{employee_id} or {email}", password])
        except Exception as e:
            db.session.rollback()
            if "UNIQUE constraint failed: person.employee_id" in str(e):
                return "Employee ID already exists"
            elif "UNIQUE constraint failed: person.email" in str(e):
                return "Email already exists"
            else:
                return str(e)

        return file.name

    def change_password(self, user, password, new_password):
        if bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
            hashed_new_password = bcrypt.hashpw(new_password.encode("utf-8"), self.salt)
            user.password = hashed_new_password
            db.session.commit()
            return True
        else:
            return False

    def edit_profile(self, person_id, email, phone_no, company_id):
        try:
            # Get the user's person record based on the selected person_id
            person = Person.query.get(person_id)
            # Update user's profile information
            person.email = email
            person.phone_no = phone_no
            person.company_id = company_id
            # Commit the changes to the database
            db.session.commit()

            return True  # Indicate success
        except Exception as e:
            print(e)  # Handle or log the error
            db.session.rollback()  # Rollback changes on error
            return False  # Indicate failure

    def get_user(self, identifier):
        return Person.query.filter(
            or_(Person.email == identifier, Person.employee_id == identifier)
        ).first()

    def get_ledger_report(self, ledger, ledger_id):
        if ledger == "asset":
            return Asset.query.filter_by(id=ledger_id).first()
        elif ledger == "expense":
            return Expense.query.filter_by(id=ledger_id).first()
        elif ledger == "liability":
            return Liability.query.filter_by(id=ledger_id).first()
        elif ledger == "investment":
            return Investment.query.filter_by(id=ledger_id).first()
        elif ledger == "income":
            return Income.query.filter_by(id=ledger_id).first()

    def validate_password(self, email, password):
        user_password = (
            self.db.session.query(Person).filter(Person.email == email).first()
        )
        if user_password.check_password(password):
            return True
        else:
            return False

    def create_new_company(self, name, balance_bfd):
        try:
            self.db.session.add(
                Company(
                    name=name, balance_bfd=balance_bfd, amount_accumulated=balance_bfd
                )
            )
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return str(e)

    def create_bank(self, name, balance):
        try:
            bank = Bank(
                name=name, balance_bfd=balance, new_balance=balance
            )  # remember to add to form for admin or ask in meeting
            db.session.add(bank)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return str(e)

    def save_amount(self, employee_id, amount, date, ref_no, bank_id, description=None):
        try:
            person = Person.query.filter_by(id=employee_id).first()
            bank = Bank.query.filter_by(id=bank_id).first()
            if person:
                person.available_balance += float(amount)

                saving_payment = SavingPayment(
                    amount=amount,
                    date=date,
                    person_id=person.id,
                    exact_date=datetime.utcnow(),
                    description=description,
                    ref_no=ref_no,
                    balance=person.available_balance,
                    bank_id=bank.id,
                )

                self.db.session.add(saving_payment)

                bank.new_balance += float(amount)
                bank_payment = BankPayment(
                    amount=amount,
                    date=date,
                    person_id=person.id,
                    exact_date=datetime.utcnow(),
                    description=description,
                    ref_no=ref_no,
                    bank_balance=bank.new_balance,
                    bank_id=bank.id,
                )

                self.db.session.add(bank_payment)

                self.db.session.commit()
        except Exception as e:
            self.db.session.rollback()
            return str(e)

    def add_transaction(self, id, sub_id, amount, date, ref_no, bank_id, description):
        if id == 1:
            self.add_asset(sub_id, amount, date, ref_no, bank_id, description)
        elif id == 2:
            self.add_expense(sub_id, amount, date, ref_no, bank_id, description)
        elif id == 3:
            self.add_investment(sub_id, amount, date, ref_no, bank_id, description)
        elif id == 4:
            self.add_liability(sub_id, amount, date, ref_no, bank_id, description)


    
    def registeration_payment(
        self, id, amount, date, ref_no, bank_id, description, loan=False,guarantors=[]
    ):
        try:
            person = Person.query.filter_by(id=id).first()
            if person:
    
                form_payment = LoanFormPayment(name=person.name,loan_amount=amount,person_id=person.id,guarantors=guarantors)
                self.db.session.add(form_payment)

                if loan:
                    name = "Loan Application Form"

                income = Income.query.filter_by(name=name).first()
                self.add_income(
                     income, amount, date, ref_no, bank_id, description
                )
                self.db.session.commit()
                return True
        except Exception as e:
            self.db.session.rollback()
            return str(e)
        
    def update_loan(self, loan_id, amount, date, ref_no, bank_id, description, guarantors=[]):
        try:
            loan = LoanFormPayment.query.get(loan_id)

            if loan:
                # Update the loan record with the new values
                loan.loan_amount = amount
                loan.date = date
                loan.ref_no = ref_no
                loan.bank_id = bank_id
                loan.description = description

                # Clear existing guarantors and add new ones
                loan.guarantors.clear()
                for guarantor in guarantors:
                    loan.guarantors.append(guarantor)

                self.db.session.commit()
                return True
            else:
                return False  # Loan record with the given loan_id not found
        except Exception as e:
            self.db.session.rollback()
            return str(e)
        
        
    def give_consent(self, loan, person, amount):
        try:
            existing_contributions = GuarantorContribution.query.filter_by(
            loan_form_payment_id=loan.id,
            guarantor_id=person.id
            ).first()

            if existing_contributions is None:
                loan.consent += 1
                # Update the guarantor_amount
                loan.guarantor_amount += float(amount)
                loan.move_to_loan()

                # Create a new GuarantorContribution record to track the contribution
                contribution = GuarantorContribution(loan_form_payment=loan, guarantor=person, contribution_amount=float(amount))
                db.session.add(contribution)

                person.available_balance -= float(amount)
                person.balance_withheld += float(amount)
                db.session.commit()
                log_report(loan.loan)
                return True
            else:
                return "You have already given consent"
        except Exception as e:
            db.session.rollback()
            return str(e)

            

    def add_income(self, id, amount, date, ref_no, bank_id, description):
        bank = Bank.query.filter_by(id=bank_id).first()
        if bank:
            income = id
            income.balance += float(amount)
            income_payment = IncomePayment(
                amount=float(amount),
                date=date,
                exact_date=datetime.utcnow(),
                description=description,
                ref_no=ref_no,
                balance=income.balance,
                bank_id=bank.id,
                income_id=income.id,
            )

            self.db.session.add(income_payment)

            bank.new_balance += float(amount)
            bank_payment = BankPayment(
                amount=amount,
                date=date,
                exact_date=datetime.utcnow(),
                description=description,
                ref_no=ref_no,
                bank_balance=bank.new_balance,
                bank_id=bank.id,
            )

            self.db.session.add(bank_payment)

            self.db.session.commit()

    def add_expense(self, id, amount, date, ref_no, bank_id, description=None):
        bank = Bank.query.filter_by(id=bank_id).first()
        if bank:
            expense = Expense.query.filter_by(id=id).first()
            expense.balance += float(amount)
            expense_payment = ExpensePayment(
                amount=float(amount),
                date=date,
                exact_date=datetime.utcnow(),
                description=description,
                ref_no=ref_no,
                balance=expense.balance,
                bank_id=bank.id,
                expense_id=id,
            )

            self.db.session.add(expense_payment)

            bank.new_balance -= float(amount)
            bank_payment = BankPayment(
                amount=-amount,
                date=date,
                exact_date=datetime.utcnow(),
                description=description,
                ref_no=ref_no,
                bank_balance=bank.new_balance,
                bank_id=bank.id,
            )

            self.db.session.add(bank_payment)

            self.db.session.commit()

    def add_asset(self, id, amount, date, ref_no, bank_id, description=None):
        try:
            bank = Bank.query.filter_by(id=bank_id).first()
            if bank:
                asset = Asset.query.filter_by(id=id).first()
                asset.balance += float(amount)
                asset_payment = AssetPayment(
                    amount=float(amount),
                    date=date,
                    exact_date=datetime.utcnow(),
                    description=description,
                    ref_no=ref_no,
                    balance=asset.balance,
                    bank_id=bank.id,
                    asset_id=id,
                )

                self.db.session.add(asset_payment)

                bank.new_balance -= float(amount)
                bank_payment = BankPayment(
                    amount=-amount,
                    date=date,
                    exact_date=datetime.utcnow(),
                    description=description,
                    ref_no=ref_no,
                    bank_balance=bank.new_balance,
                    bank_id=bank.id,
                )

                self.db.session.add(bank_payment)

                self.db.session.commit()
        except Exception as e:
            self.db.session.rollback()
            return str(e)

    def add_liability(self, id, amount, date, ref_no, bank_id, description=None):
        bank = Bank.query.filter_by(id=bank_id).first()
        if bank:
            liability = Liability.query.filter_by(id=id).first()
            liability.balance += float(amount)
            liability_payment = LiabilityPayment(
                amount=float(amount),
                date=date,
                exact_date=datetime.utcnow(),
                description=description,
                ref_no=ref_no,
                balance=liability.balance,
                bank_id=bank.id,
                liability_id=id,
            )

            self.db.session.add(liability_payment)

            bank.new_balance -= float(amount)
            bank_payment = BankPayment(
                amount=-amount,
                date=date,
                exact_date=datetime.utcnow(),
                description=description,
                ref_no=ref_no,
                bank_balance=bank.new_balance,
                bank_id=bank.id,
            )

            self.db.session.add(bank_payment)

            self.db.session.commit()

    def add_investment(self, id, amount, date, ref_no, bank_id, description=None):
        bank = Bank.query.filter_by(id=bank_id).first()
        if bank:
            investment = Expense.query.filter_by(id=id).first()
            investment.balance += float(amount)
            investment_payment = InvestmentPayment(
                amount=float(amount),
                date=date,
                exact_date=datetime.utcnow(),
                description=description,
                ref_no=ref_no,
                balance=investment.balance,
                bank_id=bank.id,
                investment_id=id,
            )

            self.db.session.add(investment_payment)

            bank.new_balance -= float(amount)
            bank_payment = BankPayment(
                amount=-amount,
                date=date,
                exact_date=datetime.utcnow(),
                description=description,
                ref_no=ref_no,
                bank_balance=bank.new_balance,
                bank_id=bank.id,
            )

            self.db.session.add(bank_payment)

            self.db.session.commit()

    def create_new_ledger(self, ledger, name, description):
        if ledger == 1:
            asset = Asset(name=name, description=description)
            db.session.add(asset)
            db.session.commit()

        elif ledger == 2:
            expense = Expense(name=name, description=description)
            db.session.add(expense)
            db.session.commit()

        elif ledger == 3:
            income = Income(name=name, description=description)
            db.session.add(income)
            db.session.commit()

        elif ledger == 4:
            liability = Liability(name=name, description=description)
            db.session.add(liability)
            db.session.commit()

        elif ledger == 5:
            investment = Investment(name=name, description=description)
            db.session.add(investment)
            db.session.commit()

    # payments
    def withdraw(self, id, amount, description, ref_no, bank_id, date):
        try:
            person = Person.query.filter_by(id=id).first()
            if not person:
                raise ValueError("Person not found.")

            if person:
                person.available_balance -= float(amount)
                saving_payment = SavingPayment(
                    amount=-amount,
                    date=date,
                    person_id=person.id,
                    exact_date=datetime.utcnow(),
                    description=description,
                    ref_no=ref_no,
                    balance=person.available_balance,
                )
                self.db.session.add(saving_payment)
                bank = Bank.query.filter_by(id=bank_id).first()

                if bank:
                    bank.new_balance -= float(amount)
                    bank_payment = BankPayment(
                        amount=-1 * amount,
                        date=date,
                        person_id=person.id,
                        exact_date=datetime.utcnow(),
                        description=description,
                        bank_balance=bank.new_balance,
                        bank_id=bank.id,
                    )
                    self.db.session.add(bank_payment)
                    self.db.session.commit()
                    return True
        except Exception as e:
            self.db.session.rollback()
            return str(e)

    def save_amount_company(self, employee_id, amount, date, ref_no, description=None):
        try:
            person = Person.query.filter_by(employee_id=employee_id).first()
            if not person:
                raise ValueError("Person not found.")
            if person:
                company = person.company
                person.available_balance += float(amount)

                saving_payment = SavingPayment(
                    amount=float(amount),
                    date=date,
                    person_id=person.id,
                    exact_date=datetime.utcnow(),
                    description=description,
                    ref_no=ref_no,
                    company_id=company.id,
                    balance=person.available_balance,
                )

                self.db.session.add(saving_payment)

                company.amount_accumulated += float(amount)
                company_payment = CompanyPayment(
                    amount=float(amount),
                    date=date,
                    exact_date=datetime.utcnow(),
                    description=description,
                    ref_no=ref_no,
                    company_id=company.id,
                    balance=company.amount_accumulated,
                )

                self.db.session.add(company_payment)

                self.db.session.commit()
                return True
        except Exception as e:
            self.db.session.rollback()
            return str(e)


    def make_loan_request(
        self,
        id,
        pre_loan,
        interest_rate,
        start_date,
        end_date,
        bank_id,
        description,
        ref_no,
    ):
        try:
            person = Person.query.filter_by(id=id).first()

            if not person:
                raise ValueError("Person not found.")

            if person:
                loan = Loan(
                    person_id=person.id,
                    amount=pre_loan.loan_amount,
                    interest_rate=interest_rate,
                    start_date=start_date,
                    end_date=end_date,
                    bank_id=bank_id,
                    description=description,
                    ref_no=ref_no,
                    is_approved=True
                )
                self.db.session.add(loan)
                self.db.session.commit()
                log_report('how e take reach here')
                for contribution in pre_loan.guarantor_contributions:
                    contribution.loan_id = loan.id
                pre_loan.is_approved = True
                self.db.session.commit()
                return True
        except Exception as e:
            self.db.session.rollback()
            return str(e)
        
    def reject_loan(self, loan_id):
        try:
            loan = Loan.query.get(loan_id)
            pre_loan=self.get_registered_person(loan.person_id)

            if not pre_loan:
                raise ValueError("Loan not found.")

            if pre_loan:
                pre_loan.is_approved = False
                pre_loan.admin_approved = False
                self.db.session.commit()
            #delete loan
            self.db.session.delete(loan)
            self.db.session.commit()
            return True
            
        except Exception as e:
            self.db.session.rollback()
            return str(e)
        
    def approve_loan(self, loan_id):
        try:
            loan = Loan.query.get(loan_id)

            if not loan:
                raise ValueError("Loan not found.")

            if not loan.is_approved:
                loan.is_approved = True
                loan.admin_approved = True

                # Calculate interest amount based on loan amount and interest rate
                interest_amount = loan.amount * (loan.interest_rate / 100)

                # Update the person's loan balance by adding the loan amount and interest
                person = Person.query.get(loan.person_id)
                person.loan_balance += loan.amount + interest_amount
                self.delete_registered(person.id)
                # Create a loan payment record for the loan amount
                loan_payment = LoanPayment(
                    amount=loan.amount,
                    exact_date=datetime.utcnow(),
                    date=loan.start_date,
                    description=loan.description,
                    ref_no=loan.ref_no,
                    balance=person.loan_balance,
                    person_id=person.id,
                )
                self.db.session.add(loan_payment)

                # Create a loan payment record for the interest amount
                interest_payment = LoanPayment(
                    amount=interest_amount,
                    exact_date=datetime.utcnow(),
                    date=loan.start_date,
                    description=f"Interest on loan given to {person.employee_id}",
                    ref_no=loan.ref_no,
                    balance=person.loan_balance,
                    person_id=person.id,
                )
                self.db.session.add(interest_payment)
                name = "Interest"
                income_description = f"Interest on loan given to {person.employee_id}"
                income = Income.query.filter_by(name=name).first()

                income.balance += float(interest_amount)
                income_payment = IncomePayment(
                amount=float(interest_amount),
                date=loan.start_date,
                description=income_description,
                ref_no=loan.ref_no,
                balance=income.balance,
                bank_id=loan.bank_id,
                income_id=income.id,
                )

                self.db.session.add(income_payment)
                # Update the bank's balance by deducting the loan amount
                bank = Bank.query.get(loan.bank_id)
                bank.new_balance -= loan.amount

                # Create a bank payment record for the loan amount
                bank_payment = BankPayment(
                    amount=-1 * loan.amount,
                    date=loan.start_date,
                    person_id=person.id,
                    description=f"Loan given to {person.employee_id}",
                    bank_balance=bank.new_balance,
                    bank_id=bank.id,
                    ref_no=loan.ref_no,
                )
                self.db.session.add(bank_payment)

                self.db.session.commit()
                return True
            else:
                raise ValueError("Loan is already approved.")
        except Exception as e:
            self.db.session.rollback()
            return str(e)

    def repay_loan(self, id, amount, date, bank_id, ref_no, description=None):
        try:
            person = Person.query.filter_by(id=id).first()
            if not person:
                raise ValueError("Person not found.")
            if person:

                bank = Bank.query.filter_by(id=bank_id).first()

                person.loan_balance -= float(amount)
                loan_payment = LoanPayment(
                    amount=amount,
                    date=date,
                    person_id=person.id,
                    exact_date=datetime.utcnow(),
                    description=description,
                    ref_no=ref_no,
                    balance=person.loan_balance,
                    bank_id=bank.id,
                )
                self.db.session.add(loan_payment)

                bank.new_balance += float(amount)

                bank_payment = BankPayment(
                    amount=amount,
                    date=date,
                    person_id=person.id,
                    exact_date=datetime.utcnow(),
                    description=description,
                    ref_no=ref_no,
                    bank_balance=bank.new_balance,
                    bank_id=bank.id,
                )

                self.db.session.add(bank_payment)
                self.db.session.commit()
                return True
        except Exception as e:
            self.db.session.rollback()
            return str(e)

    def repay_loan_with_savings(
        self, id, amount, date, bank_id, ref_no, description=None
    ):
        try:
            person = Person.query.filter_by(id=id).first()
            if not person:
                raise ValueError("Person not found.")
            if person:
                bank = Bank.query.filter_by(id=bank_id).first()

                person.available_balance -= float(amount)
                savings_payment = SavingPayment(
                    amount=-amount,
                    date=date,
                    person_id=person.id,
                    exact_date=datetime.utcnow(),
                    description=description,
                    ref_no=ref_no,
                    balance=person.available_balance,
                    bank_id=bank.id,
                )
                self.db.session.add(savings_payment)

                bank.new_balance -= float(amount)

                bank_payment = BankPayment(
                    amount=-amount,
                    date=date,
                    person_id=person.id,
                    exact_date=datetime.utcnow(),
                    description=description,
                    ref_no=ref_no,
                    bank_balance=bank.new_balance,
                    bank_id=bank.id,
                )

                self.db.session.add(bank_payment)

                person.loan_balance -= float(amount)
                loan_payment = LoanPayment(
                    amount=amount,
                    date=date,
                    person_id=person.id,
                    exact_date=datetime.utcnow(),
                    description=description,
                    ref_no=ref_no,
                    balance=person.loan_balance,
                    bank_id=bank.id,
                )
                self.db.session.add(loan_payment)

                bank.new_balance += float(amount)

                bank_payment = BankPayment(
                    amount=amount,
                    date=date,
                    person_id=person.id,
                    exact_date=datetime.utcnow(),
                    description=description,
                    ref_no=ref_no,
                    bank_balance=bank.new_balance,
                    bank_id=bank.id,
                )

                self.db.session.add(bank_payment)
                self.db.session.commit()
                return True
        except Exception as e:
            self.db.session.rollback()
            return str(e)

    def repay_loan_company(self, id, amount, date, ref_no, description=None):
        try:
            person = Person.query.filter_by(employee_id=id).first()
            if not person:
                raise ValueError("Person not found.")

            if person:
                company = person.company
                person.loan_balance -= float(amount)
                loan_payment = LoanPayment(
                    amount=amount,
                    date=date,
                    person_id=person.id,
                    exact_date=datetime.utcnow(),
                    description=description,
                    ref_no=ref_no,
                    balance=person.loan_balance,
                    company_id=company.id,
                )
                self.db.session.add(loan_payment)

                company.amount_accumulated += float(amount)
                company_payment = CompanyPayment(
                    amount=amount,
                    date=date,
                    exact_date=datetime.utcnow(),
                    description=description,
                    ref_no=ref_no,
                    company_id=company.id,
                    balance=company.amount_accumulated,
                )

                self.db.session.add(company_payment)
                self.db.session.commit()
                
                return True
        except Exception as e:
            self.db.session.rollback()
            return str(e)

    def company_payment(self, company_id, amount, description, ref_no, bank_id):
        try:
            company = Company.query.filter_by(id=company_id).first()
            if not company:
                raise ValueError("Company not found.")
            if company:
                company.amount_acumulated -= float(amount)
                company_payment = CompanyPayment(
                    amount=-amount,
                    date=date,
                    exact_date=datetime.utcnow(),
                    description=description,
                    ref_no=ref_no,
                    company_id=company.id,
                    balance=company.amount_accumulated,
                )
                self.db.session.add(company_payment)

            bank = Bank.query.filter_by(id=bank_id).first()
            if bank:
                bank.balance += float(amount)
                bank_payment = BankPayment(
                    amount=amount,
                    date=date,
                    exact_date=datetime.utcnow(),
                    description=description,
                    ref_no=ref_no,
                    bank_balance=bank.new_balance,
                    bank_id=bank.id,
                )
                self.db.session.add(bank_payment)

                self.db.session.commit()
                return True
        except Exception as e:
            self.db.session.rollback()
            return str(e)

    # API
    def sub_accounts(self, ledger):
        if ledger == 1:
            sub_accounts = Asset.query.all()
            return sub_accounts

        elif ledger == 2:
            sub_accounts = Expense.query.all()
            return sub_accounts

        elif ledger == 4:
            sub_accounts = Liability.query.all()
            return sub_accounts

        elif ledger == 3:
            sub_accounts = Investment.query.all()
            return sub_accounts

    # queries
    def get_companies(self):
        company = Company.query.all()

        return company

    def get_company(self, company_id):
        company = Company.query.filter_by(id=company_id).first()

        return company

    def get_persons(self):
        person = Person.query.all()

        return person
    
    def get_registered(self):

        return LoanFormPayment.query.all()
    
    def get_registered_person(self,id):

        return LoanFormPayment.query.filter_by(id=id).first()
    
    def delete_registered(self,id):
        person = LoanFormPayment.query.filter_by(id=id).first()
        db.session.delete(person)
        
    
    def get_person(self, person_id):
        person = Person.query.filter_by(id=person_id).first()
        return person

    def get_savings(self):
        payments = SavingPayment.query.order_by(SavingPayment.id.desc()).all()
        return payments

    def get_individual_savings(self, person_id):
        payments = SavingPayment.query.filter_by(id=person_id).all()
        return payments

    def get_loans(self):
        loans = Loan.query.all()
        return loans

    def get_bank(self, bank_id):
        bank = Bank.query.get(bank_id)
        return bank

    def get_banks(self):
        bank = Bank.query.all()
        return bank

    def get_income(self):
        loans = Income.query.all()
        return loans
    
    def get_net_income(self):
        income = Income.query.all()
        expense = Expense.query.all()
        net_income = sum([i.balance for i in income if i.balance]) - sum([e.balance for e in expense if e.balance])
        return net_income

    def get_person_loans(self, person_id):
        loans = Loan.query.filter_by(person_id=person_id).first()
        return loans

    def get_investments(self):
        investment = Investment.query.all()
        return investment

    def get_expenses(self):
        expence = Expense.query.all()
        return expence

    def get_cash_and_banks(self):
        bank = Bank.query.all()
        total = sum([b.new_balance for b in bank if b.new_balance])
        return total
    
    def get_accounts_receivable(self):
        persons = Person.query.all()
        total = sum([p.loan_balance for p in persons if p.loan_balance])
        return total
    
    def get_accounts_payable(self):
        persons = Person.query.all()
        total = sum([p.available_balance for p in persons if p.available_balance])
        return total
    
    def get_total_investment(self):
        investment = Investment.query.all()
        total = sum([i.balance for i in investment if i.balance])
        return total
    
    def get_company_receivables(self):
        company = Company.query.all()
        total = sum([c.amount_accumulated for c in company if c.amount_accumulated])
        return total
    
    def get_fixed_assets(self):
        asset = Asset.query.all()
        total = sum([a.balance for a in asset if a.balance])
        return total
    
    def get_total_liabilities(self):
        liability = Liability.query.all()
        total = sum(l.balance for l in liability if l.balance)
        return total
