import copy
import operator

import django.forms
import django.utils.timezone
import djchoices
import polymorphic.models
from cached_property import cached_property
from django.core import urlresolvers
from django.db import models, transaction, IntegrityError

import frontend.forms
import schools.models
import sistema.models
import users.models
from sistema.helpers import group_by
from . import forms


class AbstractQuestionnaireBlock(polymorphic.models.PolymorphicModel):
    questionnaire = models.ForeignKey(
        'Questionnaire',
        on_delete=models.CASCADE,
        related_name='blocks',
    )

    short_name = models.CharField(
        max_length=100,
        help_text='Используется в урлах. Лучше обойтись латинскими буквами, '
                  'цифрами и подчёркиванием')

    order = models.IntegerField(
        default=0,
        help_text='Блоки выстраиваются по возрастанию порядка')

    is_question = False

    def __str__(self):
        return '%s. %s' % (self.questionnaire, self.short_name)

    class Meta:
        verbose_name = 'questionnaire block'
        unique_together = [('short_name', 'questionnaire'),
                           ('questionnaire', 'order')]
        ordering = ('questionnaire_id', 'order')

    def copy_to_questionnaire(self, to_questionnaire):
        """
        Make a copy of this block in the specified questionnaire.

        In order for this method to work correctly for each particular subclass
        the subclass should override _copy_fields_to_instance.

        :param to_questionnaire: A questionnaire to copy the block to.
        """
        new_instance = self.__class__(
            questionnaire=to_questionnaire,
            short_name=self.short_name,
            order=self.order,
        )
        self._copy_fields_to_instance(new_instance)
        new_instance.save()
        self._copy_dependencies_to_instance(new_instance)
        return new_instance

    def _copy_fields_to_instance(self, other):
        """
        Subclasses must override this method. The implementation should:
        - call super()._copy_fields_to_instance(other),
        - copy its field values to the passed instance.

        :param other: The instance to copy field values to.
        """
        pass

    def _copy_dependencies_to_instance(self, other):
        """
        Override this method in a subclass to copy any objects having a
        reference to this block.

        The override must:
        - call super()._copy_dependencies_to_instance(other),
        - make copies of the dependencies for the passed instance.

        :param other: The instance to copy dependencies for.
        """
        pass


class MarkdownQuestionnaireBlock(AbstractQuestionnaireBlock):
    block_name = 'markdown'

    markdown = models.TextField()

    def __str__(self):
        return self.markdown[:40]

    def _copy_fields_to_instance(self, other):
        super()._copy_fields_to_instance(other)
        other.markdown = self.markdown


class AbstractQuestionnaireQuestion(AbstractQuestionnaireBlock):
    is_question = True

    text = models.TextField(help_text='Вопрос')

    is_required = models.BooleanField(
        help_text='Является ли вопрос обязательным',
    )

    help_text = models.CharField(
        max_length=400,
        blank=True,
        help_text='Подсказка, помогающая ответить на вопрос',
    )

    is_disabled = models.BooleanField(
        default=False,
        help_text='Выключена ли возможность ответить на вопрос. Не может быть '
                  'отмечено одновременно с is_required',
    )

    def get_form_field(self, attrs=None):
        raise NotImplementedError(
            'Child should implement its own method get_form_field()')

    def save(self, *args, **kwargs):
        if self.is_disabled and self.is_required:
            raise IntegrityError(
                'questionnaire.AbstractQuestionnaireBlock: is_disabled can not '
                'be set with is_required')
        super().save(*args, **kwargs)

    def __str__(self):
        return '%s: %s' % (self.questionnaire, self.text)

    def _copy_fields_to_instance(self, other):
        super()._copy_fields_to_instance(other)
        other.text = self.text
        other.is_required = self.is_required
        other.help_text = self.help_text
        other.is_disabled = self.is_disabled


class TextQuestionnaireQuestion(AbstractQuestionnaireQuestion):
    block_name = 'text_question'

    is_multiline = models.BooleanField()

    placeholder = models.TextField(
        blank=True,
        help_text='Подсказка, показываемая в поле для ввода; пример',
    )

    fa = models.CharField(
        max_length=20,
        blank=True,
        help_text='Имя иконки FontAwesome, которую нужно показать в поле',
    )

    def _copy_fields_to_instance(self, other):
        super()._copy_fields_to_instance(other)
        other.is_multiline = self.is_multiline
        other.placeholder = self.placeholder
        other.fa = self.fa

    def get_form_field(self, attrs=None):
        if attrs is None:
            attrs = {}

        if 'placeholder' not in attrs:
            attrs['placeholder'] = self.placeholder

        if self.is_multiline:
            attrs['class'] = 'gui-textarea ' + attrs.pop('class', '')
        else:
            attrs['class'] = 'gui-input ' + attrs.pop('class', '')

        if self.fa != '':
            if 'fa' not in attrs:
                attrs['fa'] = self.fa
            if self.is_multiline:
                widget = frontend.forms.TextareaWithFaIcon(attrs)
            else:
                widget = frontend.forms.TextInputWithFaIcon(attrs)
        else:
            if self.is_multiline:
                widget = django.forms.Textarea(attrs)
            else:
                widget = django.forms.TextInput(attrs)

        return django.forms.CharField(
            required=self.is_required,
            disabled=self.is_disabled,
            help_text=self.help_text,
            label=self.text,
            widget=widget,
        )


