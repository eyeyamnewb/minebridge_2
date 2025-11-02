

# forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import *  # Import your models from models.py
from .choices import *  # Import your choices from choices.py
from datetime import datetime
from django.contrib.auth.hashers import check_password
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate, get_user_model, password_validation
# Define your forms here


#######################   login form  ##############################################
####################################################################################
class loginform(forms.Form):
    email = forms.CharField(
        max_length=150,
        required=True
    )
    password = forms.CharField(
        widget=forms.PasswordInput, 
        required=True
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if not email:
            raise ValidationError("Email is required.")
        else:
            username = email.split('@')[0].lower()  # Assuming the username is the part before '@'

        if not User.objects.filter(username=username).exists():
            raise ValidationError("User does not exist.")
        
        user = authenticate(username=username, password=password)
        if user is None:
            raise ValidationError("Invalid password.")
        
        return cleaned_data

#######################   Registration form  #######################################
####################################################################################    
class RegistrationForm(forms.Form):

    email = forms.EmailField(
        max_length=150,
        required=True,
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput, required=True
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput, required=True
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        username = email.split('@')[0].lower()  # Assuming the username is the part before '@'
        
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already exists.")
        
        if password != confirm_password:
            raise ValidationError("Passwords do not match.")
        
        return cleaned_data

########################   mood selection form  #######################################
#####################################################################################    

class moodselectionform(forms.Form):
    mood = forms.ChoiceField(
        choices=feeling_choices, 
        required=True,
         widget=forms.Select(attrs={'class': 'mod-frm'})
        )
    
########## DDJANGO FORM FUCNTION DISSECTED ###################
##############################################################

class password_change_form(forms.Form):
    old_password = forms.CharField(
        widget=forms.PasswordInput,  #---->comented for jic
        required=True
        
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class':'_box'
                                          }), 
        required=True
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        required=True
    )
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args,**kwargs)
        self.user = user

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not check_password(old_password, self.user.password):
            raise ValidationError("The old password is incorrect.")
        return old_password
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password != confirm_password:
            raise ValidationError("New passwords do not match.")
        return cleaned_data
    
       

 ##########################   task creation form  #######################################
#####################################################################################   
class task_form(forms.Form):
        

    patient_name = forms.ChoiceField(required=True,widget=forms.Select())
    task_name = forms.ChoiceField(choices=task_choices
                                      )
    task_description = forms.CharField(max_length=10000,required=False, 
                                           widget=forms.Textarea())
    task_due_date = forms.DateField(
            widget=forms.DateInput(attrs={'type': 'date'}),
            required=True
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['patient_name'].choices = [
            (patient.who.who.id, patient.who.full_name)
            for patient in patientinfo.objects.all()
        ]

class details_form(forms.Form):
    
    first_name = forms.CharField(max_length=900, required=True)
    last_name = forms.CharField(max_length=900, required=True)
    gender = forms.ChoiceField(choices=gender_choices)
    contact = forms.IntegerField()
    dob = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    relationship = forms.ChoiceField(choices=relationship_choices)
    country = forms.ChoiceField(choices=country_choices)

########################## appoint fomr #############################################
####################################################################################

class appointment_form(forms.Form):
    patient = forms.ChoiceField(required=True,widget=forms.Select())
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    meeting = forms.ChoiceField(choices=appointment_meeting_type_choices)
    appt_type = forms.ChoiceField(choices=appointment_type_choices) 
    reminder = forms.ChoiceField(choices=appointment_reminder_choices)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['patient'].choices = [
            (patient.who.who.id, patient.who.full_name)
            for patient in patientinfo.objects.all()
        ] 

class reschedule_appointment_form(forms.Form):
    appointment_id = forms.ChoiceField(
        label="appointment to rechedule",
        required=True)
    
    new_date = forms.DateField(
        widget=forms.DateInput(
            attrs={'type': 'date'}))
    
    new_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}))
    
    meeting = forms.ChoiceField(
        choices=appointment_meeting_type_choices)
    
    appt_type = forms.ChoiceField(
        choices=appointment_type_choices)
    

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user is not None:
            appointments = patient_appointment.objects.filter(
                doctor=user,
                appointment_status='pending'  # Make sure your model has a 'status' field!
            )
        else:
            appointments = patient_appointment.objects.none()
        self.fields['appointment_id'].choices = [
            (
                appointment.id,
                f"{appointment.who.who.full_name} - {appointment.appointment_date} {appointment.appointment_time}"
            )
            for appointment in appointments
        ]

######################### mental update form ###########################################
#######################################################################################

class mentalinfo_updating(forms.Form):
    patient =patient = forms.ChoiceField( choices=[(
                    patient.who.who.id, 
                    patient.who.full_name
                ) for patient in patientinfo.objects.all()
                ],
            required=True,)
    category = forms.ChoiceField(choices=mental_category_choices)
    status = forms.ChoiceField(choices=mental_status_choices)
    priority = forms.ChoiceField(choices=mental_priority_choices)

    ################# messaging form ############################################
    ###########################################################################3

    #class messaging(forms.Form):

