from django import template

register = template.Library()


# items[position], or None when items is not a list or is too short (e.g. a row without row.was).
@register.filter
def index(items, position):
    if not isinstance(items, (list, tuple)):
        return None
    try:
        return items[position]
    except IndexError:
        return None
