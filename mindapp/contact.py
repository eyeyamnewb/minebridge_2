
from .models import UserContact, userinfo, patientinfo , doctorinfo
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.http import JsonResponse

@require_POST
def add_contact(request,user_id):
    
        
    try:
    
        request_user = userinfo.objects.get(who=request.user)
        contacted_user = userinfo.objects.get(id=user_id)

        if request.user.is_authenticated and request.user.is_staff:
            if request.method == "POST":
                UserContact.objects.get_or_create(owner=request_user, contact=contacted_user)
                UserContact.objects.get_or_create(owner=contacted_user, contact=request_user)
                messages.success(request, "Contact added successfully.")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            return JsonResponse({'status': 'success'}, status=200) 
        else:
            messages.error(request, "Sorry, you are not able to access this feature yet.")
            return HttpResponseForbidden("Not allowed.")
    
    except userinfo.DoesNotExist:
        messages.error(request, "User not found.")
        return HttpResponseForbidden("User not found.")

    

