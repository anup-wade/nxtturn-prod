# C:\Users\Vinay\Project\Loopline\community\consumers.py
# --- FINAL FIX for Global and Private Channels ---

import json
from urllib.parse import parse_qs
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model

User = get_user_model()

def get_user_from_token(token_key):
    try:
        token = Token.objects.get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return None

class UserActivityConsumer(WebsocketConsumer):
    
    # [FIX] Define group names as class attributes for clarity and reuse
    GLOBAL_GROUP_NAME = "global_notifications"

    def connect(self):
        query_string = self.scope['query_string'].decode('utf-8')
        query_params = parse_qs(query_string)
        token_key = query_params.get('token', [None])[0]
        
        if token_key is None:
            self.close()
            return
            
        user = get_user_from_token(token_key)
        
        if user is None:
            self.close()
            return

        self.scope['user'] = user
        
        # [FIX] Keep track of the user-specific group name
        self.user_group_name = f'user_{user.id}'
        
        # [FIX] Subscribe the user to THEIR PRIVATE group
        async_to_sync(self.channel_layer.group_add)(
            self.user_group_name,
            self.channel_name
        )
        
        # [FIX] Subscribe the user to THE GLOBAL group as well
        async_to_sync(self.channel_layer.group_add)(
            self.GLOBAL_GROUP_NAME,
            self.channel_name
        )
        
        self.accept()
        print(f"CONSUMER-DEBUG: User '{user.username}' CONNECTED. Joined groups: '{self.user_group_name}' and '{self.GLOBAL_GROUP_NAME}'.\n")

    def disconnect(self, close_code):
        # [FIX] Unsubscribe from both groups on disconnect
        if hasattr(self, 'user_group_name'):
            async_to_sync(self.channel_layer.group_discard)(
                self.user_group_name,
                self.channel_name
            )
        
        # Always unsubscribe from the global group
        async_to_sync(self.channel_layer.group_discard)(
            self.GLOBAL_GROUP_NAME,
            self.channel_name
        )
        print(f"CONSUMER-DEBUG: User '{self.scope['user'].username}' DISCONNECTED.")


    # --- EXISTING METHOD: Handles receiving notification events from signals ---
    def send_notification(self, event):
        message_data = event['message']
        # The frontend now expects a flat structure, so we send the inner message directly
        self.send(text_data=json.dumps(message_data))
        print(f"!!! CONSUMER-DEBUG: Sent 'new_notification' to browser for group '{self.user_group_name}'")

    # --- EXISTING METHOD: Handles receiving new post events from signals ---
    def send_live_post(self, event):
        message_data = event['message']
        # The frontend now expects a flat structure, so we send the inner message directly
        self.send(text_data=json.dumps(message_data))
        print(f"!!! CONSUMER-DEBUG: Sent 'new_post' to browser for group '{self.user_group_name}'")

    # --- [FIX] NEW GENERIC METHOD: Handles global broadcast events ---
    def broadcast_message(self, event):
        """
        Handles any message sent to the global group.
        It forwards the 'payload' of the message directly to the client.
        This is what our post_delete signal uses.
        """
        payload = event['payload']
        self.send(text_data=json.dumps(payload))
        print(f"!!! CONSUMER-DEBUG: BROADCASTED event of type '{payload.get('type')}' to ALL connected clients.")