# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-08-12 11:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mail', '0005_auto_20160802_0700'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailmessage',
            name='delivered',
            field=models.BooleanField(default=False),
        ),
    ]
