from django.urls import path

from .views import FeedbackView, WhatsNewView

app_name = "core"

urlpatterns = [
    path("feedback/", FeedbackView.as_view(), name="feedback"),
    path("novedades/", WhatsNewView.as_view(), name="whats_new"),
]
