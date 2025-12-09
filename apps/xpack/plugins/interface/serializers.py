# -*- coding: utf-8 -*-
#
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from .models import Interface


class InterfaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interface
        fields = [
            'logo_logout', 'logo_index', 'login_image', 'favicon',
            'login_title', 'theme', 'theme_info', 'footer_content'
        ]


class ThemeSerializer(serializers.Serializer):
    """主题序列化器"""
    name = serializers.CharField(label=_('Theme name'))
    title = serializers.CharField(label=_('Theme title'))
    colors = serializers.DictField(label=_('Theme colors'), required=False)

