from django.shortcuts import render
from .models import Menu, MenuItem

def index(request):
    """Главная страница со списком всех меню"""
    menus = Menu.objects.all()
    return render(request, 'tree_menu_app/index.html', {'menus': menus})

def menu_page(request, path):
    """Страница пункта меню"""
    menus = Menu.objects.all()

    # Нормализуем URL (убираем лишние слэши)
    current_url = request.path.rstrip('/')

    try:
        current_item = MenuItem.objects.get(url=current_url)
    except MenuItem.DoesNotExist:
        try:
            # Пробуем найти через named_url
            current_item = MenuItem.objects.get(named_url=current_url.strip('/'))
        except MenuItem.DoesNotExist:
            current_item = None

    return render(request, 'tree_menu_app/index.html', {
        'menus': menus,
        'current_item': current_item,
        'current_url': current_url,
    })
