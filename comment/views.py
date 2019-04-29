from datetime import datetime

from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponseBadRequest
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from video.models import Video
from video.forms import CommentForm
from ratelimit.decorators import ratelimit


# Create your views here.
#ratelime装饰器，限制每个IP每分钟只能submit2次
@ratelimit(key='ip',rate='2/m')
def submit_comment(request, pk):
    """
    提交评论
    :param request:
    :param pk:
    :return:
    """
    video = get_object_or_404(Video, pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        new_comment = form.save(commit=False)
        new_comment.user = request.user
        new_comment.nickname = request.user.nickname
        new_comment.avatar = request.user.avatar
        new_comment.video = video
        new_comment.save()

        data = dict()
        data['nickname'] = request.user.nickname
        data['avatar'] = request.user.avatar
        data['timestamp'] = datetime.fromtimestamp(datetime.now().timestamp())
        data['content'] = new_comment.content

        comments = list()
        comments.append(data)
        html = render_to_string("comment/comment_simple.html", {"comments": comments})

        return JsonResponse({"code": 0, "html": html})
    return JsonResponse({"code": 1, "msg": '评论失败！'})


def get_comments(request):
    if not request.is_ajax():
        return HttpResponseBadRequest()
    page = request.GET.get('page')
    page_size = request.GET.get('page_size')
    video_id = request.GET.get('video_id')
    video = get_object_or_404(Video, pk=video_id)
    comments = video.comment_set.order_by('-timestamp').all()
    comment_count = len(comments)

    paginator = Paginator(comments, page_size)
    try:
        rows = paginator.page(page)
    except PageNotAnInteger:
        rows = paginator.page((1))
    except EmptyPage:
        rows = []

    if len(rows) > 0:
        code = 0
        html = render_to_string("comment/comment_simple.html", {"comments": rows})
    else:
        code = 1
        html = ""

    return JsonResponse({"code": code, "html": html, "comment_count": comment_count})
