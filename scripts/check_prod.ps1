$ErrorActionPreference = "Stop"

$env:DJANGO_SETTINGS_MODULE = "config.settings.prod"
$env:ALLOWED_HOSTS = "localhost,127.0.0.1"

if (-not $env:SECRET_KEY -or $env:SECRET_KEY.Length -lt 50) {
  $env:SECRET_KEY = (python -c "import secrets; print(secrets.token_urlsafe(64))")
}

python manage.py check --deploy
python scripts/check_security.py
