# ~*~ coding: utf-8 ~*~

import json
import os
import re
import time
from urllib.parse import urlparse, quote

import pytz
from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.http.response import HttpResponseForbidden
from django.shortcuts import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from .utils import set_current_request


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tzname = request.META.get('HTTP_X_TZ')
        if not tzname or tzname == 'undefined':
            return self.get_response(request)
        try:
            tz = pytz.timezone(tzname)
            timezone.activate(tz)
        except pytz.UnknownTimeZoneError:
            pass
        response = self.get_response(request)
        return response


class DemoMiddleware:
    DEMO_MODE_ENABLED = os.environ.get("DEMO_MODE", "") in ("1", "ok", "True")
    SAFE_URL_PATTERN = re.compile(
        r'^/users/login|'
        r'^/api/terminal/v1/.*|'
        r'^/api/terminal/.*|'
        r'^/api/users/v1/auth/|'
        r'^/api/users/v1/profile/'
    )
    SAFE_METHOD = ("GET", "HEAD")

    def __init__(self, get_response):
        self.get_response = get_response

        if self.DEMO_MODE_ENABLED:
            print("Demo mode enabled, reject unsafe method and url")
            raise MiddlewareNotUsed

    def __call__(self, request):
        if self.DEMO_MODE_ENABLED and request.method not in self.SAFE_METHOD \
                and not self.SAFE_URL_PATTERN.match(request.path):
            return HttpResponse("Demo mode, only safe request accepted", status=403)
        else:
            response = self.get_response(request)
            return response


class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_request(request)
        response = self.get_response(request)
        return response


class RefererCheckMiddleware:
    def __init__(self, get_response):
        if not settings.REFERER_CHECK_ENABLED:
            raise MiddlewareNotUsed
        self.get_response = get_response
        self.http_pattern = re.compile('https?://')

    def check_referer(self, request):
        referer = request.META.get('HTTP_REFERER', '')
        referer = self.http_pattern.sub('', referer)
        if not referer:
            return True
        remote_host = request.get_host()
        return referer.startswith(remote_host)

    def __call__(self, request):
        match = self.check_referer(request)
        if not match:
            return HttpResponseForbidden('CSRF CHECK ERROR')
        response = self.get_response(request)
        return response


class SQLCountMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        if not settings.DEBUG_DEV:
            raise MiddlewareNotUsed

    def __call__(self, request):
        from django.db import connection
        response = self.get_response(request)
        response['X-JMS-SQL-COUNT'] = len(connection.queries) - 2
        return response


class StartMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        if not settings.DEBUG_DEV:
            raise MiddlewareNotUsed

    def __call__(self, request):
        request._s_time_start = time.time()
        response = self.get_response(request)
        request._s_time_end = time.time()
        if request.path == '/api/health/':
            data = response.data
            data['pre_middleware_time'] = request._e_time_start - request._s_time_start
            data['api_time'] = request._e_time_end - request._e_time_start
            data['post_middleware_time'] = request._s_time_end - request._e_time_end
            response.content = json.dumps(data)
            response.headers['Content-Length'] = str(len(response.content))
            return response
        return response


class EndMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        if not settings.DEBUG_DEV:
            raise MiddlewareNotUsed

    def __call__(self, request):
        request._e_time_start = time.time()
        response = self.get_response(request)
        request._e_time_end = time.time()
        return response


class SafeRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if not (300 <= response.status_code < 400):
            return response
        if request.resolver_match and request.resolver_match.namespace.startswith('authentication'):
            # 认证相关的路由跳过验证（core/auth/xxxx
            return response
        location = response.get('Location')
        if not location:
            return response
        parsed = urlparse(location)
        if parsed.scheme and parsed.netloc:
            target_host = parsed.netloc
            if target_host in [*settings.ALLOWED_HOSTS]:
                return response
            target_host, target_port = self._split_host_port(parsed.netloc)
            origin_host, origin_port = self._split_host_port(request.get_host())
            if target_host != origin_host:
                safe_redirect_url = '%s?%s' % (reverse('redirect-confirm'), f'next={quote(location)}')
                return redirect(safe_redirect_url)
        return response

    @staticmethod
    def _split_host_port(netloc):
        if ':' in netloc:
            host, port = netloc.split(':', 1)
            return host, port
        return netloc, '80'


class EmailRequiredMiddleware:
    """
    邮箱必填中间件
    
    当用户登录后，如果邮箱不是 @magikcompute.ai 结尾，
    则强制跳转到邮箱填写页面，直到用户填写真实的公司邮箱
    
    对于 API 请求，返回 403 错误，让前端无法正常工作
    """
    
    # 完全豁免的 URL 路径（不检查邮箱）
    EXEMPT_URLS = [
        '/core/auth/login/',
        '/core/auth/logout/',
        '/core/auth/email/required/',
        '/api/v1/authentication/',  # 认证相关 API
        '/api/v1/settings/public/',  # 公开设置 API
        '/api/health/',
        '/static/',
        '/media/',
        '/ws/',
        '/koko/',
        '/lion/',
        '/chen/',
        '/health/',
        '/favicon.ico',
    ]
    
    # 需要立即重定向的 URL（首页相关）
    REDIRECT_URLS = [
        '/',
        '/ui/',
        '/ui',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 检查是否需要跳过
        if self._should_skip(request):
            return self.get_response(request)
        
        # 检查用户是否已登录
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return self.get_response(request)
        
        # 检查用户邮箱是否是临时邮箱
        user = request.user
        if self._is_temp_email(user.email):
            email_required_url = '/core/auth/email/required/'
            
            # 对于首页相关的请求，直接重定向
            if request.path in self.REDIRECT_URLS or request.path.startswith('/ui'):
                return redirect(email_required_url)
            
            # 检查是否是 AJAX 请求
            is_ajax = (
                request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
                'application/json' in request.headers.get('Accept', '') or
                'application/json' in request.headers.get('Content-Type', '')
            )
            
            if request.path.startswith('/api/'):
                if is_ajax:
                    # AJAX 请求返回带自动跳转的 HTML（浏览器会执行）
                    html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<script>alert("请先完善您的公司邮箱");window.location.href="{email_required_url}";</script>
</head><body>正在跳转...</body></html>'''
                    return HttpResponse(html, status=200, content_type='text/html; charset=utf-8')
                else:
                    # 非 AJAX 的 API 请求，直接重定向
                    return redirect(email_required_url)
            
            # 对于其他页面请求，重定向到邮箱填写页面
            return redirect(email_required_url)
        
        return self.get_response(request)
    
    def _should_skip(self, request):
        """检查是否应该跳过邮箱检查"""
        path = request.path
        for exempt_url in self.EXEMPT_URLS:
            if path.startswith(exempt_url):
                return True
        return False
    
    @staticmethod
    def _is_temp_email(email):
        """检查是否是临时邮箱，需要用户填写真实的 @magikcompute.ai 邮箱"""
        if not email:
            return True
        # 只有 @magikcompute.ai 结尾的邮箱才是有效的，其他都需要重新填写
        return not email.endswith('@magikcompute.ai')
