# Generated by Django 5.1.7 on 2025-03-25 10:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0012_alter_customer_city_alter_customer_phone_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customer",
            name="opening_balance",
            field=models.FloatField(db_default=0, default=0),
        ),
    ]
