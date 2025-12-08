# -*- coding: utf-8 -*-
#
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class LicenseDetailView(APIView):
    """
    License详情视图 - 社区版简化实现
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """返回社区版license信息"""
        return Response({
            'license': {
                'edition': 'Community',
                'is_valid': True,
                'expired': False,
                'message': 'Community Edition'
            }
        })
