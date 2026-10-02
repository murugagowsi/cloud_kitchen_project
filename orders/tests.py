from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient

class LoginTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_login_success(self):
        response = self.client.post('/api/users/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.data)

    def test_login_invalid_password(self):
        response = self.client.post('/api/users/login/', {
            'username': 'testuser',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 401)

    def test_login_missing_username(self):
        response = self.client.post('/api/users/login/', {
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 401)

    def test_login_missing_password(self):
        response = self.client.post('/api/users/login/', {
            'username': 'testuser'
        })
        self.assertEqual(response.status_code, 401)

    def test_login_nonexistent_user(self):
        response = self.client.post('/api/users/login/', {
            'username': 'nouser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 401)


class OrderTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='orderuser',
            email='order@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_order_list(self):
        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, 200)

    def test_order_create(self):
        response = self.client.post('/api/orders/', {
            'user': self.user.id,
            'total_price': 500.00,
            'status': 'pending'
        })
        self.assertIn(response.status_code, [200, 201])

    def test_order_unauthenticated(self):
        client = APIClient()
        response = client.get('/api/orders/')
        self.assertIn(response.status_code, [401, 403])