# -*- coding: utf-8 -*-
#
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache

from jumpserver.context_processor import default_interface


class Interface(models.Model):
    """界面设置模型"""
    logo_logout = models.CharField(max_length=1024, default='/static/img/logo.png', verbose_name=_('Logo'))
    logo_index = models.CharField(max_length=1024, default='/static/img/logo_text_white.png', verbose_name=_('Logo index'))
    login_image = models.CharField(max_length=1024, default='/static/img/login_image.png', verbose_name=_('Login image'))
    favicon = models.CharField(max_length=1024, default='/static/img/facio.ico', verbose_name=_('Favicon'))
    login_title = models.CharField(max_length=1024, default='JumpServer 开源堡垒机', verbose_name=_('Login title'))
    theme = models.CharField(max_length=128, default='classic_green', verbose_name=_('Theme'))
    theme_info = models.JSONField(default=dict, verbose_name=_('Theme info'))
    footer_content = models.TextField(default='', blank=True, verbose_name=_('Footer content'))

    class Meta:
        verbose_name = _('Interface setting')
        db_table = 'xpack_interface'

    CACHE_KEY = 'INTERFACE_SETTING'
    
    @classmethod
    def get_interface_setting(cls):
        """获取界面设置，优先从缓存获取"""
        cached = cache.get(cls.CACHE_KEY)
        if cached:
            return cached
        
        try:
            obj = cls.objects.first()
            if obj:
                setting = {
                    'logo_logout': obj.logo_logout,
                    'logo_index': obj.logo_index,
                    'login_image': obj.login_image,
                    'favicon': obj.favicon,
                    'login_title': obj.login_title,
                    'theme': obj.theme,
                    'theme_info': obj.theme_info or {},
                    'footer_content': obj.footer_content or '',
                }
            else:
                setting = default_interface
        except Exception:
            setting = default_interface
        
        cache.set(cls.CACHE_KEY, setting, 3600)
        return setting

    @classmethod
    def refresh_cache(cls):
        """刷新缓存"""
        cache.delete(cls.CACHE_KEY)
        return cls.get_interface_setting()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.refresh_cache()

