# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-19 19:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entrance', '0023_absencereasonhomepageblock_enrolledstepshomepageblock_entrancestatushomepageblock_entrancestepshomep'),
    ]

    operations = [
        migrations.AddField(
            model_name='entranceexamtask',
            name='order',
            field=models.IntegerField(default=0, help_text='Задачи выстраиваются по возрастанию порядка'),
        ),
    ]
