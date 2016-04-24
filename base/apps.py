from django.apps import AppConfig
from base.models import athlete
from base.models import activity
from base.models import activity_type
from base.models import month
from stravalib.client import Client
from datetime import datetime
from datetime import timedelta
import chartit
from django.db.models import Sum, Count

this_month = datetime.today().month
this_year = datetime.today().year
#before = datetime(this_year, this_month+1, 1)
before = datetime.today()
after = datetime(this_year, this_month, 1)

class BaseConfig(AppConfig):
    name = 'base'

class stravalib_app(AppConfig):
    name = 'stravalib'

class chartit_app(AppConfig):
    name = 'chartit'

def data_scraper(date_start, date_end):
    meters_to_miles = 0.000621371
    meters_to_feet = 3.28084
    km_to_miles = 0.621371
    athlete_list = athlete.objects.all() # get list of all athletes
    for each_athlete in athlete_list: # for each athlete
        client = Client(access_token=each_athlete.access_token)
        this_athlete_activities = client.get_activities(date_end, date_start)  # get list of activities for this month
        relevant_existing_activities = [this.id for this in activity.objects.filter(athlete_id=each_athlete).filter(start_date_local__lte=date_end).filter(start_date_local__gte=date_start)]
        # print(relevant_existing_activities)
        for each_activity in this_athlete_activities:  # for each activity
            if not activity.objects.filter(pk=each_activity.id):# check if its already in the database
                new_activity = activity(
                    id=each_activity.id,
                    athlete_id=athlete.objects.filter(pk=each_activity.athlete.id)[0],
                    name=each_activity.name,
                    distance=meters_to_miles*each_activity.distance,
                    moving_time=each_activity.moving_time,
                    elapsed_time=each_activity.elapsed_time,
                    total_elevation_gain=meters_to_feet*each_activity.total_elevation_gain,
                    type=each_activity.type,
                    start_date_local=each_activity.start_date_local,
                    average_speed=km_to_miles*each_activity.average_speed,
                    calories=each_activity.calories,
                    photos=each_activity.photos,
                    day=each_activity.start_date_local.day)# if its not in the database, add it
                new_activity.save()
            else:
                try:
                    relevant_existing_activities.remove(each_activity.id)
                except ValueError:
                    pass  # print("item %d in black hole" % each_activity.id)
        for extra_activity in relevant_existing_activities:
            print('removing item %d from database since it doesnt exist on strava'%extra_activity)
            activity.objects.filter(id=extra_activity).delete()
        cum = 0
        # for this_activity in activity.objects.filter(athlete_id = each_athlete).order_by('start_date_local'):
        for each_day in range(1,(date_end-date_start).days+1):
            this_day = activity.objects.filter(athlete_id = each_athlete).filter(day=each_day).aggregate(daily_sum = Sum('total_elevation_gain'))
            cum += this_day['daily_sum'] or 0
            today = month.objects.filter(athlete_id = each_athlete).filter(day = each_day)
            if today:
                for existing_day in today:
                    existing_day.cum_elev = cum
                    existing_day.save()
            else:
                new_day = month(
                    athlete_id = each_athlete,
                    day = each_day,
                    cum_elev = cum
                )
                new_day.save()
        all_athlete_activities = activity.objects.filter(athlete_id=each_athlete).filter(start_date_local__lte=date_end).filter(start_date_local__gte=date_start).order_by('start_date_local')
        cum = 0
        for every_activity in all_athlete_activities:
            cum += every_activity.total_elevation_gain
            every_activity.cumulative_elevation = cum
            every_activity.save()
        month.objects.filter(day__gte=each_day+1).delete()

    # update the info for the types pie chart
    # find all the types
    types = activity.objects.filter(start_date_local__lte=before).filter(start_date_local__gte=after).values('type').distinct()
    elevation_by_type = activity.objects.filter(start_date_local__lte=before).filter(start_date_local__gte=after).values('type').annotate(Sum('total_elevation_gain'))
    distance_by_type = activity.objects.filter(start_date_local__lte=before).filter(start_date_local__gte=after).values('type').annotate(Sum('distance'))
    quantity_by_type = activity.objects.filter(start_date_local__lte=before).filter(start_date_local__gte=after).values('type').annotate(Count('id'))
    # for each type
    for each_value in types:
        each_type = each_value['type']
        # check to see if it already exists
        this_type = activity_type.objects.filter(pk=each_type)[0]
        if not this_type:
            new_type = activity_type(type = each_type)
            new_type.save()
    for each_item in elevation_by_type:
            this_type = activity_type.objects.filter(pk=each_item['type'])[0]
            this_type.elevation = each_item['total_elevation_gain__sum']
            this_type.save()
    for each_item in distance_by_type:
            this_type = activity_type.objects.filter(pk=each_item['type'])[0]
            this_type.distance = each_item['distance__sum']
            this_type.save()
    for each_item in quantity_by_type:
            this_type = activity_type.objects.filter(pk=each_item['type'])[0]
            this_type.quantity = each_item['id__count']
            this_type.save()



