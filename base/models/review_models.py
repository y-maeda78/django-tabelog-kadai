"""
レビューモデルを定義
"""
from django.db import models
from django.contrib.auth import get_user_model

class Review(models.Model):
    RATING = (
        (1, '★'),
        (2, '★'),
        (3, '★'),
        (4, '★'),
        (5, '★'),
    )
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, verbose_name='レビューユーザー')
    shop = models.ForeignKey('Shop', on_delete=models.CASCADE, related_name='reviews', verbose_name='レビュー店舗')

    # 評価
    stars = models.PositiveIntegerField(choices=RATING, null=True, blank=True, verbose_name='評価')
    
    # 内容
    comment = models.TextField(default='', blank=True, verbose_name='コメント')

    # 作成日
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日')

    def __str__(self):
        return f"{self.user.name} (店舗名：{self.shop.name} / {self.score}点)"