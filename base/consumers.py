from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
import os, requests

# env variables
def get_running_values():
    if os.getenv("ENV")== "DEV":
        bh = os.getenv("BH_DEV")
    elif os.getenv("ENV") == "PROD":
        bh = os.getenv("BH_PROD")
    values = {"bh":bh}
    return values



class CashienChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"        
        env_vars = get_running_values()
        
        try:
            cookie = self.scope["url_route"]["kwargs"]["auth_cookie"]
        except:
            cookie = ""

        trade_id = self.scope['url_route']['kwargs']['room_name']
        user = await sync_to_async(self.validate_user)(cookie, env_vars, trade_id)
        if user:
        # Join room group
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            print("connected")
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        print("disconnected")
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    def validate_user(self, token, env, trade_id):
        response = requests.get(env['bh'] + "/cashien/socket-validate-user"+trade_id, headers = {
            "Authorization":token,
            "Accept":"application/json"
            })
        
        if response.status_code == 200:
            return True
        else:
            return False