class ChoiceQuestionnaireQuestionVariant(models.Model):
    text = models.TextField()

    question = models.ForeignKey(
        'ChoiceQuestionnaireQuestion',
        on_delete=models.CASCADE,
        related_name='variants',
    )

    order = models.PositiveIntegerField(default=0)

    # If variant is disabled it shows as gray and can't be selected
    is_disabled = models.BooleanField(default=False)

    # If this one is selected all options are disabled
    disable_question_if_chosen = models.BooleanField(default=False)

    class Meta:
        unique_together = ('question', 'order')

    def __str__(self):
        return '{}: {} {}'.format(self.question, self.id, self.text)


class ChoiceQuestionnaireQuestion(AbstractQuestionnaireQuestion):
    block_name = 'choice_question'

    is_multiple = models.BooleanField()

    is_inline = models.BooleanField()

    def _copy_fields_to_instance(self, other):
        super()._copy_fields_to_instance(other)
        other.is_multiple = self.is_multiple
        other.is_inline = self.is_inline

    def _copy_dependencies_to_instance(self, other):
        super()._copy_dependencies_to_instance(other)
        for variant in self.variants.all():
            variant.pk = None
            variant.question = other
            variant.save()

    def get_form_field(self, attrs=None):
        if attrs is None:
            attrs = {}

        choices = ((v.id, {'label': v.text, 'disabled': v.is_disabled})
                   for v in self.variants.order_by('order', 'id'))

        attrs['inline'] = self.is_inline
        if self.is_multiple:
            field_class = forms.TypedMultipleChoiceFieldForChoiceQuestion
            widget_class = frontend.forms.SistemaCheckboxSelect
        else:
            field_class = forms.TypedChoiceFieldForChoiceQuestion
            widget_class = frontend.forms.SistemaRadioSelect

        return field_class(
            question=self,
            required=self.is_required,
            disabled=self.is_disabled,
            coerce=int,
            choices=choices,
            widget=widget_class(attrs=attrs),
            label=self.text,
            help_text=self.help_text,
        )


class YesNoQuestionnaireQuestion(AbstractQuestionnaireQuestion):
    block_name = 'yesno_question'

    def get_form_field(self, attrs=None):
        if attrs is None:
            attrs = {}

        return django.forms.TypedChoiceField(
            required=self.is_required,
            disabled=self.is_disabled,
            coerce=lambda x: x == 'True',
            choices=((False, 'Нет'), (True, 'Да')),
            widget=frontend.forms.SistemaRadioSelect(attrs=attrs),
            label=self.text,
            help_text=self.help_text,
        )


class DateQuestionnaireQuestion(AbstractQuestionnaireQuestion):
    block_name = 'date_question'

    with_year = models.BooleanField(default=True)

    min_year = models.PositiveIntegerField(null=True)

    max_year = models.PositiveIntegerField(null=True)

    def _copy_fields_to_instance(self, other):
        super()._copy_fields_to_instance(other)
        other.with_year = self.with_year
        other.min_year = self.min_year
        other.max_year = self.max_year

    def get_form_field(self, attrs=None):
        return django.forms.DateField(
            required=self.is_required,
            disabled=self.is_disabled,
            label=self.text,
            help_text=self.help_text,
            widget=django.forms.DateInput(attrs={
                'class': 'gui-input datetimepicker',
                'data-format': 'DD.MM.YYYY',
                'data-view-mode': 'years',
                'data-pick-time': 'false',
                'placeholder': 'дд.мм.гггг',
            }),
        )


