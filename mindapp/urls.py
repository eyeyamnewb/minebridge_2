# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage_view, name='index'),
    path('login/', views.login_view, name='login'),
    path('registration/', views.registration_view, name='registration'),
    path('details/', views.detail_fill, name='details'),
    path('logout/', views.logout_view, name='logout'),

    path('practitioner/dashboard/', views.practitioner_dashboard_view, name='practitioner_dashboard'),
    path('practitioner/patients/', views.practitioner_patients_view, name='practitioner_patients'),
    path('practitioner/analytics/', views.practitioner_analytics_view, name='practitioner_analytics'),
    path('practitioner/setting/', views.practitioner_setting_view, name='practitioner_setting'),
    path('practitioner/appointment/', views.practitioner_appointment_view, name='practitioner_appointment'),
    path('practitioner/appointment/make/', views.create_appointment, name='make_appointment'),
    path('practitioner/appointment/temp/', views.tempory_appointment,name = "tempo_appt"),  
    path('practionioner/task_assign/',views.assign_task, name="assign_task"),
    path('practionioner/update_mental/',views.update_mental, name="mental_update"),
    

    path('patient/dashboard/', views.patient_dashboard_view, name='patient_dashboard'),
    path('patient/mood/', views.mood_selection_view, name='mood_selection'),#this handle mood submussion
    path('patient/complete_task',views.task_complete_logic, name='complete_task'),
    path('patient/task/', views.patient_task_view, name='patient_task'),
    path('patient/setting/', views.patient_setting_view, name='patient_setting'),
    path('patient/appointment/', views.patient_appointment_view, name='patient_appointment'),

    path('password_change/',views.password_reset, name="change_password"),# handle possword reset

     #######################this is for the google calendar integration ####################
    path('google-calendar-auth/', views.google_calendar_auth, name='google_calendar_auth'),
    path('oauth2callback/', views.google_calendar_callback, name='google_calendar_callback'),
    path('login-with-google/', views.login_with_google, name='login_with_google'),
    
]