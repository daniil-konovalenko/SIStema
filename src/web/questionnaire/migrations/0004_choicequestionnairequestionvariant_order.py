# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-05-22 21:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0003_auto_20170515_1807'),
    ]

    operations = [
        migrations.AddField(
            model_name='choicequestionnairequestionvariant',
            name='order',
            field=models.PositiveIntegerField(default=0),
        ),
    ]