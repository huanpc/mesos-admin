# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-01-13 16:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('watcher', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='watcher',
            name='config',
            field=models.TextField(default=''),
        ),
    ]
