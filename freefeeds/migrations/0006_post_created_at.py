# Generated by Django 3.0 on 2019-12-22 20:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("freefeeds", "0005_auto_20191222_1241"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="created_at",
            field=models.DateTimeField(null=True),
        ),
    ]
