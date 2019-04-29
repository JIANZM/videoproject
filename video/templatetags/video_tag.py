from datetime import date, datetime
from django.utils.timezone import is_aware, utc

from django import template

register = template.Library()


@register.simple_tag
def user_liked_class(video, user):
    liked = video.user_liked(user)
    if liked == 0:
        return "red"
    else:
        return "grey"


@register.simple_tag
def user_collected_class(video, user):
    collected = video.user_collected(user)
    if collected == 0:
        return "red"
    else:
        return "grey"
