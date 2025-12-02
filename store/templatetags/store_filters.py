from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Template filter pour accéder aux éléments d'un dictionnaire"""
    if dictionary is None:
        return None
    return dictionary.get(int(key)) if key else None


@register.filter
def get_field(form, field_name):
    """Template filter pour accéder à un champ de formulaire par son nom"""
    if form is None or field_name is None:
        return None
    try:
        return form[field_name]
    except KeyError:
        return None
