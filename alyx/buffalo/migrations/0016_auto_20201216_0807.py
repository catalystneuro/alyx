# Generated by Django 3.0.7 on 2020-12-16 08:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('buffalo', '0015_buffaloasynctask_electrodelogstl'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='explantation_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]