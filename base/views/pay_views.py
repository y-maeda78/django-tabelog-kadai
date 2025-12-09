from django.views.generic import TemplateView
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from base.models import User, Order
from base.mixins import PaymentstatusRequiredMixin
import stripe


# 有料会員の登録ビュー
class SubscriptionView(LoginRequiredMixin, TemplateView):
    template_name = "pages/payment_subscription.html"


# Stripeの公開鍵をJSONで返すビュー
@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_PUBLIC_KEY}
        return JsonResponse(stripe_config, safe=False)
    


# 支払い画面に遷移させるための処理
@csrf_exempt
def create_checkout_session(request):
    if request.method == 'GET':
        domain_url = request._current_scheme_host + '/subscription/'
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            checkout_session = stripe.checkout.Session.create(
                client_reference_id=request.user.id if request.user.is_authenticated else None,
                success_url=domain_url + 'success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=domain_url + 'cancel/',
                payment_method_types=['card'],
                mode='subscription',
                line_items=[
                    {
                        'price': settings.STRIPE_PRICE_ID,
                        'quantity': 1,
                    }
                ]
            )
            return JsonResponse({'sessionId': checkout_session['id']})
        except Exception as e:
            return JsonResponse({'error': str(e)})

# 支払いに成功した後の画面
def SubscriptionSuccess(request):
    
    stripe.api_key = settings.STRIPE_SECRET_KEY
    session_id = request.GET.get('session_id')

    if not request.user.is_authenticated:
            messages.error(request, "セッションがタイムアウトしました。再度ログインしてください。")
            return redirect('login') # ログインページへリダイレクト
        
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        user = get_object_or_404(User, id=request.user.id)

        user.is_paymentstatus = True
        user.stripe_customer_id = session['customer']
        user.stripe_subscription_id = session['subscription']

        setup_intent = stripe.SetupIntent.create(
            customer=user.stripe_customer_id,
            payment_method_types=["card"],
        )
        user.stripe_setup_intent = setup_intent.client_secret

        stripe_customer = stripe.Customer.retrieve(user.stripe_customer_id)
        user.stripe_card_name =  stripe_customer.name

        stripe_PaymentMethod = stripe.PaymentMethod.list(
            customer=user.stripe_customer_id,
            type="card",
        )

        user.stripe_card_brand = stripe_PaymentMethod.data[0].card.brand
        user.stripe_card_no = stripe_PaymentMethod.data[0].card.last4

        user.save()

        # Stripeのオブジェクトを取得
        subscription = stripe.Subscription.retrieve(session['subscription'])
        price_id = subscription['items']['data'][0]['price']['id']
        price = stripe.Price.retrieve(price_id)
        MONTHLY_FEE = price['unit_amount']

        TAX_RATE = 10   # 消費税率10%
        price_without_tax = int(MONTHLY_FEE / (1 + (TAX_RATE / 100)))

        # (消費税額) = (税込み価格) - (税抜価格)
        tax_amount = MONTHLY_FEE - price_without_tax

        # Orderモデルに情報を保存
        Order.objects.create(
            user=user,
            is_confirmed=True,  # 決済成功済み
            amount=MONTHLY_FEE, # 支払額
            tax_included=tax_amount, # 消費税額
        )

        messages.info(request, '有料プランに登録しました')
        return redirect('index')

    except Exception as e:
        messages.error(request, f"決済処理中にエラーが発生しました: {e}")
        return redirect('subscription')
    

def SubscriptionCancel(request):
    messages.info(request, '有料プランの登録がキャンセルされました。')
    return redirect('subscription')



# 有料会員の退会ビュー
class CancellationView(LoginRequiredMixin, TemplateView):
    template_name = "pages/payment_cancellation.html"

# 退会処理
@require_POST
@login_required
def subscription_cancellation_save(request):
    user = get_object_or_404(User, id=request.user.id)

    # ユーザーが有料会員であること、StripeのサブスクリプションIDを持っていることを確認
    if not user.stripe_subscription_id:
        messages.error(request, "サブスクリプション情報が見つかりません。")
        return redirect('mypage')
    
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY        
        stripe.Subscription.delete(user.stripe_subscription_id)

        user.is_paymentstatus = False
        user.stripe_customer_id = ''
        user.stripe_subscription_id = ''
        user.stripe_setup_intent = ''
        user.stripe_card_brand= ''
        user.stripe_card_name = ''
        user.stripe_card_no = ''
        user.save()

        messages.info(request, '有料プランを解約しました')

        return redirect('mypage') 
    
    # その他の予期せぬエラー
    except Exception as e:
        messages.error(request, f"解約処理中にエラーが発生しました: {e}")
        return redirect('mypage')


# 支払方法変更ビュー
class SubscriptionUpdateView(LoginRequiredMixin, PaymentstatusRequiredMixin, TemplateView):
    template_name = "pages/payment_edit.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@require_POST
@login_required
def subscription_update_save(request):
    user = get_object_or_404(get_user_model(), id=request.user.id)
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    # 1. POSTデータから Payment Method ID を取得
    payment_method_id = request.POST.get('payment_method_id')
    card_name = request.POST.get('card_name')

    if not user.stripe_customer_id:
        messages.error(request, "お客様のStripe顧客情報が見つかりません。")
        return redirect('subscription_update')

    if not payment_method_id:
        messages.error(request, "支払い情報の送信に失敗しました。再度お試しください。")
        return redirect('subscription_update')

    try:
        # 2. Stripe処理：新しい支払い方法を顧客に関連付ける
        stripe.PaymentMethod.attach(
            payment_method_id,
            customer=user.stripe_customer_id,
        )

        # 3. Stripe処理：支払い方法を新しいものに更新する
        stripe.Subscription.modify(
            user.stripe_subscription_id,
            default_payment_method=payment_method_id,
        )

        # 4. Stripe処理：新しい支払い方法の詳細情報を取得
        pm = stripe.PaymentMethod.retrieve(payment_method_id)

        # 5. DB更新：ユーザーモデルに最新のカード情報を保存
        user.stripe_card_name = card_name # ユーザーが入力した名義人
        user.stripe_card_brand = pm.card.brand
        user.stripe_card_no = pm.card.last4
        user.save()

        messages.success(request, 'お支払方法を更新しました。')
        return redirect('subscription_update')
        
    except stripe.error.CardError as e:
        # カード情報に問題がある場合
        messages.error(request, f"カード情報に誤りがあります: {e.user_message}")
        return redirect('subscription_update')
    
    except Exception as e:
        # その他のエラー
        messages.error(request, f"更新処理中に予期せぬエラーが発生しました: {e}")
        return redirect('subscription_update')