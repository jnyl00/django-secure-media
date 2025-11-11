from django.test import RequestFactory, TestCase
from django.http import HttpResponse
from django_secure_media.decorators import secure_media_path
from django_secure_media.policies import MediaAccessPolicy, MediaAccessPolicyRegistry


class SecureMediaTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.policy = MediaAccessPolicy(('images/',), lambda r, p: r.user.is_authenticated)
        self.registry = MediaAccessPolicyRegistry([self.policy], default_allow=False)
        self.view = secure_media_path(lambda r, p: HttpResponse("OK"), policy_registry=self.registry)

    def test_authenticated_access(self):
        req = self.factory.get('/media/images/a.jpg')
        req.user = type("User", (), {"is_authenticated": True})()
        res = self.view(req, 'images/a.jpg')
        self.assertEqual(res.status_code, 200)

    def test_unauthenticated_access_denied(self):
        req = self.factory.get('/media/images/a.jpg')
        req.user = type("User", (), {"is_authenticated": False})()
        with self.assertRaisesMessage(Exception, "Restricted media file"):
            self.view(req, 'images/a.jpg')
