from django.contrib import admin
from .models import Menu, MenuItem


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1
    fields = ('name', 'url', 'named_url', 'parent')
    show_change_link = True


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    # readonly_fields = ('slug',)

    inlines = [MenuItemInline]

    # Показываем slug только при создании нового меню
    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if obj:  # Если объект уже существует
            fields = [f for f in fields if f != 'slug']
        return fields

    # Автозаполнение slug при создании
    def save_model(self, request, obj, form, change):
        if not change:  # Только при создании
            obj.slug = obj.generate_slug()
        super().save_model(request, obj, form, change)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'menu', 'url', 'named_url', 'parent', 'level')
    list_filter = ('menu',)
    readonly_fields = ('preview_url',)
    fields = ('menu', 'name', 'parent', 'url', 'named_url', 'preview_url')
    search_fields = ('name', 'url', 'named_url')

    def preview_url(self, obj):
        if obj.pk:  # Для существующих объектов
            return f"Будет: <code>{obj.generate_url()}</code>"
        return "Сохраните объект, чтобы увидеть URL"

    preview_url.short_description = "Пример URL"

    def level(self, obj):
        return obj.get_level()

    level.short_description = 'Level'
