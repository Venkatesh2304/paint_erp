# Generated by Django 5.1.1 on 2025-03-24 20:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0005_purchaseproduct_base_rate_purchaseproduct_discount_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="outstanding",
            name="customer",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.DO_NOTHING, to="app.customer"
            ),
        ),
    ]
