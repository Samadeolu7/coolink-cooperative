import unittest
from app.forms import YourForm

class FormTestCase(unittest.TestCase):

    def test_valid_form(self):
        form = YourForm(data={
            'input_field': 'some value'
        })
        self.assertTrue(form.validate())

    def test_invalid_form(self):
        form = YourForm(data={
            'input_field': ''
        })
        self.assertFalse(form.validate())
        self.assertIn('This field is required.', form.input_field.errors)

if __name__ == '__main__':
    unittest.main()
