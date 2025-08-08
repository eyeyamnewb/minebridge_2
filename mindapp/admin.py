from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(userinfo)
admin.site.register(patientinfo)
admin.site.register(patient_task)
admin.site.register(patient_appointment)
admin.site.register(doctorinfo)
admin.site.register(mentalinfo)