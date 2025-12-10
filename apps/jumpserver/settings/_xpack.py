# -*- coding: utf-8 -*-
#

import datetime
import os

from .base import INSTALLED_APPS, TEMPLATES
from .. import const

current_year = datetime.datetime.now().year
corporation = f'FIT2CLOUD 飞致云 © 2014-{current_year}'

XPACK_DIR = os.path.join(const.BASE_DIR, 'xpack')
XPACK_DISABLED = os.environ.get('XPACK_ENABLED') in ['0', 'false', 'False', 'no', 'No']
XPACK_ENABLED = False
if not XPACK_DISABLED:
    XPACK_ENABLED = os.path.isdir(XPACK_DIR)
XPACK_TEMPLATES_DIR = []
XPACK_CONTEXT_PROCESSOR = []
XPACK_LICENSE_IS_VALID = True  # 启用企业版功能（工单等）
XPACK_LICENSE_EDITION = "Enterprise"
XPACK_LICENSE_EDITION_ULTIMATE = False
XPACK_LICENSE_INFO = {
    'corporation': corporation,
}

XPACK_LICENSE_CONTENT = 'enterprise'  # 与 XPACK_LICENSE_EDITION 保持一致

if XPACK_ENABLED:
    from xpack.utils import get_xpack_templates_dir, get_xpack_context_processor

    INSTALLED_APPS.insert(0, 'xpack.apps.XpackConfig')
    INSTALLED_APPS.insert(1, 'xpack.plugins.interface')  # 界面设置插件
    XPACK_TEMPLATES_DIR = get_xpack_templates_dir(const.BASE_DIR)
    XPACK_CONTEXT_PROCESSOR = get_xpack_context_processor()
    TEMPLATES[0]['DIRS'].extend(XPACK_TEMPLATES_DIR)
    TEMPLATES[0]['OPTIONS']['context_processors'].extend(XPACK_CONTEXT_PROCESSOR)


    # # 飞书SSO配置 - 强制启用
    # FEISHU_SSO_ENABLED = True
    # FEISHU_SSO_APP_ID = 'cli_a9a7xxxxxdbb4'
    # FEISHU_SSO_APP_SECRET = '26YOsEhHdQ3xxxxxxxxxxxxxxxxxx7u1v3jz'
    # FEISHU_SSO_AUTO_CREATE_USER = True
    # FEISHU_SSO_ALWAYS_UPDATE_USER = True
    # FEISHU_SSO_MATCH_BY_EMAIL = False
    # FEISHU_SSO_USERNAME_FIELD = 'mobile'
    # FEISHU_SSO_DEFAULT_ORG_IDS = ['00000000-0000-0000-0000-000000000002']
    # AUTH_BACKEND_FEISHU_SSO = 'xpack.plugins.feishu_sso.auth_backend.FeishuSSOBackend'


    # 飞书SSO配置 - 从标准配置文件读取
    FEISHU_SSO_ENABLED = const.CONFIG.FEISHU_SSO_ENABLED
    FEISHU_SSO_APP_ID = const.CONFIG.FEISHU_SSO_APP_ID
    FEISHU_SSO_APP_SECRET = const.CONFIG.FEISHU_SSO_APP_SECRET
    FEISHU_SSO_AUTO_CREATE_USER = const.CONFIG.FEISHU_SSO_AUTO_CREATE_USER
    FEISHU_SSO_ALWAYS_UPDATE_USER = const.CONFIG.FEISHU_SSO_ALWAYS_UPDATE_USER
    FEISHU_SSO_MATCH_BY_EMAIL = const.CONFIG.FEISHU_SSO_MATCH_BY_EMAIL
    FEISHU_SSO_USERNAME_FIELD = const.CONFIG.FEISHU_SSO_USERNAME_FIELD
    FEISHU_SSO_DEFAULT_ORG_IDS = const.CONFIG.FEISHU_SSO_DEFAULT_ORG_IDS
    AUTH_BACKEND_FEISHU_SSO = 'xpack.plugins.feishu_sso.auth_backend.FeishuSSOBackend'
