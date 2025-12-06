# -*- coding: utf-8 -*-
"""
文件传输中转API
支持通过对象存储中转文件，绕过JumpServer服务器流量
"""
import os
import uuid
import tempfile

from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsServiceAccount, IsValidUser
from common.storage.base import get_multi_object_storage
from common.utils import get_logger
from audits.models import FTPLog

logger = get_logger(__name__)

__all__ = ['FileTransferAPI', 'FileTransferPresignedURLAPI']


class FileTransferPresignedURLAPI(APIView):
    """
    文件传输预签名URL API
    
    用于工作台文件传输功能，让koko/用户直接从对象存储上传/下载文件
    绕过JumpServer服务器，节省云服务商流量费用
    
    使用流程：
    1. 前端/koko调用此API获取上传预签名URL
    2. 前端/用户直接上传文件到对象存储
    3. 前端/koko调用此API获取下载预签名URL
    4. koko从对象存储下载文件传给目标服务器
    """
    permission_classes = [IsServiceAccount | IsValidUser]
    
    rbac_perms = {
        'POST': 'audits.add_ftplog',
        'GET': 'audits.view_ftplog',
    }
    
    def _get_storage_instance(self):
        """获取配置的对象存储实例"""
        from common.storage.jms_storage.s3 import S3Storage
        from common.storage.jms_storage.oss import OSSStorage
        from common.storage.jms_storage.obs import OBSStorage
        
        storage = get_multi_object_storage()
        if not storage:
            return None, None
        
        storage_instance = None
        if hasattr(storage, 'storage_list') and storage.storage_list:
            storage_instance = storage.storage_list[0]
        
        if not storage_instance:
            return None, None
        
        storage_type = None
        if isinstance(storage_instance, S3Storage):
            storage_type = 's3'
        elif isinstance(storage_instance, OSSStorage):
            storage_type = 'oss'
        elif isinstance(storage_instance, OBSStorage):
            storage_type = 'obs'
        
        return storage_instance, storage_type
    
    def _generate_presigned_url(self, storage_instance, storage_type, filepath, action, expires):
        """生成预签名URL"""
        from common.storage.jms_storage.s3 import S3Storage
        from common.storage.jms_storage.oss import OSSStorage
        from common.storage.jms_storage.obs import OBSStorage
        
        presigned_url = None
        
        try:
            # S3/MinIO 兼容存储
            if isinstance(storage_instance, S3Storage):
                if action == 'upload':
                    presigned_url = storage_instance.client.generate_presigned_url(
                        'put_object',
                        Params={
                            'Bucket': storage_instance.bucket,
                            'Key': filepath
                        },
                        ExpiresIn=expires
                    )
                else:  # download
                    url, err = storage_instance.generate_presigned_url(filepath, expire=expires)
                    if url and url is not False:
                        presigned_url = url
            
            # 阿里云 OSS
            elif isinstance(storage_instance, OSSStorage):
                if hasattr(storage_instance, 'client') and storage_instance.client:
                    method = 'PUT' if action == 'upload' else 'GET'
                    presigned_url = storage_instance.client.sign_url(method, filepath, expires)
            
            # 华为云 OBS
            elif isinstance(storage_instance, OBSStorage):
                if hasattr(storage_instance, 'obsClient') and storage_instance.obsClient:
                    method = 'PUT' if action == 'upload' else 'GET'
                    resp = storage_instance.obsClient.createSignedUrl(
                        method=method,
                        bucketName=storage_instance.bucket,
                        objectKey=filepath,
                        expires=expires
                    )
                    if hasattr(resp, 'signedUrl'):
                        presigned_url = resp.signedUrl
        
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
        
        return presigned_url
    
    def post(self, request, *args, **kwargs):
        """
        生成上传预签名URL
        
        请求体:
        {
            "filename": "test.txt",
            "asset": "asset_name",
            "account": "root",
            "session_id": "xxx-xxx"  # 可选
        }
        
        响应:
        {
            "upload_url": "https://...",
            "download_url": "https://...",
            "filepath": "FTP_FILES/2024-12-06/xxx",
            "ftp_log_id": "xxx-xxx",
            "expires": 3600,
            "storage_type": "s3"
        }
        """
        filename = request.data.get('filename', '')
        asset = request.data.get('asset', '')
        account = request.data.get('account', '')
        session_id = request.data.get('session_id', str(uuid.uuid4()))
        expires = int(request.data.get('expires', 3600))
        
        if not filename:
            return Response({'error': 'filename is required'}, status=400)
        
        # 获取存储实例
        storage_instance, storage_type = self._get_storage_instance()
        if not storage_instance:
            return Response({
                'error': 'No object storage configured',
                'hint': 'Please configure replay storage in System Settings'
            }, status=400)
        
        # 创建FTPLog记录
        from audits.const import OperateChoices
        ftp_log = FTPLog.objects.create(
            user=request.user.username,
            remote_addr=request.META.get('REMOTE_ADDR', ''),
            asset=asset,
            account=account,
            operate=OperateChoices.upload,
            filename=filename,
            session=session_id,
            has_file=False
        )
        
        filepath = ftp_log.filepath
        
        # 生成上传和下载URL
        upload_url = self._generate_presigned_url(
            storage_instance, storage_type, filepath, 'upload', expires
        )
        download_url = self._generate_presigned_url(
            storage_instance, storage_type, filepath, 'download', expires
        )
        
        if not upload_url:
            ftp_log.delete()
            return Response({'error': 'Failed to generate upload URL'}, status=500)
        
        logger.info(f"Generated presigned URLs for file transfer: {filename}")
        
        return Response({
            'upload_url': upload_url,
            'download_url': download_url,
            'filepath': filepath,
            'ftp_log_id': str(ftp_log.id),
            'expires': expires,
            'storage_type': storage_type
        }, status=201)
    
    def get(self, request, *args, **kwargs):
        """
        根据FTPLog ID获取下载预签名URL
        
        参数:
            ftp_log_id: FTPLog记录ID
            expires: URL有效期(秒)，默认3600
        """
        ftp_log_id = request.query_params.get('ftp_log_id')
        expires = int(request.query_params.get('expires', 3600))
        
        if not ftp_log_id:
            return Response({'error': 'ftp_log_id is required'}, status=400)
        
        ftp_log = FTPLog.objects.filter(id=ftp_log_id).first()
        if not ftp_log:
            return Response({'error': 'FTPLog not found'}, status=404)
        
        storage_instance, storage_type = self._get_storage_instance()
        if not storage_instance:
            return Response({'error': 'No object storage configured'}, status=400)
        
        filepath = ftp_log.filepath
        
        download_url = self._generate_presigned_url(
            storage_instance, storage_type, filepath, 'download', expires
        )
        
        if not download_url:
            return Response({'error': 'Failed to generate download URL'}, status=500)
        
        return Response({
            'download_url': download_url,
            'filepath': filepath,
            'filename': ftp_log.filename,
            'expires': expires,
            'storage_type': storage_type
        })


