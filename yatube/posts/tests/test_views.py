import time

from django import forms
from django.contrib.auth import get_user_model
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
        # Задержка для "ручного поста" -> "самый новый"
        time.sleep(0.1)
        cls.test_post = Post.objects.create(
            text="Текст поста",
            author=cls.test_author,
            group=Group.objects.create(
                title="ЗаголовокГруппы",
                slug="test_slug",
                description="ТестовоеОписание",
            ),
        )

    def setUp(self):
        self.test_post = PostPagesTests.test_post
        self.guest_client = Client()
        self.author = PostPagesTests.test_author
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.author)
        self.not_author = User.objects.create(username="NotAuthor")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.not_author)
        self.user_1 = PostPagesTests.user_1
        self.group_1 = PostPagesTests.group_1

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
            "index": reverse("posts:index") + "?page=3",
            "group_list": reverse(
                "posts:group_list", kwargs={"slug": self.group_1.slug}
            )
            + "?page=3",
            "profile": reverse(
                "posts:profile", kwargs={"username": self.user_1.username}
            )
            + "?page=3",
        }
        for namespace, reverse_name in reverse_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                if namespace == "index":
                    self.assertEqual(len(response.context["page_obj"]), 4)
                else:
                    self.assertEqual(len(response.context["page_obj"]), 3)

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
                "posts:profile", kwargs={
                    "username": self.test_post.author.username
                }
            ),
        }
        for namespace, reverse_name in reverse_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                first_object = response.context["page_obj"][0]
                post_id_0 = first_object.id
                post_text_0 = first_object.text
                post_pub_date_0 = first_object.pub_date
                post_author_0 = first_object.author
                post_group_0 = first_object.group
                self.assertEqual(post_id_0, self.test_post.id)
                self.assertEqual(post_text_0, self.test_post.text)
                self.assertEqual(post_pub_date_0, self.test_post.pub_date)
                self.assertEqual(post_author_0, self.test_post.author)
                self.assertEqual(post_group_0, self.test_post.group)
                if namespace == "profile":
                    post_count_0 = response.context["post_count"]
                    self.assertEqual(post_count_0, 1)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:post_detail", kwargs={
                "post_id": self.test_post.id
            })
        )
        self.assertEqual(
            response.context.get("post").text,
            self.test_post.text
        )
        self.assertEqual(
            response.context.get("post").pub_date,
            self.test_post.pub_date,
        )
        self.assertEqual(
            response.context.get("post").author,
            self.test_post.author
        )
        self.assertEqual(response.context.get("post_count"), 1)
        self.assertEqual(
            response.context.get("post").group.title,
            self.test_post.group.title
        )
        self.assertEqual(
            response.context.get("post").group.slug, self.test_post.group.slug
        )
        self.assertEqual(
            response.context.get("post").group.description,
            self.test_post.group.description,
        )

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
