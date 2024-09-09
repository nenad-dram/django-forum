from os import remove
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.test import TestCase

from forum.models import Category, Subcategory, Thread


class ModelsTest(TestCase):
    fixtures = ('test_init_cat_subcat.json', 'test_init_user.json')

    def test_categories_exist(self):
        categories = Category.objects.all()

        self.assertEqual(len(categories), 4)

    def test_subcategories_exist(self):
        subcategories = Subcategory.objects.all()

        self.assertEqual(len(subcategories), 8)

    def test_get_categories_with_subcategories(self):
        categories = Category.objects.get_all_with_subcategories()

        subcategories = categories[0].subcategory_set.all()
        self.assertEqual(len(subcategories), 2)
        self.assertEqual(subcategories[0].name, 'Football')

    def test_get_categories_and_set_cache(self):
        self.assertFalse(cache.get('categories'))

        categories = Category.get_all()

        self.assertTrue(categories)
        self.assertTrue(cache.get('categories'))

    @patch('django.core.cache.cache.get')
    def test_get_categories_from_cache(self, mock_get_all_categories):
        categories = [Category(id=1, name='first'), Category(id=2, name='second')]
        mock_get_all_categories.return_value = categories

        actual_categories = Category.get_all()

        mock_get_all_categories.assert_called_once_with('categories')
        self.assertEqual(actual_categories, categories)
        self.assertTrue(cache.get('categories'))

    def test_subcategory_by_id(self):
        subcategory = Subcategory.objects.get(id=3)

        self.assertEqual(subcategory.name, 'Skills')

    def test_subcategory_get_by_name_found(self):
        subcategory = Subcategory.get_by_name('linux')

        self.assertTrue(subcategory)
        self.assertTrue(cache.get('categories'))

    def test_subcategory_get_by_name_not_found(self):
        subcategory = Subcategory.get_by_name('Unknown')
        self.assertFalse(subcategory)

    def test_thread_create(self):
        thread_file = ContentFile('someContent', 'python.txt')
        thread = Thread(subcategory_id=1, subject='First Thread', author_name='Author name',
                        author_email='author@mail.com', message='Hello World', file=thread_file)

        thread.save()
        actual_thread = Thread.objects.get_by_id(1)

        self.assertEqual(actual_thread.id, 1)
        self.assertEqual(actual_thread.subject, 'First Thread')
        self.assertEqual(actual_thread.subcategory.name, 'Football')
        self.assertEqual(actual_thread.file_name, 'python.txt')

        remove(actual_thread.file.path)

    def test_thread_add_reply(self):
        thread = Thread(subcategory_id=1, subject='First Thread', message='Hello World')
        thread.save()

        reply = Thread(subcategory_id=1, subject='First Reply', message='Just to add something',
                       reply_to_id=thread.id, root_thread_id=thread.id)
        reply.save()

        thread = Thread.objects.get_by_id(1)
        self.assertEqual(thread.root_replies[0].subject, 'First Reply')

    def test_thread_add_reply_on_reply(self):
        root_thread = Thread(subcategory_id=1, subject='First Thread', message='Hello World')
        root_thread.save()

        init_reply = Thread(subcategory_id=1, message='Just to add something', reply_to_id=root_thread.id)
        init_reply.save()

        reply_for_init_reply = Thread(subcategory_id=1, message='Just to add something else',
                                      reply_to_id=init_reply.id, root_thread_id=root_thread.id)
        reply_for_init_reply.save()

        db_reply = Thread.objects.get(reply_to_id=1)

        self.assertEqual(db_reply.direct_replies[0].message, 'Just to add something else')

    def test_thread_get_latest(self):
        for i in range(1, 6):
            thread = Thread(subcategory_id=i, subject='Thread ' + str(i), message='Hello World')
            thread.save()
            reply1 = Thread(subcategory_id=i, subject=thread.subject, message='comment 1',
                            reply_to_id=thread.id, root_thread_id=thread.id)
            reply2 = Thread(subcategory_id=i, subject=thread.subject, message='comment 2',
                            reply_to_id=thread.id, root_thread_id=thread.id)
            reply1.save()
            reply2.save()
            Thread.objects.update_date(thread.id)

        latest_threads = Thread.objects.get_latest(['id', 'subject', 'subcategory__name'])

        self.assertTrue(len(latest_threads) == 5)

    def test_thread_recent_root_replies(self):
        thread = Thread(subcategory_id=1, subject='First Thread', message='Hello World')
        thread.save()

        reply1 = Thread(subcategory_id=1, subject='First Reply', message='Just to add something one',
                        reply_to_id=thread.id, root_thread_id=thread.id)
        reply2 = Thread(subcategory_id=1, subject='Second Reply', message='Just to add something two',
                        reply_to_id=thread.id, root_thread_id=thread.id)
        reply3 = Thread(subcategory_id=1, subject='Third Reply', message='Just to add something three',
                        reply_to_id=thread.id, root_thread_id=thread.id)
        reply1.save()
        reply2.save()
        reply3.save()

        thread = Thread.objects.get_by_id(1)

        self.assertEqual(len(thread.recent_root_replies), 2)
        self.assertEqual(thread.recent_root_replies[0].subject, 'Second Reply')
        self.assertEqual(thread.recent_root_replies[1].subject, 'Third Reply')

    def test_user_exists(self):
        db_user = User.objects.get(username='test_user')
        self.assertTrue(db_user.id)

    def test_admin_user(self):
        admin_user = User.objects.get(username='admin')
        self.assertTrue(admin_user.is_staff and admin_user.is_superuser)

    def test_thread_update_date(self):
        thread = Thread(subcategory_id=1, subject='First Thread', message='Hello World')
        thread.save()
        Thread.objects.update_date(thread.id)

        updated_thread = Thread.objects.get_by_id(thread.id)
        self.assertNotEquals(updated_thread.updated_date, thread.updated_date)

    def test_thread_update_message(self):
        new_message = 'New Message'
        thread = Thread(subcategory_id=1, subject='First Thread', message='Hello World')
        thread.save()
        Thread.objects.update_message(thread.id, new_message)

        updated_thread = Thread.objects.get_by_id(thread.id)
        self.assertNotEquals(updated_thread.updated_date, thread.updated_date)
        self.assertEquals(updated_thread.message, new_message)

    def test_thread_file_is_not_file_image(self):
        thread_file = ContentFile('someContent', 'thread_files/java.txt')
        thread = Thread(file=thread_file)

        self.assertFalse(thread.is_file_image)

    def test_thread_file_is_file_image(self):
        thread_file = ContentFile('someContent', 'thread_files/scale.jpg')
        thread = Thread(file=thread_file)

        self.assertTrue(thread.is_file_image)
