

from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from asgiref.sync import sync_to_async
from tortoise import Tortoise
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.urls import reverse

#from .models import ChatGroup
#   from .tortoise_models import ChatMessage
#from .models import ChatGroup

def test_1(request):
    if request.user.is_staff:
        context = {
            'hello' : 'hello doctor'
        }
        return render(request, 'test_2.html', context)
    else:
        context = {
            'hello' : 'hello sicko'
        }
        return render(request, 'test_2.html', context)
    