class FileTransferAPI(APIView):
    """
    文件传输确认API
    
    用于确认文件已上传到对象存储，更新FTPLog状态
    """
    permission_classes = [IsServiceAccount | IsValidUser]
    
    rbac_perms = {
        'POST': 'audits.change_ftplog',
    }
    
    def post(self, request, *args, **kwargs):
        """
        确认文件已上传到对象存储
        
        请求体:
        {
            "ftp_log_id": "xxx-xxx",
            "success": true
        }
        """
        ftp_log_id = request.data.get('ftp_log_id')
        success = request.data.get('success', True)
        
        if not ftp_log_id:
            return Response({'error': 'ftp_log_id is required'}, status=400)
        
        ftp_log = FTPLog.objects.filter(id=ftp_log_id).first()
        if not ftp_log:
            return Response({'error': 'FTPLog not found'}, status=404)
        
        if success:
            # 验证文件是否真的存在于对象存储中
            storage = get_multi_object_storage()
            if storage:
                try:
                    exists = storage.exists(ftp_log.filepath)
                    if exists:
                        ftp_log.has_file = True
                        ftp_log.is_success = True
                        ftp_log.save(update_fields=['has_file', 'is_success'])
                        logger.info(f"File transfer confirmed: {ftp_log.filename}")
                        return Response({'status': 'confirmed', 'has_file': True})
                except Exception as e:
                    logger.warning(f"Failed to verify file existence: {e}")
        
        ftp_log.is_success = success
        ftp_log.save(update_fields=['is_success'])
        
        return Response({'status': 'updated', 'has_file': ftp_log.has_file})

