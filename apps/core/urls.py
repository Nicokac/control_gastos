from django.urls import path

from .views import (
    AccountDeletionView,
    FeedbackView,
    LandingView,
    PrivacyView,
    TermsView,
    WhatsNewView,
    exchange_rate_today,
)

app_name = "core"

urlpatterns = [
    path("", LandingView.as_view(), name="landing"),
    path("feedback/", FeedbackView.as_view(), name="feedback"),
    path("novedades/", WhatsNewView.as_view(), name="whats_new"),
    path("terms/", TermsView.as_view(), name="terms"),
    path("privacy/", PrivacyView.as_view(), name="privacy"),
    path("account-deletion/", AccountDeletionView.as_view(), name="account_deletion"),
    path("api/exchange-rate/", exchange_rate_today, name="exchange_rate_today"),
]
