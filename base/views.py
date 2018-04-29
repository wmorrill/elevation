from django.shortcuts import render
from stravalib.client import Client
from datetime import datetime
from datetime import timedelta
from base.models import athlete
from base.models import activity
from base.models import data_update
from stravalib.model import ActivityPhoto
from base.apps import *
from threading import Thread
import pytz
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

# timezone definition
pst = pytz.timezone('US/Pacific')
utc = pytz.utc

# historical dates
# before = pst.localize(datetime.now())
before = pst.localize(datetime(2018, 6, 1))
after = pst.localize(datetime(2018, 5, 1))
before_utc = before.astimezone(utc)
after_utc = after.astimezone(utc)
# ----------------


# this_month = datetime.today().month
# this_year = datetime.today().year
# # before and after need to be in UTC time zone
#
# before = pst.localize(datetime.now())
# before_utc = before.astimezone(utc)
# after = pst.localize(datetime(this_year, this_month, 1))
# after_utc = after.astimezone(utc)

def faq(request):
    return render(request, 'faq.html', {'leaderboard':get_leaderboard()})

# def history(request):
#     hist_before = datetime.strptime(request.GET.get('b'), "%Y-%m-%d")
#     hist_after = datetime.strptime(request.GET.get('a'), "%Y-%m-%d")
#     leaderboard = get_leaderboard()
#     elev_chart = elevation_chart(before, after)
#     pie_chart = activity_split_chart(before, after)
#
#     total_distance = activity.objects.filter(start_date_local__lte=before).filter(start_date_local__gte=after).aggregate(distance_sum=Sum('distance'))['distance_sum']
#     total_elevation = activity.objects.filter(start_date_local__lte=before).filter(start_date_local__gte=after).aggregate(elevation_sum=Sum('total_elevation_gain'))['elevation_sum']
#     total_moving_time = activity.objects.filter(start_date_local__lte=before).filter(start_date_local__gte=after).aggregate(moving_time_sum=Sum('moving_time'))['moving_time_sum']
#     energy_wasted = 0.07 * total_elevation / (total_moving_time.days * 24 + total_moving_time.seconds / 3600) / 1000
#     ghg_prevented = 0.419 * total_distance
#     coal_prevented = 0.45 * total_distance
#     gasoline_prevented = 0.047 * total_distance
#
#     return render(request, 'index.html', {'charts':[elev_chart, pie_chart], 'leaderboard':leaderboard,
#                                           'energy_wasted':int(energy_wasted*1000), 'ghg_prevented':int(ghg_prevented),
#                                           'total_elevation':int(total_elevation), 'coal_prevented':coal_prevented,
#                                           'gasoline_prevented':gasoline_prevented, 'hike_leaderboard':get_leaderboard('Hike'),
#                                           'ride_leaderboard':get_leaderboard('Ride'), 'run_leaderboard':get_leaderboard('Run')})

def history(request):
    year = request.GET.get('year')
    if year in '2014':
        page = 'May_2014.html'
    elif year in '2015':
        page = 'May_2015.html'
    elif year in '2016':
        page = 'May_2016.html'
    else:
        page = 'May_2017.html'
    return render(request, page, {'leaderboard':get_leaderboard()})

