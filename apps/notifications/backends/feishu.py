from django.conf import settings

from common.sdk.im.feishu import FeiShu as Client
from .base import BackendBase


class FeiShu(BackendBase):
    account_field = 'feishu_id'
    is_enable_field_in_settings = 'AUTH_FEISHU'

    def __init__(self):
        self.client = Client(
            app_id=settings.FEISHU_APP_ID,
            app_secret=settings.FEISHU_APP_SECRET
        )

    def send_msg(self, users, message, subject=None, card=None):
        accounts, __, __ = self.get_accounts(users)
        if not accounts:
            return
        # 如果提供了卡片内容，使用卡片消息
        if card:
            return self.client.send_card(accounts, card)
        return self.client.send_text(accounts, message)


backend = FeiShu
