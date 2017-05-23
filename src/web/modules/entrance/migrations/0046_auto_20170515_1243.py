# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-05-15 07:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import djchoices.choices


class Migration(migrations.Migration):

    dependencies = [
        ('entrance', '0045_entrancestatus_private_comment'),
    ]

    operations = [
        migrations.CreateModel(
            name='EnsureProfileIsFullEntranceStep',
            fields=[
                ('abstractentrancestep_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='entrance.AbstractEntranceStep')),
                ('text_before_start_date', models.TextField(blank=True, help_text='Текст, который показывается до даты начала заполнения шага. Поддерживается Markdown')),
                ('text_after_finish_date_if_passed', models.TextField(blank=True, help_text='Текст, который показывается после даты окончания заполнения, если шаг выполнен. Поддерживается Markdown')),
                ('text_after_finish_date_if_not_passed', models.TextField(blank=True, help_text='Текст, который показывается после даты окончания заполнения, если шаг не выполнен. Поддерживается Markdown')),
                ('text_waiting_for_other_step', models.TextField(blank=True, help_text='Текст, который показывается, когда не пройден один из предыдущих шагов. Поддерживается Markdown')),
                ('text_step_is_not_passed', models.TextField(blank=True, help_text='Текст, который показывается, когда шаг ещё не пройден. Поддерживается Markdown')),
                ('text_step_is_passed', models.TextField(blank=True, help_text='Текст, который показывается, когда шаг пройден пользователем. Поддерживается Markdown')),
            ],
            options={
                'abstract': False,
            },
            bases=('entrance.abstractentrancestep', models.Model),
        ),
        migrations.AlterField(
            model_name='entrancestatus',
            name='status',
            field=models.IntegerField(choices=[(1, 'Не участвовал в конкурсе'), (2, 'Автоматический отказ'), (3, 'Не прошёл по конкурсу'), (4, 'Поступил'), (5, 'Подал заявку'), (6, 'В резервном списке')], validators=[djchoices.choices.ChoicesValidator({1: 'Не участвовал в конкурсе', 2: 'Автоматический отказ', 3: 'Не прошёл по конкурсу', 4: 'Поступил', 5: 'Подал заявку', 6: 'В резервном списке'})]),
        ),
    ]