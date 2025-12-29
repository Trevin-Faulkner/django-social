import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Conversation, Message

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        self.presence_group = 'presence_global'

        if not self.scope['user'].is_authenticated:
            await self.close()
            return

        is_participant = await self._is_participant(self.scope['user'].id, self.conversation_id)
        if not is_participant:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.channel_layer.group_add(self.presence_group, self.channel_name)
        await self.accept()
        await self.channel_layer.group_send(
            self.presence_group,
            {
                'type': 'presence.update',
                'user_id': self.scope['user'].id,
                'online': True,
            },
        )
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'presence.request',
                'requester': self.channel_name,
            },
        )
        await self.channel_layer.group_send(
            self.presence_group,
            {
                'type': 'presence.request',
                'requester': self.channel_name,
            },
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_send(
            self.presence_group,
            {
                'type': 'presence.update',
                'user_id': self.scope['user'].id,
                'online': False,
            },
        )
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'presence.update',
                'user_id': self.scope['user'].id,
                'online': False,
            },
        )
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.channel_layer.group_discard(self.presence_group, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        data = json.loads(text_data)
        body = data.get('body', '').strip()
        if not body:
            return

        message = await self._create_message(self.scope['user'].id, self.conversation_id, body)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'message': {
                    'message_type': 'chat',
                    'id': message['id'],
                    'body': message['body'],
                    'sender': message['sender'],
                    'sender_id': message['sender_id'],
                    'timestamp': message['timestamp'],
                },
            },
        )

    async def chat_message(self, event):
        msg = event['message']
        msg['sent_by_me'] = msg.get('sender_id') == self.scope['user'].id
        await self.send(text_data=json.dumps(msg))

    async def presence_update(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    'message_type': 'presence',
                    'user_id': event['user_id'],
                    'online': event['online'],
                }
            )
        )

    async def presence_request(self, event):
        requester = event.get('requester')
        if requester and requester != self.channel_name:
            await self.channel_layer.send(
                requester,
                {
                    'type': 'presence.response',
                    'user_id': self.scope['user'].id,
                },
            )

    async def presence_response(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    'message_type': 'presence',
                    'user_id': event['user_id'],
                    'online': True,
                }
            )
        )

    @database_sync_to_async
    def _is_participant(self, user_id, conversation_id):
        return Conversation.objects.filter(id=conversation_id, participants__id=user_id).exists()

    @database_sync_to_async
    def _create_message(self, user_id, conversation_id, body):
        conversation = Conversation.objects.get(id=conversation_id)
        sender = User.objects.get(id=user_id)
        msg = Message.objects.create(conversation=conversation, sender=sender, body=body, created_at=timezone.now())
        return {
            'id': msg.id,
            'body': msg.body,
            'sender': sender.get_full_name() or sender.username,
            'sender_id': sender.id,
            'timestamp': msg.created_at.strftime('%I:%M %p'),
        }
