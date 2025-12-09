#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jumpserver.settings')
django.setup()

from users.models import User
from users.serializers import UserProfileSerializer
import json

# 查找或创建测试用户
username = '17550585613'
try:
    user = User.objects.get(username=username)
    print(f"找到用户: {user.username}, source: {user.source}, email: {user.email}")
except User.DoesNotExist:
    print(f"用户不存在: {username}")
    user = None

if user:
    # 测试序列化器
    serializer = UserProfileSerializer(instance=user)
    
    # 检查字段配置
    fields_info = {}
    for field_name in ['email', 'name', 'username', 'phone', 'source']:
        if field_name in serializer.fields:
            field = serializer.fields[field_name]
            fields_info[field_name] = {
                'read_only': field.read_only,
                'required': field.required,
                'allow_blank': getattr(field, 'allow_blank', None),
                'disabled': getattr(field, 'disabled', None),
            }
    
    print("\n字段配置:")
    print(json.dumps(fields_info, indent=2, ensure_ascii=False))
    
    # 检查序列化后的数据
    print("\n序列化数据中的email:")
    data = serializer.data
    print(f"  email: {data.get('email')}")
    print(f"  source: {data.get('source')}")
