from django.shortcuts import render
from django.views.generic import ListView, DetailView
from base.models import Shop, Category, Tag, Favorite
from django.db.models import Avg, Q, Count
from django.shortcuts import get_object_or_404, redirect

class IndexListView(ListView):
    model = Shop
    template_name = 'pages/index.html'

    # レビューの評価値取得のために
    # object_list の代わりに shop_list を使う
    context_object_name = 'shop_list'
    def get_queryset(self):
        queryset = super().get_queryset().annotate(
            average_rating=Avg('reviews__stars'), 
            review_count=Count('reviews') 
        ).order_by('-id') 
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # テンプレートに全てのカテゴリとタグの全リストを渡す
        context['categories'] = Category.objects.all().order_by('id')
        context['tags'] = Tag.objects.all().order_by('id')
        
        return context

# 詳細ページ
class ShopDetailView(DetailView):
    model = Shop
    template_name = 'pages/restaurants_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_obj = self.request.user
        shop = get_object_or_404(Shop, pk=self.kwargs['pk'])
        if user_obj.is_authenticated:
            context['favorites'] = Favorite.objects.filter(user=self.request.user, shop=shop).count()
        else:
            context['favorites'] = 0

        # レビュー評価の平均値をテンプレートに渡す
        review_stats = shop.reviews.all().aggregate(
            average_rating=Avg('stars'), 
            review_count=Count('id') 
        )
        context['average_rating'] = review_stats['average_rating']
        context['review_count'] = review_stats['review_count']

        return context



# 検索した際に表示する店舗一覧ページ
class ShopListView(ListView):
    model = Shop
    template_name = 'pages/restaurants_list.html'
    context_object_name = 'shops'
    ordering = 'created_at' #新規掲載順
    # paginate_by = 10   # 1ページにいくつ表示するか

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_published=True).annotate(
                    average_rating=Avg('reviews__stars'),
                    review_count=Count('reviews')
                )
        # 絞り込み処理を実行する
        queryset = self._filter_by_all_params(queryset)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['categories'] = Category.objects.all()
        context['tags'] = Tag.objects.all()

        context['selected_category_id'] = self.request.GET.get('category_id')
        context['selected_tag_id'] = self.request.GET.get('tag_id')
    
        return context
    
    # 検索ロジックを統合したプライベートメソッド
    def _filter_by_all_params(self, queryset):

        # キーワードによる絞り込み (URLパラメータ:keyword )
        keyword = self.request.GET.get('keyword')
        if keyword:
            words = keyword.replace('　', ' ').split()

            # 複数の単語による検索クエリ
            for word in words:
                if word:
                    query = (
                    Q(name__icontains=word) |
                    Q(address__icontains=word) |
                    Q(description__icontains=word) |
                    Q(tags__name__icontains=word) | 
                    Q(category__name__icontains=word) 
                )
                queryset = queryset.filter(query)


        # カテゴリーIDによる絞り込み (URLパラメータ: category_id)
        category_id = self.request.GET.get('category_id')
        if category_id and category_id.isdigit():
            queryset = queryset.filter(category__id=category_id)

        # タグIDによる絞り込み (URLパラメータ: tag_id)
        tag_id = self.request.GET.get('tag_id')
        if tag_id and tag_id.isdigit():
            # tags__id=tag_id とすることで、タグIDに一致するタグを持つ店舗を検索できる
            queryset = queryset.filter(tags__id=tag_id)

        return queryset



