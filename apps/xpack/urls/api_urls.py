# -*- coding: utf-8 -*-
#
from django.urls import path, include
from xpack import views

app_name = 'xpack'

urlpatterns = [
    # 飞书SSO插件路由
    path('feishu-sso/', include('xpack.plugins.feishu_sso.urls', namespace='feishu-sso')),
    
    # 界面设置插件路由
    path('interface/', include('xpack.plugins.interface.urls', namespace='interface')),
    
    # License API
    path('license/detail', views.LicenseDetailView.as_view(), name='license-detail'),
]