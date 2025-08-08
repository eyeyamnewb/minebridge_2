import json
import os
import calendar
from collections import OrderedDict
from calendar import HTMLCalendar
from collections import defaultdict
from datetime import datetime, date, timedelta
from django.db.models import Count
from django.shortcuts import render,redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages
from datetime import date
from .sample_task import tasks
from .models import*
from .choices import *

from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

from .forms import (loginform, RegistrationForm,
                     moodselectionform, #PasswordChangeForm,
                     password_change_form, task_form,
                     mentalinfo_updating,details_form,
                     appointment_form)
from django.contrib.auth import (authenticate, hashers, 
                                 login, logout, update_session_auth_hash)


from mindbridge_2 import settings
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
#--------object variable general


############################## special script ##############################################
############################################################################################


#-----------modified htmlcalendar
class HighlightTodayCalendar(HTMLCalendar):
    def __init__(self, today=None, appointments=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.today = today or date.today()
        self._year = None
        self._month = None
        self.appointments = appointments or {}

    def formatday(self, day, weekday):
        if day == 0:
            return '<td class="noday">&nbsp;</td>'  # day outside month
        cssclass = self.cssclasses[weekday]
        cell_date = date(self._year, self._month, day)
        extra_class = ""
        if cell_date == self.today:
            extra_class += " dsh-today crb-F"
        if cell_date in self.appointments:
            extra_class += " dsh-appt crb-F"
        # Add id attribute for JS targeting
        cell_id = f"caldate-{cell_date.isoformat()}"
        return f'<td id="{cell_id}" class="{cssclass}{extra_class}" data-date="{cell_date}">{day}</td>'

    def formatmonth(self, year, month, withyear=True):
        self._year = year
        self._month = month
        return super().formatmonth(year, month, withyear)

#---------------age calcualtor---------------------    
def calculate_age(born):
    today = datetime.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


# Function to render the homepage
def homepage_view(request):
    return render(request, 'homepage.html')

############## Function to render the login page #################################
##################################################################################
def login_view(request):
    if request.method == 'POST':
        form = loginform(request.POST)
        if form.is_valid():
            # get data from cleanted data dictionary made in forms.py
            email = form.cleaned_data['email']
            username = email.split('@')[0].lower()  # Assuming the username is the part before '@'
            password = form.cleaned_data['password']
            # user authentication
            user = authenticate(username=username, password=password)
            if user.check_password(password):
            
                if user is not None:
                    login(request, user)

                    if user.is_staff:
                        return redirect('practitioner_dashboard')  # Redirect to the practitioner dashboard
                    else:
                        return redirect('patient_dashboard')  # Redirect to the patient dashboard
                        
    else:
        form = loginform()
    context = {'form': form}
    return render(request, 'login.html', context)

############### Function to render the registration page ###############################
#####################################################################################

def registration_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Process the registration
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split('@')[0].lower()  # Assuming the username is the part before '@'
       
            # Create a new user
            user = User.objects.create_user(username=username, email=email, password=password)
            user.set_password(password)  # Hash the password
            user.save()
            


            login(request, user)  # Log the user in after registration
            # Redirect to the appropriate dashboard
            return redirect('details') 
    else:
        form = RegistrationForm()
        context = {'form': form}
    # Render the registration form
    return render(request, 'registration.html', context)

"#################### this is the details completion page view ####################"
def detail_fill(request):
    if not request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = details_form(request.POST)
        if form.is_valid():
            try:
                # Set user type based on form selection
                request.user.first_name = form.cleaned_data['first_name']
                request.user.last_name = form.cleaned_data['last_name']
                request.user.save()

                # Create or update userinfo
                user_info, created = userinfo.objects.get_or_create(
                    who=request.user,
                    defaults={
                        'country': form.cleaned_data['country'],
                        'phone': form.cleaned_data['contact'],
                        'dob': form.cleaned_data['dob'],
                        'gender': form.cleaned_data['gender'],
                        'relationship': form.cleaned_data['relationship'],
                        'age': calculate_age(form.cleaned_data['dob']),
                        'full_name': f"{form.cleaned_data['first_name']} {form.cleaned_data['last_name']}",
                    }
                )

                if not created:
                    # Update existing userinfo
                    user_info.phone = form.cleaned_data['contact']
                    user_info.gender = form.cleaned_data['gender']
                    user_info.country = form.cleaned_data['country']
                    user_info.dob = form.cleaned_data['dob']
                    user_info.age = calculate_age(form.cleaned_data['dob'])
                    user_info.relationship = form.cleaned_data['relationship']
                    user_info.full_name = f"{form.cleaned_data['first_name']} {form.cleaned_data['last_name']}"
                    user_info.save()

                    # Create patient info and initial mental info
                patient, created = patientinfo.objects.get_or_create(
                    who=user_info,
                    defaults={
                        'latest_mood': 'neutral',
                        'previous_mood': 'neutral',
                        'medication': '',
                        'allergies': ''
                        }
                )
                    
                    # Apply Google credentials if available from session
                if 'google_credentials' in request.session:
                    user_info.google_auth = request.session['google_credentials']
                    user_info.save()
                    # Clear credentials from session
                    del request.session['google_credentials']
                    
                    # Create initial mental info record
                mentalinfo.objects.get_or_create(
                    who=patient,
                    defaults={
                        'mental_health_priority': 'low',
                        'mental_health_category': "stress"
                    }
                )
                    
                    # Check if Gmail user without auth - redirect to auth
                email = request.user.email
                is_gmail_user = email and (email.endswith('@gmail.com') or email.endswith('@googlemail.com'))
                if is_gmail_user and not patient.who.google_auth:
                    request.session['next_url'] = 'patient_dashboard'
                    return redirect('google_calendar_auth')
                        
                return redirect('patient_dashboard')

            except Exception as e:
                print("DETAIL_FILL ERROR:", e)
                messages.error(request, f"Error completing profile: {str(e)}")
            return redirect('login')
    else:
        form = details_form()
    
    return render(request, 'detail_form.html', {'form': form})


############################# Function to render the logout page ########################
#####################################################################################

def logout_view(request):
    if User.is_authenticated:
        logout(request)
        return redirect('index')

######################## Practitioner views ##############################################
##########################################################################################

def practitioner_dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    elif not request.user.is_staff:
        return redirect('patient_dashboard')
    
         #turn normal user to doctor and delete user patient info if exist
    user_info = userinfo.objects.get(who=request.user)
    try:
        patient = patientinfo.objects.get(who=user_info)
        patient.delete()
    except patientinfo.DoesNotExist:
        pass
   
    try: #fill newly appointed doctor user with doctor info
        doctor = doctorinfo.objects.get(who=user_info)
    except doctorinfo.DoesNotExist:
        doctor = doctorinfo.objects.create(
            who=user_info,
            speciality='General',
            medicalfirm='Not specified',
            availability='closed'
        )
   
    #get all patients models
    patient = patientinfo.objects.all()

    #get all patient appointments
    appointment = patient_appointment.objects.all()

    today_appointments = appointment.filter(
        appointment_date=date.today(),
        appointment_status__in=['pending']                                    
                                            ).order_by('appointment_date', 'appointment_time')
    
    upcoming_appointments = appointment.filter(
        appointment_date__gt=date.today(),
        appointment_status__in=['pending','Pending']
    ).order_by('appointment_date', 'appointment_time')

    task = task_form()

    cont = {
        'patient': patient,
        'today_appointments': today_appointments,
        'upcoming_appointments': upcoming_appointments,
        'form': task,

    }
    
    return render(request, 'practitioner/dashboard.html', cont)
#
#
#
def practitioner_patients_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if not request.user.is_staff:
        return redirect('patient_dashboard')
    
    patients = patientinfo.objects.all()
    patient_mentals= mentalinfo.objects.all()

    taskform = task_form()
    men_info = mentalinfo_updating()

    cont = {   
     "patients": patients,
     "patient_mentals": patient_mentals,
     "task_form":task_form,
     "mental_info_form": men_info,
    }
    
    return render(request, 'practitioner/patients.html',cont)
#
#
#
def practitioner_analytics_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if not request.user.is_staff:
        return redirect('patient_dashboard')
    
    #get patient gender for analytics
    gender_data = (
        patientinfo.objects.values('who__gender')
        .annotate(count=Count('who__gender'))
    )

     # Age data for pie chart
    age_data = (
        patientinfo.objects.values_list('who__age',flat=True)
        )
    
    age_groups = OrderedDict({
        '0-18': 0,
        '18-25': 0,
        '25-40': 0,
        '40-60': 0,
        '60+': 0,
    })

     # Count patients in each group
    for age in age_data:
        if age is None:
            continue
        if age <= 18:
            age_groups['0-18'] += 1
        elif age <= 25:
            age_groups['18-25'] += 1
        elif age <= 40:
            age_groups['25-40'] += 1
        elif age <= 60:
            age_groups['40-60'] += 1
        else:
            age_groups['60+'] += 1


    #query mental and gender for object counting 
    
    gender_category_data = (
    mentalinfo.objects.values('mental_health_category', 'who__who__gender')
    .annotate(count=Count('id'))
)   
    #varables
    age_labels = list(age_groups.keys()) 
    age_counts = list(age_groups.values())
    gender_labels = [g['who__gender'] for g in gender_data]
    gender_counts = [g['count'] for g in gender_data]
    #bar variables

    categories = [c[0] for c in mental_category_choices]
    genders = [g[0] for g in gender_choices]

# Build a matrix: rows = categories, columns = genders
    data_matrix = []
    for gender in genders:
        row = []
        for category in categories:
            found = next(
            (
            item for item in gender_category_data
            if item['mental_health_category'] == category and item['who__who__gender'] == gender),
            None
            )
            row.append(found['count'] if found else 0)
        print(row)
        data_matrix.append(row)

    patient_mental_States = mentalinfo.objects.all()

    cont = {'gender_labels': json.dumps(gender_labels),
        'gender_counts': json.dumps(gender_counts),
        'age_labels': json.dumps(age_labels),
        'age_counts': json.dumps(age_counts),
        
        'bar_genders': json.dumps(genders),
        'bar_categories': json.dumps(categories),
        'bar_data_matrix': json.dumps(data_matrix),

        'patient_mental_States': patient_mental_States,
        }
    
    return render(request, 'practitioner/analytics.html',cont)
#
#
#
def practitioner_setting_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if not request.user.is_staff:
        return redirect('patient_dashboard')
    
    pass_change = password_change_form(request.user)
    
    cont = {
        "pass_change": pass_change,
    }
    return render(request, 'practitioner/setting.html', cont)
#
#
#
def practitioner_appointment_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if not request.user.is_staff:
        return redirect('patient_dashboard')
    
    # get pending appointments for the practitioner
    # and sort by appointment date and time

    user_info = userinfo.objects.get(who=request.user)
    doctor_info = doctorinfo.objects.get(who=user_info)

    pending = patient_appointment.objects.filter(
        doctor = doctor_info,
        appointment_status='pending'
    ).order_by('appointment_date', 'appointment_time')

# get complete/ cancelled appointments for the practitioner
    # and sort by appointment date and time

    complete = patient_appointment.objects.filter(
        doctor=doctor_info,
        appointment_status__in=["complete","cancelled"]
    ).order_by('appointment_date', 'appointment_time')

    form = appointment_form()
    cont = {
        "pending_appointment": pending,
        "complete_appointment": complete,
        'appointment' : form,

    }
    
    return render(request, 'practitioner/appointment.html', cont)

############################# Patient views ##############################################
##########################################################################################

#
#vvvvvvvvvv calendar logic function 
#

def get_date(req_day):
    if req_day:
        year, month = (int(x) for x in req_day.split("-"))
        return date(year, month, day=1)
    return datetime.today()

#
#
#
def prev_month(d):
    first = d.replace(day=1)
    prev_month = first - timedelta(days=1)
    return f"month={prev_month.year}-{prev_month.month}"
#
#
#
def next_month(d):
    days_in_month = calendar.monthrange(d.year, d.month)[1]
    last = d.replace(day=days_in_month)
    next_month = last + timedelta(days=1)
    return f"month={next_month.year}-{next_month.month}"

#
#^^^^^^^^^^^^^ calendar logic function
#
def patient_dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    elif request.user.is_staff:
        return redirect('practitioner_dashboard')
    else:
        user_info = userinfo.objects.get(who=request.user)
        name = user_info.full_name 
        mood_form = moodselectionform()
        reg_user = userinfo.objects.get(who = request.user)
        patientinfo.objects.get_or_create(who=reg_user)
        patient = patientinfo.objects.get(who=reg_user)
        
        new_tasks = patient_task.objects.filter(
            who=patient,
            task_status__in=['pending', 'delayed', 'in progress'],
            task_created=date.today()   # Filter for non-completed statuses
        ).order_by('task_created')

        pending_tasks = patient_task.objects.filter(
            who=patient,
            task_status__in=['pending', 'delayed', 'in progress'],  # Filter for non-completed statuses
            task_created__lt=date.today()
        ).order_by('task_due')  # Order by due date


        #--- calendar handler here--------vvvvvvvvvvv
        d = get_date(request.GET.get("month", None))

        appointments = patient_appointment.objects.filter(
        who=patient,
        appointment_date__year=d.year,
        appointment_date__month=d.month
        ).values_list('appointment_date', flat=True)
        
        appointment_dates = set(appointments) #set appointment date as object for callendar
        
        appointments_qs = patient_appointment.objects.filter(
        who=patient,
        appointment_date__year=d.year,
        appointment_date__month=d.month
        )
        appointments_dict = defaultdict(list)
        for appt in appointments_qs:
            appointments_dict[appt.appointment_date].append(appt)

        calendar_html =  HighlightTodayCalendar(today=date.today(), appointments=appointments_dict).formatmonth(d.year, d.month)
        prev_month_link = prev_month(d)
        next_month_link = next_month(d)

       
    #-----calendar appointment
        appointments_json = {}
        for day, appts in appointments_dict.items():
            appointments_json[day.isoformat()] = [
            f"{a.appointment_time} with Dr. {a.doctor.who}" for a in appts
            ]
        

    context = {
        'appointments_json' : json.dumps(appointments_json),
        'month': d.month,
        'year': d.year,
        'calendar': calendar_html,
        'prev_month': prev_month_link,
        'next_month': next_month_link,
        'name': name,
        'mood_form': mood_form,
        'new_task': new_tasks,
        'pending_task': pending_tasks,
        'previous_mood':patient.previous_mood}
    return render(request, 'patient/dashboard.html',context)
#
#--------function to handle mood submit------------
#
def mood_selection_view(request):
    if request.method == 'POST':
        form = moodselectionform(request.POST)
        if form.is_valid():
            # Process the mood selection
            mood = form.cleaned_data['mood']
            if mood != None:
                reg_user = userinfo.objects.get(who=request.user)
                patient = patientinfo.objects.get(who=reg_user)
                patient.previous_mood = patient.latest_mood
                patient.latest_mood = mood
                patient.save()
            
    return redirect('patient_dashboard')  # Redirect to the patient dashboard
#
#
#
def patient_task_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_staff:
        return redirect('practitioner_dashboard')
    
    reg_user = userinfo.objects.get(who=request.user)
    patient = patientinfo.objects.get(who=reg_user)
    
    assign_task = patient_task.objects.filter(
        who = patient,
        task_status__in=['pending', 'delayed', 'in progress'],
        )   

    complete_task = patient_task.objects.filter(
        who=patient,
        task_status = 'complete',
        )
    
    cont = {
        'assign_task': assign_task,
        'complete_task': complete_task,
        }

    return render(request, 'patient/task.html',cont)
#
#
#
def patient_setting_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_staff:
        return redirect('practitioner_dashboard')
    else:
        set_pass_form = password_change_form(request.user)
    cont = {
            "pass_reset":set_pass_form,
        }
    return render(request , 'patient/setting.html',cont)
#
#--------password reset logic handling------------- 
#
def password_reset(request):
    if request.method == 'POST':
        form = password_change_form(request.user, request.POST)
        if form.is_valid():
            new_pass = form.cleaned_data['new_password']
            user = request.user
            user.set_password(new_pass)
            user.save()

            login(request,user)
            if request.user.is_staff:
                return redirect('practitioner_dashboard')
            else:
                return redirect('patient_dashboard')
#
#
#
def patient_appointment_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_staff:
        return redirect('practitioner_dashboard')
    
    user_info = userinfo.objects.get(who=request.user)
    patient = patientinfo.objects.get(who=user_info)    
    
    pending_appointment = patient_appointment.objects.filter(
        who=patient,
        appointment_status__in= ['pending','Pending'],
    ).order_by('appointment_date')

    complete_appointment = patient_appointment.objects.filter(
        who=patient,
        appointment_status__in = ['completed','cancelled'],
    ).order_by('appointment_date')

    
    cont = {
        'pending_appointment': pending_appointment,
        'complete_appointment':complete_appointment,
    }
    
    return render(request, 'patient/appointment.html',cont)

######################### logic fucntion habdling ################
##################################################################

def assign_task(request):
    if request.user.is_staff:
        if request.method == "POST":
            form = task_form(request.POST)
            if form.is_valid():
                patient_id = form.cleaned_data['patient_name']
                task_title = form.cleaned_data['task_name']
                description  = form.cleaned_data['task_description']
                task_due = form.cleaned_data['task_due_date']
                
                try:
                    patient = patientinfo.objects.get(who__who__id=patient_id)
                except patientinfo.DoesNotExist:
                    return HttpResponse('yer mom gae', status=404)

                patient_task.objects.create(
                    who = patient,
                    task_title=task_title,
                    task_description=description,
                    task_due=task_due,
                    task_status='pending',
                )

                return redirect('practitioner_dashboard')
    else:
        return redirect('login')    

#
#--------function for update patient mental states--------
#

def update_mental(request):
    if not request.user.is_staff:
        return redirect('login')

    if request.method == 'POST':
         form = mentalinfo_updating(request.POST)
         if form.is_valid():
                patient_id = form.cleaned_data['patient']
                category = form.cleaned_data['category']
                status  = form.cleaned_data['status']
                priority = form.cleaned_data['priority']
                
                try:
                    patient = patientinfo.objects.get(who__who__id=patient_id)
                except patientinfo.DoesNotExist:
                    return HttpResponse('yer mom gae', status=404)

                mentals = mentalinfo.objects.get(who = patient)
                mentals.mental_health_category = category
                mentals.mental_health_status=status
                mentals.mental_health_priority=priority


                mentals.save()

                return redirect('practitioner_patients')
    else:
        return redirect('login')    
        
#
#--------function to handle update taask completion------------
#
def task_complete_logic(request):
    if not request.user.is_authenticated:
        pass #create error here nextime
    if request.method == "POST":
        task_id = request.POST.get('task_id')

        reg_user = userinfo.objects.get(who=request.user)
        patient = patientinfo.objects.get(who=reg_user) 
        try:
            task = patient_task.objects.get(id=task_id, who=patient)
        except patient_task.DoesNotExist:
            return HttpResponse("Task not found.", status=404)
        task.task_status = 'complete'
        task.save()

    source = request.META.get('HTTP_REFERER')

    if source:
        return redirect(source)
    else:
        return redirect('patient_dashboard')
#
# ----------------------appointmnet stuff -----------------------
#

def tempory_appointment(request):
    if not request.is_staff:
        return  redirect('index')

    if request.method == 'POST': 
        form = appointment_form(request.POST)
        if form.is_valid:
            patient_id = form.cleaned_data['patient']
            date = form.cleaned_data['date']
            time = form.cleaned_data['time']
            meeting = form.cleaned_data['meeting']
            appt_type = form.cleaned_data['appt_type']
            reminder = form.cleaned_data['reminder']
    
    reg_user = userinfo.object.get(who=request.user)
    patient_user = userinfo.objects.get(who=patient_id)
    patient = patientinfo.objects.get(who=patient_user)
    appt = patient_appointment.object.get(who=patient)

    appt.doctor= reg_user
    appt.appointment_date= date
    appt.appointment_time= time
    appt.appointment_meeting_type = meeting 
    appt.appointment_type = appt_type
    appt.appointment_reminder = reminder
    appt.save()

    return redirect('practitioner_appointment')

##!!!!!!!!here be for google appointment !!!!!!!!! x    
def create_appointment(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    if request.method == 'POST':
        try:
            doctor = doctorinfo.objects.get(who__who=request.user)
            patient = patientinfo.objects.get(who__who__id=request.POST.get('patient'))
            appointment_date = datetime.strptime(request.POST.get('date'), '%Y-%m-%d').date()
            appointment_time = request.POST.get('time')
            
            # Set reminder date to one day before the appointment
            reminder_date = appointment_date - timedelta(days=1)
            
            appointment = patient_appointment.objects.create(
                who=patient,
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                appointment_type=request.POST.get('appt_type'),
                appointment_status=request.POST.get('appointment_status', 'pending'),
                appointment_meeting_type=request.POST.get('meeting', 'online'),
                appointment_reminder=request.POST.get('reminder', '1 hour')
            )
            
            # Add appointment to patient's Google Calendar if they have authorized
            if patient.who.google_auth:
                try:
                    # Create credentials object from stored token
                    credentials = Credentials.from_authorized_user_info(info=patient.who.google_auth)
                    
                    # If credentials are expired, refresh them
                    if credentials.expired and credentials.refresh_token:
                        credentials.refresh(Request())
                        # Update stored credentials
                        patient.who.google_auth = {
                            'token': credentials.token, 
                            'refresh_token': credentials.refresh_token,
                            'token_uri': credentials.token_uri,
                            'client_id': credentials.client_id,
                            'client_secret': credentials.client_secret,
                            'scopes': credentials.scopes
                        }
                        patient.save()
                        
                    # Build the Google Calendar service
                    service = build('calendar', 'v3', credentials=credentials)
                    
                    # Format the start and end times (end time is 1 hour after start)
                    start_datetime = f"{appointment_date}T{appointment_time}:00"
                    end_hour = int(appointment_time.split(':')[0]) + 1
                    end_minute = appointment_time.split(':')[1]
                    end_datetime = f"{appointment_date}T{end_hour:02d}:{end_minute}:00"
                    
                    # Create the event with appropriate details
                    event = {
                        'summary': f"Appointment with Dr. {doctor.who.full_name}",
                        'location': 'Online' if appointment.appointment_meeting_type == 'online' else 'In-Person',
                        'description': f"Appointment type: {appointment.appointment_type}",
                        'start': {
                            'dateTime': start_datetime,
                            'timeZone': 'Asia/Kuala_Lumpur'
                        },
                        'end': {
                            'dateTime': end_datetime,
                            'timeZone': 'Asia/Kuala_Lumpur'
                        },
                        'reminders': {
                            'useDefault': False,
                            'overrides': [
                                {'method': 'email', 'minutes': 24 * 60},
                                {'method': 'popup', 'minutes': 60},
                            ]
                        }
                    }
                    
                    # Add the event to the patient's calendar
                    created_event = service.events().insert(calendarId='primary', body=event).execute()
                    
                    # Optionally store the event ID in your appointment record for future updates
                    appointment.google_event_id = created_event.get('id')
                    appointment.save()
                    
                except Exception as e:
                    # Log error but don't prevent appointment creation
                    print(f"Error adding to patient's Google Calendar: {str(e)}")
            
            # Add appointment to doctor's Google Calendar if they have authorized
            if doctor.who.google_auth:
                try:
                    # Create credentials object from stored token
                    credentials = Credentials.from_authorized_user_info(info=doctor.who.google_auth)
                    
                    # Build the Google Calendar service
                    # If credentials are expired, refresh them
                    if credentials.expired and credentials.refresh_token:
                        credentials.refresh(Request())
                        # Update stored credentials
                        doctor.who.google_auth = {
                            'token': credentials.token, 
                            'refresh_token': credentials.refresh_token,
                            'token_uri': credentials.token_uri,
                            'client_id': credentials.client_id,
                            'client_secret': credentials.client_secret,
                            'scopes': credentials.scopes
                        }
                        doctor.save()
                        
                    # Build the Google Calendar service
                    service = build('calendar', 'v3', credentials=credentials)
                    
                    # Format the start and end times (end time is 1 hour after start)
                    start_datetime = f"{appointment_date}T{appointment_time}:00"
                    end_hour = int(appointment_time.split(':')[0]) + 1
                    end_minute = appointment_time.split(':')[1]
                    end_datetime = f"{appointment_date}T{end_hour:02d}:{end_minute}:00"
                    
                    # Create the event with appropriate details
                    event = {
                        'summary': f"Appointment with {patient.who.full_name}",
                        'location': 'Online' if appointment.appointment_meeting_type == 'online' else 'In-Person',
                        'description': f"Appointment type: {appointment.appointment_type}",
                        'start': {
                            'dateTime': start_datetime,
                            'timeZone': 'Asia/Kuala_Lumpur'
                        },
                        'end': {
                            'dateTime': end_datetime,
                            'timeZone': 'Asia/Kuala_Lumpur'
                        },
                        'reminders': {
                            'useDefault': False,
                            'overrides': [
                                {'method': 'email', 'minutes': 24 * 60},
                                {'method': 'popup', 'minutes': 60},
                            ]
                        }
                    }
                    
                    # Add the event to the patient's calendar
                    created_event = service.events().insert(calendarId='primary', body=event).execute()
                    
                    # Optionally store the event ID in your appointment record for future updates
                    appointment.google_event_id = created_event.get('id')
                    appointment.save()
                
                except Exception as e:
                    # Log error but don't prevent appointment creation
                    print(f"Error adding to doctor's Google Calendar: {str(e)}")
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)

def update_appointment(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    if request.method == 'POST':
        try:
            appointment = patient_appointment.objects.get(id=request.POST.get('appointment_id'))
            appointment.appointment_status = request.POST.get('appointment_status')
            appointment.appointment_type = request.POST.get('appointment_type')
            appointment.appointment_reminder = request.POST.get('appointment_reminder')
            appointment.appointment_meeting_type = request.POST.get('appointment_meeting_type')
            appointment.save()
            return JsonResponse({'success': True})
        except patient_appointment.DoesNotExist:
            return JsonResponse({'error': 'Appointment not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)

def reschedule_appointment(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    if request.method == 'POST':
        try:
            appointment = patient_appointment.objects.get(id=request.POST.get('appointment_id'))
            new_date = request.POST.get('new_date')
            new_time = request.POST.get('new_time')

            doctor = doctorinfo.objects.get(who__who=request.user)
            
            # Update appointment in database
            appointment.appointment_date = new_date
            appointment.appointment_time = new_time
            appointment.save()
            
            # Update appointment in patient's Google Calendar if they have authorized
            patient = appointment.who
            if patient.who.google_auth and appointment.google_event_id:
                try:
                    # Create credentials object from stored token
                    credentials = Credentials.from_authorized_user_info(info=patient.who.google_auth)
                    
                    # If credentials are expired, refresh them
                    if credentials.expired and credentials.refresh_token:
                        credentials.refresh(Request())
                        # Update stored credentials
                        patient.who.google_auth = {
                            'token': credentials.token, 
                            'refresh_token': credentials.refresh_token,
                            'token_uri': credentials.token_uri,
                            'client_id': credentials.client_id,
                            'client_secret': credentials.client_secret,
                            'scopes': credentials.scopes
                        }
                        patient.save()
                        
                    # Build the Google Calendar service
                    service = build('calendar', 'v3', credentials=credentials)
                    
                    # Format the start and end times (end time is 1 hour after start)
                    start_datetime = f"{new_date}T{new_time}:00"
                    end_hour = int(new_time.split(':')[0]) + 1
                    end_minute = new_time.split(':')[1]
                    end_datetime = f"{new_date}T{end_hour:02d}:{end_minute}:00"
                    
                    # First, get the existing event
                    event = service.events().get(calendarId='primary', eventId=appointment.google_event_id).execute()
                    
                    # Update event times
                    event['start'] = {
                        'dateTime': start_datetime,
                        'timeZone': 'Asia/Kuala_Lumpur'
                    }
                    event['end'] = {
                        'dateTime': end_datetime,
                        'timeZone': 'Asia/Kuala_Lumpur'
                    }
                    
                    # Update the event in Google Calendar
                    updated_event = service.events().update(
                        calendarId='primary', 
                        eventId=appointment.google_event_id, 
                        body=event
                    ).execute()
                    
                    print(f"Successfully updated Google Calendar event {appointment.google_event_id} for patient {patient.who.who.username}")
                    
                except ValueError as e:
                    print(f"Invalid Google auth data for patient {patient.who.who.username}: {str(e)}")
                except Exception as e:
                    # Log error but don't prevent appointment rescheduling
                    print(f"Error updating Google Calendar event: {str(e)}")
            
            if doctor.who.google_auth and appointment.google_event_id:
                try:
                    # Create credentials object from stored token
                    credentials = Credentials.from_authorized_user_info(info=doctor.who.google_auth)
                    
                    # If credentials are expired, refresh them
                    if credentials.expired and credentials.refresh_token:
                        credentials.refresh(Request())
                        # Update stored credentials
                        doctor.who.google_auth = {
                            'token': credentials.token, 
                            'refresh_token': credentials.refresh_token,
                            'token_uri': credentials.token_uri,
                            'client_id': credentials.client_id,
                            'client_secret': credentials.client_secret,
                            'scopes': credentials.scopes
                        }
                        doctor.save()
                        
                    # Build the Google Calendar service
                    service = build('calendar', 'v3', credentials=credentials)
                    
                    # Format the start and end times (end time is 1 hour after start)
                    start_datetime = f"{new_date}T{new_time}:00"
                    end_hour = int(new_time.split(':')[0]) + 1
                    end_minute = new_time.split(':')[1]
                    end_datetime = f"{new_date}T{end_hour:02d}:{end_minute}:00"
                    
                    # First, get the existing event
                    event = service.events().get(calendarId='primary', eventId=appointment.google_event_id).execute()
                    
                    # Update event times
                    event['start'] = {
                        'dateTime': start_datetime,
                        'timeZone': 'Asia/Kuala_Lumpur'
                    }
                    event['end'] = {
                        'dateTime': end_datetime,
                        'timeZone': 'Asia/Kuala_Lumpur'
                    }
                    
                    # Update the event in Google Calendar
                    updated_event = service.events().update(
                        calendarId='primary', 
                        eventId=appointment.google_event_id, 
                        body=event
                    ).execute()
                    
                    print(f"Successfully updated Google Calendar event {appointment.google_event_id} for DR. {doctor.who.who.username}")
                    
                except ValueError as e:
                    print(f"Invalid Google auth data for patient {patient.who.who.username}: {str(e)}")
                except Exception as e:
                    # Log error but don't prevent appointment rescheduling
                    print(f"Error updating Google Calendar event: {str(e)}")

            return JsonResponse({'success': True})
        except patient_appointment.DoesNotExist:
            return JsonResponse({'error': 'Appointment not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)
#
#--------- transfer no jutsu--------------
#

def transfer_no_jutsu(request, patient_id):
    if not request.user.is_staff:
        return redirect('login')
    patient = patientinfo.objects.get(id=patient_id)
    if request.method == 'POST':
        new_doctor_id = request.POST.get('doctor_id')
        new_doctor = doctorinfo.objects.get(id=new_doctor_id)
        patient.doctor = new_doctor
        patient.save()
        return redirect('practitioner_patients')
    doctors = doctorinfo.objects.all()
    return render(request, 'practitioner/transfer_patient.html', {'patient': patient, 'doctors': doctors})


############################# google stuff touchy if u know wat this #############################################
#################################################################################################

def google_calendar_auth(request):
    # Store the next URL to redirect to after authentication
    next_url = request.GET.get('next', 'patient_dashboard')
    request.session['next_url'] = next_url
    
    email = request.user.email  # Get the email from the logged-in user
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/userinfo.email', 'openid'],
        redirect_uri='http://localhost:8000/oauth2callback'
    )
    
    # Include login_hint to try to pre-select the user's email
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
        login_hint=email  # This helps Google suggest this email
    )
    
    request.session['state'] = state
    return redirect(authorization_url)

def google_calendar_callback(request):
    if request.user.is_anonymous:
        return redirect('patient_dashboard')
    
    state = request.GET.get('state')
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/userinfo.email', 'openid'],
        state=state
    )
    flow.redirect_uri = 'http://localhost:8000/oauth2callback'  
    authorization_response = request.build_absolute_uri()
    
    flow.fetch_token(authorization_response=authorization_response)
    
    # Get user info from Google
    credentials = flow.credentials
    service = build('oauth2', 'v2', credentials=credentials)
    user_info_google = service.userinfo().get().execute()
    google_email = user_info_google.get('email')
    
    # Update user's email if different
    if google_email and request.user.email != google_email:
        request.user.email = google_email
        request.user.save()
    
    # Get our user's info
    try:
        user_info = userinfo.objects.get(who=request.user)
        
        # Check if user is a patient before trying to store credentials
        try:
            patient = patientinfo.objects.get(who=user_info)
            
            # Store Google credentials with explicit conversion to dict
            credential_data = {
                'token': credentials.token, 
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
            
            # Debug print
            print(f"Saving credentials to patient: {credential_data}")
            
            patient.who.google_auth = credential_data
            patient.who.save()
            
            print(f"After save - Patient google_auth: {patient.who.google_auth}")
            
            # Redirect to the appropriate dashboard
            next_url = request.session.get('next_url', 'patient_dashboard')
            return redirect(next_url)
            
        except patientinfo.DoesNotExist:
            # Store credentials in session to apply later
            request.session['google_credentials'] = {
                'token': credentials.token, 
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
            return redirect('details_completion')
            
    except userinfo.DoesNotExist:
        # User profile doesn't exist yet, store credentials in session
        request.session['google_credentials'] = {
            'token': credentials.token, 
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        return redirect('details_completion')

def login_with_google(request):
    """Login directly with Google account"""
    request.session['next_url'] = 'patient_dashboard'  # After auth, go to dashboard
    return google_calendar_auth(request)

