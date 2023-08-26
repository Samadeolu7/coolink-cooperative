import unittest
from app import app

class AuthenticationTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_login(self):
        response = self.app.post('/login', data=dict(
            username='testuser',
            password='testpassword'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome', response.data)

if __name__ == '__main__':
    unittest.main()
