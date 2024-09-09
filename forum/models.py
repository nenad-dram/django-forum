import imghdr
import os

from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.utils import timezone


class CategoryManager(models.Manager):
    def get_all_with_subcategories(self):
        queryset = self.get_queryset()
        return queryset.prefetch_related('subcategory_set')


class Category(models.Model):
    name = models.CharField(max_length=50)
    auth_required = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Categories"

    objects = CategoryManager()

    @classmethod
    def get_all(cls):
        categories_data = cache.get('categories')
        if not categories_data:
            categories_data = cls.objects.get_all_with_subcategories()
            cache.set('categories', categories_data)

        return categories_data


class Subcategory(models.Model):
    category = models.ForeignKey(to=Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name_plural = "Subcategories"

    @classmethod
    def get_by_name(cls, name):
        categories_data = Category.get_all()
        for category in categories_data:
            for subcat in category.subcategory_set.all():
                if subcat.name.lower() == name:
                    return subcat


class ThreadManager(models.Manager):
    def get_by_id(self, thread_id):
        queryset = self.get_queryset()
        return queryset.get(id=thread_id)

    def get_latest(self, fields, limit=5):
        queryset = self.get_queryset()
        return queryset.values_list(*fields).filter(
            root_thread_id__isnull=True).order_by('-updated_date')[:limit]

    def get_subcategory_latest(self, subcat_id):
        queryset = self.get_queryset()
        return queryset.filter(subcategory=subcat_id,
                               reply_to=None).order_by('-created_date')

    def update_date(self, thread_id):
        queryset = self.get_queryset()
        queryset.filter(id=thread_id).update(updated_date=timezone.now())

    def update_message(self, thread_id, new_message):
        queryset = self.get_queryset()
        queryset.filter(id=thread_id).update(message=new_message, updated_date=timezone.now())


class Thread(models.Model):
    subcategory = models.ForeignKey(to=Subcategory, on_delete=models.CASCADE)
    subject = models.CharField(max_length=50, blank=True)
    author_name = models.CharField(max_length=150, blank=True)
    author_email = models.CharField(max_length=254, blank=True)
    message = models.TextField()
    file = models.FileField(upload_to='thread_files/', null=True, blank=True)
    reply_to = models.ForeignKey(to='Thread', on_delete=models.CASCADE, blank=True, null=True,
                                 related_name="%(class)s_reply_to")
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now_add=True)
    root_thread = models.ForeignKey(to='Thread', on_delete=models.CASCADE, blank=True, null=True,
                                    related_name="%(class)s_root_thread")

    objects = ThreadManager()

    @property
    def direct_replies(self):
        return self.thread_reply_to.order_by('created_date')

    @property
    def root_replies(self):
        return self.thread_root_thread.order_by('created_date')

    @property
    def recent_root_replies(self):
        return self.thread_root_thread.order_by('-created_date')[:2:-1]

    @property
    def file_name(self):
        """Return file name without 'upload_to' prefix
           e.g. input upload_to/file.txt returns file.txt
        """
        return os.path.basename(self.file.name)

    @property
    def is_file_image(self):
        """Checks if the thread's file is an image.
           imghdr.what will return None if the file is not an image or
           image's format if it is
        """
        return imghdr.what(settings.MEDIA_ROOT + "/" + self.file.name)
