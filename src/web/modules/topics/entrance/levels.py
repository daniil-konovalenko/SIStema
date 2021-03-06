import collections
import operator

from modules.entrance import levels
from modules.entrance import models as entrance_models
from sistema.helpers import group_by

from django.db import models as django_models


class EntranceLevelRequirement(django_models.Model):
    """
    Каждое требование задаётся кортежом (tag, max_penalty).
    Это значит, что сумма баллов школьника по всем шкалам всех тем с тегом tag должна отличаться
    от максимальной не более чем на max_penalty.
    """
    questionnaire = django_models.ForeignKey(
        'topics.TopicQuestionnaire',
        on_delete=django_models.CASCADE,
    )

    entrance_level = django_models.ForeignKey(
        entrance_models.EntranceLevel,
        on_delete=django_models.CASCADE,
    )

    tag = django_models.ForeignKey(
        'topics.Tag',
        on_delete=django_models.CASCADE,
    )

    max_penalty = django_models.PositiveIntegerField()

    class Meta:
        unique_together = ('questionnaire', 'entrance_level', 'tag')

    def __str__(self):
        return 'EntranceLevelRequirement(level: {}, tag: {}, max_penalty: {})'.format(
                    self.entrance_level.name, self.tag.title, self.max_penalty)

    def satisfy(self, sum_marks, max_marks):
        return max_marks - sum_marks <= self.max_penalty


# TODO: cache results for each users
class TopicsEntranceLevelLimiter(levels.EntranceLevelLimiter):
    def __init__(self, school):
        super().__init__(school)
        self.questionnaire = self.school.topicquestionnaire
        if self.questionnaire is None:
            raise Exception('modules.topics.entrance.levels.TopicsEntranceLevelLimiter:'
                            'can\'t use TopicsEntranceLevelLimiter without topics questionnaire for this school')

    def get_limit(self, user):
        # TODO: check status, if not FINISHED, return self._find_minimal_level()
        # It's here to avoid cyclic imports
        import modules.topics.models.main as models

        user_marks = models.UserMark.objects.filter(user=user, scale_in_topic__topic__questionnaire=self.questionnaire)\
            .prefetch_related('scale_in_topic__topic__tags')

        requirements = list(EntranceLevelRequirement.objects.filter(questionnaire=self.questionnaire)
                            .prefetch_related('entrance_level'))
        requirements_by_tag = group_by(requirements, operator.attrgetter('tag_id'))
        requirements_by_level = group_by(requirements, operator.attrgetter('entrance_level'))
        sum_marks_for_requirements = collections.defaultdict(int)
        max_marks_for_requirements = collections.defaultdict(int)

        for mark in user_marks:
            scale_in_topic = mark.scale_in_topic
            topic = scale_in_topic.topic
            topic_tags = topic.tags.all()

            for tag in topic_tags:
                for requirement in requirements_by_tag[tag.id]:
                    sum_marks_for_requirements[requirement.id] += mark.mark
                    max_marks_for_requirements[requirement.id] += scale_in_topic.scale.max_mark

        # Если всё плохо, самый просто уровень считаем выполненным — иначе нечего будет решать
        maximum_satisfied_level = entrance_models.EntranceLevel.objects.filter(school=self.school)\
            .order_by('order').first()
        for level, requirements_for_level in requirements_by_level.items():
            all_satisfied = True
            for requirement in requirements_for_level:
                all_satisfied = all_satisfied and requirement.satisfy(sum_marks_for_requirements[requirement.id],
                                                                      max_marks_for_requirements[requirement.id])

            if all_satisfied:
                if level.order > maximum_satisfied_level.order:
                    maximum_satisfied_level = level

        return levels.EntranceLevelLimit(maximum_satisfied_level)
