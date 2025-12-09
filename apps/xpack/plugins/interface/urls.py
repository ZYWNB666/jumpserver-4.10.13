# -*- coding: utf-8 -*-
#
from django.urls import path
from . import views

app_name = 'interface'

urlpatterns = [
    path('setting/', views.InterfaceSettingView.as_view(), name='setting'),
    path('setting/themes/', views.ThemeListView.as_view(), name='themes'),
]

