# -*- coding: utf-8 -*-
#
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rbac.permissions import RBACPermission
from .models import Interface
from .serializers import InterfaceSerializer


# 预定义主题列表
THEMES = [
    {'name': 'classic_green', 'title': '经典绿'},
    {'name': 'classic_blue', 'title': '经典蓝'},
    {'name': 'dark', 'title': '暗黑'},
    {'name': 'light', 'title': '明亮'},
]


class InterfaceSettingView(APIView):
    """界面设置视图"""
    permission_classes = [RBACPermission]
    rbac_perms = {
        'GET': 'settings.change_interface',
        'PUT': 'settings.change_interface',
        'PATCH': 'settings.change_interface',
    }

    def get(self, request):
        """获取界面设置"""
        obj = Interface.objects.first()
        if not obj:
            obj = Interface.objects.create()
        serializer = InterfaceSerializer(obj)
        return Response(serializer.data)

    def put(self, request):
        """更新界面设置"""
        obj = Interface.objects.first()
        if not obj:
            obj = Interface.objects.create()
        serializer = InterfaceSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        """部分更新界面设置"""
        return self.put(request)


class ThemeListView(APIView):
    """主题列表视图"""
    permission_classes = [RBACPermission]
    rbac_perms = {
        'GET': 'settings.change_interface',
    }

    def get(self, request):
        """获取可用主题列表"""
        return Response(THEMES)

