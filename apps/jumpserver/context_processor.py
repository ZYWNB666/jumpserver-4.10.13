# -*- coding: utf-8 -*-
#
import os
import json
import datetime

from django.conf import settings
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _


def _load_interface_settings():
    """加载已保存的界面设置"""
    interface_file = os.path.join(settings.BASE_DIR, 'data', 'interface_settings.json')
    saved = {}
    try:
        if os.path.exists(interface_file):
            with open(interface_file, 'r', encoding='utf-8') as f:
                saved = json.load(f)
    except Exception:
        pass
    
    # 默认值
    defaults = {
        'logo_logout': static('img/logo.png'),
        'logo_index': static('img/logo_text_white.png'),
        'login_image': static('img/login_image.png'),
        'favicon': static('img/facio.ico'),
        'login_title': _('JumpServer - An open-source PAM'),
        'theme': 'classic_green',
        'theme_info': {},
        'footer_content': '',
    }
    
    # 用已保存的值覆盖默认值
    for key, value in saved.items():
        if value is not None and value != '':
            defaults[key] = value
    
    return defaults


default_interface = _load_interface_settings()

current_year = datetime.datetime.now().year

default_context = {
    'DEFAULT_PK': '00000000-0000-0000-0000-000000000000',
    'LOGIN_CAS_logo_logout': static('img/login_cas_logo.png'),
    'LOGIN_WECOM_logo_logout': static('img/login_wecom_logo.png'),
    'LOGIN_DINGTALK_logo_logout': static('img/login_dingtalk_logo.png'),
    'LOGIN_FEISHU_logo_logout': static('img/login_feishu_logo.png'),
    'COPYRIGHT': f'{_("FIT2CLOUD")} © 2014-{current_year}',
    'INTERFACE': default_interface,
}


def jumpserver_processor(request):
    # Setting default pk
    context = {**default_context}
    context.update({
        'VERSION': settings.VERSION,
        'SECURITY_COMMAND_EXECUTION': settings.SECURITY_COMMAND_EXECUTION,
        'SECURITY_MFA_VERIFY_TTL': settings.SECURITY_MFA_VERIFY_TTL,
        'FORCE_SCRIPT_NAME': settings.FORCE_SCRIPT_NAME,
        'SECURITY_VIEW_AUTH_NEED_MFA': settings.SECURITY_VIEW_AUTH_NEED_MFA,
    })
    return context
