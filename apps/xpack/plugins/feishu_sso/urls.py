# -*- coding: utf-8 -*-
#
from django.urls import path
from . import views

app_name = 'feishu_sso'

urlpatterns = [
    # 飞书SSO登录入口
    path('login/', views.FeishuSSOLoginView.as_view(), name='login'),
    
    # 飞书OAuth回调
    path('callback/', views.FeishuSSOCallbackView.as_view(), name='callback'),
    
    # 飞书JS-SDK配置
    path('jssdk/config/', views.FeishuJSSDKConfigView.as_view(), name='jssdk-config'),
    
    # 飞书绑定状态检查
    path('status/', views.FeishuSSOStatusView.as_view(), name='status'),
]