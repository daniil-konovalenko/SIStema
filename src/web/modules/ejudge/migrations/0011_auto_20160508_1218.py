# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djchoices.choices


class Migration(migrations.Migration):

    dependencies = [
        ('ejudge', '0010_auto_20160406_2005'),
    ]

    operations = [
        migrations.AlterField(
            model_name='solutioncheckingresult',
            name='result',
            field=models.PositiveIntegerField(choices=[(0, 'OK'), (1, 'Compilation error'), (2, 'Run-time error'), (3, 'Time-limit exceeded'), (4, 'Presentation error'), (5, 'Wrong answer'), (6, 'Check failed'), (7, 'Partial solution'), (12, 'Memory limit exceeded'), (13, 'Security violation'), (14, 'Coding style violation'), (15, 'Wall time-limit exceeded'), (18, 'Skipped'), (100, 'Unknown result')], validators=[djchoices.choices.ChoicesValidator({0: 'OK', 1: 'Compilation error', 2: 'Run-time error', 3: 'Time-limit exceeded', 4: 'Presentation error', 5: 'Wrong answer', 6: 'Check failed', 7: 'Partial solution', 12: 'Memory limit exceeded', 13: 'Security violation', 14: 'Coding style violation', 15: 'Wall time-limit exceeded', 18: 'Skipped', 100: 'Unknown result'})], db_index=True),
        ),
        migrations.AlterField(
            model_name='testcheckingresult',
            name='result',
            field=models.PositiveIntegerField(choices=[(0, 'OK'), (1, 'Compilation error'), (2, 'Run-time error'), (3, 'Time-limit exceeded'), (4, 'Presentation error'), (5, 'Wrong answer'), (6, 'Check failed'), (7, 'Partial solution'), (12, 'Memory limit exceeded'), (13, 'Security violation'), (14, 'Coding style violation'), (15, 'Wall time-limit exceeded'), (18, 'Skipped'), (100, 'Unknown result')], validators=[djchoices.choices.ChoicesValidator({0: 'OK', 1: 'Compilation error', 2: 'Run-time error', 3: 'Time-limit exceeded', 4: 'Presentation error', 5: 'Wrong answer', 6: 'Check failed', 7: 'Partial solution', 12: 'Memory limit exceeded', 13: 'Security violation', 14: 'Coding style violation', 15: 'Wall time-limit exceeded', 18: 'Skipped', 100: 'Unknown result'})], db_index=True),
        ),
    ]
