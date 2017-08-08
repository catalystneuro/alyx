# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-08-08 14:06
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('actions', '0002_experiment'),
        ('data', '0002_auto_20170808_1504'),
        ('imaging', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='roi',
            name='created_date',
        ),
        migrations.RemoveField(
            model_name='roidetection',
            name='created_date',
        ),
        migrations.RemoveField(
            model_name='svdcompressedmovie',
            name='created_date',
        ),
        migrations.RemoveField(
            model_name='twophotonimaging',
            name='created_date',
        ),
        migrations.RemoveField(
            model_name='widefieldimaging',
            name='created_date',
        ),
        migrations.AddField(
            model_name='roi',
            name='created_datetime',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, help_text='The creation datetime.', null=True),
        ),
        migrations.AddField(
            model_name='roi',
            name='experiment',
            field=models.ForeignKey(blank=True, help_text='The Experiment to which this data belongs', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='imaging_roi_session_related', to='actions.Experiment'),
        ),
        migrations.AddField(
            model_name='roi',
            name='generating_software',
            field=models.CharField(blank=True, help_text="e.g. 'ChoiceWorld 0.8.3'", max_length=255),
        ),
        migrations.AddField(
            model_name='roi',
            name='provenance_directory',
            field=models.ForeignKey(blank=True, help_text='link to directory containing intermediate results', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='imaging_roi_provenance_related', to='data.Dataset'),
        ),
        migrations.AddField(
            model_name='roidetection',
            name='created_datetime',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, help_text='The creation datetime.', null=True),
        ),
        migrations.AddField(
            model_name='roidetection',
            name='experiment',
            field=models.ForeignKey(blank=True, help_text='The Experiment to which this data belongs', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='imaging_roidetection_session_related', to='actions.Experiment'),
        ),
        migrations.AddField(
            model_name='roidetection',
            name='generating_software',
            field=models.CharField(blank=True, help_text="e.g. 'ChoiceWorld 0.8.3'", max_length=255),
        ),
        migrations.AddField(
            model_name='roidetection',
            name='provenance_directory',
            field=models.ForeignKey(blank=True, help_text='link to directory containing intermediate results', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='imaging_roidetection_provenance_related', to='data.Dataset'),
        ),
        migrations.AddField(
            model_name='svdcompressedmovie',
            name='created_datetime',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, help_text='The creation datetime.', null=True),
        ),
        migrations.AddField(
            model_name='svdcompressedmovie',
            name='experiment',
            field=models.ForeignKey(blank=True, help_text='The Experiment to which this data belongs', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='imaging_svdcompressedmovie_session_related', to='actions.Experiment'),
        ),
        migrations.AddField(
            model_name='svdcompressedmovie',
            name='generating_software',
            field=models.CharField(blank=True, help_text="e.g. 'ChoiceWorld 0.8.3'", max_length=255),
        ),
        migrations.AddField(
            model_name='svdcompressedmovie',
            name='provenance_directory',
            field=models.ForeignKey(blank=True, help_text='link to directory containing intermediate results', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='imaging_svdcompressedmovie_provenance_related', to='data.Dataset'),
        ),
        migrations.AddField(
            model_name='twophotonimaging',
            name='created_datetime',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, help_text='The creation datetime.', null=True),
        ),
        migrations.AddField(
            model_name='twophotonimaging',
            name='experiment',
            field=models.ForeignKey(blank=True, help_text='The Experiment to which this data belongs', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='imaging_twophotonimaging_session_related', to='actions.Experiment'),
        ),
        migrations.AddField(
            model_name='twophotonimaging',
            name='generating_software',
            field=models.CharField(blank=True, help_text="e.g. 'ChoiceWorld 0.8.3'", max_length=255),
        ),
        migrations.AddField(
            model_name='twophotonimaging',
            name='provenance_directory',
            field=models.ForeignKey(blank=True, help_text='link to directory containing intermediate results', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='imaging_twophotonimaging_provenance_related', to='data.Dataset'),
        ),
        migrations.AddField(
            model_name='widefieldimaging',
            name='created_datetime',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, help_text='The creation datetime.', null=True),
        ),
        migrations.AddField(
            model_name='widefieldimaging',
            name='experiment',
            field=models.ForeignKey(blank=True, help_text='The Experiment to which this data belongs', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='imaging_widefieldimaging_session_related', to='actions.Experiment'),
        ),
        migrations.AddField(
            model_name='widefieldimaging',
            name='generating_software',
            field=models.CharField(blank=True, help_text="e.g. 'ChoiceWorld 0.8.3'", max_length=255),
        ),
        migrations.AddField(
            model_name='widefieldimaging',
            name='provenance_directory',
            field=models.ForeignKey(blank=True, help_text='link to directory containing intermediate results', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='imaging_widefieldimaging_provenance_related', to='data.Dataset'),
        ),
    ]
