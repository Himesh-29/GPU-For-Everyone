# Django 6.0 + DEFAULT_AUTO_FIELD = BigAutoField
# The Site model's id must match the project's DEFAULT_AUTO_FIELD.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sites", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="site",
            name="id",
            field=models.BigAutoField(
                auto_created=True,
                primary_key=True,
                serialize=False,
                verbose_name="ID",
            ),
        ),
    ]
