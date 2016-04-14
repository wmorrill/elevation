from django.shortcuts import render
from stravalib.client import Client
from datetime import datetime
from datetime import timedelta
from base.models import athlete
from base.models import activity
from base.models import data_update
from base.apps import *

def index(request):
    # check timestamp of last update
    if data_update.objects.all():
        last_check = data_update.objects.all().order_by('-id')[0]
    else:
        last_check = data_update(time_stamp=datetime.today())
    # if its been more than some time (15 mins?)
    if datetime.utcnow() > last_check.time_stamp.replace(tzinfo=datetime.utcnow().tzinfo) + timedelta(minutes=15):
        # add a new time stamp so no one else updates
        new_stamp = data_update(time_stamp=datetime.utcnow())
        new_stamp.save()
        # go through each user and update their activities for this month
        this_month = datetime.today().month
        this_year = datetime.today().year
        before = datetime(this_year, this_month+1, 1)
        after = datetime(this_year, this_month, 1)
        data_scraper(after, before)
    else:
        print("updated in the last 15 mins at %s" % str(last_check.time_stamp))

    this_month = datetime.today().month
    this_year = datetime.today().year
    before = datetime(this_year, this_month+1, 1)
    after = datetime(this_year, this_month, 1)
    leaderboard = get_leaderboard()
    elev_chart = elevation_chart(before, after)
    return render(request, 'index.html', {'sample_chart':elev_chart, 'leaderboard':leaderboard})

def individual(request):
    leaderboard = get_leaderboard()
    athlete_id = request.GET.get('id')
    print(athlete_id)
    this_person = athlete.objects.filter(id = athlete_id)
    chart = athlete_chart(this_person)
    activity_list = activity.objects.filter(athlete_id = this_person).order_by('start_date_local')
    return render(request, 'individual.html', {'this_person': this_person, 'sample_chart': chart, 'activity_list':activity_list, 'leaderboard':leaderboard})

def auth(request):
    client = Client()
    auth_link = client.authorization_url(5928,'https://elevation-challenge.herokuapp.com/auth_success/')
    return render(request, 'auth.html', {'leaderboard':get_leaderboard(), 'auth_link':auth_link})

def auth_success(request):
    temp_code = request.GET.get('code')  # temp auth code
    print(temp_code)
    client = Client()
    token = client.exchange_code_for_token(5928, 'a486a0b19c8d16aef41090371b7726dc510ee4a7', temp_code)
    if not athlete.objects.filter(pk=client.get_athlete().id):
        new_athlete = athlete(
            id = client.get_athlete().id,
            firstname = client.get_athlete().firstname,
            lastname = client.get_athlete().lastname,
            access_token = token
        )
        new_athlete.save()
        result = 'added'
    else:
        result = 'already exists'
    return render(request, 'auth_success.html', {'leaderboard':get_leaderboard(), 'result':result})

def force_update(request):
    new_stamp = data_update(time_stamp=datetime.utcnow())
    new_stamp.save()
    # go through each user and update their activities for this month
    this_month = datetime.today().month
    this_year = datetime.today().year
    before = datetime(this_year, this_month+1, 1)
    after = datetime(this_year, this_month, 1)
    data_scraper(after, before)
    return render(request, 'force_update.html')