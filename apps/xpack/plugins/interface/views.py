# -*- coding: utf-8 -*-
#
import os
import json
import uuid

from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework import serializers as drf_serializers
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.metadata import SimpleMetadata

from jumpserver.context_processor import default_interface


# 预定义主题列表
THEMES = [
    {'name': 'classic_green', 'title': '经典绿'},
    {'name': 'classic_blue', 'title': '经典蓝'},
    {'name': 'dark', 'title': '暗黑'},
    {'name': 'light', 'title': '明亮'},
]

# 界面设置存储文件路径
INTERFACE_SETTINGS_FILE = os.path.join(settings.BASE_DIR, 'data', 'interface_settings.json')


def get_saved_settings():
    """读取已保存的界面设置"""
    try:
        if os.path.exists(INTERFACE_SETTINGS_FILE):
            with open(INTERFACE_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_settings(data):
    """保存界面设置到文件"""
    try:
        os.makedirs(os.path.dirname(INTERFACE_SETTINGS_FILE), exist_ok=True)
        with open(INTERFACE_SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def save_uploaded_file(uploaded_file, field_name):
    """保存上传的文件并返回URL路径"""
    if not uploaded_file or not hasattr(uploaded_file, 'read'):
        return None
    
    # 生成唯一文件名
    ext = os.path.splitext(uploaded_file.name)[1] if hasattr(uploaded_file, 'name') else '.png'
    filename = f"interface/{field_name}_{uuid.uuid4().hex[:8]}{ext}"
    
    # 保存文件
    saved_path = default_storage.save(filename, uploaded_file)
    return default_storage.url(saved_path)


class FlexibleField(drf_serializers.Field):
    """灵活字段，接受字符串、文件或 null"""
    def __init__(self, field_name='', **kwargs):
        self.field_name = field_name
        super().__init__(**kwargs)
    
    def to_internal_value(self, data):
        if data is None or data == '':
            return None
        if hasattr(data, 'read'):  # 文件对象
            # 保存文件并返回 URL
            url = save_uploaded_file(data, self.field_name)
            return url if url else None
        return str(data)
    
    def to_representation(self, value):
        if value is None:
            return None
        return str(value)


class InterfaceSettingSerializer(drf_serializers.Serializer):
    """界面设置序列化器"""
    logo_logout = FlexibleField(required=False, allow_null=True, label='Logo', field_name='logo_logout')
    logo_index = FlexibleField(required=False, allow_null=True, label='Logo index', field_name='logo_index')
    login_image = FlexibleField(required=False, allow_null=True, label='Login image', field_name='login_image')
    favicon = FlexibleField(required=False, allow_null=True, label='Favicon', field_name='favicon')
    login_title = drf_serializers.CharField(required=False, allow_blank=True, allow_null=True, label='Login title')
    theme = drf_serializers.CharField(required=False, allow_blank=True, allow_null=True, label='Theme')
    theme_info = drf_serializers.JSONField(required=False, allow_null=True, label='Theme info')
    footer_content = drf_serializers.CharField(required=False, allow_blank=True, allow_null=True, label='Footer content')


class InterfaceMetadata(SimpleMetadata):
    """自定义元数据类，确保返回 PUT 操作的字段信息"""
    
    def determine_actions(self, request, view):
        """返回 PUT 操作的元数据"""
        actions = {}
        serializer = InterfaceSettingSerializer()
        actions['PUT'] = self.get_serializer_info(serializer)
        return actions


class InterfaceSettingView(generics.RetrieveUpdateAPIView):
    """界面设置视图"""
    permission_classes = [IsAuthenticated]
    serializer_class = InterfaceSettingSerializer
    metadata_class = InterfaceMetadata

    def get_interface_data(self):
        """获取当前界面设置"""
        # 先获取默认值
        data = {
            'logo_logout': default_interface.get('logo_logout', '/static/img/logo.png'),
            'logo_index': default_interface.get('logo_index', '/static/img/logo_text_white.png'),
            'login_image': default_interface.get('login_image', '/static/img/login_image.png'),
            'favicon': default_interface.get('favicon', '/static/img/facio.ico'),
            'login_title': default_interface.get('login_title', 'JumpServer 开源堡垒机'),
            'theme': default_interface.get('theme', 'classic_green'),
            'theme_info': default_interface.get('theme_info', {}),
            'footer_content': default_interface.get('footer_content', ''),
        }
        # 用已保存的设置覆盖
        saved = get_saved_settings()
        for key, value in saved.items():
            if value is not None and value != '':
                data[key] = value
        return data

    def get_object(self):
        """返回界面设置数据的字典对象"""
        return self.get_interface_data()

    def retrieve(self, request, *args, **kwargs):
        """获取界面设置"""
        data = self.get_interface_data()
        serializer = self.get_serializer(data)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """更新界面设置"""
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # 获取当前设置
        current_data = self.get_interface_data()
        
        # 合并新数据（只更新非空值）
        for key, value in serializer.validated_data.items():
            if value is not None:
                current_data[key] = value
        
        # 保存到文件
        save_settings(current_data)
        
        # 更新全局 context_processor 的 default_interface
        from jumpserver import context_processor
        for key, value in current_data.items():
            if value is not None:
                context_processor.default_interface[key] = value
        
        return Response(current_data)


class ThemeListView(APIView):
    """主题列表视图"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """获取可用主题列表"""
        return Response(THEMES)
