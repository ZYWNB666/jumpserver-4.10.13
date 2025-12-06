# -*- coding: utf-8 -*-
#
from importlib import import_module

from django.conf import settings
from django.db.models import F, Value, CharField, Q
from django.db.models.functions import Cast
from django.http import HttpResponse, FileResponse
from django.utils.encoding import escape_uri_path
from django_celery_beat.models import PeriodicTask
from rest_framework import generics
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.api import CommonApiMixin
from common.const.http import GET, POST
from common.drf.filters import DatetimeRangeFilterBackend
from common.permissions import IsServiceAccount
from common.plugins.es import QuerySet as ESQuerySet
from common.sessions.cache import user_session_manager
from common.storage.ftp_file import FTPFileStorageHandler
from common.storage.base import get_multi_object_storage
from common.utils import is_uuid, get_logger, lazyproperty
from ops.const import Types
from ops.models import Job
from orgs.mixins.api import OrgReadonlyModelViewSet, OrgModelViewSet
from orgs.models import Organization
from orgs.utils import current_org, tmp_to_root_org
from rbac.permissions import RBACPermission
from terminal.models import default_storage
from users.models import User
from .backends import TYPE_ENGINE_MAPPING
from .const import ActivityChoices, ActionChoices
from .filters import UserSessionFilterSet, OperateLogFilterSet
from .models import (
    FTPLog, UserLoginLog, OperateLog, PasswordChangeLog,
    ActivityLog, JobLog, UserSession, IntegrationApplicationLog
)
from .serializers import (
    FTPLogSerializer, UserLoginLogSerializer, JobLogSerializer,
    OperateLogSerializer, OperateLogActionDetailSerializer,
    PasswordChangeLogSerializer, ActivityUnionLogSerializer,
    FileSerializer, UserSessionSerializer, JobsAuditSerializer,
    ServiceAccessLogSerializer
)
from .utils import construct_userlogin_usernames, record_operate_log_and_activity_log

logger = get_logger(__name__)


class JobLogAuditViewSet(OrgReadonlyModelViewSet):
    model = JobLog
    extra_filter_backends = [DatetimeRangeFilterBackend]
    date_range_filter_fields = [
        ('date_start', ('date_from', 'date_to'))
    ]
    search_fields = ['creator__name', 'material']
    filterset_fields = ['creator__name', 'material']
    serializer_class = JobLogSerializer
    ordering = ['-date_start']


class JobsAuditViewSet(OrgModelViewSet):
    model = Job
    search_fields = ['creator__name', 'args', 'name']
    filterset_fields = ['creator__name', 'args', 'name']
    serializer_class = JobsAuditSerializer
    ordering = ['-is_periodic', '-date_updated']
    http_method_names = ['get', 'options', 'patch']

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.exclude(type=Types.upload_file).filter(instant=False)
        return queryset

    def perform_update(self, serializer):
        job = self.get_object()
        is_periodic = serializer.validated_data.get('is_periodic')
        if job.is_periodic != is_periodic:
            job.is_periodic = is_periodic
            job.save()
        name, task, args, kwargs = job.get_register_task()
        task_obj = PeriodicTask.objects.filter(name=name).first()
        if task_obj:
            is_periodic = job.is_periodic
            if task_obj.enabled != is_periodic:
                task_obj.enabled = is_periodic
                task_obj.save()
        return super().perform_update(serializer)


