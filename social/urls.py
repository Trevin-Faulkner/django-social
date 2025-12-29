from django.urls import path

from . import views

urlpatterns = [
    path('', views.LandingView.as_view(), name='landing'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('login/', views.BrandedLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('discover/', views.discover, name='discover'),
    path('connect/<int:user_id>/', views.connect_user, name='connect_user'),
    path('profile/', views.profile, name='profile'),
    path('profile/<str:username>/', views.profile, name='profile_detail'),
    path('messages/', views.messages_view, name='messages'),
    path('messages/<int:conversation_id>/', views.messages_view, name='messages'),
    path('start-chat/<int:user_id>/', views.start_chat, name='start_chat'),
    path('api/messages/<int:conversation_id>/', views.messages_api, name='messages_api'),
    path('api/messages/<int:conversation_id>/send/', views.send_message_api, name='send_message_api'),
    path('google-login/', views.google_login_placeholder, name='google_login'),
    path('upgrade/<str:plan>/', views.upgrade_plan, name='upgrade_plan'),
    path('connections/<int:connection_id>/accept/', views.accept_connection, name='accept_connection'),
    path('billing/paypal/create-order/', views.create_paypal_order, name='create_paypal_order'),
    path('billing/paypal/capture-order/', views.capture_paypal_order, name='capture_paypal_order'),
    path('billing/paypal/cancel/', views.paypal_cancel, name='paypal_cancel'),
]
