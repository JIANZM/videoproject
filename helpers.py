import smtplib

from django.http import HttpResponseBadRequest, HttpResponse
from django.views.generic import View
from django.shortcuts import redirect
from django.utils.html import strip_tags
from django.conf import settings
from django.core.mail import send_mass_mail, send_mail
from django.core.exceptions import PermissionDenied


def get_page_list(paginator, page):
    page_list = []
    if paginator.num_pages > 10:
        if page.numgber <= 5:
            start_page = 1
        elif page.numgber > paginator.num_pages - 5:
            start_page = paginator.num_pages - 9
        else:
            start_page = page.numgber - 5

        for i in range(start_page, start_page + 10):
            page_list.append(i)

    else:
        for i in range(1, paginator.num_pages + 1):
            page_list.append(i)

    return page_list


def ajax_required(func):
    def wrapper(request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest()
        else:
            return func(request, *args, **kwargs)

    wrapper.__doc__ = func.__doc__
    wrapper.__name__ = func.__name__
    return wrapper


class AuthorRequiredMixin(View):
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj != self.request.user:
            raise PermissionDenied('用户无权限')
        return super().dispatch(request, *args, **kwargs)


class AdminUserRequiredMixin(View):
    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_staff:
            return redirect('myadmin:login')
        return super().dispatch(request, *args, **kwargs)


class SuperUserRequiredMixin(View):
    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_superuser:
            return HttpResponse('无权限')

        return super().dispatch(request, *args, **kwargs)


def send_html_email(subject, html_message, to_list):
    plain_message = strip_tags(html_message)
    from_email = settings.EMAIL_HOST_USER
    send_mail(subject, plain_message, from_email, to_list, html_message=html_message)


def send_email(subject, content, to_list):
    """
    example
    :param subject:邮件标题
    :param content:邮件内容
    :param to_list:待发邮件列表
    :return:
    """
    try:
        message = (subject, content, settings.EMAIL_HOST_USER, to_list)
        # do not forget set password
        print("--> is sending email")
        send_mass_mail((message,))
    except smtplib.SMTPException:
        print("--> send fail")
        return HttpResponse("fail")
    else:
        print("--> send success")
        return HttpResponse("success")
