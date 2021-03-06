from django.contrib import admin

import users.admin
from modules.smartq import models


@admin.register(models.Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        'short_name',
        'created_date',
        'modified_date',
    )


@admin.register(models.GeneratedQuestion)
@admin.register(models.StaffGeneratedQuestion)
class GeneratedQuestionAdmin(users.admin.UserAutocompleteModelAdminMixIn,
                             admin.ModelAdmin):
    list_display = (
        'base_question',
        'seed',
        'user',
    )

    list_filter = (
        'base_question',
    )

    search_fields = (
        'base_question__short_name',
        '=seed',
        'user__profile__first_name',
        'user__profile__middle_name',
        'user__profile__last_name',
    )
