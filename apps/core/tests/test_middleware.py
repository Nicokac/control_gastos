"""Tests para RequestTimingMiddleware."""

from django.test import RequestFactory

from apps.core.middleware import RequestTimingMiddleware


class TestRequestTimingMiddleware:
    def _make_response(self, status_code=200):
        from django.http import HttpResponse

        return HttpResponse(status=status_code)

    def test_returns_response(self):
        factory = RequestFactory()
        request = factory.get("/")
        response = self._make_response()

        middleware = RequestTimingMiddleware(get_response=lambda r: response)
        result = middleware(request)

        assert result is response

    def test_logs_request_info(self):
        from unittest.mock import patch

        factory = RequestFactory()
        request = factory.get("/test-path/")
        response = self._make_response(200)

        middleware = RequestTimingMiddleware(get_response=lambda r: response)

        with patch("apps.core.middleware.logger") as mock_logger:
            middleware(request)

        mock_logger.info.assert_called_once()
        args = mock_logger.info.call_args[0]
        assert "GET" in str(args)
        assert "/test-path/" in str(args)
        assert "200" in str(args)

    def test_logs_duration_ms(self):
        from unittest.mock import patch

        factory = RequestFactory()
        request = factory.get("/")
        response = self._make_response()

        middleware = RequestTimingMiddleware(get_response=lambda r: response)

        with patch("apps.core.middleware.logger") as mock_logger:
            middleware(request)

        args = mock_logger.info.call_args[0]
        assert "duration_ms" in str(args)

    def test_logs_post_method(self):
        from unittest.mock import patch

        factory = RequestFactory()
        request = factory.post("/submit/")
        response = self._make_response(302)

        middleware = RequestTimingMiddleware(get_response=lambda r: response)

        with patch("apps.core.middleware.logger") as mock_logger:
            middleware(request)

        args = mock_logger.info.call_args[0]
        assert "POST" in str(args)
        assert "302" in str(args)

    def test_logs_error_status(self):
        from unittest.mock import patch

        factory = RequestFactory()
        request = factory.get("/not-found/")
        response = self._make_response(404)

        middleware = RequestTimingMiddleware(get_response=lambda r: response)

        with patch("apps.core.middleware.logger") as mock_logger:
            middleware(request)

        args = mock_logger.info.call_args[0]
        assert "404" in str(args)
