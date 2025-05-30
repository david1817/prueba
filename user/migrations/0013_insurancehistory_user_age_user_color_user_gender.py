# Generated by Django 5.1.1 on 2024-10-27 03:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0012_alter_comments_phone'),
    ]

    operations = [
        migrations.CreateModel(
            name='InsuranceHistory',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('identification', models.CharField(max_length=10)),
                ('name_insurance', models.CharField(max_length=100)),
                ('value', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 't_insurance_history',
            },
        ),
        migrations.AddField(
            model_name='user',
            name='age',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='gender',
            field=models.CharField(default='M', max_length=20),
        ),
    ]
