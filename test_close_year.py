import unittest
from create_app import create_app  # Import your Flask app and SQLAlchemy setup
from models import Liability, LiabilityPayment  # Import your models
from sqlalchemy import func
from datetime import datetime

class TestLiabilityFunctions(unittest.TestCase):
    def setUp(self):
        # Create a test Flask app and configure it for testing
        t = create_app()
        self.app = t["app"]
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.db = t["db"]
        self.query = t["query"]
        self.db.create_all()

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()
        self.app_context.pop()

    def test_get_liabilities_per_year(self):
        # Create test data
        test_year = 2023  # Replace with your desired test year

        # Create sample liabilities and payments for testing
        liability1 = Liability(name="Liability 1", balance=100)
        liability2 = Liability(name="Liability 2", balance=200)
        self.db.session.add(liability1)
        self.db.session.add(liability2)
        self.db.session.commit()

        # Create sample payments for the test year
        payment1 = LiabilityPayment(
            amount=50,
            year=test_year,
            date=datetime(2023, 5, 15),  # Date in the specified year
            liability=liability1,
        )
        payment2 = LiabilityPayment(
            amount=75,
            year=test_year,
            date=datetime(2023, 11, 20),  # Date in the specified year
            liability=liability2,
        )
        payment3 = LiabilityPayment(
            amount=100,
            year=test_year + 1,
            date=datetime(2024, 5, 15),  # Date in the next year
            liability=liability1,
        )
        payment4 = LiabilityPayment(
            amount=150,
            year=test_year + 1,
            date=datetime(2024, 11, 20),  # Date in the next year
            liability=liability2,
        )
        
        self.db.session.add(payment1)
        self.db.session.add(payment2)
        self.db.session.add(payment3)
        self.db.session.add(payment4)
        self.db.session.commit()

        # Call the function to be tested
        result = self.query.get_liabilities_per_year(test_year)
        print(result)

        # Assert the results
        self.assertEqual(len(result), 2)  # Assuming there are 2 liabilities for the test year
        # Add more specific assertions based on your expected results

if __name__ == "__main__":
    unittest.main()
