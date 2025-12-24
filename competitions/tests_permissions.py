from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Competition, CompetitionParticipant

User = get_user_model()


class CompetitionPermissionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.manager = User.objects.create_user(username='manager', password='pass')
        # attach userprofile with is_manager True if exists
        try:
            self.manager.userprofile.is_manager = True
            self.manager.userprofile.save()
        except Exception:
            pass

        self.user = User.objects.create_user(username='player', password='pass')
        self.other = User.objects.create_user(username='other', password='pass')

        self.comp_public = Competition.objects.create(name='pub', mode='text', created_by=self.manager, is_public=True, status='pending')
        self.comp_private = Competition.objects.create(name='priv', mode='text', created_by=self.manager, is_public=False, status='pending')
        self.comp_code = Competition.objects.create(name='withcode', mode='text', created_by=self.manager, access_code='secret', is_public=False, status='pending')

    def test_join_public_competition(self):
        self.client.login(username='player', password='pass')
        url = reverse('competitions:join', args=[self.comp_public.id])
        resp = self.client.post(url, {})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(CompetitionParticipant.objects.filter(user=self.user, competition=self.comp_public).exists())

    def test_join_private_without_access_and_not_added(self):
        self.client.login(username='other', password='pass')
        url = reverse('competitions:join', args=[self.comp_private.id])
        resp = self.client.post(url, {'access_code': ''})
        # should redirect back with error and not create participant
        self.assertTrue(resp.status_code in (302, 200))
        self.assertFalse(CompetitionParticipant.objects.filter(user=self.other, competition=self.comp_private).exists())

    def test_join_with_access_code(self):
        self.client.login(username='other', password='pass')
        url = reverse('competitions:join', args=[self.comp_code.id])
        resp = self.client.post(url, {'access_code': 'secret'})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(CompetitionParticipant.objects.filter(user=self.other, competition=self.comp_code).exists())
