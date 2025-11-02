
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import UserContact,message, theraphy_room,userinfo
from django.db.models import Count,Q
from django.contrib.auth.models import User
import uuid


def fetch_messages(request,room_id):
    if not request.user.is_authenticated :
        return{}
    
    try:
    
        room = theraphy_room.objects.get(room_id = room_id)
        print(room.room_id)
        print(room_id)
    except theraphy_room.DoesNotExist:
        return JsonResponse({'error':'the room have demanifest itself'}, status= 404 )
    
    if request.user.userinfo != room.participant_1 and request.user.userinfo != room.participant_2:
        return JsonResponse({"error": "Forbidden"}, status=403)

    messages = message.objects.filter(room=room_id).order_by('timestamp').values(
        'sender__who__id',
        'sender__full_name',
        'content',
        'timestamp') 

    message_list = list(messages)

    return JsonResponse(message_list,safe=False)  
    
    



