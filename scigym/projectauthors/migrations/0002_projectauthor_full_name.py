# Generated by Django 2.1.7 on 2019-03-02 17:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projectauthors', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectauthor',
            name='full_name',
            field=models.CharField(default='Erik Niehaus', max_length=256),
            preserve_default=False,
        ),
    ]
