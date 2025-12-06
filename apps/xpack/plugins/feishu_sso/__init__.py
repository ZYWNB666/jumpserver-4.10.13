# -*- coding: utf-8 -*-
#
"""
飞书企业单点登录(SSO)插件

功能特性：
1. 支持飞书企业自建应用的OAuth 2.0认证
2. 支持用户从飞书工作台直接登录JumpServer
3. 支持网页内通过飞书JS-SDK免登录
4. 自动创建和同步用户信息
"""

default_app_config = 'xpack.plugins.feishu_sso.apps.FeishuSsoConfig'