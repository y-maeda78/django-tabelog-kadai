from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Sum, Count, Q
from django.utils import timezone
from base.models import *


# 管理者権限のアクセス処理
class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        # 管理者権限を持っているかチェック
        return self.request.user.is_admin

class SalesSummaryView(StaffRequiredMixin, TemplateView):
    template_name = 'admin/admin_summary.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        MONTHLY_FEE = 300   # サービス設定金額

        # 総売上と総会員数の集計
        total_users = User.objects.filter(is_active=True,is_admin=False).count() # 総会員数
        total_subscriptionusers = User.objects.filter(is_paymentstatus=True,is_admin=False).count() # 有料会員数
        total_revenue = Order.objects.filter(is_confirmed=True).aggregate(Sum('amount'))['amount__sum'] or 0

        context['total_users'] = total_users
        context['total_subscriptionusers'] = total_subscriptionusers
        context['total_revenue'] = total_revenue
        context['fee'] = MONTHLY_FEE
        
        return context