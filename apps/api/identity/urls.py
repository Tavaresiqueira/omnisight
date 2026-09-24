from django.urls import path

from identity.views import LoginView, MeView, OrganizationDetailView, RegisterView


urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/me/", MeView.as_view(), name="me"),
    path(
        "organizations/<uuid:organization_id>/",
        OrganizationDetailView.as_view(),
        name="organization-detail",
    ),
]

