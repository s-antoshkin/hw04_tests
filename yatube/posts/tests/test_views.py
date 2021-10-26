import datetime

from django import forms
from django.contrib.auth import get_user_model
from django.forms.models import model_to_dict
from django.test import Client, TestCase
from django.urls import reverse
from mixer.backend.django import mixer

from ..models import Group, Post, User

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_author = User.objects.create(username="HasNoName")
        cls.user_1 = mixer.blend(User)
        cls.group_1 = mixer.blend(Group)
        mixer.cycle(23).blend(Post, group=cls.group_1, author=cls.user_1)
        cls.test_post = Post.objects.create(
            text="Текст поста",
            author=cls.test_author,
            group=Group.objects.create(
                title="ЗаголовокГруппы",
                slug="test_slug",
                description="ТестовоеОписание",
            ),
        )
        cls.test_post.pub_date += datetime.timedelta(days=1)
        cls.test_post.save()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.test_author)
        self.not_author = User.objects.create(username="NotAuthor")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.not_author)

    def test_first_page_contains_ten_records(self):
        """Количество постов на странице равно 10."""
        reverse_names = {
            "index": reverse("posts:index"),
            "group_list": reverse(
                "posts:group_list", kwargs={"slug": self.group_1.slug}
            ),
            "profile": reverse(
                "posts:profile", kwargs={"username": self.user_1.username}
            ),
        }
        for namespace, reverse_name in reverse_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(len(response.context["page_obj"]), 10)

    def test_third_page_contains_four_records(self):
        """
        На третьей странице должно быть четыре поста в index,
        в group_list и profile - по три.
        """
        reverse_names = {
            "index": (reverse("posts:index") + "?page=3", 4),
            "group_list": (
                reverse(
                    "posts:group_list",
                    kwargs={"slug": self.group_1.slug}
                )
                + "?page=3",
                3,
            ),
            "profile": (
                reverse(
                    "posts:profile",
                    kwargs={"username": self.user_1.username}
                )
                + "?page=3",
                3,
            ),
        }
        for namespace, reverse_list in reverse_names.items():
            reverse_name = reverse_list[0]
            post_count = reverse_list[1]
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(
                    len(response.context["page_obj"]),
                    post_count
                )

    def test_pages_show_correct_context(self):
        """
        Шаблоны index, group_list, profile
        сформированы с правильным контекстом.
        """
        reverse_names = {
            "index": reverse("posts:index"),
            "group_list": reverse(
                "posts:group_list", kwargs={"slug": self.test_post.group.slug}
            ),
            "profile": reverse(
                "posts:profile",
                kwargs={"username": self.test_post.author.username}
            ),
        }
        for namespace, reverse_name in reverse_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                first_object = response.context["page_obj"][0]
                post_fields = model_to_dict(first_object)
                test_post = model_to_dict(self.test_post)
                self.assertDictEqual(post_fields, test_post)
                if namespace == "profile":
                    post_count_0 = response.context["post_count"]
                    self.assertEqual(post_count_0, 1)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                "posts:post_detail",
                kwargs={"post_id": self.test_post.id}
            )
        )
        self.assertEqual(response.context.get("post_count"), 1)
        post_object = response.context.get("post")
        post_fields = model_to_dict(post_object)
        test_post = model_to_dict(self.test_post)
        self.assertDictEqual(post_fields, test_post)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }
        response = self.authorized_client.get(reverse("posts:post_create"))
        self.assertEqual(response.context.get("title"), "Новый пост")
        self.assertEqual(response.context.get("button"), "Сохранить")
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }
        response = self.authorized_client_author.get(
            reverse("posts:post_edit", kwargs={"post_id": self.test_post.id})
        )
        self.assertEqual(
            response.context.get("title"),
            "Редактировать запись"
        )
        self.assertEqual(response.context.get("button"), "Добавить")
        self.assertEqual(
            response.context.get("post").text,
            self.test_post.text
        )
        self.assertEqual(
            response.context.get("post").group.slug, self.test_post.group.slug
        )
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_pages_contains_test_post(self):
        """Страницы index, group_list, profile
        содержат созданный пост
        """
        new_post = Post.objects.create(
            text="Текст нового поста",
            author=self.test_author,
            group=Group.objects.create(
                title="Заголовок Новой Группы",
                slug="test_slug_new",
                description="Тут должно быть описание новой группы",
            ),
        )
        reverse_names = {
            "index": reverse("posts:index"),
            "group_list": reverse(
                "posts:group_list", kwargs={"slug": new_post.group.slug}
            ),
            "profile": reverse(
                "posts:profile", kwargs={
                    "username": new_post.author.username
                }
            ),
        }
        for namespace, reverse_name in reverse_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertIn(new_post, response.context["page_obj"])

        # Проверка на отсутсвие нового поста в другой группе
        response = self.client.get(
            reverse("posts:group_list", kwargs={"slug": self.group_1.slug})
        )
        self.assertNotIn(new_post, response.context["page_obj"])
