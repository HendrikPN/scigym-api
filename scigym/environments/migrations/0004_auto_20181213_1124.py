# Generated by Django 2.1.3 on 2018-12-13 11:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('environments', '0003_auto_20181213_1101'),
    ]

    operations = [
        migrations.AlterField(
            model_name='environment',
            name='repository',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='repositories.Repository'),
        ),
    ]
