from django import template


register = template.Library()


@register.filter
def get_field(form, name):
    try:
        return form[name]
    except Exception:
        return ''


@register.filter
def get_item(mapping, key):
    try:
        return mapping.get(key)
    except Exception:
        return None
