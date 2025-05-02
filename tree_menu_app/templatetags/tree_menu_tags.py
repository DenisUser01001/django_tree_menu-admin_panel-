# tree_menu_app/templatetags/tree_menu_tags.py
from django import template
from django.urls import reverse, resolve
from tree_menu_app.models import Menu, MenuItem

register = template.Library()


@register.inclusion_tag('tree_menu_app/menu.html', takes_context=True)
def draw_menu(context, menu_slug):
    request = context['request']
    current_url = request.path.rstrip('/')
    current_item = context.get('current_item')

    try:
        menu = Menu.objects.prefetch_related('items').get(slug=menu_slug)
    except Menu.DoesNotExist:
        return {'menu': None}

    items = menu.items.all()
    active_item = None
    expanded_items = set()

    # Find active item and its ancestors
    for item in items:
        if item.url and item.url == current_url:
            active_item = item
            break
        elif item.named_url:
            try:
                if reverse(item.named_url) == current_url:
                    active_item = item
                    break
            except:
                continue

    if active_item:
        # Add all ancestors of active item
        parent = active_item.parent
        while parent:
            expanded_items.add(parent.id)
            parent = parent.parent

    return {
        'menu': menu,
        'items': items,
        'active_item': active_item,
        'expanded_items': expanded_items,
        'current_url': current_url,
    }
