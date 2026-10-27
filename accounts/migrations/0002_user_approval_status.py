
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        # Preserve access for users who already exist.
        migrations.AddField(
            model_name="user",
            name="approval_status",
            field=models.CharField(
                max_length=20,
                choices=[
                    ("pending", "Pending Approval"),
                    ("approved", "Approved"),
                    ("rejected", "Rejected"),
                ],
                default="approved",
            ),
        ),
        # New User instances should default to pending approval.
        migrations.AlterField(
            model_name="user",
            name="approval_status",
            field=models.CharField(
                max_length=20,
                choices=[
                    ("pending", "Pending Approval"),
                    ("approved", "Approved"),
                    ("rejected", "Rejected"),
                ],
                default="pending",
            ),
        ),
    ]
