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
        if self.url and self.named_url:
            raise ValidationError("Можно задать либо URL, либо Named URL, одновременное задание обоих невозможно.")

        if not self.url and not self.named_url:
            # Авто генерация URL исходя из иерархии меню
            if self.parent:
                self.url = f"{self.parent.url}/{slugify(self.name)}"
            else:
                self.url = f"/{slugify(self.name)}"
        elif self.named_url:
            try:
                # Валидация named URL
                reverse(self.named_url)
            except NoReverseMatch:
                raise ValidationError(f" Такой Named URL '{self.named_url}' не существует в urls.py")
        elif self.url:
            # Валидация формата URL
            parsed = urlparse(self.url)
            if not (parsed.scheme == '' and parsed.netloc == '' and parsed.path.startswith('/')):
                raise ValidationError("URL должен начинаться с символа '/'")

            # Валидация иерархии
            if self.parent and not self.url.startswith(self.parent.url):
                raise ValidationError(
                    f"URL должен начинаться с родительского пути URL'{self.parent.url}'. "
                    f"Рекомендуемый URL: '{self.parent.url}/{slugify(self.name)}'"
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

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
