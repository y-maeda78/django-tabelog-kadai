from django.views.generic import CreateView, UpdateView
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.contrib.messages.views import SuccessMessageMixin # 追加
from base.forms import CustomUserCreationForm, UserUpdateForm
from django.contrib import messages
from django.urls import reverse_lazy # 追加
from base.forms import EmailAuthenticationForm,CustomUserCreationForm, UserUpdateForm
from django.views.generic import TemplateView # 追加

User = get_user_model()

# 新規登録のビュー
# 変更：SuccessMessageMixinで form_valid のメッセージ処理を不要にする
class SignUpView(SuccessMessageMixin, CreateView):
    model = User
    form_class = CustomUserCreationForm # 修正：フォーム名変更のため
    success_url = reverse_lazy('login')
    template_name = 'pages/signup.html'
    success_message = '新規登録が完了しました。続けてログインしてください。'

# フォームの処理を削除
"""
    # 追加：フォームの処理
    def post(self, request, *args, **kwargs):
        user_form = CustomUserCreationForm(request.POST)
        profile_form = ProfileForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            return self.forms_valid(user_form, profile_form)
        else:
            print("User Form Errors:", user_form.errors)
            print("Profile Form Errors:", profile_form.errors)
            return self.forms_invalid(user_form, profile_form)
    
    # 追加
    @transaction.atomic
    # 新規登録が有効だった場合
    def forms_valid(self, user_form, profile_form):
        # Userモデルを保存
        self.object = user_form.save()
        
        # Profileモデルを保存
        profile = profile_form.save(commit=False)
        profile.user = self.object # ユーザーとProfileを紐づけ
        profile.save()

        messages.success(self.request, '新規登録が完了しました。続けてログインしてください。')
        return super().form_valid(user_form, profile_form)

    # # 新規登録が有効だった場合
    # def form_valid(self, form):
    #     messages.success(self.request, '新規登録が完了しました。続けてログインしてください。')
    #     return super().form_valid(form)
    
    # 追加：エラーの場合（両方のフォームをコンテキストに戻す）
    def forms_invalid(self, user_form, profile_form):  
        messages.error(self.request, user_form.errors)
        messages.error(self.request, profile_form.errors)
        return self.render_to_response(self.get_context_data(user_form=user_form, profile_form=profile_form))
"""

# ログイン
class Login(LoginView):
    template_name = 'pages/login.html'

    # indexに戻す
    success_url = reverse_lazy('index')
    # 認証する処理
    form_class = EmailAuthenticationForm

    def form_valid(self, form):
        messages.success(self.request, 'ログインしました。')
        return super().form_valid(form)
 
    def form_invalid(self, form):
        messages.error(self.request, 'ログインエラー：入力内容に誤りがあります。')
        return super().form_invalid(form)


# アカウントの編集
# LoginRequiredMixin:ログインしていなければ見えない 
class AccountUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'pages/account_edit.html'
    success_url = reverse_lazy('account_detail')
    success_message = 'アカウント情報を更新しました。'
 
    def get_object(self):
        # ログイン中のユーザーオブジェクトを返す
        return self.request.user
"""
    def get_object(self):
        # URL変数ではなく、現在のユーザーから直接pkを取得
        self.kwargs['pk'] = self.request.user.pk
        return super().get_object()
"""


# マイページビュー
class MyPageView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/account_mypage.html'


# 会員情報確認ビュー (UserUpdateViewを読み取り専用として再利用)
class AccountDetailView(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = UserUpdateForm
    template_name = 'pages/account_detail.html' # 修正後の会員情報確認テンプレート名
    
    # フォームを読み取り専用にする
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs['readonly'] = 'readonly'
        return form

    def get_object(self):
        return self.request.user