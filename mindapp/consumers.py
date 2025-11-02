# ...existing code...
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import Q 
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import message, UserContact, userinfo, theraphy_room
from asgiref.sync import sync_to_async


class notificationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        if  not self.scope['user'].is_authenticated:
            await self.close()

        self.user_id = self.scope['user'].id
        self.group_name = f"notification_for_user{self.user_id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        print('nitifcation connect')

        await self.accept()


    async def disconnect(self, code):
        
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def new_message_noti(self,event):
        
        ('is notified')
        await self.send(text_data=json.dumps({
            'type':'new_message',
            'from_user_id':event['from_user_id'],
            'from_user_name': event['from_user_name']
        }))

##########################################################################

class Chatconsumer(AsyncWebsocketConsumer):

    async def connect(self):
        if not self.scope['user'].is_authenticated:
            print('debugging')
            await self.close()

        print('chat is connecting')

        self.room_id = self.scope['url_route']['kwargs']['room_id'] 
        self.sender = self.scope['url_route']['kwargs']['sender_id']
        self.receiver = self.scope['url_route']['kwargs']['receiver_id']
        
        self.room_group_name = f"{self.room_id}"
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        print(f'connected, pass 1 :{self.channel_name}')
    
    
    
    async def disconnect(self, close_code):
        
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        print(f'disconnected , pass end: {self.channel_name}')
    

    
    async def receive(self, text_data):

        text_data_json = json.loads(text_data) 
        message_content = text_data_json['message']

        sender = await sync_to_async(User.objects.get)(id=self.sender)
        receiver = await sync_to_async(User.objects.get)(id=self.receiver) 
        sender_info = await sync_to_async(userinfo.objects.get)(who=sender) 
        receiver_info = await sync_to_async(userinfo.objects.get)(who=receiver)

        room = await sync_to_async(theraphy_room.objects.get)(room_id = self.room_id)
        
        #save to database
        saved_message = await sync_to_async(message.objects.create)(
            sender = sender_info,
            receiver = receiver_info,
            content = message_content,
            room = room
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': saved_message.content,
                'sender_id': sender.id,
                'sender_username': sender.username,
                'reciever_id': receiver.id,
                'receiver_username':receiver.username,
                'room_id': self.room_id,
                'timestamp': saved_message.timestamp.isoformat()

            }
        )

        await self.channel_layer.group_send(
            f'notification_for_user{receiver.id}',
            {
                'type': 'new_message_noti',
                'from_user_id':sender.id,
                'from_user_name':sender_info.full_name
            }
        )


    async def chat_message(self,event):

        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'reciever_id': event['reciever_id'],
            'receiver_username':event['receiver_username'],
            'room_id': event['room_id'],
            'timestamp': event['timestamp']

        }))



        

        #await sync_to_async(message.objects.create)()

    
    


#room check class t ocheck and create room if not exists
class room_checker_maker(AsyncWebsocketConsumer):

    async def connect(self):
        #await self.check_room()
        
        room = await self.check_room()
        
        await sync_to_async(print)('bob',room.room_id)
        await self.accept()
        
        
        await self.send(text_data=json.dumps({
            'type': 'room_id_init',
            'room_id': str(room.room_id)
        }))

    async def disconnect(self, code):
        await self.close()

    async def check_room(self): #scoping for url

        request_user_id = self.scope['url_route']['kwargs']['requesting_user']
        contact_user = self.scope['url_route']['kwargs']['contact_user']

        self.requesting_user = await sync_to_async(User.objects.get)(id=request_user_id)
        self.contact_user = await sync_to_async(User.objects.get)(id=contact_user)

        self.request_user_info = await sync_to_async(userinfo.objects.get)(who=self.requesting_user)
        self.contact_user_info = await sync_to_async(userinfo.objects.get)(who=self.contact_user)
        


        await sync_to_async(print)(f"test pass returning requestee contact: {self.contact_user_info.full_name}") 
        try:
            in_contact = await sync_to_async(UserContact.objects.filter)(
                Q( owner = self.request_user_info,
                    contact= self.contact_user_info)|
                Q(owner = self.contact_user_info,
                    contact= self.request_user_info)
                )
            
            if await sync_to_async(in_contact.count)() == 2:
                await sync_to_async(print)("test pass in try",in_contact)

                room_query = Q(
                    Q(participant_1=self.request_user_info, participant_2=self.contact_user_info) |
                    Q(participant_1=self.contact_user_info, participant_2=self.request_user_info)
               )

                room_check = await sync_to_async(theraphy_room.objects.filter)(room_query)
                await sync_to_async(print)('passing queary check',self.request_user_info.id)

                if not await sync_to_async(room_check.exists)():
                    print("no room yet, creating one")

                    participant_1 = self.request_user_info
                    participant_2 = self.contact_user_info

                    self.room = await sync_to_async(theraphy_room.objects.create)(
                        participant_1=participant_1,
                        participant_2=participant_2
                    )
                    await sync_to_async(print)(f"New room created: {self.room.room_id}")

                
                get_room = await sync_to_async(room_check.first)()
                await sync_to_async(print)(get_room.room_id)
                return get_room
        except Exception as e:
            print(e)

###############################################################

        

        