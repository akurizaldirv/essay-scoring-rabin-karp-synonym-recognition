# Generated by Django 3.1.1 on 2023-05-02 12:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scoring', '0004_auto_20230318_0006'),
    ]

    operations = [
        migrations.AddField(
            model_name='kuncijawaban',
            name='soal',
            field=models.TextField(blank=True, null=True),
        ),
    ]
