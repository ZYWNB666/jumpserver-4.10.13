# -*- coding: utf-8 -*-
#
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views import View

from common.utils import get_logger

logger = get_logger(__file__)

__all__ = ['EmailRequiredView']


def is_temp_email(email):
    """检查是否是临时邮箱，需要用户填写真实的 @magikcompute.ai 邮箱"""
    if not email:
        return True
    # 只有 @magikcompute.ai 结尾的邮箱才是有效的，其他都需要重新填写
    return not email.endswith('@magikcompute.ai')


class EmailRequiredView(LoginRequiredMixin, View):
    """
    邮箱填写页面视图
    当用户的邮箱是临时邮箱时，强制用户填写真实的公司邮箱
    """
    template_name = 'authentication/email_required.html'
    login_url = '/core/auth/login/'
    
    def get(self, request):
        user = request.user
        
        # 如果用户已经有有效邮箱，直接跳转到首页
        if not is_temp_email(user.email):
            return redirect('/')
        
        context = {
            'user': user,
            'INTERFACE': self.get_interface_settings(),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        user = request.user
        email = request.POST.get('email', '').strip()
        
        context = {
            'user': user,
            'INTERFACE': self.get_interface_settings(),
            'email_value': email,
        }
        
        # 验证邮箱
        if not email:
            context['error'] = _('Please enter your email address')
            return render(request, self.template_name, context)
        
        if not email.endswith('@magikcompute.ai'):
            context['error'] = _('Email must end with @magikcompute.ai')
            return render(request, self.template_name, context)
        
        # 检查邮箱是否已被使用
        from users.models import User
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            context['error'] = _('This email is already in use')
            return render(request, self.template_name, context)
        
        # 更新用户邮箱，同时标记不是首次登录
        try:
            user.email = email
            user.is_first_login = False  # 标记已完成首次登录设置
            user.save(update_fields=['email', 'is_first_login'])
            logger.info(f'User {user.username} updated email to {email}')
            
            # 跳转到首页
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
        except Exception as e:
            logger.error(f'Failed to update email for user {user.username}: {e}')
            context['error'] = _('Failed to update email, please try again')
            return render(request, self.template_name, context)
    
    @staticmethod
    def get_interface_settings():
        """获取界面设置"""
        from settings.utils import get_interface_setting_or_default
        return get_interface_setting_or_default()

