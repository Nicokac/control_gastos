from .views import APP_VERSION, WHATS_NEW


def app_version(request):
    latest_release = WHATS_NEW[0] if WHATS_NEW else None
    return {
        "APP_VERSION": APP_VERSION,
        "LATEST_RELEASE": latest_release,
    }
