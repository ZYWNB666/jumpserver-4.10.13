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
XPACK_LICENSE_IS_VALID = False
XPACK_LICENSE_EDITION = ""
XPACK_LICENSE_EDITION_ULTIMATE = False
XPACK_LICENSE_INFO = {
    'corporation': corporation,
}

XPACK_LICENSE_CONTENT = 'community'

if XPACK_ENABLED:
    from xpack.utils import get_xpack_templates_dir, get_xpack_context_processor

    INSTALLED_APPS.insert(0, 'xpack.apps.XpackConfig')
    XPACK_TEMPLATES_DIR = get_xpack_templates_dir(const.BASE_DIR)
    XPACK_CONTEXT_PROCESSOR = get_xpack_context_processor()
    TEMPLATES[0]['DIRS'].extend(XPACK_TEMPLATES_DIR)
    TEMPLATES[0]['OPTIONS']['context_processors'].extend(XPACK_CONTEXT_PROCESSOR)
    
    # 飞书SSO配置 - 强制启用
    FEISHU_SSO_ENABLED = True
    FEISHU_SSO_APP_ID = 'cli_a9a720278879dbb4'
    FEISHU_SSO_APP_SECRET = '26YOsEhHdQ3ms4UP2dtwXfPDA7u1v3jz'
    FEISHU_SSO_AUTO_CREATE_USER = True
    FEISHU_SSO_ALWAYS_UPDATE_USER = True
    FEISHU_SSO_MATCH_BY_EMAIL = False
    FEISHU_SSO_USERNAME_FIELD = 'mobile'
    FEISHU_SSO_DEFAULT_ORG_IDS = ['00000000-0000-0000-0000-000000000002']
