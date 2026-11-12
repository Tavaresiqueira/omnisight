from django.conf import settings
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path('api/', include('identity.urls')),
    path('', serve, {'path': 'index.html', 'document_root': settings.BASE_DIR.parent / 'web/out'}),
    re_path(r'^(?P<path>.*)$', serve, {'document_root': settings.BASE_DIR.parent / 'web/out'}),
]
