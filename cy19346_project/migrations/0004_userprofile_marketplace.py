# Generated by Django 5.0.6 on 2024-06-12 08:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cy19346_project', '0003_userprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='marketplace',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
