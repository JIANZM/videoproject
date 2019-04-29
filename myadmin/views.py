import datetime
import smtplib
import logging

from django.shortcuts import render, redirect, reverse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.views import generic
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.conf import settings
from django.template.loader import render_to_string

from chunked_upload.views import ChunkedUploadView, ChunkedUploadCompleteView

from .forms import UserLoginForm, ClassificationEditForm, ClassificationAddForm, UserEditForm, UserAddForm
from .models import MyChunkedUpload
from helpers import AdminUserRequiredMixin, SuperUserRequiredMixin, get_page_list, ajax_required, send_html_email
from video.models import Video, Classification
from users.models import User, Feedback
from comment.models import Comment

logger = logging.getLogger('my_logger')


# Create your views here.
def login(request):
    if request.method == 'POST':
        form = UserLoginForm(request=request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None and user.is_staff:
                auth_login(request, user)
                return redirect('myadmin:index')
            else:
                form.add_error('', '请输入管理员账号')
    else:
        form = UserLoginForm()
    return render(request, 'myadmin/login.html', {'form': form})


def logout(request):
    auth_logout(request)
    return redirect('myadmin:login')


class IndexView(AdminUserRequiredMixin, generic.View):
    """
    数据总览
    """

    def get(self, request):
        video_count = Video.objects.get_count()
        video_has_published_count = Video.objects.get_published_count()
        video_not_published_count = Video.objects.get_not_published_count()
        user_count = User.objects.count()
        user_today_count = User.objects.exclude(date_joined__lt=datetime.date.today()).count()
        comment_count = Comment.objects.get_count()
        comment_today_count = Comment.objects.get_today_count()
        data = {"video_count": video_count,
                "video_has_published_count": video_has_published_count,
                "video_not_published_count": video_not_published_count,
                "user_count": user_count,
                "user_today_count": user_today_count,
                "comment_count": comment_count,
                "comment_today_count": comment_today_count}
        return render(self.request, 'myadmin/index.html', data)


class AddVideoView(SuperUserRequiredMixin, generic.TemplateView):
    template_name = 'myadmin/video_add.html'


class MyChunkedUploadView(ChunkedUploadView):
    model = MyChunkedUpload
    field_name = 'the_file'


class MyChunkedUploadCompleteView(ChunkedUploadCompleteView):
    model = MyChunkedUpload

    def on_completion(self, uploaded_file, request):
        print('uploaded--->', uploaded_file.name)
        pass

    def get_response_data(self, chunked_upload, request):
        video = Video.objects.create(file=chunked_upload.file)
        return {'code': 0, 'video_id': video.id, 'msg': 'success'}


class VideoListView(AdminUserRequiredMixin, generic.ListView):
    model = Video
    template_name = 'myadmin/video_list.html'
    context_object_name = 'video_list'
    paginate_by = 2
    q = ''

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(VideoListView, self).get_context_data(**kwargs)
        paginator = context.get('paginator')
        page = context.get('page_obj')
        page_list = get_page_list(paginator, page)
        context['page_list'] = page_list
        context['q'] = self.q
        return context

    def get_queryset(self):
        self.q = self.request.GET.get('q', "")
        return Video.objects.get_search_list(self.q)


class ClassificationListView(AdminUserRequiredMixin, generic.ListView):
    model = Classification
    template_name = 'myadmin/classification_list.html'
    context_object_name = 'classification_list'
    paginate_by = 10
    q = ''

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(ClassificationListView, self).get_context_data(**kwargs)
        paginator = context['paginator']
        page = context['page_obj']
        page_list = get_page_list(paginator, page)
        context['page_list'] = page_list
        context['q'] = self.q
        return context

    def get_queryset(self):
        self.q = self.request.GET.get('q', '')
        return Classification.objects.filter(title__contains=self.q)


class ClassificationAddView(AdminUserRequiredMixin, generic.View):
    def get(self, request):
        form = ClassificationAddForm()
        return render(self.request, 'myadmin/classification_add.html', {'form': form})

    def post(self, request):
        form = ClassificationAddForm(data=request.POST)
        if form.is_valid():
            form.save(commit=True)
            return render(self.request, 'myadmin/classification_add_success.html')
        return render(self.request, 'myadmin/classification_add.html', {'form': form})


@ajax_required
@require_http_methods(["POST"])
def classification_delete(request):
    if not request.user.is_superuser:
        return JsonResponse({'code': 1, 'msg': '无删除权限'})
    classification_id = request.POST['classification_id']
    instance = Classification.objects.get(id=classification_id)
    instance.delete()
    return JsonResponse({'code': 0, 'msg': 'success'})


class ClassificationEditView(SuperUserRequiredMixin, generic.UpdateView):
    model = Classification
    form_class = ClassificationEditForm
    template_name = 'myadmin/classification_edit.html'

    def get_success_url(self):
        messages.success(self.request, '保存成功')
        return reverse('myadmin:classification_edit', kwargs={'pk': self.kwargs['pk']})


class CommentListView(AdminUserRequiredMixin, generic.ListView):
    model = Comment
    template_name = 'myadmin/comment_list.html'
    context_object_name = 'comment_list'
    paginate_by = 10
    q = ''

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(CommentListView, self).get_context_data(**kwargs)
        paginator = context.get('paginator')
        page = context.get('page_obj')
        page_list = get_page_list(paginator, page)
        context['page_list'] = page_list
        context['q'] = self.q
        return context

    def get_queryset(self):
        self.q = self.request.GET.get("q", "")
        return Comment.objects.filter(content__contains=self.q).order_by('-timestamp')


@ajax_required
@require_http_methods(["POST"])
def comment_delete(request):
    if not request.user.is_superuser:
        return JsonResponse({"code": 1, "msg": "无删除权限"})
    comment_id = request.POST['comment_id']
    instance = Comment.objects.get(id=comment_id)
    instance.delete()
    return JsonResponse({"code": 0, "msg": "success"})


class UserListView(AdminUserRequiredMixin, generic.ListView):
    model = User
    template_name = 'myadmin/user_list.html'
    context_object_name = 'user_list'
    paginate_by = 10
    q = ''

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(UserListView, self).get_context_data(**kwargs)
        paginator = context.get('paginator')
        page = context.get('page_obj')
        page_list = get_page_list(paginator, page)
        context['page_list'] = page_list
        context['q'] = self.q
        return context

    def get_queryset(self):
        self.q = self.request.GET.get("q", "")
        return User.objects.filter(username__contains=self.q).order_by('-date_joined')


class UserAddView(SuperUserRequiredMixin, generic.View):
    def get(self, request):
        form = UserAddForm()
        return render(self.request, 'myadmin/user_add.html', {'form': form})

    def post(self, request):
        form = UserAddForm(data=request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')
            user.set_password(password)
            user.save()
            return render(self.request, 'myadmin/user_add_success.html')
        return render(self.request, 'myadmin/user_add.html', {'form': form})


class UserEditView(SuperUserRequiredMixin, generic.UpdateView):
    model = User
    form_class = UserEditForm
    template_name = 'myadmin/user_edit.html'

    def get_success_url(self):
        messages.success(self.request, "保存成功")
        return reverse('myadmin:user_edit', kwargs={'pk': self.kwargs['pk']})


@ajax_required
@require_http_methods(["POST"])
def user_delete(request):
    if not request.user.is_superuser:
        return JsonResponse({"code": 1, "msg": "无删除权限"})
    user_id = request.POST['user_id']
    instance = User.objects.get(id=user_id)
    if instance.is_superuser:
        return JsonResponse({"code": 1, "msg": "不能删除管理员"})
    instance.delete()
    return JsonResponse({"code": 0, "msg": "success"})


class SubscribeView(SuperUserRequiredMixin, generic.View):
    """
    订阅推送
    """

    def get(self, request):
        """
        页面展示
        :param request:
        :return:
        """
        video_list = Video.objects.get_published_list()
        return render(request, 'myadmin/subscribe.html', {'video_list': video_list})

    def post(self, request):
        """
        邮件发送
        :param request:
        :return:
        """
        if not request.user.is_superuser:
            return JsonResponse({"code": 1, "msg": "无权限"})
        video_id = request.POST['video_id']
        video = Video.objects.get(id=video_id)
        subject = video.title
        context = {'video': video, 'site_url': settings.SITE_URL}
        html_message = render_to_string('myadmin/mail_template.html', context)
        email_list = User.objects.filter(subscribe=True).values_list('email', flat=True)
        email_list = [email_list[i:i + 2] for i in range(0, len(email_list), 2)]

        if email_list:
            for to_list in email_list:
                try:
                    send_html_email(subject, html_message, to_list)
                except smtplib.SMTPException as e:
                    logger.error(e)
                    return JsonResponse({"code": 1, "msg": "发送失败"})
            return JsonResponse({"code": 0, "msg": "success"})
        else:
            return JsonResponse({"code": 1, "msg": "邮件列表为空"})


class FeedbackListView(AdminUserRequiredMixin, generic.ListView):
    model = Feedback
    template_name = 'myadmin/feedback_list.html'
    context_object_name = 'feedback_list'
    paginate_by = 10
    q = ''

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(FeedbackListView, self).get_context_data(**kwargs)
        paginator = context.get('paginator')
        page = context.get('page_obj')
        page_list = get_page_list(paginator, page)
        context['page_list'] = page_list
        context['q'] = self.q
        return context

    def get_queryset(self):
        self.q = self.request.GET.get("q", "")
        return Feedback.objects.filter(content__contains=self.q).order_by('-timestamp')


@ajax_required
@require_http_methods(["POST"])
def feedback_delete(request):
    if not request.user.is_superuser:
        return JsonResponse({"code": 1, "msg": "无删除权限"})
    feedback_id = request.POST['feedback_id']
    instance = Feedback.objects.get(id=feedback_id)
    instance.delete()
    return JsonResponse({"code": 0, "msg": "success"})
