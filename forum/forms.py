from django.forms import ModelForm

from forum.models import Thread


class ThreadForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ThreadForm, self).__init__(*args, **kwargs)
        self.label_suffix = ''

    class Meta:
        model = Thread
        fields = ['subcategory', 'subject', 'author_name', 'author_email', 'message', 'file', 'reply_to']

        labels = {
            'author_name': 'Your name',
            'author_email': 'Your email',
            'file': 'Upload file'
        }
