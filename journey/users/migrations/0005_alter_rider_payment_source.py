# Generated by Django 4.1.9 on 2023-05-29 03:42

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0004_rename_tokenized_card_rider_payment_source"),
    ]

    operations = [
        migrations.AlterField(
            model_name="rider",
            name="payment_source",
            field=models.IntegerField(blank=True, help_text="data created in the payment api", null=True),
        ),
    ]
