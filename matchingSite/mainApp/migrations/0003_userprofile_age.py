# Generated by Django 2.1.2 on 2018-12-07 22:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainApp', '0002_remove_userprofile_age'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='age',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]
