from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='subtitle_file',
            field=models.FileField(blank=True, help_text='VTT or SRT subtitle file', null=True, upload_to='subtitles/'),
        ),
        migrations.AddField(
            model_name='video',
            name='subtitle_text',
            field=models.TextField(blank=True, help_text='Extracted text from subtitles or video content', null=True),
        ),
    ]
