import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Text, CodeSnippet, UserResult

User = get_user_model()


class SaveResultTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='tester', password='pass')
        self.text = Text.objects.create(title='T1', difficulty='easy', word_count=4, body='one two three four')
        self.code = CodeSnippet.objects.create(title='C1', language='python', difficulty='easy', code_body='print("hi")')

    def login(self):
        self.client.login(username='tester', password='pass')

    def test_full_text_save_success(self):
        self.login()
        url = reverse('typing_practice:save_result')
        body = {
            'text_id': self.text.id,
            'typed_text': self.text.body,
            'wpm': 50,
            'accuracy': 100,
            'mistakes': 0,
            'mistakes_list': [],
            'duration_seconds': 4
        }
        resp = self.client.post(url, data=json.dumps(body), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))
        self.assertTrue(UserResult.objects.filter(user=self.user, text=self.text).exists())

    def test_incomplete_text_rejected(self):
        self.login()
        url = reverse('typing_practice:save_result')
        body = {
            'text_id': self.text.id,
            'typed_text': 'one two',
            'wpm': 30,
            'accuracy': 60,
            'mistakes': 1,
            'mistakes_list': [],
            'duration_seconds': 10
        }
        resp = self.client.post(url, data=json.dumps(body), content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_time_mode_allows_incomplete(self):
        self.login()
        url = reverse('typing_practice:save_result')
        body = {
            'text_id': self.text.id,
            'typed_text': 'one two',
            'allow_incomplete': True,
            'mode': 'time',
            'time_limit': 5,
            'wpm': 30,
            'accuracy': 60,
            'mistakes': 1,
            'mistakes_list': [],
            'duration_seconds': 10
        }
        resp = self.client.post(url, data=json.dumps(body), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))

    def test_tampered_wpm_gets_overridden(self):
        self.login()
        url = reverse('typing_practice:save_result')
        # 4 words, duration 2 => server_wpm = (4/2)*60 = 120
        body = {
            'text_id': self.text.id,
            'typed_text': self.text.body,
            'wpm': 9999,
            'accuracy': 100,
            'mistakes': 0,
            'mistakes_list': [],
            'duration_seconds': 2
        }
        resp = self.client.post(url, data=json.dumps(body), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        # Check stored result
        result = UserResult.objects.filter(user=self.user, text=self.text).first()
        self.assertIsNotNone(result)
        # server should have adjusted wpm to near 120
        self.assertAlmostEqual(result.wpm, 120, delta=5)
