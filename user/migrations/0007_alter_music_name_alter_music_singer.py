# Generated by Django 4.2.6 on 2024-01-22 04:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0006_alter_music_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='music',
            name='name',
            field=models.CharField(max_length=64),
        ),
        migrations.AlterField(
            model_name='music',
            name='singer',
            field=models.CharField(max_length=64),
        ),
    ]
