import httplib

from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User


class ViewsTestCase(TestCase):
    username = 'dummyuser'
    email = 'dummyuser@example.com'
    password = 'staffpassword'
    is_anonymous = False
    is_staff = False
    is_superuser = False

    def setUp(self):
        self.client = Client()
        if not self.is_anonymous:
            self.user = self.create_user()
            self.client.login(username=self.username, 
                              password=self.password)

    def create_user(self):
        user = User.objects.create_user(self.username,
                                        self.email,
                                        self.password)
        user.is_staff = self.is_staff
        user.is_superuser = self.is_superuser
        user.save()
        return user

    def assertIsRedirect(self, response):
        self.assertEqual(httplib.FOUND, response.status_code)

    def assertIsOk(self, response):
        self.assertEqual(httplib.OK, response.status_code)
