# Generated by Django 5.2 on 2025-05-02 09:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='is_generated',
            field=models.BooleanField(default=False),
        ),
    ]
