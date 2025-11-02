# mindapp/context_processors.py
from django.contrib.auth import get_user_model
from .models import userinfo, UserContact, message

user = get_user_model()
staff = user.objects.filter(is_staff=True)
non_staff = user.objects.filter(is_staff=False)

def staff_contacts(request):
    if request.user.is_authenticated:
        
        user_info = userinfo.objects.all().exclude(who=request.user.pk)
        doctor = user_info.filter(who__is_staff=True)

        patient = user_info.filter(who__is_staff=False)
        
        
        return {'doctor_contact': doctor,
                'patient_contact':patient,
                'registered_user':user_info}
    return {}


def fetch_current_contact(request):
    if request.user.is_authenticated:
        
        if userinfo.objects.filter(who=request.user).exists():
            
            requesting_user = userinfo.objects.get(who = request.user.pk )
            contact_list = UserContact.objects.all().filter(owner=requesting_user)
    
            return {'exist_contact_list': contact_list}
    return {}

def fetch_message(request):
    if request.user.is_authenticated:

        messages = message.objects.all()


        return{'message_pile': message,}
    return {}