import unittest
from app import app, db
from models import Person

class DatabaseTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_database_interaction(self):
        user = Person(username='testuser')
        db.session.add(user)
        db.session.commit()

        retrieved_user = Person.query.filter_by(username='testuser').first()
        self.assertEqual(retrieved_user, user)

if __name__ == '__main__':
    unittest.main()
