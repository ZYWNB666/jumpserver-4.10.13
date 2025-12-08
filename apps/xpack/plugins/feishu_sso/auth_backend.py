# -*- coding: utf-8 -*-
#
from django.contrib.auth.backends import BaseBackend
from django.conf import settings
from users.models import User
from common.utils import get_logger
from .sdk.client import FeishuSSOClient

logger = get_logger(__file__)


class FeishuSSOBackend(BaseBackend):
    """
    飞书SSO认证后端
    
    实现Django的认证接口，支持通过飞书OAuth code进行用户认证
    
    认证流程：
    1. 接收OAuth authorization code
    2. 通过SDK获取飞书用户信息
    3. 查找或创建JumpServer用户
    4. 返回认证结果
    """
    
    def authenticate(self, request, feishu_code=None, **kwargs):
        """
        使用飞书code进行认证
        
        Args:
            request: HTTP请求对象
            feishu_code: 飞书OAuth授权码
            **kwargs: 其他参数
        
        Returns:
            User: 认证成功返回用户对象，失败返回None
        """
        if not feishu_code:
            logger.debug('No feishu_code provided in authentication')
            return None
        
        # 检查是否启用飞书SSO
        if not getattr(settings, 'FEISHU_SSO_ENABLED', False):
            logger.warning('Feishu SSO is not enabled')
            return None
        
        try:
            # 初始化飞书客户端
            client = FeishuSSOClient(
                app_id=settings.FEISHU_SSO_APP_ID,
                app_secret=settings.FEISHU_SSO_APP_SECRET
            )
            
            # 通过code获取用户信息
            user_info = client.get_user_info_by_code(feishu_code)
            
            if not user_info:
                logger.warning('Failed to get user info from Feishu')
                return None
            
            feishu_user_id = user_info.get('user_id')
            if not feishu_user_id:
                logger.warning('No user_id in Feishu user info')
                return None
            
            # 查找已存在的用户
            user = self._find_user(feishu_user_id, user_info)
            
            if user:
                # 更新用户信息
                if getattr(settings, 'FEISHU_SSO_ALWAYS_UPDATE_USER', True):
                    self._update_user_info(user, user_info)
                
                logger.info(f'User authenticated via Feishu SSO: {user.username}')
                return user if user.is_active else None
            
            # 自动创建用户（如果配置允许）
            if getattr(settings, 'FEISHU_SSO_AUTO_CREATE_USER', False):
                user = self._create_user_from_feishu(user_info)
                if user:
                    logger.info(f'New user created via Feishu SSO: {user.username}')
                    return user
            
            logger.warning(f'User not found and auto-create is disabled: {feishu_user_id}')
            return None
            
        except Exception as e:
            logger.error(f'Error in Feishu SSO authentication: {str(e)}', exc_info=True)
            return None
    
    def _find_user(self, feishu_user_id, user_info):
        """
        查找用户
        
        查找策略：
        1. 优先通过feishu_id查找
        2. 如果没找到，尝试通过email查找（如果配置允许）
        
        Args:
            feishu_user_id: 飞书用户ID
            user_info: 飞书用户信息
        
        Returns:
            User: 用户对象或None
        """
        # 优先通过feishu_id查找
        try:
            user = User.objects.get(feishu_id=feishu_user_id)
            return user
        except User.DoesNotExist:
            pass
        
        # 如果允许，通过email查找
        if getattr(settings, 'FEISHU_SSO_MATCH_BY_EMAIL', False):
            email = user_info.get('email')
            if email:
                try:
                    user = User.objects.get(email=email)
                    # 绑定飞书ID
                    user.feishu_id = feishu_user_id
                    user.save(update_fields=['feishu_id'])
                    logger.info(f'Bound feishu_id to existing user by email: {email}')
                    return user
                except User.DoesNotExist:
                    pass
        
        return None
    
    def _create_user_from_feishu(self, user_info):
        """
        从飞书用户信息创建JumpServer用户
        
        Args:
            user_info: 飞书用户信息字典
        
        Returns:
            User: 创建的用户对象或None
        """
        try:
            feishu_user_id = user_info.get('user_id')
            name = user_info.get('name', '')
            email = user_info.get('email', '')
            mobile = user_info.get('mobile', '')
            
            # 使用飞书用户ID作为username
            # 如果想使用其他字段，可以通过配置自定义
            username_field = getattr(settings, 'FEISHU_SSO_USERNAME_FIELD', 'user_id')
            username = user_info.get(username_field, feishu_user_id)
            
            # 检查username是否已存在
            if User.objects.filter(username=username).exists():
                logger.warning(f'Username already exists: {username}')
                return None
            
            # 获取默认组织
            from orgs.models import Organization
            default_org_ids = getattr(settings, 'FEISHU_SSO_DEFAULT_ORG_IDS', [])
            if default_org_ids:
                default_org = Organization.objects.filter(id__in=default_org_ids).first()
            else:
                default_org = Organization.default()
            
            # 创建用户
            user = User.objects.create(
                username=username,
                name=name or username,
                email=email,
                phone=mobile,
                feishu_id=feishu_user_id,
                source='feishu_sso',
                is_active=True,
            )
            
            # 添加到组织(使用add_member方法,它会自动创建正确的角色绑定)
            if default_org:
                default_org.add_member(user)
            
            logger.info(f'Created new user from Feishu: {username}')
            return user
            
        except Exception as e:
            logger.error(f'Error creating user from Feishu: {str(e)}', exc_info=True)
            return None
    
    def _update_user_info(self, user, user_info):
        """
        更新用户信息
        
        Args:
            user: 用户对象
            user_info: 飞书用户信息
        """
        try:
            updated_fields = []
            
            # 更新名称
            name = user_info.get('name')
            if name and user.name != name:
                user.name = name
                updated_fields.append('name')
            
            # 更新邮箱
            email = user_info.get('email')
            if email and user.email != email:
                user.email = email
                updated_fields.append('email')
            
            # 更新手机号
            mobile = user_info.get('mobile')
            if mobile and user.phone != mobile:
                user.phone = mobile
                updated_fields.append('phone')
            
            # 确保feishu_id设置正确
            feishu_user_id = user_info.get('user_id')
            if feishu_user_id and user.feishu_id != feishu_user_id:
                user.feishu_id = feishu_user_id
                updated_fields.append('feishu_id')
            
            if updated_fields:
                user.save(update_fields=updated_fields)
                logger.debug(f'Updated user fields: {updated_fields}')
                
        except Exception as e:
            logger.error(f'Error updating user info: {str(e)}', exc_info=True)
    
    def get_user(self, user_id):
        """
        通过用户ID获取用户对象
        
        Args:
            user_id: 用户ID
        
        Returns:
            User: 用户对象或None
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None