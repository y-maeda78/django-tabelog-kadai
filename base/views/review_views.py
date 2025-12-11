from django.views.generic import DetailView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from base.models import Shop, Review
from base.forms import ReviewForm # 追加：作成したフォームをインポート
from django.db.models import Avg, Count
from base.mixins import PaymentstatusRequiredMixin

# レビュー一覧
class ShopReviewView(LoginRequiredMixin, DetailView):
    model = Shop
    template_name = "pages/reviews_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 平均値計算ロジック
        review_stats = self.object.reviews.all().aggregate(
            average_rating=Avg('stars'), 
            review_count=Count('id') 
        )
        context['average_rating'] = review_stats['average_rating']
        context['review_count'] = review_stats['review_count']

        # 対象店舗の全レビューを作成日の新しい順に取得
        all_reviews = self.object.reviews.all().order_by('-created_at')

        my_review = None
        other_reviews = []
        is_reviewed = False

        try:
            my_review = all_reviews.get(user=self.request.user)
            is_reviewed = True
            
            # 自分のレビューを除いた他のレビューを取得 (all_reviewsから除外)
            other_reviews = all_reviews.exclude(user=self.request.user)

        except Review.DoesNotExist:
            # 自分のレビューがなければ、他のレビューを含む全てのレビューが other_reviews になる
            # is_reviewed は False のまま
            other_reviews = all_reviews

        # テンプレートの処理
        context['my_review'] = my_review    # 自分のレビュー
        context['other_reviews'] = other_reviews    # 他のユーザーのレビュー
        context['is_reviewed'] = is_reviewed # レビュー投稿ボタンの表示制御に使用

        return context
            

# レビューの作成
class ShopReviewCreateView(LoginRequiredMixin, PaymentstatusRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = "pages/reviews_create.html"

    # URLから店舗情報を受け取るための準備
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shop_pk = self.kwargs.get('pk') 
        shop = get_object_or_404(Shop, pk=shop_pk)
        context['shop'] = shop

        # 平均値計算ロジック
        review_stats = shop.reviews.all().aggregate(
            average_rating=Avg('stars'), 
            review_count=Count('id') 
        )
        context['average_rating'] = review_stats['average_rating']
        context['review_count'] = review_stats['review_count']
        
        return context    

    def form_valid(self, form):
        review = form.save(commit=False)
        
        shop = get_object_or_404(Shop, pk=self.kwargs.get('pk'))
        review.shop = shop    
    
        review.user = self.request.user
        
        # レビューを保存
        review.save()       
        return super().form_valid(form)
    
    # 投稿成功時のリダイレクト先
    def get_success_url(self):
        return reverse_lazy('reviews', kwargs={'pk': self.kwargs.get('pk')})


# レビューの削除
class ShopReviewDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Review
    pk_url_kwarg = 'review_pk'
    
    # 削除後のリダイレクト先を設定
    def get_success_url(self):
        shop_pk = self.kwargs['shop_pk']
        return reverse_lazy('reviews', kwargs={'pk': shop_pk})
    
    # 削除できるのは自分のレビューのみ
    def test_func(self):
        # URLから削除対象のレビューを取得
        review = self.get_object()
        # ログインユーザーがそのレビューの投稿者であれば True を返す
        return review.user == self.request.user