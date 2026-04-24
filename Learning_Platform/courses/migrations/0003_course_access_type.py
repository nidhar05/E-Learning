from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="access_type",
            field=models.CharField(
                choices=[("free", "Free"), ("subscription", "Subscription")],
                default="free",
                max_length=20,
            ),
        ),
    ]
