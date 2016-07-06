# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-06-21 12:30
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('equipment', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Allele',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('standard_name', models.CharField(help_text='MGNC-standard genotype name e.g. Pvalb<tm1(cre)Arbr>, http://www.informatics.jax.org/mgihome/nomen/', max_length=1023)),
                ('informal_name', models.CharField(help_text='informal name in lab, e.g. Pvalb-Cre', max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Cage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('type', models.CharField(choices=[('I', 'IVC'), ('R', 'Regular')], default='I', help_text='Is this an IVC or regular cage?', max_length=1)),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='equipment.LabLocation')),
            ],
        ),
        migrations.CreateModel(
            name='Litter',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('descriptive_name', models.CharField(max_length=255)),
                ('notes', models.TextField(blank=True, null=True)),
                ('birth_date', models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('notes', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Species',
            fields=[
                ('binomial', models.CharField(help_text='Binomial name, e.g. "mus musculus"', max_length=255, primary_key=True, serialize=False)),
                ('display_name', models.CharField(help_text='common name, e.g. "mouse"', max_length=255)),
            ],
            options={
                'verbose_name_plural': 'species',
            },
        ),
        migrations.CreateModel(
            name='Strain',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('descriptive_name', models.CharField(help_text='Standard descriptive name E.g. "C57BL/6J", http://www.informatics.jax.org/mgihome/nomen/', max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('nickname', models.CharField(blank=True, help_text='Easy-to-remember, unique name (e.g. “Hercules”).', max_length=255, null=True, unique=True)),
                ('sex', models.CharField(choices=[('M', 'Male'), ('F', 'Female'), ('U', 'Unknown')], default='U', max_length=1)),
                ('birth_date', models.DateField(blank=True, null=True)),
                ('death_date', models.DateField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('cage', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='subjects.Cage')),
            ],
        ),
        migrations.CreateModel(
            name='Zygosity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('zygosity', models.IntegerField()),
                ('allele', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='subjects.Allele')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='subjects.Subject')),
            ],
        ),
        migrations.AddField(
            model_name='subject',
            name='genotype',
            field=models.ManyToManyField(through='subjects.Zygosity', to='subjects.Allele'),
        ),
        migrations.AddField(
            model_name='subject',
            name='litter',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='subjects.Litter'),
        ),
        migrations.AddField(
            model_name='subject',
            name='responsible_user',
            field=models.ForeignKey(blank=True, help_text='Who has primary or legal responsibility for the subject.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subjects_responsible', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='subject',
            name='source',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='subjects.Source'),
        ),
        migrations.AddField(
            model_name='subject',
            name='species',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='subjects.Species'),
        ),
        migrations.AddField(
            model_name='subject',
            name='strain',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='subjects.Strain'),
        ),
        migrations.AddField(
            model_name='litter',
            name='father',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='litter_father', to='subjects.Subject'),
        ),
        migrations.AddField(
            model_name='litter',
            name='mother',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='litter_mother', to='subjects.Subject'),
        ),
    ]