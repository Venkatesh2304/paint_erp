# Generated by Django 5.1.7 on 2025-03-25 09:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0008_product_mrp_alter_product_base_alter_product_dpl_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="dpl",
            field=models.IntegerField(db_default=0, default=0),
        ),
    ]
