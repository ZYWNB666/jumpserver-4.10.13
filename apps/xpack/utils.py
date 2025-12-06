# -*- coding: utf-8 -*-
#
import os


def get_xpack_templates_dir(base_dir):
    """返回xpack的模板目录列表"""
    xpack_dir = os.path.join(base_dir, 'xpack')
    templates_dir = os.path.join(xpack_dir, 'templates')
    return [templates_dir] if os.path.exists(templates_dir) else []


def get_xpack_context_processor():
    """返回上下文处理器列表"""
    return []