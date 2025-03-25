# Generated by Django 5.1.1 on 2025-03-24 12:53

import datetime
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Customer",
            fields=[
                (
                    "name",
                    models.CharField(max_length=100, primary_key=True, serialize=False),
                ),
                ("gstin", models.CharField(blank=True, max_length=100, null=True)),
                ("phone", models.CharField(max_length=100)),
                ("address", models.TextField()),
                ("opening_balance", models.FloatField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name="Outstanding",
            fields=[
                ("customer", models.CharField(max_length=100)),
                (
                    "bill_no",
                    models.CharField(max_length=20, primary_key=True, serialize=False),
                ),
                ("balance", models.FloatField()),
                ("date", models.DateField()),
            ],
            options={
                "verbose_name_plural": "Outstanding",
            },
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                (
                    "name",
                    models.CharField(
                        editable=False,
                        max_length=100,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("company", models.CharField(max_length=100)),
                ("category", models.CharField(max_length=100)),
                ("base", models.CharField(max_length=100)),
                ("size", models.CharField(max_length=100)),
                ("pur_price", models.FloatField()),
                ("sale_price", models.FloatField()),
                ("opening_stock", models.FloatField()),
                ("hsn", models.CharField(max_length=100)),
                ("rt", models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name="Purchase",
            fields=[
                (
                    "bill_no",
                    models.CharField(max_length=15, primary_key=True, serialize=False),
                ),
                ("date", models.DateField()),
                ("amt", models.FloatField(null=True, verbose_name="Total Bill Value")),
            ],
        ),
        migrations.CreateModel(
            name="Supplier",
            fields=[
                (
                    "name",
                    models.CharField(max_length=100, primary_key=True, serialize=False),
                ),
                ("gstin", models.CharField(blank=True, max_length=100, null=True)),
                ("phone", models.CharField(max_length=100)),
                ("address", models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name="Collection",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date", models.DateField(verbose_name="Collection Date")),
                (
                    "mode",
                    models.CharField(
                        choices=[
                            ("Cash", "Cash"),
                            ("Cheque", "Cheque"),
                            ("UPI", "UPI"),
                        ],
                        max_length=100,
                    ),
                ),
                ("amt", models.FloatField(verbose_name="Amount Collected")),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="app.customer",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PurchaseProduct",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("qty", models.FloatField()),
                ("price", models.FloatField()),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="purchase",
                        to="app.product",
                    ),
                ),
                (
                    "purchase",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="products",
                        to="app.purchase",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Sale",
            fields=[
                (
                    "bill_no",
                    models.CharField(max_length=15, primary_key=True, serialize=False),
                ),
                ("date", models.DateField(default=datetime.date.today)),
                ("amt", models.FloatField(null=True, verbose_name="Total Bill Value")),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="app.customer"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CollectionBillEntry",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("amt", models.FloatField(verbose_name="Amount Collected")),
                (
                    "collection",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="app.collection"
                    ),
                ),
                (
                    "bill",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="app.sale",
                        verbose_name="Sales Bill No",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SaleProduct",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("qty", models.FloatField()),
                ("price", models.FloatField()),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="sales",
                        to="app.product",
                    ),
                ),
                (
                    "sale",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="products",
                        to="app.sale",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="purchase",
            name="supplier",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="app.supplier"
            ),
        ),
    ]
