# Generated by Django 5.1.6 on 2025-04-21 14:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0007_remove_order_ordered_date_cart_ordered_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='slug',
            field=models.SlugField(blank=True, max_length=128),
        ),
    ]
