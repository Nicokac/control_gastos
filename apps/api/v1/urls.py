from django.urls import include, path

from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.api.v1.views.auth import MeView, RegisterView
from apps.api.v1.views.categories import CategoryViewSet
from apps.api.v1.views.expenses import ExpenseViewSet
from apps.api.v1.views.income import IncomeViewSet
from apps.api.v1.views.savings import SavingViewSet

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"expenses", ExpenseViewSet, basename="expense")
router.register(r"income", IncomeViewSet, basename="income")
router.register(r"savings", SavingViewSet, basename="saving")

urlpatterns = [
    # Auth
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/me/", MeView.as_view(), name="me"),
    # Resources
    path("", include(router.urls)),
]
