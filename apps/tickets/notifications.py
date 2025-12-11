import json
from urllib.parse import urljoin

from django.conf import settings
from django.core.cache import cache
from django.forms import model_to_dict
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _, gettext

from common.db.encoder import ModelJSONFieldEncoder
from common.sdk.im.wecom import wecom_tool
from common.utils import get_logger, random_string, reverse
from notifications.notifications import UserMessage
from . import const
from .models import Ticket, ApplyAssetTicket

logger = get_logger(__file__)


class BaseTicketMessage(UserMessage):
    title: ''
    ticket: Ticket
    content_title: str

    def get_ticket_detail_url(self, external=True):
        detail_url = const.TICKET_DETAIL_URL.format(
            id=str(self.ticket.id), type=self.ticket.type
        )
        if not external:
            return detail_url
        return urljoin(settings.SITE_URL, detail_url)

    @property
    def content_title(self):
        raise NotImplementedError

    @property
    def subject(self):
        raise NotImplementedError

    def get_html_context(self):
        return {'ticket_detail_url': self.get_ticket_detail_url()}

    def get_wecom_context(self):
        ticket_detail_url = wecom_tool.wrap_redirect_url(
            self.get_ticket_detail_url(external=False)
        )
        return {'ticket_detail_url': ticket_detail_url}

    def gen_html_string(self, **other_context):
        context = {
            'title': self.content_title, 'content': self.content,
        }
        context.update(other_context)
        message = render_to_string(
            'tickets/_msg_ticket.html', context
        )
        return {'subject': self.subject, 'message': message}

    def get_html_msg(self) -> dict:
        return self.gen_html_string(**self.get_html_context())

    def get_wecom_msg(self):
        message = self.gen_html_string(**self.get_wecom_context())
        return self.html_to_markdown(message)
    
    def get_feishu_msg(self) -> dict:
        """
        生成飞书卡片消息
        https://open.feishu.cn/document/common-capabilities/message-card/overview
        """
        card = self._build_feishu_card()
        return {
            'subject': str(self.subject),
            'message': '',  # 卡片消息不需要 message
            'card': card
        }
    
    def _build_feishu_card(self, approval_url=None):
        """构建飞书卡片内容"""
        # 根据工单状态选择卡片颜色
        state_colors = {
            'pending': 'orange',      # 待处理 - 橙色
            'approved': 'green',      # 已批准 - 绿色
            'rejected': 'red',        # 已拒绝 - 红色
            'closed': 'grey',         # 已关闭 - 灰色
        }
        template_color = state_colors.get(self.ticket.state, 'blue')
        
        elements = []
        
        # 添加工单基本信息部分
        basic_items = self.basic_items
        if basic_items:
            elements.append({
                'tag': 'div',
                'text': {
                    'tag': 'lark_md',
                    'content': f'📋 **{gettext("Ticket basic info")}**'
                }
            })
            elements.append({'tag': 'hr'})
            
            # 使用两列布局显示基本信息
            fields = []
            for item in basic_items:
                value = str(item['value'])[:100]  # 限制长度
                fields.append({
                    'is_short': True,
                    'text': {
                        'tag': 'lark_md',
                        'content': f"**{item['title']}**\n{value}"
                    }
                })
            
            # 飞书卡片每行最多显示2个字段，需要分组
            for i in range(0, len(fields), 2):
                chunk = fields[i:i+2]
                elements.append({
                    'tag': 'div',
                    'fields': chunk
                })
        
        # 添加工单申请信息部分
        spec_items = self.spec_items
        if spec_items:
            elements.append({
                'tag': 'div',
                'text': {
                    'tag': 'lark_md',
                    'content': f'📝 **{gettext("Ticket applied info")}**'
                }
            })
            elements.append({'tag': 'hr'})
            
            # 申请信息可能较长，使用单列显示
            for item in spec_items:
                value = str(item['value'])[:200]  # 限制长度
                elements.append({
                    'tag': 'div',
                    'text': {
                        'tag': 'lark_md',
                        'content': f"**{item['title']}：** {value}"
                    }
                })
        
        # 添加操作按钮
        actions = []
        detail_url = self.get_ticket_detail_url()
        actions.append({
            'tag': 'button',
            'text': {
                'tag': 'plain_text',
                'content': gettext('View details')
            },
            'type': 'primary',
            'url': detail_url
        })
        
        if approval_url:
            actions.append({
                'tag': 'button',
                'text': {
                    'tag': 'plain_text',
                    'content': gettext('Direct approval')
                },
                'type': 'default',
                'url': approval_url
            })
        
        elements.append({'tag': 'hr'})
        elements.append({
            'tag': 'action',
            'actions': actions
        })
        
        card = {
            'header': {
                'title': {
                    'tag': 'plain_text',
                    'content': str(self.subject)
                },
                'template': template_color
            },
            'elements': elements
        }
        
        return card

    @classmethod
    def gen_test_msg(cls):
        return None

    @property
    def content(self):
        content = [
            {'title': _('Ticket basic info'), 'content': self.basic_items},
            {'title': _('Ticket applied info'), 'content': self.spec_items},
        ]
        return content

    def _get_fields_items(self, item_names):
        fields = self.ticket._meta._forward_fields_map
        json_data = json.dumps(model_to_dict(self.ticket), cls=ModelJSONFieldEncoder)
        data = json.loads(json_data)
        items = []

        for name in item_names:
            field = fields[name]
            item = {'name': name, 'title': field.verbose_name}
            value = self.ticket.get_field_display(name, field, data)
            if not value:
                continue
            item['value'] = value
            items.append(item)
        return items

    @property
    def basic_items(self):
        item_names = ['serial_num', 'title', 'type', 'state', 'org_id', 'applicant', 'comment']
        return self._get_fields_items(item_names)

    @property
    def spec_items(self):
        fields = self.ticket._meta.local_fields + self.ticket._meta.local_many_to_many
        excludes = ['ticket_ptr', 'flow']
        item_names = [field.name for field in fields if field.name not in excludes]
        return self._get_fields_items(item_names)


