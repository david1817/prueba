# Generated by Django 5.1.1 on 2024-09-26 04:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='comments',
            unique_together={('identification', 'phone')},
        ),
        migrations.RemoveField(
            model_name='comments',
            name='email',
        ),
    ]
