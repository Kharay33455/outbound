from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
import os, requests, json

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
        self.env = get_running_values()
        self.auth_cookie = self.scope["url_route"]["kwargs"]["auth_cookie"]
        
        trade_id = self.scope['url_route']['kwargs']['room_name']
        user = await sync_to_async(self.validate_user)(self.auth_cookie,trade_id)
        if user:
        # Join room group
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)


    # Receive message from WebSocket
    async def receive(self, text_data):
        import time
        
        text_data_json = json.loads(text_data)
        if text_data_json['type'] == "new_text":
            message = text_data_json["text"]
            message_created = await sync_to_async(self.create_new_message)(message)
            if message_created:
                # Send message to room group
                await self.channel_layer.group_send(
                    self.room_group_name, {"type": "chat.message", "message": message_created}
                )
        
        if text_data_json['type'] == 'receipt':
            image_as_b64 = text_data_json['image']
            receipt = await sync_to_async(self.append_receipt)(image_as_b64)
            if receipt:
                await self.channel_layer.group_send(
                    self.room_group_name, {"type" : "receipt.message", "image_url": receipt}
                )
            
        if text_data_json['type'] == 'release':
            release_context = await sync_to_async(self.release_usdt)()
            if release_context:
                await self.channel_layer.group_send(
                    self.room_group_name, {"type":"release.message", "context":release_context}
                )


    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]
        # Send message to WebSocket
        await self.send(text_data=json.dumps({"type" : "new_text","message": message}))

    async def receipt_message(self, event):
        image_url = event['image_url']
        await self.send(text_data = json.dumps({"type":"receipt", "image_url":image_url}))


    async def release_message(self, event):
        context = event['context']
        await self.send(text_data = json.dumps({"type":"release", "context":context}))


    def create_new_message(self, message_text):
        response = requests.post(self.env['bh'] +"/cashien/socket-create-new-message/", headers={
            "Authorization": self.auth_cookie,
            "Content-Type":"application/json"
        }, json={
            "trade_id":self.room_name,
            "text":message_text
        })
        if response.status_code == 200:
            return response.json()['msg']
        else:
            return False

    def append_receipt(self, b64img):
        if b64img.startswith("data:image"):
            b64img = b64img.split(",")[1]
        response = requests.post(self.env['bh'] +"/cashien/socket-append-receipt/", headers={
            "Authorization": self.auth_cookie,
            "Content-Type":"application/json"
        }, json={
            "trade_id":self.room_name,
            "image": b64img
        })
        if response.status_code == 200:
            return response.json()['msg']
        else:
            return False
    
    def release_usdt(self):
        response = requests.post(self.env['bh'] +"/cashien/socket-release-usdt/", headers={
            "Authorization": self.auth_cookie,
            "Content-Type":"application/json"
        }, json={
            "trade_id":self.room_name,
        })
        if response.status_code == 200:
            return response.json()['msg']
        else:
            return False
    


    def validate_user(self, token, trade_id):
        response = requests.get(self.env['bh'] + "/cashien/socket-validate-user"+trade_id, headers = {
            "Authorization":token,
            "Accept":"application/json"
            })
        
        if response.status_code == 200:
            return True
        else:
            return False


class CashienDisputeConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_name = f"dispute_{self.scope['url_route']['kwargs']['room_name']}"
        self.room_group_name = f"grou_{self.room_name}"        
        self.env = get_running_values()
        self.auth_cookie = self.scope['url_route']['kwargs']['auth_cookie']
        dispute_data = await sync_to_async(self.get_dispute_data)()
        if dispute_data:
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
            await self.send(text_data = json.dumps({'type':"dispute_data","data" : dispute_data}))


    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)



    
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        if(text_data_json['type'] == "newMessage"):
            message = await sync_to_async(self.create_new_message)(text_data_json)
            if message:
                await self.channel_layer.group_send(
                    self.room_group_name,{"type":"new.message", "message" : message}
                )

    async def new_message(self, event):
        await self.send(text_data = json.dumps({"type":"new_message","data":event['message']}))

    def create_new_message(self, event):
        response = requests.post(self.env['bh'] +"/cashien/socket-create-new-dispute-message/", headers={
            "Authorization":self.auth_cookie,
            "Content-Type":"application/json"
        }, json={
            "trade_id": self.scope['url_route']['kwargs']['room_name'],
            "data" : event
        })
        if response.status_code == 200:
            return response.json()['msg']


    def get_dispute_data(self):
        response = requests.get(self.env['bh']+'/cashien/socket-get-dispute-data'+self.scope['url_route']['kwargs']['room_name'], headers={
            "Authorization": self.auth_cookie,
            "Accept" : "application/json"
        })
        if response.status_code == 200:
            return response.json()['msg']
        else:
            return False
