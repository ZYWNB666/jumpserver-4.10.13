# -*- coding: utf-8 -*-
#
import secrets
from urllib.parse import urlencode

from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import login as auth_login
from django.views import View
from django.conf import settings
from django.http import JsonResponse
from rest_framework.permissions import AllowAny

from common.utils import get_logger
from authentication.mixins import AuthMixin
from .auth_backend import FeishuSSOBackend
from .sdk.client import FeishuSSOClient

logger = get_logger(__file__)


class FeishuSSOLoginView(View):
    """
    飞书SSO登录入口视图
    
    功能：
    1. 生成OAuth授权URL
    2. 重定向到飞书授权页面
    3. 使用state参数防止CSRF攻击
    """
    
    permission_classes = (AllowAny,)
    
    def get(self, request):
        """
        处理GET请求，重定向到飞书OAuth授权页面
        
        Args:
            request: HTTP请求对象
        
        Returns:
            HttpResponseRedirect: 重定向到飞书授权页面
        """
        # 检查是否启用飞书SSO
        if not getattr(settings, 'FEISHU_SSO_ENABLED', False):
            logger.warning('Feishu SSO is not enabled')
            return JsonResponse({
                'error': 'Feishu SSO is not enabled'
            }, status=400)
        
        # 构造回调URL
        redirect_uri = request.build_absolute_uri('/api/v1/xpack/feishu-sso/callback/')
        
        # 生成state并保存到session
        state = self._generate_state(request)
        
        # 保存原始请求URL，用于登录后跳转
        next_url = request.GET.get('next', '/')
        request.session['feishu_sso_next'] = next_url
        
        # 构造飞书OAuth授权URL
        params = {
            'app_id': settings.FEISHU_SSO_APP_ID,
            'redirect_uri': redirect_uri,
            'state': state,
        }
        
        auth_url = f'https://open.feishu.cn/open-apis/authen/v1/index?{urlencode(params)}'
        
        logger.info(f'Redirecting to Feishu OAuth: {auth_url}')
        return redirect(auth_url)
    
    def _generate_state(self, request):
        """
        生成并保存state参数
        
        state用于防止CSRF攻击，是OAuth 2.0协议的安全要求
        
        Args:
            request: HTTP请求对象
        
        Returns:
            str: 生成的state字符串
        """
        state = secrets.token_urlsafe(32)
        request.session['feishu_sso_state'] = state
        request.session.save()
        logger.debug(f'Generated state: {state[:10]}...')
        return state