class TicketAppliedToAssigneeMessage(BaseTicketMessage):
    def __init__(self, user, ticket):
        self.token = random_string(32)
        self.ticket = ticket
        super().__init__(user)

    @property
    def content_title(self):
        return _('Your has a new ticket, applicant - {}').format(self.ticket.applicant)

    @property
    def subject(self):
        title = _('{}: New Ticket - {} ({})').format(
            self.ticket.applicant,
            self.ticket.title,
            self.ticket.get_type_display()
        )
        return title

    def get_ticket_approval_url(self, external=True):
        if isinstance(self.ticket, ApplyAssetTicket):
            no_assets = not self.ticket.apply_assets.exists()
            no_nodes = not self.ticket.apply_nodes.exists()
            no_accounts = not self.ticket.apply_accounts

            if (no_assets and no_nodes) or no_accounts:
                return None

        url = reverse('tickets:direct-approve', kwargs={'token': self.token})
        if not external:
            return url
        return urljoin(settings.SITE_URL, url)

    def get_html_context(self):
        context = super().get_html_context()
        context['ticket_approval_url'] = self.get_ticket_approval_url()
        data = {
            'ticket_id': self.ticket.id,
            'approver_id': self.user.id, 'content': self.content,
        }
        cache.set(self.token, data, 3600)
        return context
    
    def get_feishu_msg(self) -> dict:
        """
        生成飞书卡片消息（包含直接批准按钮）
        """
        # 缓存批准 token
        data = {
            'ticket_id': self.ticket.id,
            'approver_id': self.user.id,
            'content': self.content,
        }
        cache.set(self.token, data, 3600)
        
        approval_url = self.get_ticket_approval_url()
        card = self._build_feishu_card(approval_url=approval_url)
        return {
            'subject': str(self.subject),
            'message': '',
            'card': card
        }

    @classmethod
    def gen_test_msg(cls):
        from .models import Ticket
        from users.models import User
        ticket = Ticket.objects.first()
        user = User.objects.first()
        return cls(user, ticket)


class TicketProcessedToApplicantMessage(BaseTicketMessage):
    def __init__(self, user, ticket, processor):
        self.ticket = ticket
        self.processor = processor
        super().__init__(user)

    @property
    def content_title(self):
        return _('Your ticket has been processed, processor - {}').format(str(self.processor))

    @property
    def subject(self):
        title = _('Ticket has processed - {} ({})').format(
            self.ticket.title, self.ticket.get_type_display()
        )
        return title

    @classmethod
    def gen_test_msg(cls):
        from .models import Ticket
        from users.models import User
        ticket = Ticket.objects.first()
        user = User.objects.first()
        processor = User.objects.last()
        return cls(user, ticket, processor)
