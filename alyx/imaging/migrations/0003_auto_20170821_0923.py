# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-08-21 08:23
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('imaging', '0002_auto_20170808_1506'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='roi',
            name='experiment',
        ),
        migrations.RemoveField(
            model_name='roidetection',
            name='experiment',
        ),
        migrations.RemoveField(
            model_name='svdcompressedmovie',
            name='experiment',
        ),
        migrations.RemoveField(
            model_name='twophotonimaging',
            name='experiment',
        ),
        migrations.RemoveField(
            model_name='widefieldimaging',
            name='experiment',
        ),
    ]