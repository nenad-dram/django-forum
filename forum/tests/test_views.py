from math import trunc
from os import remove

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from forum.models import Thread


class ViewTest(TestCase):
    fixtures = ('test_init_cat_subcat.json', 'test_init_user.json')

    def test_thread_get_update_date(self):
        thread = Thread(subcategory_id=1, subject="First Thread", message="Hello World")
        thread.save()
        thread_update_timestamp = trunc(thread.updated_date.timestamp())

        response = self.client.get(reverse('thread_get_update', kwargs={'thread_id': thread.id}))
        db_update_timestamp = int(response.content.decode('utf-8'))
        self.assertEqual(db_update_timestamp, thread_update_timestamp)

    def test_thread_update_thread_message(self):
        thread = Thread(subcategory_id=1, subject="First Thread", message="Hello World")
        thread.save()

        new_message = "New thread message"
        response = self.client.post(reverse('thread_edit_message', kwargs={'thread_id': thread.id}),
                                    data={"newMessage": new_message},
                                    content_type='application/json',
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        updated_thread = Thread.objects.get_by_id(thread.id)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(new_message, updated_thread.message)

    def test_thread_update_reply_message(self):
        thread = Thread(subcategory_id=1, subject="First Thread", message="Hello World")
        thread.save()
        reply = Thread(subcategory_id=1, subject="First Reply", message="Just to add something",
                       reply_to_id=thread.id, root_thread_id=thread.id)
        reply.save()

        new_message = "New reply message"
        response = self.client.post(reverse('thread_edit_message', kwargs={'thread_id': thread.id}),
                                    data={"replyId": reply.id, "newMessage": new_message},
                                    content_type='application/json',
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        updated_reply = Thread.objects.get_by_id(reply.id)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(new_message, updated_reply.message)

    def test_thread_update_message_badRequest(self):
        response = self.client.post(reverse('thread_edit_message', kwargs={'thread_id': 1}),
                                    data={"replyId": "", "newMessage": ""},
                                    content_type='application/json')

        self.assertEqual(response.status_code, 400)

    def test_dashboard_without_threads(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        self.assertEqual(len(response.context['categories']), 4)
        self.assertEqual(len(response.context['recent_updates']), 0)

    def test_dashboard_with_threads(self):
        for i in range(1, 5):
            thread = Thread(subcategory_id=i, subject="Thread " + str(i), message="Hello World")
            thread.save()
        expected_most_recent_update = {'id': 4, 'subject': 'Thread 4', 'subcategory__name': 'Linux'}

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        self.assertEqual(len(response.context['categories']), 4)
        self.assertEqual(len(response.context['recent_updates']), 4)
        self.assertEqual(response.context['recent_updates'][0], expected_most_recent_update)

    def test_subcategory_no_auth_required(self):
        response = self.client.get(reverse('subcategory', kwargs={'name': 'skills'}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'subcategory.html')
        self.assertEqual(len(response.context['categories']), 4)
        self.assertEqual(len(response.context['threads']), 0)
        self.assertEqual(response.context['subcategory'].name, 'Skills')

    def test_subcategory_auth_required_user_not_auth(self):
        response = self.client.get(reverse('subcategory', kwargs={'name': 'stuffing'}))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/forum/login?next=/forum/stuffing')

    def test_subcategory_auth_required_user_auth(self):
        self.client.login(username='test_user', password='password')

        response = self.client.get(reverse('subcategory', kwargs={'name': 'stuffing'}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'subcategory.html')
        self.assertEqual(len(response.context['categories']), 4)
        self.assertEqual(len(response.context['threads']), 0)
        self.assertEqual(response.context['subcategory'].name, 'Stuffing')

    def test_subcategory_with_threads(self):
        threads = []
        for i in range(3, 5):
            for j in range(1, 4):
                thread = Thread(subcategory_id=i, subject="Thread " + str(i) + str(j), message="Hello World " + str(j))
                threads.append(thread)
        Thread.objects.bulk_create(threads)

        response = self.client.get(reverse('subcategory', kwargs={'name': 'skills'}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'subcategory.html')
        self.assertEqual(len(response.context['categories']), 4)
        self.assertEqual(len(response.context['threads']), 3)
        self.assertEqual(response.context['subcategory'].name, 'Skills')

    def test_subcategory_unquote_name(self):
        response = self.client.get(reverse('subcategory', kwargs={'name': 'c%2B%2B'}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'subcategory.html')
        self.assertEqual(len(response.context['categories']), 4)
        self.assertEqual(len(response.context['threads']), 0)
        self.assertEqual(response.context['subcategory'].name, 'c++')

    def test_thread_create(self):
        file = SimpleUploadedFile('django.txt', b'file_content')
        thread_request = {'subcategory': 1, 'subject': 'Subject name', 'author_name': 'Author name',
                          'author_email': 'author@mail.com', 'message': 'message content', 'file': file}

        response = self.client.post(reverse('thread_create', kwargs={'subcategory_name': 'london'}),
                                    data=thread_request)
        created_thread = Thread.objects.get_by_id(1)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/forum/london')
        self.assertEqual(created_thread.subject, 'Subject name')
        self.assertEqual(created_thread.file_name, 'django.txt')

        remove(created_thread.file.path)

    def test_thread_view(self):
        thread = Thread(subcategory_id=1, subject="First Thread", message="Hello World")
        thread.save()

        response = self.client.get(reverse('thread_view', kwargs={'id': 1}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'thread.html')
        self.assertEqual(len(response.context['categories']), 4)
        self.assertEqual(response.context['thread'].id, 1)

    def test_thread_reply(self):
        thread = Thread(subcategory_id=1, subject="First Thread", message="Hello World")
        thread.save()

        reply_request = {'subcategory': '1', 'subject': 'Subject name', 'author_name': 'Author name',
                         'author_email': 'author@mail.com', 'message': 'message content', 'reply_to': 1}

        response = self.client.post(reverse('thread_reply', kwargs={'root_id': 1}), data=reply_request)

        created_reply = Thread.objects.get_by_id(1).direct_replies[0]
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/forum/thread/1')
        self.assertEqual(created_reply.subject, 'Subject name')

    def test_login_successful(self):
        response = self.client.login(username='test_user', password='password')

        self.assertTrue(response)

    def test_login_failed(self):
        response = self.client.login(username='test_user', password='incorrect')

        self.assertFalse(response)

    def test_logout(self):
        self.client.login(username='test_user', password='incorrect')

        response = self.client.post(reverse('logout'))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/forum/home')

    def test_thread_not_found_raise_404(self):
        response = self.client.get(reverse('thread_view', kwargs={'id': 1}))

        self.assertEqual(response.status_code, 404)