def index(request):
    # if datetime.today().day == 1 and datetime.now().hour < 12:
    #     return render(request, 'get_going.html')
    last_check = data_update.objects.all().order_by('-id')[0].time_stamp
    # # check timestamp of last update
    # if data_update.objects.all():
    #     last_check = data_update.objects.all().order_by('-id')[0]
    # else:
    #     last_check = data_update(time_stamp=datetime.today())
    # # if its been more than some time (15 mins?)
    # print("Now")
    # print(datetime.utcnow())
    # print("Last Update")
    # print(last_check.time_stamp.replace(tzinfo=datetime.utcnow().tzinfo))
    # if datetime.utcnow() > last_check.time_stamp.replace(tzinfo=datetime.utcnow().tzinfo) + timedelta(minutes=15):
    #     # add a new time stamp so no one else updates
    #     new_stamp = data_update(time_stamp=datetime.utcnow())
    #     new_stamp.save()
    #     # go through each user and update their activities for this month
    #     t = Thread(target=data_scraper, args=[after_utc, before_utc])
    #     t.daemon = True
    #     t.start()
    #     # data_scraper(after, before)
    # else:
    #     print("updated in the last 15 mins at %s" % str(last_check.time_stamp.astimezone(pst)))

    leaderboard = get_leaderboard()
    try:
        elev_chart = elevation_chart(before, after)
        pie_chart = activity_split_chart(before, after)
        total_distance = activity.objects.filter(start_date_local__lte=before).filter(start_date_local__gte=after).aggregate(distance_sum=Sum('distance'))['distance_sum']
        total_elevation = activity.objects.filter(start_date_local__lte=before).filter(start_date_local__gte=after).aggregate(elevation_sum=Sum('total_elevation_gain'))['elevation_sum']
        total_moving_time = activity.objects.filter(start_date_local__lte=before).filter(start_date_local__gte=after).aggregate(moving_time_sum=Sum('moving_time'))['moving_time_sum']
        energy_wasted = 800 * (total_moving_time.days * 24 + total_moving_time.seconds / 3600) / 860.421 / 1000
        ghg_prevented = 0.419 * total_distance
        coal_prevented = 0.45 * total_distance
        gasoline_prevented = 0.047 * total_distance
        hours_tv = total_moving_time
        burritos = 800 * (total_moving_time.days * 24 + total_moving_time.seconds / 3600) / 665 # 800 calories per hour burned, 665 calories per burrito
    except:
        elev_cart = ""
        pie_chart = ""
        burritos = 0
        hours_tv = 0
        coal_prevented = 0
        ghg_prevented = 0
        energy_wasted = 0
        total_moving_time = 0
        total_distance = 0
        total_elevation = 0
    
    return render(request, 'index.html', {'charts':[elev_chart, pie_chart], 'leaderboard':leaderboard,
                                          'energy_wasted':int(energy_wasted*1000), 'ghg_prevented':int(ghg_prevented),
                                          'total_elevation':int(total_elevation), 'coal_prevented':coal_prevented,
                                          'gasoline_prevented':gasoline_prevented, 'hike_leaderboard':get_leaderboard('Hike'),
                                          'ride_leaderboard':get_leaderboard('Ride'), 'run_leaderboard':get_leaderboard('Run'),
                                          'tv_not_watched': hours_tv, 'burritos': burritos, 'last_update':last_check})

def individual(request):
    leaderboard = get_leaderboard()
    athlete_id = request.GET.get('id')
    print(athlete_id)
    this_person = athlete.objects.filter(id = athlete_id)
    data_scraper(after_utc, before_utc, this_person)
    chart = athlete_chart(this_person)
    activity_list = activity.objects.filter(athlete_id = this_person).filter(start_date_local__lte=before).filter(start_date_local__gte=after).order_by('start_date_local')
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
        data_scraper(after_utc, before_utc, client.get_athlete().id)
        result = 'added'
    else:
        result = 'already exists'
    return render(request, 'auth_success.html', {'leaderboard':get_leaderboard(), 'result':result})

def force_update(request):
    #get_activity_photos()
    last_update = data_update.objects.all()[0]
    # data_scraper(last_update.time_stamp, before)
    last_update.time_stamp=utc.localize(datetime.utcnow()).astimezone(pst)
    last_update.save()
    data_scraper(last_update.time_stamp-timedelta(days=5), before)
    # new_stamp = data_update(time_stamp=utc.localize(datetime.utcnow()).astimezone(pst))
    # new_stamp.save()
    # go through each user and update their activities for this month
    # t = Thread(target=data_scraper, args=[after_utc, before_utc])
    # t.daemon = True
    # t.start()
    # data_scraper(after, before)
    return render(request, 'force_update.html')

def test(request):
    # my_id = 547220628
    # client = Client(access_token='12363c99d46a329f5e810e3fb7135bc45caaa7c7')
    # photos = client.get_activity_photos(my_id)
    #
    # # this_activity = client.get_activity(547220628)
    # print("###############DEBUG##############")
    # # print(this_activity_photos)
    # # for photo in this_activity_photos:
    # #     print(photo.urls)
    # print(photos)
    # # for item in this_activity:
    # #     print('made it here')
    # #     print(item)
    # #     print(item.calories)
    # #     print(item.photos)
    print("test...")
    get_emails()
    print("##################################")
    return render(request, 'test.html', {'result1': 1, 'result2': 2})

def leaderboard(request):
    return render(request, 'leaderboard.html', {'leaderboard':get_leaderboard(),
                                          'hike_leaderboard':get_leaderboard('Hike'),
                                          'ride_leaderboard':get_leaderboard('Ride'),
                                          'run_leaderboard':get_leaderboard('Run')})