class FTPLogViewSet(OrgModelViewSet):
    model = FTPLog
    serializer_class = FTPLogSerializer
    extra_filter_backends = [DatetimeRangeFilterBackend]
    date_range_filter_fields = [
        ('date_start', ('date_from', 'date_to'))
    ]
    filterset_fields = ['user', 'asset', 'account', 'filename', 'session']
    search_fields = filterset_fields
    ordering = ['-date_start']
    http_method_names = ['post', 'get', 'head', 'options', 'patch']
    rbac_perms = {
        'download': 'audits.view_ftplog',
        'presigned_url': 'audits.view_ftplog',
    }

    def get_storage(self):
        return FTPFileStorageHandler(self.get_object())

    def _get_object_storage_presigned_url(self, ftp_log, expires=3600):
        """
        从配置的对象存储生成预签名URL
        支持 S3/OSS/OBS/MinIO 等兼容 S3 的对象存储
        
        文件下载时，用户将直接从对象存储下载，绕过JumpServer服务器
        这样可以避免阿里云等云服务商的出流量费用
        """
        from common.storage.jms_storage.s3 import S3Storage
        from common.storage.jms_storage.oss import OSSStorage
        from common.storage.jms_storage.obs import OBSStorage
        
        storage = get_multi_object_storage()
        if not storage:
            logger.debug("No external object storage configured")
            return None
        
        # 获取第一个可用的存储实例
        storage_instance = None
        if hasattr(storage, 'storage_list') and storage.storage_list:
            storage_instance = storage.storage_list[0]
        
        if not storage_instance:
            logger.debug("No available storage instance found")
            return None
        
        filepath = ftp_log.filepath
        
        # 先检查文件是否存在于对象存储中
        try:
            if not storage_instance.exists(filepath):
                logger.debug(f"File {filepath} not found in object storage")
                return None
        except Exception as e:
            logger.debug(f"Failed to check file existence: {e}")
            return None
        
        try:
            # S3/MinIO 兼容存储 - 使用已有的 generate_presigned_url 方法
            if isinstance(storage_instance, S3Storage):
                presigned_url, err = storage_instance.generate_presigned_url(filepath, expire=expires)
                if presigned_url and presigned_url is not False:
                    logger.info(f"Generated S3/MinIO presigned URL for {filepath}")
                    return presigned_url
                if err:
                    logger.warning(f"S3 presigned URL generation error: {err}")
            
            # 阿里云 OSS - 使用 oss2.Bucket.sign_url 方法
            elif isinstance(storage_instance, OSSStorage):
                if hasattr(storage_instance, 'client') and storage_instance.client:
                    presigned_url = storage_instance.client.sign_url('GET', filepath, expires)
                    logger.info(f"Generated OSS presigned URL for {filepath}")
                    return presigned_url
            
            # 华为云 OBS
            elif isinstance(storage_instance, OBSStorage):
                if hasattr(storage_instance, 'obsClient') and storage_instance.obsClient:
                    resp = storage_instance.obsClient.createSignedUrl(
                        method='GET',
                        bucketName=storage_instance.bucket,
                        objectKey=filepath,
                        expires=expires
                    )
                    if hasattr(resp, 'signedUrl'):
                        logger.info(f"Generated OBS presigned URL for {filepath}")
                        return resp.signedUrl
        
        except Exception as e:
            logger.warning(f"Failed to generate presigned URL: {e}")
        
        return None

    @action(
        methods=[GET], detail=True, permission_classes=[RBACPermission, ],
        url_path='file/download'
    )
    def download(self, request, *args, **kwargs):
        """
        文件下载接口 - 优先使用对象存储预签名URL
        如果配置了对象存储，将重定向到预签名URL，用户直接从对象存储下载
        这样可以避免JumpServer服务器的流量费用
        """
        from django.http import HttpResponseRedirect
        
        ftp_log = self.get_object()
        
        # 尝试生成对象存储预签名URL
        presigned_url = self._get_object_storage_presigned_url(ftp_log, expires=3600)
        
        if presigned_url:
            # 记录下载操作
            record_operate_log_and_activity_log(
                [ftp_log.id], ActionChoices.download, '', self.model,
                resource_display=f'{ftp_log.asset}: {ftp_log.filename}',
            )
            
            # 重定向到对象存储预签名URL，绕过JumpServer流量
            logger.info(f"Redirecting download to object storage for {ftp_log.filename}")
            return HttpResponseRedirect(presigned_url)
        
        # 回退到原有逻辑：从本地存储下载
        logger.info(f"Using local storage download for {ftp_log.filename}")
        ftp_storage = self.get_storage()
        local_path, url = ftp_storage.get_file_path_url()
        if local_path is None:
            # url => error message
            return HttpResponse(url)

        file = open(default_storage.path(local_path), 'rb')
        response = FileResponse(file)
        response['Content-Type'] = 'application/octet-stream'
        filename = escape_uri_path(ftp_log.filename)
        response["Content-Disposition"] = "attachment; filename*=UTF-8''{}".format(filename)

        record_operate_log_and_activity_log(
            [ftp_log.id], ActionChoices.download, '', self.model,
            resource_display=f'{ftp_log.asset}: {ftp_log.filename}',
        )
        return response

    @action(
        methods=[GET], detail=True, permission_classes=[IsServiceAccount, ],
        url_path='presigned-url'
    )
    def presigned_url(self, request, *args, **kwargs):
        """
        获取预签名URL接口
        用于koko/lion等组件直接获取上传/下载URL，实现直传对象存储
        
        参数:
            action: 'upload' 或 'download' (默认: download)
            expires: URL有效期秒数 (默认: 3600)
        
        使用场景:
            - koko/lion 获取上传URL后，直接将文件上传到对象存储
            - koko/lion 获取下载URL后，直接从对象存储下载文件到目标服务器
            - 这样可以完全绕过JumpServer服务器，避免云服务商流量费用
        """
        from common.storage.jms_storage.s3 import S3Storage
        from common.storage.jms_storage.oss import OSSStorage
        from common.storage.jms_storage.obs import OBSStorage
        
        ftp_log = self.get_object()
        url_action = request.query_params.get('action', 'download')
        expires = int(request.query_params.get('expires', 3600))
        
        storage = get_multi_object_storage()
        if not storage:
            return Response({'error': 'No external storage configured'}, status=400)
        
        storage_instance = None
        if hasattr(storage, 'storage_list') and storage.storage_list:
            storage_instance = storage.storage_list[0]
        
        if not storage_instance:
            return Response({'error': 'No available storage instance'}, status=400)
        
        filepath = ftp_log.filepath
        presigned_url = None
        
        try:
            # S3/MinIO 兼容存储
            if isinstance(storage_instance, S3Storage):
                if url_action == 'upload':
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
                    method = 'PUT' if url_action == 'upload' else 'GET'
                    presigned_url = storage_instance.client.sign_url(method, filepath, expires)
            
            # 华为云 OBS
            elif isinstance(storage_instance, OBSStorage):
                if hasattr(storage_instance, 'obsClient') and storage_instance.obsClient:
                    method = 'PUT' if url_action == 'upload' else 'GET'
                    resp = storage_instance.obsClient.createSignedUrl(
                        method=method,
                        bucketName=storage_instance.bucket,
                        objectKey=filepath,
                        expires=expires
                    )
                    if hasattr(resp, 'signedUrl'):
                        presigned_url = resp.signedUrl
            
            if presigned_url:
                return Response({
                    'presigned_url': presigned_url,
                    'filepath': filepath,
                    'action': url_action,
                    'expires': expires,
                    'storage_type': storage_instance.__class__.__name__
                })
            else:
                return Response({'error': 'Failed to generate presigned URL'}, status=500)
        
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            return Response({'error': str(e)}, status=500)

    @action(methods=[POST], detail=True, permission_classes=[IsServiceAccount, ], serializer_class=FileSerializer)
    def upload(self, request, *args, **kwargs):
        """
        文件上传接口
        保持原有逻辑不变，文件上传到本地后会自动同步到对象存储
        """
        ftp_log = self.get_object()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            file = serializer.validated_data['file']
            name, err = ftp_log.save_file_to_storage(file)
            if not name:
                msg = "Failed save file `{}`: {}".format(ftp_log.id, err)
                logger.error(msg)
                return Response({'msg': str(err)}, status=400)
            
            # 标记文件已上传，可以下载
            ftp_log.has_file = True
            ftp_log.save(update_fields=['has_file'])
            
            url = default_storage.url(name)
            return Response({'url': url}, status=201)
        else:
            msg = 'Upload data invalid: {}'.format(serializer.errors)
            logger.error(msg)
            return Response({'msg': serializer.errors}, status=401)


