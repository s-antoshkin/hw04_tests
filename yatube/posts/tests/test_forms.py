from django.test import Client, TestCase
from django.urls import reverse
from posts.forms import PostForm
from ..models import Post, User, Group


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
        cls.form = PostForm()

    def setUp(self):
        self.group = PostFormTests.group
        self.test_user = PostFormTests.test_author
        self.authorized_client = Client()
        self.authorized_client.force_login(self.test_user)

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
                kwargs={"username": self.test_user.username}
            ),
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)

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
        response = self.authorized_client.get(
            reverse(
                "posts:post_detail",
                kwargs={"post_id": self.test_post.id}
            )
        )
        self.assertEqual(response.context.get("post").text, form_data["text"])
        self.assertEqual(response.context.get("post").group, None)
        self.assertEqual(Post.objects.count(), posts_count)
