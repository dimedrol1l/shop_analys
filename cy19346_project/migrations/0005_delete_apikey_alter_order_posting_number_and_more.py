# Generated by Django 5.0.6 on 2024-06-12 08:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cy19346_project', '0004_userprofile_marketplace'),
    ]

    operations = [
        migrations.DeleteModel(
            name='APIKey',
        ),
        migrations.AlterField(
            model_name='order',
            name='posting_number',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='api_key',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='client_id',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='marketplace',
            field=models.CharField(default='Ozon', max_length=50),
        ),
        migrations.AlterModelTable(
            name='order',
            table=None,
        ),
    ]