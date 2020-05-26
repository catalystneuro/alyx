# Generated by Django 3.0.5 on 2020-05-25 17:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('buffalo', '0002_auto_20200524_0227'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='platform',
            field=models.CharField(blank=True, choices=[('unity', 'Unity'), ('monkeylogic', 'Monkeylogic'), ('cortex', 'Cortex')], default='', max_length=180),
        ),
    ]