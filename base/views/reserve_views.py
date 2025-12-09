from django.views.generic import ListView, DetailView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from base.models import Shop, Reserve
from base.forms import ReserveForm
from datetime import date
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Avg, Count
from django.contrib import messages
from django.views.generic import DeleteView
from base.mixins import PaymentstatusRequiredMixin
from django.utils import timezone

# 予約作成ビュー
class ReserveCreateView(LoginRequiredMixin, PaymentstatusRequiredMixin, CreateView):
    model = Reserve
    form_class = ReserveForm
    template_name = 'pages/reserve_create.html'

    # フォームに shop オブジェクトを渡す
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # URLのpkからShopオブジェクトを取得し、キーワード引数に追加
        kwargs['shop'] = get_object_or_404(Shop, pk=self.kwargs['pk'])
        return kwargs
    
    # テンプレートに shop オブジェクトを渡す
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 店舗情報、レビュー情報などをテンプレートに渡す
        shop = get_object_or_404(Shop, pk=self.kwargs['pk'])
        context['shop'] = shop
        
        # 評価情報の集計を渡す
        review_stats = shop.reviews.all().aggregate(
            average_rating=Avg('stars'), 
            review_count=Count('id')
        )
        context['average_rating'] = review_stats['average_rating']
        context['review_count'] = review_stats['review_count']

        return context
    
    """
    # 予約前に有料会員のチェックを行う
    def get(self, request, *args, **kwargs):
        if self.request.user.profile.user_type == 'free':
            messages.info(request, 'この機能を利用するには有料プランへの登録が必要です')
            return redirect('subscription')
        return super().get(request, *args, **kwargs)
    """
    
    # バリデーション成功後の保存処理
    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.shop = get_object_or_404(Shop, pk=self.kwargs['pk'])
        
        # 予約が完了したメッセージを表示
        messages.success(self.request, f'【{form.instance.shop.name}】の予約が完了しました。')
        
        # CreateView の form_valid は、設定された instance を保存し、get_success_urlへリダイレクトします
        return super().form_valid(form)
    
    # フォームにエラーがあった場合
    def form_invalid(self, form):
        # messages.error(self.request, '予約内容に誤りがあります。入力内容を確認してください。') # フォーム内でエラー表示のため
        return super().form_invalid(form)

    def get_success_url(self):
        # 予約一覧ページにリダイレクト
        return reverse_lazy('reserve_list') 


# 予約一覧のビュー
class ReserveListView(LoginRequiredMixin, PaymentstatusRequiredMixin, ListView):
    model = Reserve
    template_name = 'pages/reserve_list.html'
    context_object_name = 'reservations'
    login_url = '/login/' 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reservations'] = Reserve.objects.filter(user=self.request.user).order_by('-reserved_date') 
        context['today'] = date.today() 
        context['now'] = timezone.now()

        return context
    

# 予約キャンセルのビュー
class ReserveDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Reserve
    template_name = 'pages/reserve_delete.html'
    success_url = reverse_lazy('reserve_list')
    
    # 予約の所有者であることをテスト
    def test_func(self):
        # 削除対象の予約オブジェクトを取得
        reserve = self.get_object()
        # 予約のユーザーとリクエストユーザーが一致する場合のみTrueを返す
        return reserve.user == self.request.user
