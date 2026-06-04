from django.urls import include, path

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.api.v1.views.auth import MeView, RegisterView
from apps.api.v1.views.categories import CategoryViewSet
from apps.api.v1.views.dashboard import DashboardView
from apps.api.v1.views.expenses import ExpenseViewSet
from apps.api.v1.views.income import IncomeViewSet
from apps.api.v1.views.recurring import RecurringExpenseViewSet
from apps.api.v1.views.recurring_income import RecurringIncomeViewSet
from apps.api.v1.views.savings import SavingViewSet
from apps.api.v1.views.shared_expenses import HouseholdMemberViewSet, SharedExpenseViewSet

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"expenses", ExpenseViewSet, basename="expense")
router.register(r"income", IncomeViewSet, basename="income")
router.register(r"savings", SavingViewSet, basename="saving")
router.register(r"recurring", RecurringExpenseViewSet, basename="recurring")
router.register(r"recurring-income", RecurringIncomeViewSet, basename="recurring-income")
router.register(r"shared-expenses", SharedExpenseViewSet, basename="shared-expense")
router.register(r"household-members", HouseholdMemberViewSet, basename="household-member")

urlpatterns = [
    # Auth
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/me/", MeView.as_view(), name="me"),
    # Dashboard
    path("dashboard/", DashboardView.as_view(), name="api-dashboard"),
    # Docs
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # Resources
    path("", include(router.urls)),
]
