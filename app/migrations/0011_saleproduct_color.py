# Generated by Django 5.1.7 on 2025-03-25 10:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0010_customer_city_customer_pincode"),
    ]

    operations = [
        migrations.AddField(
            model_name="saleproduct",
            name="color",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="Color"
            ),
        ),
    ]
