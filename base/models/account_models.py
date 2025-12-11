"""
カスタマイズユーザーモデルを定義
"""

from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from base.models.shop_models import create_id

# ユーザーモデル
class UserManager(BaseUserManager):

    def create_user(self, email, username, password=None,                
                    **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(
            username=username,
            email=self.normalize_email(email),
            zipcode=extra_fields.get('zipcode'), 
            prefecture=extra_fields.get('prefecture'),
            city=extra_fields.get('city'),
            address1=extra_fields.get('address1'),
            address2=extra_fields.get('address2'),
            tel=extra_fields.get('tel'),
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None):
        user = self.create_user(
            email,
            username,            
            password=password,
        )
        user.is_admin = True
        user.is_superuser = True
        user.save(using=self._db)
        return user




# ユーザーのプロフィール情報
class User(AbstractBaseUser, PermissionsMixin):
    id = models.CharField(default=create_id, primary_key=True, max_length=50)
    username = models.CharField(max_length=50, unique=True, verbose_name='ユーザー名')
    email = models.EmailField(max_length=255, unique=True, verbose_name='メールアドレス')
    zipcode = models.CharField(default='', blank=True, max_length=8, verbose_name='郵便番号')
    prefecture = models.CharField(default='', blank=True, max_length=50, verbose_name='都道府県')
    city = models.CharField(default='', blank=True, max_length=50, verbose_name='市町村')
    address1 = models.CharField(default='', blank=True, max_length=50, verbose_name='住所1 丁目・番地・号')
    address2 = models.CharField(default='', blank=True, max_length=50, verbose_name='住所2 マンション・アパート名')
    # birthday = models.DateField(null=True, blank=True, verbose_name='誕生日')
    tel = models.CharField(default='', blank=True, max_length=15, verbose_name='電話番号')
    is_paymentstatus = models.BooleanField(default=False, verbose_name='有料会員')
    is_active = models.BooleanField(default=True, verbose_name='アクティブ状態')
    is_admin = models.BooleanField(default=False, verbose_name='管理者権限')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    stripe_customer_id = models.CharField(default='',max_length=255, blank=True)
    stripe_subscription_id = models.CharField(default='',max_length=255, blank=True)
    stripe_card_name = models.CharField(default='',max_length=255, blank=True)
    stripe_setup_intent = models.CharField(default='',max_length=255, blank=True)
    stripe_card_no = models.CharField(default='',max_length=20, blank=True)
    stripe_card_brand = models.CharField(default='',max_length=20, blank=True)

    objects = UserManager()
    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username
    
    @property
    def is_staff(self):
        # 管理画面へのアクセス権 (Djangoが要求する属性)
        # is_admin が True なら、is_staff も True とる
        return self.is_admin
    
    def has_perm(self, perm, obj=None):
        return self.is_admin 

    def has_module_perms(self, app_label):
        return self.is_admin

