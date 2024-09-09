from django.test import TestCase

from forum.forms import ThreadForm


class ThreadFormTestCase(TestCase):
    fixtures = ['test_init_cat_subcat.json']

    def test_form_valid(self):
        form_data = {
            'subcategory': '1',
            'subject': 'Something to ask',
            'author_name': 'John Doe',
            'author_email': 'johndoe@example.com',
            'message': 'My Message'
        }
        form = ThreadForm(data=form_data)
        form.is_valid()
        self.assertTrue(form.is_valid())

    def test_form_invalid(self):
        form_data = {
            'subcategory': '',
            'subject': '',
            'author_name': '',
            'author_email': 'invalidemail',
            'message': '',
            'file': None,
            'reply_to': None
        }
        form = ThreadForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_form_labels(self):
        form = ThreadForm()
        self.assertEqual(form.fields['author_name'].label, 'Your name')
        self.assertEqual(form.fields['author_email'].label, 'Your email')
        self.assertEqual(form.fields['file'].label, 'Upload file')
