from django.contrib import admin
from base.models import *
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from base.forms import CustomUserCreationForm
from django import forms  # 追記
import json  # 追記

 
 
class TagInline(admin.TabularInline):
    model = Shop.tags.through

class IrregularHolidayInline(admin.TabularInline):
    model = IrregularHoliday
    extra = 1   # 新規作成時や編集時に空のフォームを1つ表示
    fields = ('date',)

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    inlines = [TagInline, IrregularHolidayInline]
    exclude = ['tags']

class CustomUserAdmin(admin.ModelAdmin):
    # 管理画面のUser詳細画面で表示される項目
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password',)}),
        ('個人情報', {'fields': ('zipcode', 'prefecture', 'city', 'address1', 'address2', 'tel',)}),
        ('権限', {'fields': ('is_paymentstatus', 'is_active', 'is_admin',)}),
        ('日付', {'fields': ('created_at', 'updated_at',)}),
    )

    # 読み取り専用フィールドの設定 (created_at/updated_at は編集不可)
    readonly_fields = ('created_at', 'updated_at',)

    # 管理画面のUser一覧で表示される項目
    list_display = ('username', 'email', 'is_admin', 'is_active', 'updated_at',)
    list_filter = ('is_admin', 'is_paymentstatus', 'is_active',)
    ordering = ('-updated_at',)
    filter_horizontal = ()

    # --- adminでuser作成用に追加 ---
    add_fieldsets = (
        (None, {'fields': ('username', 'email', 'password',)}),
        ('詳細情報', {'fields': ('is_paymentstatus', 'is_admin',)}),
    )
    # --- adminでuser作成用に追加 ---

    # add_form = UserCreationForm
    add_form = CustomUserCreationForm # 修正：フォーム名変更のため

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', ) 
    prepopulated_fields = {'slug': ('name',)}

class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', ) 
    prepopulated_fields = {'slug': ('name',)}

 
admin.site.register(Category, CategoryAdmin)
admin.site.register(Tag, TagAdmin)

admin.site.register(User, CustomUserAdmin)
admin.site.unregister(Group)