from django.test import RequestFactory, SimpleTestCase, override_settings
from campus.views import health_check


class HealthCheckTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(HEALTH_CHECK_TOKEN="")
    def test_health_is_public_when_no_token_configured(self):
        response = health_check(self.factory.get("/health/"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")

    @override_settings(HEALTH_CHECK_TOKEN="test-secret")
    def test_health_requires_configured_header(self):
        response = health_check(self.factory.get("/health/"))
        self.assertEqual(response.status_code, 401)

    @override_settings(HEALTH_CHECK_TOKEN="test-secret")
    def test_health_accepts_correct_header(self):
        response = health_check(self.factory.get(
            "/health/", HTTP_X_UNIMAP_HEALTH_TOKEN="test-secret"
        ))
        self.assertEqual(response.status_code, 200)
