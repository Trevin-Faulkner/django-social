import json
import requests
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import FormView, TemplateView
from django.views.decorators.csrf import csrf_exempt

from .forms import (
    BrandedAuthenticationForm,
    MessageForm,
    ProfileForm,
    SignupForm,
)
from .models import Connection, Conversation, Message, User


class LandingView(TemplateView):
    template_name = 'landing.html'


class SignupView(FormView):
    template_name = 'auth/signup.html'
    form_class = SignupForm
    success_url = reverse_lazy('discover')

    def form_valid(self, form):
        user = form.save()
        # New users are not authenticated via backend yet; explicitly set default backend.
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(self.request, 'Welcome to ConnectPro!')
        return super().form_valid(form)


class BrandedLoginView(LoginView):
    authentication_form = BrandedAuthenticationForm
    template_name = 'auth/login.html'
    redirect_authenticated_user = True


def logout_view(request):
    """Allow logout over GET to avoid 405s from the default LogoutView."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('landing')


def _conversation_between(user, partner):
    existing = Conversation.objects.filter(participants=user).filter(participants=partner).first()
    if existing:
        return existing
    convo = Conversation.objects.create()
    convo.participants.add(user, partner)
    return convo


@login_required
def discover(request):
    q = request.GET.get('q', '')
    target_role = User.ROLE_CLIENT if request.user.role == User.ROLE_DEVELOPER else User.ROLE_DEVELOPER
    users = (
        User.objects.filter(role=target_role)
        .exclude(id=request.user.id)
        .order_by('first_name', 'last_name')
    )
    if q:
        users = users.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(headline__icontains=q)
            | Q(skills__icontains=q)
            | Q(location__icontains=q)
        )

    connections_qs = Connection.objects.filter(
        Q(requester=request.user) | Q(receiver=request.user)
    ).select_related('requester', 'receiver')
    status_map = {}
    for c in connections_qs:
        other = c.receiver if c.requester_id == request.user.id else c.requester
        status_map[other.id] = {
            'status': c.status,
            'is_requester': c.requester_id == request.user.id,
            'connection_id': c.id,
        }
    my_connections = connections_qs.filter(status=Connection.STATUS_ACCEPTED)[:5]

    context = {
        'users': users,
        # 'connection_ids': connection_ids,
        'connection_ids': {},  # retained for template safety; all logic uses status_map now
        'remaining': request.user.remaining_connections_today,
        'limit': request.user.connection_limit,
        'my_connections': my_connections,
        'q': q,
        'target_label': 'Clients' if target_role == User.ROLE_CLIENT else 'Developers',
        'popular_skills': ['React', 'Node.js', 'Python', 'AWS', 'TypeScript', 'Docker', 'Design', 'Product'],
        'status_map': status_map,
    }
    return render(request, 'discover.html', context)


@login_required
def connect_user(request, user_id):
    target = get_object_or_404(User, id=user_id)
    if target.role == request.user.role:
        messages.error(request, 'You can only connect with the opposite role.')
        return redirect('discover')

    existing = Connection.objects.filter(
        Q(requester=request.user, receiver=target) | Q(requester=target, receiver=request.user)
    ).exists()
    if existing:
        messages.info(request, 'You already connected with this user.')
        return redirect('discover')

    limit = request.user.connection_limit
    if limit is not None:
        today_count = Connection.objects.filter(
            requester=request.user, created_at__date=timezone.now().date()
        ).count()
        if today_count >= limit:
            messages.error(request, 'You have reached your daily connection limit.')
            return redirect('discover')

    Connection.objects.create(requester=request.user, receiver=target, status=Connection.STATUS_PENDING)
    messages.success(request, f"Connection request sent to {target.get_full_name() or target.username}.")
    return redirect('discover')


@login_required
def profile(request, username=None):
    profile_user = request.user
    if username and username != request.user.username:
        profile_user = get_object_or_404(User, username=username)

    can_edit = profile_user == request.user
    form = ProfileForm(instance=profile_user)
    if request.method == 'POST' and can_edit:
        form = ProfileForm(request.POST, request.FILES, instance=profile_user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('profile')

    context = {
        'profile_user': profile_user,
        'form': form,
        'active_connections': profile_user.active_connections_count(),
        'remaining': profile_user.remaining_connections_today,
        'experiences': profile_user.experiences.all(),
    }
    return render(request, 'profile.html', context)


@login_required
def start_chat(request, user_id):
    partner = get_object_or_404(User, id=user_id)
    convo = _conversation_between(request.user, partner)
    return redirect('messages', conversation_id=convo.id)


@login_required
def messages_view(request, conversation_id=None):
    conversations = (
        request.user.conversations.all()
        .prefetch_related('participants', 'messages__sender')
        .order_by('-created_at')
    )
    convos_with_partner = [
        {'conversation': convo, 'partner': convo.other_participant(request.user)}
        for convo in conversations
    ]
    active_conversation = None
    if conversation_id:
        active_conversation = get_object_or_404(conversations, id=conversation_id)
    elif conversations.exists():
        active_conversation = conversations.first()

    partner = active_conversation.other_participant(request.user) if active_conversation else None
    form = MessageForm()
    if request.method == 'POST' and active_conversation:
        form = MessageForm(request.POST)
        if form.is_valid():
            Message.objects.create(
                conversation=active_conversation,
                sender=request.user,
                body=form.cleaned_data['body'],
            )
            return redirect('messages', conversation_id=active_conversation.id)

    context = {
        'conversations': conversations,
        'convos_with_partner': convos_with_partner,
        'active_conversation': active_conversation,
        'partner': partner,
        'form': form,
    }
    return render(request, 'messages.html', context)


@login_required
def messages_api(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    data = [
        {
            'id': m.id,
            'body': m.body,
            'sender': m.sender.get_full_name() or m.sender.username,
            'sent_by_me': m.sender_id == request.user.id,
            'timestamp': m.created_at.strftime('%I:%M %p'),
        }
        for m in conversation.messages.all()
    ]
    return JsonResponse({'messages': data})


@login_required
def send_message_api(request, conversation_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    body = request.POST.get('body', '').strip()
    if not body:
        return JsonResponse({'error': 'Message cannot be empty'}, status=400)
    message = Message.objects.create(conversation=conversation, sender=request.user, body=body)
    return JsonResponse(
        {
            'id': message.id,
            'body': message.body,
            'sender': message.sender.get_full_name() or message.sender.username,
            'timestamp': message.created_at.strftime('%I:%M %p'),
        }
    )


def google_login_placeholder(request):
    return redirect('/accounts/google/login/')


@login_required
def upgrade_plan(request, plan):
    if plan not in dict(User.PLAN_CHOICES):
        messages.error(request, 'Unknown plan selected.')
        return redirect('discover')
    if not settings.PAYPAL_CLIENT_ID or not settings.PAYPAL_CLIENT_SECRET:
        messages.error(request, 'PayPal is not configured. Please set PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET.')
        return redirect('discover')
    amount = '1.00' if plan == User.PLAN_PLUS else '2.00'

    return render(
        request,
        'billing/paypal_checkout.html',
        {
            'paypal_client_id': settings.PAYPAL_CLIENT_ID,
            'plan': plan,
            'amount': amount,
        },
    )


@login_required
def paypal_confirm(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)
    plan = request.POST.get('plan')
    if plan not in dict(User.PLAN_CHOICES):
        return JsonResponse({'ok': False, 'error': 'Invalid plan'}, status=400)
    request.user.membership_plan = plan
    request.user.save(update_fields=['membership_plan'])
    return JsonResponse({'ok': True})


@login_required
def paypal_execute(request, plan):
    messages.info(request, 'Legacy PayPal execute endpoint not used.')
    return redirect('discover')


@login_required
def paypal_cancel(request):
    messages.info(request, 'PayPal payment was cancelled.')
    return redirect('discover')


@csrf_exempt
@login_required
def create_paypal_order(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    body = json.loads(request.body or '{}')
    plan = body.get('plan')
    amount = body.get('amount')
    if plan not in dict(User.PLAN_CHOICES):
        return JsonResponse({'error': 'Invalid plan'}, status=400)
    if not amount:
        amount = '1.00' if plan == User.PLAN_PLUS else '2.00'
    try:
        token = _paypal_access_token()
        order_id = _paypal_create_order(token, amount, 'USD')
        return JsonResponse({'orderID': order_id})
    except Exception as exc:  # pylint: disable=broad-except
        return JsonResponse({'error': str(exc)}, status=400)


@csrf_exempt
@login_required
def capture_paypal_order(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    body = json.loads(request.body or '{}')
    order_id = body.get('orderID')
    plan = body.get('plan')
    if not order_id or plan not in dict(User.PLAN_CHOICES):
        return JsonResponse({'error': 'Missing order or plan'}, status=400)
    try:
        token = _paypal_access_token()
        result = _paypal_capture_order(token, order_id)
        status = result.get('status')
        if status == 'COMPLETED':
            request.user.membership_plan = plan
            request.user.save(update_fields=['membership_plan'])
        return JsonResponse(result)
    except Exception as exc:  # pylint: disable=broad-except
        return JsonResponse({'error': str(exc)}, status=400)


def _paypal_access_token():
    url = f"{_paypal_base_url()}/v1/oauth2/token"
    resp = requests.post(
        url,
        auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
        data={'grant_type': 'client_credentials'},
        timeout=10,
    )
    if resp.status_code != 200:
        raise Exception(f'Could not get token ({resp.status_code})')
    return resp.json().get('access_token')


def _paypal_base_url():
    return 'https://api-m.sandbox.paypal.com' if settings.PAYPAL_ENV == 'sandbox' else 'https://api-m.paypal.com'


def _paypal_create_order(token, amount, currency):
    url = f"{_paypal_base_url()}/v2/checkout/orders"
    payload = {
        'intent': 'CAPTURE',
        'purchase_units': [{'amount': {'currency_code': currency, 'value': amount}}],
    }
    resp = requests.post(url, headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}, json=payload, timeout=10)
    if resp.status_code not in (201, 200):
        raise Exception(f'Order create failed ({resp.status_code})')
    return resp.json().get('id')


def _paypal_capture_order(token, order_id):
    url = f"{_paypal_base_url()}/v2/checkout/orders/{order_id}/capture"
    resp = requests.post(url, headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}, timeout=10)
    if resp.status_code not in (201, 200):
        raise Exception(f'Capture failed ({resp.status_code})')
    return resp.json()


@login_required
def accept_connection(request, connection_id):
    conn = get_object_or_404(
        Connection, id=connection_id, receiver=request.user, status=Connection.STATUS_PENDING
    )
    conn.status = Connection.STATUS_ACCEPTED
    conn.accepted_at = timezone.now()
    conn.save(update_fields=['status', 'accepted_at'])
    _conversation_between(conn.requester, conn.receiver)
    messages.success(request, f'You are now connected with {conn.requester.get_full_name() or conn.requester.username}.')
    return redirect('discover')

# Create your views here.
from django.conf import settings
