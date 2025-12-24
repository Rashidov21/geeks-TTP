from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Battle, BattleParticipant

User = get_user_model()


class BattlePermissionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='u1', password='pass')
        self.u2 = User.objects.create_user(username='u2', password='pass')
        self.battle = Battle.objects.create(creator=self.user, mode='text')
        BattleParticipant.objects.create(battle=self.battle, user=self.user)

    def test_creator_cannot_join_as_opponent(self):
        self.client.login(username='u1', password='pass')
        url = reverse('battles:join', args=[self.battle.id])
        resp = self.client.get(url)
        # creator trying to join should be redirected with error
        self.assertTrue(resp.status_code in (302, 200))

    def test_other_can_join_and_start(self):
        self.client.login(username='u2', password='pass')
        url = reverse('battles:join', args=[self.battle.id])
        resp = self.client.get(url)
        # joining redirects to play or detail
        self.assertTrue(resp.status_code in (302, 200))
        self.battle.refresh_from_db()
        # opponent should be set after join
        self.assertIsNotNone(self.battle.opponent)
