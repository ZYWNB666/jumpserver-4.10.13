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
        
        # 硬编码配置 - 直接启用飞书SSO
        settings.FEISHU_SSO_ENABLED = True
        settings.FEISHU_SSO_APP_ID = 'cli_a9a720278879dbb4'
        settings.FEISHU_SSO_APP_SECRET = '26YOsEhHdQ3ms4UP2dtwXfPDA7u1v3jz'
        settings.FEISHU_SSO_AUTO_CREATE_USER = True
        settings.FEISHU_SSO_ALWAYS_UPDATE_USER = True
        settings.FEISHU_SSO_MATCH_BY_EMAIL = False
        settings.FEISHU_SSO_USERNAME_FIELD = 'mobile'
        settings.FEISHU_SSO_DEFAULT_ORG_IDS = ['00000000-0000-0000-0000-000000000002']
        
        # 注册认证后端
        auth_backends = list(settings.AUTHENTICATION_BACKENDS)
        backend_path = 'xpack.plugins.feishu_sso.auth_backend.FeishuSSOBackend'
        
        if backend_path not in auth_backends:
            auth_backends.insert(0, backend_path)
            settings.AUTHENTICATION_BACKENDS = tuple(auth_backends)