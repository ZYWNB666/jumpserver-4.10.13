# -*- coding: utf-8 -*-
#
from django.urls import path, include
from xpack import views

app_name = 'xpack'

urlpatterns = [
    # 飞书SSO插件路由
    path('feishu-sso/', include('xpack.plugins.feishu_sso.urls', namespace='feishu-sso')),
    
    # License API
    path('license/detail', views.LicenseDetailView.as_view(), name='license-detail'),
]