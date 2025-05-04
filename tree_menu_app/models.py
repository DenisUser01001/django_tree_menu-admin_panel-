from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.urls import reverse, NoReverseMatch
from urllib.parse import urlparse


class Menu(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_slug()
        super().save(*args, **kwargs)

    def generate_slug(self):
        return slugify(self.name)

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=100)
    url = models.CharField(max_length=200, blank=True, verbose_name="URL (Не заполняйте для авто-генерации)")
    named_url = models.CharField(max_length=100, blank=True, verbose_name="Named URL")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    class Meta:
        ordering = ['id']

    def clean(self):
        # Добавляем проверку на пустой slug
        if not slugify(self.name, allow_unicode=True):
            raise ValidationError("Название должно содержать буквы или цифры")

        # Запрещаем создание вложенных элементов для нового меню
        if self.parent and self.parent.menu_id and not Menu.objects.filter(pk=self.parent.menu_id).exists():
            raise ValidationError("Нельзя создавать вложенные элементы для несохраненного меню. Сначала сохраните меню.")

        # Проверка взаимоисключения полей
        if self.url and self.named_url:
            raise ValidationError("Можно задать либо URL, либо Named URL, одновременное задание обоих невозможно.")

        # Автогенерация URL если оба поля пусты
        if not self.url and not self.named_url:
            self.url = self.generate_url()

        # Валидация named_url
        if self.named_url:
            try:
                reverse(self.named_url)
            except NoReverseMatch:
                raise ValidationError(f"Named URL '{self.named_url}' не существует в urls.py")

        # Полная валидация ручного URL
        if self.url:
            # Проверка, что меню уже создано, имеет свой слаг, который будет использоваться для генерации URL
            if not self.menu_id:
                raise ValidationError("Сначала сохраните меню перед добавлением пунктов для дальнейшей создания URL элементов")

            # Проверка формата (слеши)
            if not (self.url.startswith('/') and self.url.endswith('/')):
                raise ValidationError("URL должен начинаться и заканчиваться слешем (/).")

            # Проверка на повторяющиеся слеши
            if '//' in self.url:
                raise ValidationError("URL не должен содержать повторяющихся слешей (//).")

            # Проверка принадлежности к меню
            required_menu_prefix = f"/{slugify(self.menu.slug)}/"
            if not self.url.startswith(required_menu_prefix):
                raise ValidationError(
                    f"URL должен начинаться с '/{slugify(self.menu.slug)}/'. "
                    f"Текущий URL: '{self.url}'"
                )

            # Проверка уровня вложенности на основе свойства level
            url_depth = self.url.strip('/').count('/')  # Глубина URL
            expected_depth = self.level + 1  # Ожидаемая глубина

            if url_depth != expected_depth:
                raise ValidationError(
                    f"Некорректная глубина URL. Уровень элемента: {self.level}\n"
                    f"Ожидается {expected_depth} сегмента(ов) после '/{self.menu.slug}/', "
                    f"получено {url_depth}.\n"
                )

            # Проверка соответствия родительскому URL (для вложенных элементов)
            if self.parent and not self.url.startswith(self.parent.url.rstrip('/') + '/'):
                raise ValidationError(
                    f"URL должен начинаться с родительского пути '{self.parent.url}'\n"
                    f"Ожидается: '{self.parent.url.rstrip('/')}/{slugify(self.name)}/'"
                )


    # def generate_url(self):
    #     """Генерирует URL с гарантией слешей в начале и конце"""
    #     path = slugify(self.name)
    #     if self.parent:
    #         parent_path = self.parent.url.rstrip('/')
    #         return f"{parent_path}/{path}/"
    #     return f"/{slugify(self.menu.slug)}/{path}/"

    # def generate_url(self):
    #     # Добавляем параметр allow_unicode=True для поддержки кириллицы
    #     path = slugify(self.name, allow_unicode=True) or 'item'
    #     if self.parent:
    #         return f"{self.parent.url.rstrip('/')}/{path}/"
    #     return f"/{slugify(self.menu.slug, allow_unicode=True)}/{path}/"

    def generate_url(self):
        # Генерация slug для пункта меню
        item_slug = slugify(self.name)
        if not item_slug:  # Если slugify вернул пустую строку (для русских символов без allow_unicode)
            item_slug = f"item-{self.pk}" if self.pk else "item"

        # Генерация slug для меню (если меню существует)
        menu_slug = slugify(self.menu.name) if hasattr(self, 'menu') and self.menu else "menu"

        if self.parent:
            parent_url = self.parent.url.rstrip('/')
            return f"{parent_url}/{item_slug}/"
        return f"/{menu_slug}/{item_slug}/"


    def save(self, *args, **kwargs):
        if not self.url and not self.named_url:
            self.url = self.generate_url()
        super().save(*args, **kwargs)


    def get_full_path(self):
        path_parts = []
        item = self

        # Собираем все родительские элементы
        while item:
            path_parts.append(item.name)
            item = item.parent

        # Разворачиваем порядок (от корня к текущему элементу)
        path_parts.reverse()

        # Добавляем название меню в начало
        menu_name = self.menu.name if hasattr(self, 'menu') else ''
        return f"{menu_name}: {' > '.join(path_parts)}"

    def __str__(self):
        return self.get_full_path()


    @property
    def level(self):
        return self.get_level()

    def get_level(self):
        level = 0
        item = self
        while item.parent is not None:
            level += 1
            item = item.parent
        return level


