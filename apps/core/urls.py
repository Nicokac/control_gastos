from django.urls import path

from .views import FeedbackView

app_name = "core"

urlpatterns = [
    path("feedback/", FeedbackView.as_view(), name="feedback"),
]
