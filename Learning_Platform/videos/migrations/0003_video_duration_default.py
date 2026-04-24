from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("videos", "0002_add_subtitles"),
    ]

    operations = [
        migrations.AlterField(
            model_name="video",
            name="duration",
            field=models.IntegerField(default=0),
        ),
    ]
