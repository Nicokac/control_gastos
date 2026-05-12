from django.urls import path

from .views import FeedbackView, LandingView, WhatsNewView

app_name = "core"

urlpatterns = [
    path("", LandingView.as_view(), name="landing"),
    path("feedback/", FeedbackView.as_view(), name="feedback"),
    path("novedades/", WhatsNewView.as_view(), name="whats_new"),
]
