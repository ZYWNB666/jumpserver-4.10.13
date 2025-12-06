# -*- coding: utf-8 -*-
#
from django.apps import AppConfig


class XpackConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'xpack'
    verbose_name = 'XPack Extensions'
    
    def ready(self):
        """初始化xpack应用"""
        pass