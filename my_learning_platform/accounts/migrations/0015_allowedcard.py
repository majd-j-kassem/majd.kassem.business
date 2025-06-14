# Generated by Django 5.2.1 on 2025-05-22 05:45

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_alter_customuser_user_type_delete_course'),
    ]

    operations = [
        migrations.CreateModel(
            name='AllowedCard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('card_number', models.CharField(help_text='The 16-digit card number.', max_length=16, unique=True)),
                ('expiry_month', models.IntegerField(help_text='Expiry month (1-12)', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(12)])),
                ('expiry_year', models.IntegerField(help_text='Expiry year (e.g., 2025)', validators=[django.core.validators.MinValueValidator(2025)])),
                ('added_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Allowed Card',
                'verbose_name_plural': 'Allowed Cards',
                'unique_together': {('card_number', 'expiry_month', 'expiry_year')},
            },
        ),
    ]
