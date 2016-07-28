from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.core import mail, urlresolvers
from django.db import transaction
from django.shortcuts import redirect, get_object_or_404

from sistema import settings, decorators
from . import forms
from . import models


def get_email_confirmation_link(request, user):
    return request.build_absolute_uri(urlresolvers.reverse('confirm', args=[user.email_confirmation_token]))


def send_confirmation_email(request, user):
    return 0 < mail.send_mail('Регистрация в ЛКШ',
                              'Здравствуйте, ' + user.first_name + ' ' + user.last_name + '!\n\n'
                              'Кто-то (возможно, и вы) указали этот адрес при регистрации в Летней компьютерной школе (http://sistema.lksh.ru). '
                              'Для окончания регистрации просто пройдите по этой ссылке: ' +
                              get_email_confirmation_link(request, user) + '\n\n' +
                              'Если вы не регистрировались, игнорируйте это письмо.\n\n'
                              'С уважением,\n'
                              'Команда ЛКШ',
                              settings.SERVER_EMAIL,
                              [user.email])


def get_password_recovery_link(request, recovery):
    return request.build_absolute_uri(urlresolvers.reverse('recover', args=[recovery.recovery_token]))


def send_password_recovery_email(request, recovery):
    user = recovery.user
    return 0 < mail.send_mail('Восстановление пароля в ЛКШ',
                              'Здравствуйте, ' + user.first_name + ' ' + user.last_name + '!\n\n'
                              'Для восстановления пароля просто пройдите по этой ссылке: ' +
                              get_password_recovery_link(request, recovery) + '\n\n' +
                              'С уважением,\n'
                              'Команда ЛКШ',
                              settings.SERVER_EMAIL,
                              [user.email])


@transaction.atomic
@decorators.form_handler('user/login.html', forms.AuthForm)
def login(request, form):
    user = auth.authenticate(username=form.cleaned_data['email'], password=form.cleaned_data['password'])
    if user is not None:
        if not user.is_email_confirmed:
            form.add_error('email', 'Электронная почта не подтверждена. Перейдите по ссылке из письма')
            return None

        auth.login(request, user)
        return redirect('home')

    form.add_error('password', 'Неверный пароль')
    return None


@transaction.atomic
@decorators.form_handler('user/registration.html', forms.RegistrationForm)
def register(request, form):
    email = form.cleaned_data['email']

    if models.User.objects.filter(username=email).exists():
        # TODO: make link to forget-password
        form.add_error('email', 'Вы уже зарегистрированы. Забыли пароль?')
        return None

    password = form.cleaned_data['password']
    first_name = form.cleaned_data['first_name']
    last_name = form.cleaned_data['last_name']
    user = models.User.objects.create_user(username=email,
                                           email=email,
                                           password=password,
                                           first_name=first_name,
                                           last_name=last_name,
                                           )

    user.save()
    send_confirmation_email(request, user)

    return redirect('home')


def fill_complete_form(request):
    if not request.user.is_authenticated():
        return redirect('login')
    return {'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            }


@transaction.atomic
@decorators.form_handler('user/complete.html',
                         forms.CompleteUserCreationForm,
                         fill_complete_form)
def complete(request, form):
    email = form.cleaned_data['email']

    if models.User.objects.filter(username=email).exists():
        # TODO: make link to forget-password
        form.add_error('email', 'Вы уже зарегистрированы. Забыли пароль?')
        return None

    request.user.email = email
    request.user.username = request.user.email
    request.user.first_name = form.cleaned_data['first_name']
    request.user.last_name = form.cleaned_data['last_name']
    request.user.set_password(form.cleaned_data['password'])
    request.user.save()

    send_confirmation_email(request, request.user)
    return redirect('home')


# TODO: only POST with csrf token
@login_required
def logout(request):
    auth.logout(request)
    return redirect('home')


@transaction.atomic
def confirm(request, token):
    user = get_object_or_404(models.User, email_confirmation_token=token)

    user.is_email_confirmed = True
    user.save()

    # Don't use authenticate(), for details see
    # http://stackoverflow.com/questions/2787650/manually-logging-in-a-user-without-password
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    auth.login(request, user)
    return redirect('home')


@decorators.form_handler('user/forget.html',
                         forms.ForgetPasswordForm)
def forget(request, form):
    email = form.cleaned_data['email']

    if not models.User.objects.filter(username=email).exists():
        form.add_error('email', 'Пользователя с таким адресом не зарегистрировано')
        return None

    user = models.User.objects.filter(username=email).get()
    recovery = models.UserPasswordRecovery(user=user)
    recovery.save()

    # TODO: show form with message "We've send an email to you"
    send_password_recovery_email(request, recovery)
    return redirect('home')


@decorators.form_handler('user/recover.html',
                         forms.PasswordRecoveryForm)
def recover(request, form, token):
    recoveries = models.UserPasswordRecovery.objects.filter(recovery_token=token, is_used=False)
    if recoveries.exists():
        recovery = recoveries.first()
        recovery.is_used = True
        recovery.save()

        user = recovery.user
        user.set_password(form.cleaned_data['password'])
        user.save()

        # Don't use authenticate(), for details see
        # http://stackoverflow.com/questions/2787650/manually-logging-in-a-user-without-password
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        auth.login(request, user)

        return redirect('home')

    return None