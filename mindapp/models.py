from django.db import models
from datetime import datetime
from django.contrib.auth.models import User
from .choices import *

class userinfo(models.Model):
    who = models.OneToOneField(User, on_delete=models.CASCADE,default=None)
    is_verified = models.BooleanField(default=False)
    full_name = models.CharField(max_length=100, default='jonathan joestar')
    phone = models.CharField(max_length=70, default='backend say this person is shy to give their number UwU')
    country = models.CharField(max_length=100, choices=country_choices,default='atlantis')
    dob = models.DateField(default=datetime.now)
    age = models.IntegerField(default=0)
    gender = models.CharField(max_length=100, choices=gender_choices,default='oyster like my idol samsmith' )
    relationship = models.CharField(max_length=100, choices=relationship_choices,default='single and ready to mingle')
    google_auth = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.who.username

class doctorinfo(models.Model):
    who = models.OneToOneField(userinfo, on_delete=models.CASCADE,default=None)
    speciality = models.CharField(max_length=100, choices=speciality_choices,default='psychiatrist')
    medicalfirm = models.CharField(max_length=100)
    availability = models.CharField(max_length=100, choices=availability_choices,default='closed')
    doctor_google_auth = models.JSONField(null=True, blank=True)

class patientinfo(models.Model):
    who = models.ForeignKey(userinfo, on_delete=models.CASCADE)
    doctor = models.ForeignKey(doctorinfo, on_delete=models.SET_NULL, null=True, blank=True)
    latest_mood = models.CharField(max_length=100, choices=feeling_choices, default='dying inside')
    previous_mood = models.CharField(max_length=100, choices=feeling_choices, default='dying inside')
    medication = models.CharField(max_length=100,blank=True)
    allergies = models.CharField(max_length=100,blank=True)

    def __str__(self):
        return f"{self.who}"

class pastient_note(models.Model):
    who = models.ForeignKey(patientinfo, on_delete=models.CASCADE)
    notes = models.CharField(max_length=3000, blank = True)
    
    def __Str__(self): #ill add some more extra here beofre this 
        return f"{self.who}"

class mentalinfo(models.Model):
    who = models.ForeignKey(patientinfo, on_delete=models.CASCADE)  
    mental_health_priority = models.CharField(max_length=100, choices=mental_priority_choices,default='low')
    mental_health_category = models.CharField(max_length=100, choices=mental_category_choices,default='depressed')
    mental_health_status = models.CharField(max_length=100, choices=mental_status_choices,default='stable')
     
    def __Str__(self):
        return f"{self.who}"

class patient_task(models.Model):
    who = models.ForeignKey(patientinfo, on_delete=models.CASCADE)
    task_title = models.CharField(max_length=100, choices=task_choices,default='exercise')
    task_description = models.TextField()
    task_status = models.CharField(max_length=100, choices=task_status_choices,default='he skipping')
    task_due = models.DateField(default=datetime.now)
    task_created = models.DateField(default=datetime.now)

    def __str__(self):
        return f"{self.who} - {self.task_title}"  
    
class patient_appointment(models.Model):
    who = models.OneToOneField(patientinfo, on_delete=models.CASCADE)
    doctor = models.ForeignKey(doctorinfo, on_delete=models.CASCADE)
    appointment_date = models.DateField(default=datetime.now)
    appointment_time = models.TimeField(default=datetime.now)
    appointment_meeting_type = models.CharField(max_length=100, choices=appointment_meeting_type_choices,default='online')
    appointment_status = models.CharField(max_length=100, choices=appointment_choices,default='pending')
    appointment_type = models.CharField(max_length=100, choices=appointment_type_choices,default='follow up')
    appointment_reminder = models.CharField(max_length=100, choices=appointment_reminder_choices,default='1 hour')
    google_event_id = models.CharField(max_length=255, null=True, blank=True)

class patient_daily_login(models.Model):
    who = models.ForeignKey(patientinfo, on_delete=models.CASCADE)
    login_count_per_week = models.IntegerField(default=0)
    login_count_per_month = models.IntegerField(default=0)
    login_date = models.DateField(default=datetime.now)
    session_duration = models.IntegerField(default=0)
    successful_login = models.BooleanField(default=False)

class messaging_model(models.Model):
    sender = models.ForeignKey(User, related_name='sent_message', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_message', on_delete=models.CASCADE)
    textcontent = models.TextField(blank=True)
    timestamp = models.DateField(default=datetime.now)
    is_read = models.BooleanField(default=False)

