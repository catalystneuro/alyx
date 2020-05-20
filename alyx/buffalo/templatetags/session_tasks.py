from django import template

from buffalo.models import SessionTask

register = template.Library()


@register.filter
def get_tasks(session_id):
    tasks = SessionTask.objects.filter(session__pk=session_id)
    return tasks


@register.filter
def get_users(labMemberObj):
    users_names = labMemberObj.all().values_list("username", flat=True)
    names = ", ".join([name for name in users_names])

    return names
