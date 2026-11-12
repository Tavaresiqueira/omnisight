from django.test import RequestFactory, SimpleTestCase, override_settings
from django.middleware.security import SecurityMiddleware
from django.http import HttpResponse


@override_settings(SECURE_SSL_REDIRECT=True, ALLOWED_HOSTS=['healthcheck.railway.app'])
class DeploymentHealthTests(SimpleTestCase):
    def test_internal_health_probe_does_not_redirect_to_https(self):
        middleware = SecurityMiddleware(lambda request: HttpResponse('ok'))
        response = middleware(RequestFactory().get('/api/health/', HTTP_HOST='healthcheck.railway.app'))
        self.assertEqual(response.status_code, 200)

    def test_other_api_paths_keep_https_redirect(self):
        middleware = SecurityMiddleware(lambda request: HttpResponse('ok'))
        response = middleware(RequestFactory().get('/api/auth/login/', HTTP_HOST='healthcheck.railway.app'))
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], 'https://healthcheck.railway.app/api/auth/login/')
