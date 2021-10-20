from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        "Текст поста",
        help_text="Введите текст поста"
    )
    pub_date = models.DateTimeField(
        "Дата публикации",
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Автор"
    )

    group = models.ForeignKey(
        Group,
        related_name="posts",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name="Группа",
        help_text="Выберите группу"
    )

    def __str__(self):
        return self.text[:15]

    class Meta:
        ordering = ("-pub_date",)
