"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.core.cache import cache
from django.http import HttpResponse
from django.urls import include, path

SITE_URL = "https://control-gastos-fr8z.onrender.com"


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /$",
        "Allow: /terms/",
        "Allow: /privacy/",
        "Disallow: /",
        f"Sitemap: {SITE_URL}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def sitemap_xml(request):
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{SITE_URL}/</loc><changefreq>monthly</changefreq><priority>1.0</priority></url>
  <url><loc>{SITE_URL}/terms/</loc><changefreq>yearly</changefreq><priority>0.3</priority></url>
  <url><loc>{SITE_URL}/privacy/</loc><changefreq>yearly</changefreq><priority>0.3</priority></url>
</urlset>"""
    return HttpResponse(content, content_type="application/xml")


_HEALTHZ_LIMIT = 30  # máx requests por IP en la ventana
_HEALTHZ_WINDOW = 60  # segundos


def healthz(request):
    """Health check endpoint que verifica conexión a DB."""
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    if "Render" not in user_agent:
        ip = (
            request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", ""))
            .split(",")[0]
            .strip()
        )
        cache_key = f"healthz_hits_{ip}"
        hits = cache.get(cache_key, 0)
        if hits >= _HEALTHZ_LIMIT:
            return HttpResponse("too many requests", content_type="text/plain", status=429)
        cache.set(cache_key, hits + 1, timeout=_HEALTHZ_WINDOW)

    from django.db import connection

    try:
        connection.ensure_connection()
        return HttpResponse("ok", content_type="text/plain")
    except Exception as e:
        return HttpResponse(f"error: {e}", content_type="text/plain", status=503)


urlpatterns = [
    path("admin/", admin.site.urls),
    # API
    path("api/v1/", include("apps.api.v1.urls")),
    # Apps
    path("healthz/", healthz),
    path("robots.txt", robots_txt),
    path("sitemap.xml", sitemap_xml),
    path("users/", include("apps.users.urls")),
    path("categories/", include("apps.categories.urls")),
    path("expenses/", include("apps.expenses.urls")),
    path("income/", include("apps.income.urls")),
    path("savings/", include("apps.savings.urls")),
    path("recurring/", include("apps.recurring.urls")),
    path("recurring-income/", include("apps.recurring_income.urls")),
    path("shared/", include("apps.shared_expenses.urls")),
    path("", include("apps.core.urls")),
    path("dashboard/", include("apps.reports.urls")),
    # path("boom/", boom),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

    try:
        import debug_toolbar

        urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
    except ImportError:
        pass
