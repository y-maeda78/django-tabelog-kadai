"""
ユーザーが有料会員であるかどうかを確認する処理
無料会員の場合、メッセージと共に有料会員登録ページへリダイレクトする
"""

from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

class PaymentstatusRequiredMixin(AccessMixin):

    membership_url_name = 'subscription' 

    def dispatch(self, request, *args, **kwargs):
        # 1. ログインチェック (AccessMixinの機能)
        if not request.user.is_authenticated:
            # ログインしていない場合は、通常のログイン処理に任せる
            return self.handle_no_permission()
        
        # 2. 有料会員チェック
        if not request.user.is_paymentstatus:
            messages.error(request, 'この機能を利用するには有料プランへの登録が必要です。')
            return redirect(reverse(self.membership_url_name))
            
        # 有料会員であれば、本来のビュー処理へ進む
        return super().dispatch(request, *args, **kwargs)