from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Connection, Conversation, Experience, Message, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            'Profile',
            {
                'fields': (
                    'role',
                    'headline',
                    'bio',
                    'skills',
                    'goals',
                    'location',
                    'profile_image',
                    'membership_plan',
                    'profile_views',
                )
            },
        ),
    )
    list_display = ['username', 'email', 'role', 'membership_plan']


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'company', 'start_year', 'end_year']
    list_filter = ['company', 'start_year']


@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ['requester', 'receiver', 'created_at']
    search_fields = ['requester__username', 'receiver__username']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at']
    filter_horizontal = ['participants']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'sender', 'created_at']
    search_fields = ['sender__username', 'body']
