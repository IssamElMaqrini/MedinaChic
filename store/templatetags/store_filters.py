from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Template filter pour accéder aux éléments d'un dictionnaire"""
    if dictionary is None:
        return None
    return dictionary.get(int(key)) if key else None
