# -*- coding: utf-8 -*-
#
from django.apps import AppConfig


class FeishuSsoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'xpack.plugins.feishu_sso'
    verbose_name = '飞书企业单点登录'
    
    def ready(self):
        """初始化飞书SSO插件"""
        from django.conf import settings
        
        # 注册认证后端
        if settings.FEISHU_SSO_ENABLED:
            auth_backends = list(settings.AUTHENTICATION_BACKENDS)
            backend_path = 'xpack.plugins.feishu_sso.auth_backend.FeishuSSOBackend'
            
            if backend_path not in auth_backends:
                auth_backends.insert(0, backend_path)
                settings.AUTHENTICATION_BACKENDS = tuple(auth_backends)