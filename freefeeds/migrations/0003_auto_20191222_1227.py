# Generated by Django 3.0 on 2019-12-22 12:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("freefeeds", "0002_auto_20191218_2023"),
    ]

    operations = [
        migrations.RenameField(
            model_name="post",
            old_name="comment_likes",
            new_name="comments",
        ),
        migrations.AddField(
            model_name="post",
            name="likes",
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
