# Generated by Django 4.2.1 on 2023-06-04 17:28

import colorfield.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0003_alter_cart_recipe_alter_favorite_recipe_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tag",
            name="color",
            field=colorfield.fields.ColorField(
                default="#FF0000", image_field=None, max_length=18, samples=None
            ),
        ),
    ]