# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-04-14 06:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0011_activity_day'),
    ]

    operations = [
        migrations.CreateModel(
            name='month',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.IntegerField()),
                ('cum_elev', models.FloatField()),
                ('athlete_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.athlete')),
            ],
        ),
        migrations.RemoveField(
            model_name='calendar_total',
            name='athlete',
        ),
        migrations.DeleteModel(
            name='calendar_total',
        ),
    ]
