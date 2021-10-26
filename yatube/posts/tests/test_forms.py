from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_author = User.objects.create(username="PostAuthor")
        cls.group = Group.objects.create(
            title="ЗаголовокГруппы",
            slug="test_slug",
            description="ТестовоеОписание",
        )
        cls.test_post = Post.objects.create(
            text="Текст поста", author=cls.test_author, group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.test_author)

    def test_create_post(self):
        """Валидная форма создает новый Post"""
        posts_count = Post.objects.count()
        form_data = {
            "text": "Текст нового поста",
            "group": self.group.id,
        }
        response = self.authorized_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                "posts:profile",
                kwargs={"username": self.test_author.username}
            ),
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        new_post = Post.objects.all()[0]
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.group.id, form_data['group'])
        self.assertEqual(new_post.author, self.test_author)

    def test_edit_post(self):
        """Валидная форма изменяет существующий Post"""
        posts_count = Post.objects.count()
        form_data = {
            "text": "Текст изменённого поста",
        }
        response = self.authorized_client.post(
            reverse("posts:post_edit", kwargs={"post_id": self.test_post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                "posts:post_detail",
                kwargs={"post_id": self.test_post.id}
            ),
        )
        edited_post = Post.objects.get(id=self.test_post.id)
        self.assertEqual(edited_post.text, form_data["text"])
        self.assertEqual(edited_post.group, None)
        self.assertEqual(Post.objects.count(), posts_count)