class UserLoginCommonMixin:
    model = UserLoginLog
    serializer_class = UserLoginLogSerializer
    extra_filter_backends = [DatetimeRangeFilterBackend]
    date_range_filter_fields = [
        ('datetime', ('date_from', 'date_to'))
    ]
    filterset_fields = ['id', 'username', 'ip', 'city', 'type', 'status', 'mfa']
    search_fields = ['id', 'username', 'ip', 'city']


class UserLoginLogViewSet(UserLoginCommonMixin, OrgReadonlyModelViewSet):
    @staticmethod
    def get_org_member_usernames():
        user_queryset = current_org.get_members()
        users = construct_userlogin_usernames(user_queryset)
        return users

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.model.filter_queryset_by_org(queryset)
        return queryset


class MyLoginLogViewSet(UserLoginCommonMixin, OrgReadonlyModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        username = self.request.user.username
        q = Q(username=username) | Q(username__icontains=f'({username})')
        qs = qs.filter(q)
        return qs


class ResourceActivityAPIView(generics.ListAPIView):
    serializer_class = ActivityUnionLogSerializer
    ordering_fields = ['datetime']
    rbac_perms = {
        'GET': 'audits.view_activitylog',
    }

    @staticmethod
    def get_operate_log_qs(fields, limit, org_q, resource_id=None):
        q, user = Q(resource_id=resource_id), None
        if is_uuid(resource_id):
            user = User.objects.filter(id=resource_id).first()
        if user is not None:
            q |= Q(user=str(user))
        queryset = OperateLog.objects.filter(q, org_q).annotate(
            r_type=Value(ActivityChoices.operate_log, CharField()),
            r_detail_id=Cast(F('id'), CharField()), r_detail=Value(None, CharField()),
            r_user=F('user'), r_action=F('action'),
        ).values(*fields)[:limit]
        return queryset

    @staticmethod
    def get_activity_log_qs(fields, limit, org_q, **filters):
        queryset = ActivityLog.objects.filter(org_q, **filters).annotate(
            r_type=F('type'), r_detail_id=F('detail_id'),
            r_detail=F('detail'), r_user=Value(None, CharField()),
            r_action=Value(None, CharField()),
        ).values(*fields)[:limit]
        return queryset

    def get_queryset(self):
        limit = 30
        resource_id = self.request.query_params.get('resource_id')
        fields = (
            'id', 'datetime', 'r_detail', 'r_detail_id',
            'r_user', 'r_action', 'r_type'
        )

        org_q = Q()
        if not current_org.is_root():
            org_q = Q(org_id=Organization.SYSTEM_ID) | Q(org_id=current_org.id)
            if resource_id:
                org_q |= Q(org_id='') | Q(org_id=Organization.ROOT_ID)

        with tmp_to_root_org():
            qs1 = self.get_operate_log_qs(fields, limit, org_q, resource_id=resource_id)
            qs2 = self.get_activity_log_qs(fields, limit, org_q, resource_id=resource_id)
            queryset = qs2.union(qs1)
        return queryset.order_by('-datetime')[:limit]


class OperateLogViewSet(OrgReadonlyModelViewSet):
    model = OperateLog
    serializer_class = OperateLogSerializer
    extra_filter_backends = [DatetimeRangeFilterBackend]
    date_range_filter_fields = [
        ('datetime', ('date_from', 'date_to'))
    ]
    filterset_class = OperateLogFilterSet
    search_fields = ['resource', 'user']
    ordering = ['-datetime']

    @lazyproperty
    def is_action_detail(self):
        return self.detail and self.request.query_params.get('type') == 'action_detail'

    def get_serializer_class(self):
        if self.is_action_detail:
            return OperateLogActionDetailSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        current_org_id = str(current_org.id)

        with tmp_to_root_org():
            qs = OperateLog.objects.all()
            if current_org_id != Organization.ROOT_ID:
                filtered_org_ids = {current_org_id}
                if current_org_id == Organization.DEFAULT_ID:
                    filtered_org_ids.update(Organization.INTERNAL_IDS)
                if self.is_action_detail:
                    filtered_org_ids.add(Organization.SYSTEM_ID)
                qs = OperateLog.objects.filter(org_id__in=filtered_org_ids)

        es_config = settings.OPERATE_LOG_ELASTICSEARCH_CONFIG
        if es_config:
            engine_mod = import_module(TYPE_ENGINE_MAPPING['es'])
            store = engine_mod.OperateLogStore(es_config)
            if store.ping(timeout=2):
                qs = ESQuerySet(store)
                qs.model = OperateLog
        return qs


class PasswordChangeLogViewSet(OrgReadonlyModelViewSet):
    model = PasswordChangeLog
    serializer_class = PasswordChangeLogSerializer
    extra_filter_backends = [DatetimeRangeFilterBackend]
    date_range_filter_fields = [
        ('datetime', ('date_from', 'date_to'))
    ]
    filterset_fields = ['user', 'change_by', 'remote_addr']
    search_fields = filterset_fields
    ordering = ['-datetime']

    def get_queryset(self):
        queryset = super().get_queryset()
        return self.model.filter_queryset_by_org(queryset)


class UserSessionViewSet(CommonApiMixin, viewsets.ModelViewSet):
    http_method_names = ('get', 'post', 'head', 'options', 'trace')
    serializer_class = UserSessionSerializer
    filterset_class = UserSessionFilterSet
    search_fields = ['id', 'ip', 'city']
    rbac_perms = {
        'offline': ['audits.offline_usersession']
    }

    @property
    def org_user_ids(self):
        user_ids = current_org.get_members().values_list('id', flat=True)
        return user_ids

    def get_queryset(self):
        keys = user_session_manager.get_keys()
        queryset = UserSession.objects.filter(key__in=keys)
        if current_org.is_root():
            return queryset
        user_ids = self.org_user_ids
        queryset = queryset.filter(user_id__in=user_ids)
        return queryset

    @action(['POST'], detail=False, url_path='offline')
    def offline(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        queryset = self.get_queryset()
        session_key = request.session.session_key
        queryset = queryset.exclude(key=session_key).filter(id__in=ids)
        if not queryset.exists():
            return Response(status=status.HTTP_200_OK)

        keys = queryset.values_list('key', flat=True)
        for key in keys:
            user_session_manager.remove(key)
        queryset.delete()
        return Response(status=status.HTTP_200_OK)


class ServiceAccessLogViewSet(OrgReadonlyModelViewSet):
    model = IntegrationApplicationLog
    serializer_class = ServiceAccessLogSerializer
    extra_filter_backends = [DatetimeRangeFilterBackend]
    date_range_filter_fields = [
        ('datetime', ('date_from', 'date_to'))
    ]
    filterset_fields = ['account', 'remote_addr', 'service_id']
    search_fields = filterset_fields
    ordering = ['-datetime']
