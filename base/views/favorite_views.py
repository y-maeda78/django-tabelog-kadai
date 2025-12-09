from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, TemplateView, DetailView, RedirectView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from base.models import Shop, Favorite
from django.db.models import Avg, Count # Avg
from base.mixins import PaymentstatusRequiredMixin

class FavoritesView(LoginRequiredMixin, PaymentstatusRequiredMixin, ListView):
    model = Favorite
    template_name = "pages/favorites.html"
    context_object_name = 'favorites'
    # paginate_by = 10 # 必要に応じてページネーションを追加

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related('shop')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 該当店舗の平均評価と件数をテンプレートに渡す処理
        favorites_list = context['favorites']
        for favorite in favorites_list:
            shop = favorite.shop
            review_stats = shop.reviews.all().aggregate(
                average_rating=Avg('stars'), 
                review_count=Count('id') 
            )
            shop.average_rating = review_stats['average_rating']
            shop.review_count = review_stats['review_count']

        return context


# お気に入りの登録 or 解除を切り替える
class FavoriteToggleView(LoginRequiredMixin, PaymentstatusRequiredMixin, RedirectView):
    http_method_names = ['post']

    def get_redirect_url(self, *args, **kwargs):
        shop_pk = self.kwargs.get('pk')
        shop = get_object_or_404(Shop, pk=shop_pk)
        user = self.request.user

        # 既存のお気に入りレコードを検索
        favorite = Favorite.objects.filter(user=user, shop=shop).first()

        if favorite:
            # 存在すれば削除（解除）
            favorite.delete()
        else:
            # 存在しなければ作成（登録）
            Favorite.objects.create(user=user, shop=shop)

        # リダイレクト先の決定ロジック
        current_url_name = self.request.resolver_match.url_name
        base_redirect_url = reverse('restaurants_detail', kwargs={'pk': shop_pk})

        if current_url_name == 'favorites_delete':
            # お気に入り一覧からの削除の場合
            return reverse('favorites') 
        
        elif current_url_name == 'favorites_toggle02':
            # 店舗詳細ページ上部♡アイコンからのトグルの場合
            return f"{base_redirect_url}#favorite"
        
        else:
            # 店舗詳細ページ下部お気に入りボタンからのトグルの場合
            return base_redirect_url