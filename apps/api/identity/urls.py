from django.urls import path

from identity.views import DemoLoginView, LoginView, MeView, OrganizationDetailView, RegisterView, SitesView, RequestScanView, ScanDetailView, ScanReportView, ScanActionView, HealthView
from identity.views import AccountClosureView, AccountExportView


urlpatterns = [
    path('auth/account/close/', AccountClosureView.as_view(), name='close-account'),
    path('auth/account/export/', AccountExportView.as_view(), name='export-account'),
    path("health/",HealthView.as_view(),name="health"),
    path("scans/<uuid:scan_id>/report/", ScanReportView.as_view(), name="scan-report"),
    path("scans/<uuid:scan_id>/actions/", ScanActionView.as_view(), name="scan-action"),
    path("sites/<uuid:site_id>/scans/", RequestScanView.as_view(), name="request-scan"),
    path("scans/<uuid:scan_id>/", ScanDetailView.as_view(), name="scan-detail"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/demo/", DemoLoginView.as_view(), name="demo-login"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("sites/", SitesView.as_view(), name="sites"),
    path(
        "organizations/<uuid:organization_id>/",
        OrganizationDetailView.as_view(),
        name="organization-detail",
    ),
]