def get_athlete_daily_activities(athlete, date_start, date_end):
    daily_dictionary = {}
    relevant_activities = activity.objects.filter(athlete_id=athlete).filter(start_date_local__lte=date_end).filter(start_date_local__gte=date_start)
    for day in range((date_end-date_start).days):
        this_day_activities = activity.objects.filter(id__in=relevant_activities).filter(start_date_local__gte=date_start+timedelta(day)).filter(start_date_local__lte=date_start+timedelta(day)+timedelta(days=1)).annotate()
        # this_day_activities = activity.objects.filter(id__in=relevant_activities).filter(start_date_local=date_start+timedelta(day)).annotate()
        # print(this_day_activities)
        # this_day_activities = relevant_activities.objects.filter(start_date_local=date_start+datetime.timedelta(day))
        daily_dictionary[day] = this_day_activities
    return daily_dictionary

def get_elevation_sum(daily_dictionary):
    daily_elevation_list = {}
    daily_elevation_sum = {}
    total_elevation = 0
    for day in daily_dictionary:
        daily_elevation = 0
        for each_activity in daily_dictionary[day]:
            daily_elevation += each_activity.total_elevation_gain
            total_elevation += each_activity.total_elevation_gain
        daily_elevation_list[day+1] = daily_elevation
        daily_elevation_sum[day+1] = total_elevation
    return daily_elevation_list, daily_elevation_sum

def get_leaderboard():
    # return a queryset of athletes in order of elevation total
    return athlete.objects.annotate(elevation=Sum('activity__total_elevation_gain')).order_by('-elevation')

def elev_per_day(activity_set, before, after):
    date_start = after
    date_end = before
    daily_dictionary = {}
    cumulative = 0
    for day in range((date_end-date_start).days):
        this_day_activities = activity.objects.filter(id__in=activity_set).filter(start_date_local__gte=date_start+timedelta(day)).filter(start_date_local__lte=date_start+timedelta(day)+timedelta(days=1)).aggregate(Sum('total_elevation_gain'))
        if this_day_activities['total_elevation_gain__sum']:
            cumulative += this_day_activities['total_elevation_gain__sum']
        daily_dictionary[day+1] = cumulative
    return daily_dictionary

def elevation_chart(before, after):
    # make a list of options/terms for each athlete
    this_series = []
    position = 1
    for each_athlete in get_leaderboard():
        # cumulative_set = get_cumulative_queryset(each_athlete, after, before)
        cumulative_set = month.objects.filter(athlete_id = each_athlete)
        this_series.append({'options':{'source': cumulative_set},
                       'terms':[{str(each_athlete)+'_date':'day'}, {str(each_athlete): 'cum_elev'}]})
        position += 1
        #add pie chart to line chart
        this_series.append({'options':{'source': activity_type.objects.all()},
                            'terms':['type', 'elevation']})
    ds = chartit.DataPool(this_series)

    athlete_list_date = [str(x)+'_date' for x in get_leaderboard()]
    athlete_list_elevation = [str(x) for x in get_leaderboard()]
    term_dict = {}
    for key, value in enumerate(athlete_list_date):
        term_dict[value] = [athlete_list_elevation[key],]
    chart_series = [{'options':{'type': 'spline', 'stacking': False}, 'terms':term_dict}]
    # adding pie chart to line chart
    chart_series.append({'options':{'type': 'pie', 'center': [100, 80], 'size':200}, 'terms':{'type': ['elevation']}})
    title = 'Elevation Summary - ' + datetime.today().strftime("%B")
    cht = chartit.Chart(
        datasource=ds,
        series_options=chart_series,
        chart_options={'title': {'text': title},
                       'xAxis': {'title': {'text': 'Day'}},
                       'yAxis': {'title': {'text': 'Elevation (feet)'}},
                       'legend': {'layout': 'vertical',
                                 'align': 'left',
                                 'verticalAlign': 'top',
                                 'reversed': 'true',
                                 'maxHeight':500}
        }
    )
    return cht

def athlete_chart(this_person):

    ds = chartit.DataPool(
       series=
        [{'options': {'source': activity.objects.filter(athlete_id=this_person).filter(start_date_local__lte=before).filter(start_date_local__gte=after)},
          'terms': [{'day':'day'}, 'total_elevation_gain', 'cumulative_elevation']}]
    )

    cht = chartit.Chart(
        datasource=ds,
        series_options=[{'options':{'type': 'column', 'xAxis': 0, 'yAxis': 0, 'zAxis': 0},
                         'terms':{'day': ['total_elevation_gain']}},
                        {'options':{'type': 'spline', 'xAxis': 1, 'yAxis':1},
                         'terms':{'day': ['cumulative_elevation']},
                        }],
        chart_options={'title': {'text': 'Activity Stats'}}
    )

    return cht

def activity_split_chart(before, after):
    ds = chartit.DataPool(
       series=
        [{'options': {'source': activity_type.objects.all()},
          'terms': ['type', 'elevation']}]
    )

    cht = chartit.Chart(
        datasource=ds,
        series_options=[{'options':{'type': 'pie'},
                         'terms':{'type': ['elevation']}
                        }],
        chart_options={'title': {'text': 'Activity Breakdown'}}
    )

    return cht

