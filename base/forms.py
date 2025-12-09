from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm 
from django.contrib.auth.forms import AuthenticationForm # 追加：認証するため
# from django.contrib.auth.forms import PasswordChangeForm # パスワード変更専用
from base.models import Review, Reserve
from datetime import datetime, timedelta, time
from django.core.exceptions import ValidationError
from django.utils import timezone
 
User = get_user_model()

# class UserCreationForm(forms.ModelForm):
class CustomUserCreationForm(BaseUserCreationForm):

    class Meta:
        model = User
        fields = (
            "username",
            "email",
        )
 
# ユーザー情報更新用フォーム
class UserUpdateForm(forms.ModelForm):
    
    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "tel",
            "zipcode",
            "prefecture",
            "city",
            "address1",
            "address2",
        )
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Bootstrapのスタイルを適用
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
"""
# パスワード変更専用フォーム
class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
"""


# 追加 メールアドレス認証用フォーム
class EmailAuthenticationForm(AuthenticationForm):

    username = forms.CharField(widget=forms.HiddenInput(), required=False) # 必須ではない隠しフィールドとして再定義
    email = forms.EmailField(label='メールアドレス', max_length=254,
                                widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'メールアドレス'}))

    def clean(self):
        # この clean メソッド内で、メールアドレスをユーザー名として扱い、
        # 親クラスの AuthenticationForm が DB を検索・認証します
        email = self.cleaned_data.get('email')
        if email:
            self.cleaned_data['username'] = email
        return super().clean()
    

# レビュー用のフォーム
class ReviewForm(forms.ModelForm):
    # Reviewモデルに定義されている RATING を再利用
    # choicesとwidgetを指定することで、HTMLでラジオボタンとして表示される
    stars = forms.ChoiceField(
        choices=Review.RATING,
        widget=forms.RadioSelect,
        label='評価',
    )
    
    class Meta:
        model = Review
        # フォームとして使用するフィールドを指定
        fields = ('stars', 'comment')
        
        # フィールドごとのウィジェットや属性をカスタマイズ
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'お店の感想を具体的にご記入ください（1000文字まで）'
            }),
        }
        
        # フィールドのラベルを日本語化
        labels = {
            'stars': '評価',
            'comment': 'コメント',
        }

# 予約用のフォーム
class ReserveForm(forms.ModelForm):
    # 予約日
    reserved_date = forms.DateField(
        label='予約日',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'id': 'id_reserved_date',
            'placeholder': '選択してください。',
            'class': 'form-control',
            }),
    )

    # 時間 
    reserved_time = forms.TimeField(
        label='予約時間',
        widget=forms.Select(attrs={'class': 'form-select bg-light'}), 
    )

    # 予約人数
    number_of_people = forms.IntegerField(
        label='人数',
        widget=forms.Select(attrs={'class': 'form-select bg-light'}),
    )

    class Meta:
        model = Reserve
        fields = ('reserved_date', 'reserved_time', 'number_of_people')

    def __init__(self, *args, **kwargs):
        shop = kwargs.pop('shop', None)
        super().__init__(*args, **kwargs)

        # 人数の選択肢: 1名から10名まで
        people_choices = [(i, f'{i}名') for i in range(1, 11)]
        self.fields['number_of_people'].widget.choices = [('', '選択してください')] + people_choices

        # 予約時間の選択肢
        if shop and shop.reserve_start_time and shop.reserve_end_time:
            time_choices = [('', '選択してください')]
            start_time = datetime.combine(datetime.today().date(), shop.reserve_start_time)
            end_time = datetime.combine(datetime.today().date(), shop.reserve_end_time)
            
            current_time = start_time
            # 30分間隔で選択肢を生成
            while current_time <= end_time:
                # 'HH:MM' 形式で値と表示名を設定
                time_str = current_time.strftime('%H:%M')
                time_choices.append((time_str, time_str))
                # 30分追加
                current_time += timedelta(minutes=30) 
            
            self.fields['reserved_time'].widget.choices = time_choices

        # Bootstrapのスタイルを適用する処理
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            if field.required:
                field.widget.attrs['required'] = 'required'


    def clean(self):
        """
        予約日時が過去になっていないかチェックする。
        """
        cleaned_data = super().clean()
        
        # フォームから予約日と予約時刻を取得 (フィールド名は reserved_date, reserved_time)
        reserve_date = cleaned_data.get('reserved_date')
        reserve_time = cleaned_data.get('reserved_time')
        
        # 日付と時刻の両方が存在する場合のみチェックを実行
        if reserve_date and reserve_time:
            # 1. 日付と時刻を結合して datetime オブジェクトを作成
            # 2. timezone.make_aware() で設定済みのタイムゾーン情報 (JSTなど) を付与
            reservation_datetime = timezone.make_aware(
                datetime.combine(reserve_date, reserve_time)
            )
            
            # 現在の時刻（タイムゾーン情報付き）を取得
            now = timezone.now()
            
            # 予約日時が現在時刻以下（過去または現在）でないかチェック
            # 予約が確定した瞬間より過去の時間はすべて無効にする
            if reservation_datetime <= now:
                raise forms.ValidationError(
                    "過去の日時を選択することはできません。現在時刻よりも後の日時を選択してください。"
                )
            
        return cleaned_data