class FeishuSSOCallbackView(AuthMixin, View):
    """
    飞书SSO回调视图
    
    功能：
    1. 接收飞书OAuth回调
    2. 验证state参数
    3. 使用code进行认证
    4. 登录用户并跳转
    """
    
    permission_classes = (AllowAny,)
    
    def get(self, request):
        """
        处理飞书OAuth回调
        
        Args:
            request: HTTP请求对象,包含code和state参数
        
        Returns:
            HttpResponseRedirect: 登录成功后重定向到目标页面
            JsonResponse: 登录失败返回错误信息
        """
        # 调试: 检查请求开始时的session状态
        logger.info(f'Callback request session_key at start: {request.session.session_key}')
        logger.info(f'Callback request COOKIES: {list(request.COOKIES.keys())}')
        
        code = request.GET.get('code')
        state = request.GET.get('state')
        
        # 验证参数
        if not code or not state:
            logger.warning('Missing code or state in callback')
            return JsonResponse({
                'error': 'Missing required parameters'
            }, status=400)
        
        # 验证state
        session_state = request.session.get('feishu_sso_state')
        if not session_state or state != session_state:
            logger.warning(f'Invalid state: expected {session_state}, got {state}')
            return JsonResponse({
                'error': 'Invalid state parameter'
            }, status=400)
        
        # 清除session中的state
        if 'feishu_sso_state' in request.session:
            del request.session['feishu_sso_state']
        
        # 使用认证后端进行认证
        backend = FeishuSSOBackend()
        user = backend.authenticate(request, feishu_code=code)
        
        if user:
            # 设置 user.backend 属性,Django login() 需要这个
            user.backend = settings.AUTH_BACKEND_FEISHU_SSO
            
            # 先调用 JumpServer 的认证检查,设置 session 数据
            try:
                self.check_oauth2_auth(user, settings.AUTH_BACKEND_FEISHU_SSO)
                logger.info(f'check_oauth2_auth completed: auth_password={request.session.get("auth_password")}, user_id={request.session.get("user_id")}')
            except Exception as e:
                self.set_login_failed_mark()
                msg = str(e)
                logger.error(f'Feishu SSO auth check failed: {msg}')
                return JsonResponse({
                    'error': 'Authentication failed',
                    'message': msg
                }, status=401)
            
            # 然后调用 Django 标准登录,这会:
            # 1. 设置 user 到 request.user
            # 2. 调用 cycle_key() 创建新的 session key
            # 3. 设置 Django 的 session 变量
            # 4. 标记 session 为 modified
            auth_login(request, user)
            logger.info(f'Django login completed for user: {user.username}')
            logger.info(f'Session key after login: {request.session.session_key}')
            logger.info(f'Session data: auth_password={request.session.get("auth_password")}, _auth_user_backend={request.session.get("_auth_user_backend")}')
            logger.info(f'Session modified flag: {request.session.modified}')
            
            # 显式保存session，确保数据持久化到Redis
            request.session.save()
            logger.info(f'Session explicitly saved after login')
            
            logger.info(f'User logged in via Feishu SSO: {user.username}')
            
            # 构建重定向URL
            guard_url = reverse('authentication:login-guard')
            args = request.META.get('QUERY_STRING', '')
            if args:
                guard_url = "%s?%s" % (guard_url, args)
            
            logger.info(f'Final redirect to guard view: {guard_url}')
            
            # 返回重定向
            response = redirect(guard_url)
            logger.info(f'Redirect response created, session_key in response: {request.session.session_key}')
            return response
        else:
            logger.warning('Authentication failed')
            return JsonResponse({
                'error': 'Authentication failed',
                'message': '飞书登录失败，请检查您的账号是否已绑定或联系管理员'
            }, status=401)


class FeishuJSSDKConfigView(View):
    """
    飞书JS-SDK配置视图
    
    功能：
    提供JS-SDK初始化所需的配置参数，用于网页内免登录
    """
    
    permission_classes = (AllowAny,)
    
    def get(self, request):
        """
        获取JS-SDK配置
        
        Args:
            request: HTTP请求对象
        
        Query Parameters:
            url: 当前页面的完整URL（必需）
        
        Returns:
            JsonResponse: JS-SDK配置JSON
        """
        # 检查是否启用飞书SSO
        if not getattr(settings, 'FEISHU_SSO_ENABLED', False):
            return JsonResponse({
                'error': 'Feishu SSO is not enabled'
            }, status=400)
        
        # 获取URL参数
        url = request.GET.get('url')
        if not url:
            # 如果没有提供URL，使用当前请求的URL
            url = request.build_absolute_uri()
        
        try:
            # 初始化飞书客户端
            client = FeishuSSOClient(
                app_id=settings.FEISHU_SSO_APP_ID,
                app_secret=settings.FEISHU_SSO_APP_SECRET
            )
            
            # 获取JS-SDK配置
            config = client.get_jssdk_config(url)
            
            logger.debug(f'Generated JS-SDK config for URL: {url}')
            return JsonResponse(config)
            
        except Exception as e:
            logger.error(f'Error generating JS-SDK config: {str(e)}', exc_info=True)
            return JsonResponse({
                'error': 'Failed to generate JS-SDK config',
                'message': str(e)
            }, status=500)


class FeishuSSOStatusView(View):
    """
    飞书SSO状态检查视图
    
    功能：
    检查当前用户的飞书SSO绑定状态
    """
    
    def get(self, request):
        """
        获取当前用户的飞书绑定状态
        
        Returns:
            JsonResponse: 绑定状态信息
        """
        if not request.user.is_authenticated:
            return JsonResponse({
                'bound': False,
                'message': '用户未登录'
            })
        
        is_bound = bool(request.user.feishu_id)
        
        return JsonResponse({
            'bound': is_bound,
            'feishu_id': request.user.feishu_id if is_bound else None,
            'username': request.user.username,
        })