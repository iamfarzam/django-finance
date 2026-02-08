"""Add default_currency to User."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="default_currency",
            field=models.CharField(
                default="USD",
                help_text="Default currency for new records and views.",
                max_length=3,
            ),
        ),
    ]