class Questionnaire(models.Model):
    title = models.CharField(max_length=100, help_text='Название анкеты')

    short_name = models.CharField(
        max_length=100,
        help_text='Используется в урлах. Лучше обойтись латинскими буквами, '
                  'цифрами и подчёркиванием',
    )

    school = models.ForeignKey(
        schools.models.School,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    session = models.ForeignKey(
        schools.models.Session,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    close_time = models.ForeignKey(
        'dates.KeyDate',
        on_delete=models.SET_NULL,
        related_name='+',
        blank=True,
        null=True,
        verbose_name='Время закрытия',
        help_text='Начиная с этого момента пользователи видят анкету в режиме '
                  'только для чтения',
    )

    enable_autofocus = models.BooleanField(
        default=True,
        help_text='Будет ли курсор автоматически фокусироваться на первом '
                  'вопросе при загрузке страницы',
    )

    should_record_typing_dynamics = models.BooleanField(default=False)

    class Meta:
        unique_together = ('school', 'short_name')

    def __str__(self):
        if self.school is not None:
            return '%s. %s' % (self.school, self.title)
        return self.title

    def save(self, *args, **kwargs):
        if (self.school is not None and self.session is not None and
                self.session.school != self.school):
            raise IntegrityError(
                "Questionnaire's session should belong to the questionnaire's "
                "school")
        super().save(*args, **kwargs)

    # TODO: Extract to ModelWithCloseTime?
    def is_closed_for_user(self, user):
        return (self.close_time is not None and
                self.close_time.passed_for_user(user))

    @cached_property
    def ordered_blocks(self):
        return self.blocks.order_by('order')

    @cached_property
    def questions(self):
        return self.blocks.instance_of(AbstractQuestionnaireQuestion)

    @cached_property
    def ordered_questions(self):
        return self.questions.order_by('order')

    @cached_property
    def show_conditions(self):
        conditions = (QuestionnaireBlockShowCondition.objects
                      .filter(block__questionnaire=self))
        return group_by(conditions, operator.attrgetter('block_id'))

    def get_form_class(self, attrs=None):
        if attrs is None:
            attrs = {}

        fields = {
            'prefix': self.get_prefix(),
        }

        is_first = True
        for question in self.ordered_questions:
            question_attrs = copy.copy(attrs)
            if is_first:
                if self.enable_autofocus:
                    question_attrs['autofocus'] = 'autofocus'
                is_first = False

            fields[question.short_name] = (
                question.get_form_field(question_attrs))

        form_class = type('%sForm' % self.short_name.title(),
                          (forms.QuestionnaireForm,),
                          fields)
        return form_class

    def get_prefix(self):
        return 'questionnaire_' + self.short_name

    def get_absolute_url(self):
        if self.school is None:
            return urlresolvers.reverse(
                'questionnaire',
                kwargs={'questionnaire_name': self.short_name},
            )
        else:
            return urlresolvers.reverse(
                'school:questionnaire',
                kwargs={'questionnaire_name': self.short_name,
                        'school_name': self.school.short_name}
            )

    def is_filled_by(self, user):
        user_status = self.statuses.filter(user=user).first()
        if user_status is None:
            return False

        return user_status.status == UserQuestionnaireStatus.Status.FILLED

    # A unique object used as the default argument value in the clone method.
    # Needed, because we want to handle None.
    KEEP_VALUE = object()

    @transaction.atomic
    def clone(self,
              new_school=KEEP_VALUE,
              new_short_name=KEEP_VALUE,
              new_session=KEEP_VALUE,
              new_close_time=KEEP_VALUE):
        """
        Make and return a full copy of the questionnaire. The copy should have
        a unique `(school, short_name)` combination. You can change either of
        them by setting the corresponding method argument.

        :param new_school: The school for the new questionnaire. By default is
            equal to the source questionnaire's school.
        :param new_short_name: The short name for the new questionnaire. By
            default is equal to the source questionnaire's school.
        :param new_session: The session for the new questionnaire. By default
            keeps its value if the school is unchanged, or is set to None
            otherwise.
        :param new_close_time: The `dates.KeyDate` object for the closing time.
            By default keeps its value if the school is unchanged, or is set to
            `None` otherwise.
        :return: The fresh copy of the questionnaire.
        """
        if self.pk is None:
            raise ValueError(
                "The questionnaire should be in database to be cloned")

        if new_school == self.KEEP_VALUE:
            new_school = self.school
        if new_short_name == self.KEEP_VALUE:
            new_short_name = self.short_name
        school_unchanged = (new_school == self.school)
        if new_session == self.KEEP_VALUE:
            new_session = self.session if school_unchanged else None
        if new_close_time == self.KEEP_VALUE:
            new_close_time = self.close_time if school_unchanged else None

        # Copy
        new_questionnaire = Questionnaire.objects.get(pk=self.pk)
        new_questionnaire.pk = None
        new_questionnaire.school = new_school
        new_questionnaire.short_name = new_short_name
        new_questionnaire.session = new_session
        new_questionnaire.close_time = new_close_time
        new_questionnaire.save()

        self._copy_blocks_to_questionnaire(new_questionnaire)
        self._copy_block_show_conditions_to_questionnaire(new_questionnaire)

        return new_questionnaire

    def _copy_blocks_to_questionnaire(self, to_questionnaire):
        for block in self.blocks.all():
            block.copy_to_questionnaire(to_questionnaire)

    def _copy_block_show_conditions_to_questionnaire(self, to_questionnaire):
        """
        Copy all the `QuestionnaireBlockShowCondition` objects to the specified
        questionnaire.

        Conditions are skipped if the target questionnaire doesn't have a block
        with the same `short_name` or a variant with the same `order`.

        :param to_questionnaire: The questionnaire to copy the conditions to.
        :return: (<number of copied conditions>, <number of skipped conditions>)
        """
        copied_count = 0
        skipped_count = 0
        for block in self.blocks.all():
            for condition in block.show_conditions.all():
                new_condition = (
                    condition.copy_condition_to_questionnaire(to_questionnaire))
                if new_condition is None:
                    skipped_count += 1
                else:
                    copied_count += 1
        return copied_count, skipped_count


class QuestionnaireAnswer(models.Model):
    questionnaire = models.ForeignKey(
        Questionnaire,
        on_delete=models.CASCADE,
        related_name='answers',
    )

    user = models.ForeignKey(
        users.models.User,
        on_delete=models.CASCADE,
        related_name='questionnaire_answers',
    )

    # TODO: may be ForeignKey is better?
    question_short_name = models.CharField(max_length=100)

    answer = models.TextField(blank=True)

    def __str__(self):
        return 'Ответ «%s» на вопрос %s анкеты %s' % (
            self.answer.replace('\n', '\\n'),
            self.question_short_name,
            self.questionnaire,
        )

    @property
    def question(self):
        return AbstractQuestionnaireQuestion.objects.filter(
            questionnaire=self.questionnaire,
            short_name=self.question_short_name).first()

    class Meta:
        index_together = ('questionnaire', 'user', 'question_short_name')


# TODO: maybe extract base class for this and
#       modules.topics.models.UserQuestionnaireStatus?
class UserQuestionnaireStatus(models.Model):
    class Status(djchoices.DjangoChoices):
        NOT_FILLED = djchoices.ChoiceItem(1)
        FILLED = djchoices.ChoiceItem(2)

    user = models.ForeignKey(
        users.models.User,
        on_delete=models.CASCADE,
        related_name='+',
    )

    questionnaire = models.ForeignKey(
        Questionnaire,
        on_delete=models.CASCADE,
        related_name='statuses',
    )

    status = models.PositiveIntegerField(
        choices=Status.choices,
        validators=[Status.validator],
    )

    class Meta:
        verbose_name_plural = 'User questionnaire statuses'
        unique_together = ('user', 'questionnaire')

    def __str__(self):
        return 'Status {} of {} for {}'.format(
            self.status, self.questionnaire, self.user)


class QuestionnaireBlockShowCondition(models.Model):
    # If there is at least one conditions for `block`,
    # it will be visible only if one `need_to_be_checked` is checked
    block = models.ForeignKey(
        AbstractQuestionnaireBlock,
        on_delete=models.CASCADE,
        related_name='show_conditions',
    )

    need_to_be_checked = models.ForeignKey(
        ChoiceQuestionnaireQuestionVariant,
        on_delete=models.CASCADE,
        related_name='+',
    )

    def __str__(self):
        return 'Show %s only if %s' % (self.block, self.need_to_be_checked)

    def copy_condition_to_questionnaire(self, to_questionnaire):
        """
        Copy block show condition to the specified questionnaire. Shouldn't be
        used outside questionnaire.models.

        Target questionnaire should have a block with the same `short_name` and
        a variant with the same `order`. Otherwise the copy is not created.

        :param to_questionnaire: The questionnaire to copy the condition to.
        :return: The new `QuestionnaireBlockShowCondition` on success or `None`
            on failre.
        """
        target_block = (
            to_questionnaire.blocks
            .filter(short_name=self.block.short_name)
            .first())
        if target_block is None:
            return None

        source_variant_block = self.need_to_be_checked.question
        target_variant = (
            ChoiceQuestionnaireQuestionVariant.objects
            .filter(
                question__questionnaire=to_questionnaire,
                question__short_name=source_variant_block.short_name,
                order=self.need_to_be_checked.order)
            .first())
        if target_variant is None:
            return None

        return QuestionnaireBlockShowCondition.objects.create(
            block=target_block,
            need_to_be_checked=target_variant,
        )


# Used to evaluate fraction of accounts where different persons filled
# questionnaires for students and parents. The estimation will be biased, but
# we will probably be able to measure changes in the next year comparing with
# the current one.
class QuestionnaireTypingDynamics(models.Model):
    user = models.ForeignKey(
        users.models.User,
        on_delete=models.CASCADE,
        related_name='+',
    )

    questionnaire = models.ForeignKey(
        Questionnaire,
        on_delete=models.CASCADE,
        related_name='+',
    )

    typing_data = sistema.models.CompressedTextField(
        help_text='JSON с данными о нажатиях клавиш'
    )

    created_at = models.DateTimeField(auto_now_add=True)
