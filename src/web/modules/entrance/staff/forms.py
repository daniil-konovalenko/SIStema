from django import forms

import sistema.forms

from .. import models


class FileEntranceExamTasksMarkForm(forms.Form):
    FIELD_ID_TEMPLATE = 'tasks__file__mark_%d'

    def __init__(self, tasks, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for task in tasks:
            field_id = self.FIELD_ID_TEMPLATE % task.id
            self.fields[field_id] = forms.IntegerField(min_value=0,
                                                       max_value=task.max_score,
                                                       widget=forms.HiddenInput(attrs={'id': field_id}),
                                                       required=False,
                                                       )
            self.fields[field_id].task_id = task.id

    def set_initial_mark(self, task_id, mark):
        field_id = self.FIELD_ID_TEMPLATE % task_id
        self.fields[field_id].initial = mark


class EntranceRecommendationForm(forms.Form):
    comment = forms.CharField(widget=sistema.forms.TextInputWithFaIcon(attrs={'fa': 'comment'}),
                              label='Комментарий',
                              required=False)

    score = forms.IntegerField(label='Баллы', initial=0)

    RECOMMENDED_PARALLEL_UNFILLED = -2

    recommended_parallel = forms.TypedChoiceField(widget=forms.Select(),
                                                  label='Рекомендованная параллель',
                                                  coerce=int,
                                                  )

    def __init__(self, school, *args, **kwargs):
        super().__init__(*args, **kwargs)

        parallels = school.parallels.all()
        parallels = [(p.id, p.name) for p in parallels]

        available_parallels = [(self.RECOMMENDED_PARALLEL_UNFILLED, 'Выберите параллель'), (-1, 'Не зачислить')] + list(parallels)
        self.fields['recommended_parallel'].choices = available_parallels


class PutIntoCheckingGroupForm(forms.Form):
    def __init__(self, school, *args, **kwargs):
        super().__init__(*args, **kwargs)

        groups = models.CheckingGroup.objects.filter(for_school=school)
        groups = [(g.id, g.name) for g in groups]
        self.fields['group_id'] = forms.ChoiceField(widget=forms.Select(), choices=list(groups))