# Generated by Django 4.1.1 on 2022-09-13 16:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0004_thread_updated_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='thread',
            name='file',
            field=models.FileField(upload_to='thread_files/'),
        ),
    ]
