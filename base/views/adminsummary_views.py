from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
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
        
        # 月別売上集計
        sales_data_query = Order.objects.filter(
            created_at__isnull=False,
            is_confirmed=True # 決済完了しているユーザー
        ).annotate(
            month=TruncMonth('created_at') # 契約作成日から月別集計
        ).values('month').annotate(
            # 新規契約者数をカウント（その月にOrderを作成したユーザー数）
            new_subscriptions=Count('user', distinct=True),
            # 累計金額
            monthly_revenue=Sum('amount'), 
        ).order_by('-month')

        sales_data = []
        for item in sales_data_query:
            # 日付フォーマットを 'YYYY年MM月' に変換
            month_value = item['month']
            if not month_value:
                formatted_month = '不明な月'
            else:
                try:
                    formatted_month = month_value.strftime('%Y年%m月')
                except ValueError:
                    formatted_month = 'フォーマットエラー'
                    
            sales_data.append({
                'month': formatted_month,
                'monthly_revenue': item['monthly_revenue'],
                'new_subscriptions': item['new_subscriptions'],
            })

        # 総売上と総会員数の集計
        total_users = User.objects.filter(is_active=True).count() # 総会員数
        total_subscriptionusers = User.objects.filter(is_paymentstatus=True).count() # 有料会員数
        total_revenue = Order.objects.filter(is_confirmed=True).aggregate(Sum('amount'))['amount__sum'] or 0

        context['sales_data'] = sales_data
        context['total_users'] = total_users
        context['total_subscriptionusers'] = total_subscriptionusers
        context['total_revenue'] = total_revenue
        context['fee'] = MONTHLY_FEE
        
        return context