# -*- coding: utf-8 -*-
#
import time
import hashlib
import random
import string
import requests
from django.core.cache import cache
from common.utils import get_logger

logger = get_logger(__file__)


class FeishuSSOClient:
    """
    飞书企业自建应用SDK客户端
    
    实现功能：
    1. 获取企业级access_token
    2. 通过code获取用户信息
    3. 生成JS-SDK配置（用于网页内免登录）
    """
    
    BASE_URL = 'https://open.feishu.cn/open-apis'
    
    def __init__(self, app_id, app_secret):
        """
        初始化飞书客户端
        
        Args:
            app_id: 飞书应用的App ID
            app_secret: 飞书应用的App Secret
        """
        self.app_id = app_id
        self.app_secret = app_secret
    
    def get_tenant_access_token(self):
        """
        获取tenant_access_token（企业级访问令牌）
        
        tenant_access_token用于访问企业级API，有效期2小时
        使用缓存机制避免频繁请求
        
        Returns:
            str: tenant_access_token
        
        Raises:
            Exception: 获取token失败时抛出异常
        """
        cache_key = f'feishu_sso_token:{self.app_id}'
        token = cache.get(cache_key)
        
        if token:
            logger.debug(f'Using cached tenant_access_token for app_id: {self.app_id}')
            return token
        
        url = f'{self.BASE_URL}/auth/v3/tenant_access_token/internal'
        data = {
            'app_id': self.app_id,
            'app_secret': self.app_secret
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get('code') == 0:
                token = result['tenant_access_token']
                # 提前60秒过期，避免边界问题
                expire = result.get('expire', 7200) - 60
                cache.set(cache_key, token, expire)
                logger.info(f'Successfully obtained tenant_access_token for app_id: {self.app_id}')
                return token
            else:
                error_msg = f"Failed to get tenant_access_token: {result}"
                logger.error(error_msg)
                raise Exception(error_msg)
        except requests.RequestException as e:
            error_msg = f"Network error when getting tenant_access_token: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def get_user_info_by_code(self, code):
        """
        通过OAuth code获取用户信息
        
        工作流程：
        1. 使用code换取user_access_token
        2. 使用user_access_token获取用户详细信息
        
        Args:
            code: OAuth授权code（临时授权码）
        
        Returns:
            dict: 用户信息字典，包含user_id, name, email等
                  返回None表示获取失败
        
        Example:
            {
                'user_id': 'ou_xxx',
                'name': '张三',
                'en_name': 'Zhang San',
                'email': 'zhangsan@example.com',
                'mobile': '+86-13800138000',
                'avatar_url': 'https://...',
            }
        """
        tenant_token = self.get_tenant_access_token()
        
        # 步骤1: 通过code获取user_access_token
        url = f'{self.BASE_URL}/authen/v1/access_token'
        headers = {
            'Authorization': f'Bearer {tenant_token}',
            'Content-Type': 'application/json'
        }
        data = {
            'grant_type': 'authorization_code',
            'code': code
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            result = response.json()
            
            if result.get('code') != 0:
                logger.warning(f"Failed to get user_access_token: {result}")
                return None
            
            user_access_token = result['data']['access_token']
            
            # 步骤2: 获取用户详细信息
            url = f'{self.BASE_URL}/authen/v1/user_info'
            headers = {
                'Authorization': f'Bearer {user_access_token}'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            result = response.json()
            
            if result.get('code') == 0:
                user_info = result['data']
                logger.info(f"Successfully obtained user info for user_id: {user_info.get('user_id')}")
                return user_info
            else:
                logger.warning(f"Failed to get user info: {result}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Network error when getting user info: {str(e)}")
            return None
    
    def get_jssdk_config(self, url):
        """
        获取飞书JS-SDK配置
        
        用于在飞书客户端内嵌网页中实现免登录
        
        Args:
            url: 当前网页的完整URL（必须是当前页面URL，用于签名验证）
        
        Returns:
            dict: JS-SDK配置字典
        
        Example:
            {
                'appId': 'cli_xxx',
                'timestamp': 1234567890,
                'nonceStr': 'abc123',
                'signature': 'xxx'
            }
        """
        tenant_token = self.get_tenant_access_token()
        
        # 获取jsapi_ticket
        api_url = f'{self.BASE_URL}/jssdk/ticket/get'
        headers = {
            'Authorization': f'Bearer {tenant_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(api_url, headers=headers, json={}, timeout=10)
            result = response.json()
            
            if result.get('code') != 0:
                error_msg = f"Failed to get jsapi_ticket: {result}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            ticket = result['data']['ticket']
            timestamp = int(time.time())
            noncestr = self._generate_nonce_str()
            
            # 生成签名
            signature = self._generate_signature(ticket, noncestr, timestamp, url)
            
            config = {
                'appId': self.app_id,
                'timestamp': timestamp,
                'nonceStr': noncestr,
                'signature': signature
            }
            
            logger.debug(f"Generated JS-SDK config for URL: {url}")
            return config
            
        except requests.RequestException as e:
            error_msg = f"Network error when getting JS-SDK config: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _generate_signature(self, ticket, noncestr, timestamp, url):
        """
        生成JS-SDK签名
        
        签名算法：
        1. 将参数按key=value格式拼接，用&连接
        2. 对拼接字符串进行SHA1哈希
        
        Args:
            ticket: jsapi_ticket
            noncestr: 随机字符串
            timestamp: 时间戳
            url: 当前页面URL
        
        Returns:
            str: 签名字符串（十六进制）
        """
        string = f'jsapi_ticket={ticket}&noncestr={noncestr}&timestamp={timestamp}&url={url}'
        signature = hashlib.sha1(string.encode('utf-8')).hexdigest()
        return signature
    
    def _generate_nonce_str(self, length=16):
        """
        生成随机字符串
        
        Args:
            length: 字符串长度，默认16
        
        Returns:
            str: 随机字符串
        """
        chars = string.ascii_letters + string.digits
        return ''.join(random.choices(chars, k=length))
    
    def get_department_list(self, parent_department_id='0'):
        """
        获取部门列表（用于组织架构同步）
        
        Args:
            parent_department_id: 父部门ID，0表示根部门
        
        Returns:
            list: 部门列表
        """
        tenant_token = self.get_tenant_access_token()
        
        url = f'{self.BASE_URL}/contact/v3/departments'
        headers = {
            'Authorization': f'Bearer {tenant_token}'
        }
        params = {
            'parent_department_id': parent_department_id,
            'fetch_child': True
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            result = response.json()
            
            if result.get('code') == 0:
                departments = result.get('data', {}).get('items', [])
                logger.info(f"Successfully obtained {len(departments)} departments")
                return departments
            else:
                logger.warning(f"Failed to get department list: {result}")
                return []
                
        except requests.RequestException as e:
            logger.error(f"Network error when getting department list: {str(e)}")
            return []