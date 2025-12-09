from django.contrib import admin
from django.urls import path
from base import views
from django.contrib.auth.views import LogoutView
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('summary/', views.SalesSummaryView.as_view(), name='admin_summary'),

    # トップページ
    path('', views.IndexListView.as_view(), name='index'),

    # 店舗一覧
    path('restaurants/', views.ShopListView.as_view(), name="restaurants_list"),

    # 店舗詳細
    path('restaurants/<int:pk>/', views.ShopDetailView.as_view(), name="restaurants_detail"),

    # Account
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),          # ただログアウトさせるだけなのでDjangoの標準機能を実装し、viewsの指定はなし
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('mypage/', views.MyPageView.as_view(), name='mypage'),
    path('mypage/account/', views.AccountDetailView.as_view(), name='account_detail'),
    path('mypage/account/edit/', views.AccountUpdateView.as_view(), name='account_edit'),

    # favorite
    path('mypage/favorites/', views.FavoritesView.as_view(), name='favorites'),
    path('mypage/favorites/<int:pk>/', views.FavoriteToggleView.as_view(), name='favorites_toggle01'),
    path('mypage/favorites/<int:pk>#favarite', views.FavoriteToggleView.as_view(), name='favorites_toggle02'),
    path('mypage/favorites/<int:pk>/delete/', views.FavoriteToggleView.as_view(), name='favorites_delete'),

    # review
    path('restaurants/<int:pk>/reviews/', views.ShopReviewView.as_view(), name='reviews'),
    path('restaurants/<int:pk>/reviews/create/', views.ShopReviewCreateView.as_view(), name='review_create'),
    path('restaurants/<int:shop_pk>/reviews/<int:review_pk>/delete/', views.ShopReviewDeleteView.as_view(), name='review_delete'),

    # reserve
    path('restaurants/<int:pk>/reserve/', views.ReserveCreateView.as_view(), name='reserve'),
    path('mypage/reservations/', views.ReserveListView.as_view(), name='reserve_list'),
    path('reserve/<str:pk>/delete/', views.ReserveDeleteView.as_view(), name='reserve_delete'),

    # pay
    # 有料会員の登録
    path('subscription/', views.SubscriptionView.as_view(), name="subscription"),

    # カード情報の登録成功
    path('subscription/success/', views.SubscriptionSuccess, name='subscription_success'),

    # カード情報の失敗
    path('subscription/cancel/', views.SubscriptionCancel, name='subscription_cancel'),

    path('subscription/config/', views.stripe_config, name='stripe_config'),
    path('subscription/create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),

    # カード情報の変更
    path('subscription/update/', views.SubscriptionUpdateView.as_view(), name="subscription_update"),
    path('subscription/update_save/', views.subscription_update_save, name="subscription_update_save"),

    # 有料会員の退会
    path('subscription/cancellation/', views.CancellationView.as_view(), name="subscription_cancellation"),
    path('subscription_cancellation_save/', views.subscription_cancellation_save, name="subscription_cancellation_save"),

]

# 画像の設定
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)