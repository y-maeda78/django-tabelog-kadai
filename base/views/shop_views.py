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


"""       
        context['prices'] = range(500, 10001, 500)

    # キーワード検索
    def get_context_data_keyword_search(self, context):  
        keyword = self.request.GET.get('keyword')
        if keyword is not None and not '':
            query = Q()
            words = keyword.replace('　', ' ').split(' ')
            for word in words:
                if word == " ":
                    continue
            
                query &= Q(category__name__contains=word) | Q(detail__contains=word) | Q(name__contains=word) | Q(address__contains=word)
            
            context['shops'] = context['shops'].filter(query)

    # カテゴリ検索
    def get_context_data_category_search(self, context):        
        context['categories'] = Category.objects.all()
        category_id = self.request.GET.get('category_id')
        if category_id is not None and not '':
            context['category_id'] = int(category_id)
            category_query = Q(category__id=category_id) | Q(category2__id=category_id) | Q(category3__id=category_id)
            context['shops'] = context['shops'].filter(category_query)

    # タグ検索
    def get_context_data_tag_search(self, context):
        context['tags'] = Tag.objects.all()
        tag_id = self.request.GET.get('tag_id')
        if tag_id is not None and not '':
            context['tag_id'] = int(tag_id)
            tag_query = Q(tag__id=tag_id) | Q(tag2__id=tag_id) | Q(tag3__id=tag_id)
            context['shops'] = context['shops'].filter(tag_query)

    # 料金検索
    def get_context_data_price_search(self, context):        
        context['prices'] = range(500, 10001, 500)
        price = self.request.GET.get('price')
        if price is not None and not '':
            context['sprice'] = price
            context['shops'] = Shop.objects.filter(budget_min__lte=context['sprice'] , budget_max__gte=context['sprice'])

    # 表示順
    def get_context_data_sort_order(self, context):
        context['sort_order'] = { 'created_at desc':'掲載日が新しい順', 'price asc':'価格が安い順', 'rating desc':'評価が高い順', 'popular desc':'予約数が多い順', }
        select_sort = self.request.GET.get('select_sort')
        if select_sort is not None and not '':
            context['selected_sort'] = select_sort

            if select_sort == 'created_at desc':
                context['shops'] = context['shops'].order_by('-created_at')
            elif select_sort == 'price asc':
                context['shops'] = context['shops'].order_by('budget_min')
            elif select_sort == 'rating desc':
                context['shops'] = context['shops'].annotate(average_stars = Avg('reviews__stars')).order_by('-average_stars')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 店舗
        context['shops'] = Shop.objects.all()

        # キーワード検索
        self.get_context_data_keyword_search(context)

        # カテゴリ検索
        self.get_context_data_category_search(context)

        # 料金検索
        self.get_context_data_price_search(context)

        # 表示順
        self.get_context_data_sort_order(context)
        
        return context

"""

