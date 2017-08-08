# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-08-08 14:04
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('actions', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Experiment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('json', django.contrib.postgres.fields.jsonb.JSONField(blank=True, help_text='Structured data, formatted in a user-defined way', null=True)),
                ('parent_experiment', models.ForeignKey(blank=True, help_text='Hierarchical parent to this experiment', null=True, on_delete=django.db.models.deletion.CASCADE, to='actions.Experiment')),
                ('session', models.ForeignKey(blank=True, help_text='The session to which this experiment belongs', null=True, on_delete=django.db.models.deletion.CASCADE, to='actions.Session')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
