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


# マイページビュー
class MyPageView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/account_mypage.html'


# 会員情報確認ビュー (UserUpdateViewを読み取り専用として再利用)
class AccountDetailView(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = UserUpdateForm
    template_name = 'pages/account_detail.html'
    
    # フォームを読み取り専用にする
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs['readonly'] = 'readonly'
        return form

    def get_object(self):
        return self.request.user