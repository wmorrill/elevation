from base.models import athlete
from base.models import activity
from base.models import activity_type
from base.models import month
from stravalib.client import Client
from datetime import datetime
from django.db.models import Sum, Count
import pytz
import time

pst = pytz.timezone('US/Pacific')
utc = pytz.utc

# historical dates
before = pst.localize(datetime.now())
# before = pst.localize(datetime(2016, 6, 1))
after = pst.localize(datetime(2018, 5, 1))
before_utc = before.astimezone(utc)
after_utc = after.astimezone(utc)


def data_scraper(date_end, date_start, athletes=None):
    meters_to_miles = 0.000621371
    meters_to_feet = 3.28084
    km_to_miles = 0.621371
    if athletes:
        athlete_list = athlete.objects.filter(id=athletes)
    else:
        athlete_list = athlete.objects.all() # get list of all athletes
    for each_athlete in athlete_list: # for each athlete
        client = Client(access_token=each_athlete.access_token)
        this_athlete_activities = client.get_activities(date_end, date_start)  # get list of activities for this month
        relevant_existing_activities = [this.id for this in activity.objects.filter(athlete_id=each_athlete).filter(start_date_local__lte=date_end).filter(start_date_local__gte=date_start)]
        # print(relevant_existing_activities)
        # print(each_athlete, this_athlete_activities)
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
                    start_date_local=utc.localize(each_activity.start_date_local).astimezone(pst),
                    average_speed=km_to_miles*each_activity.average_speed,
                    calories=each_activity.calories,
                    day=each_activity.start_date_local.day)# if its not in the database, add it
                new_activity.save()
                get_activity_photos(client, each_activity.id)
            else:
                get_activity_photos(client, each_activity.id)
                try:
                    relevant_existing_activities.remove(each_activity.id)
                except ValueError:
                    pass  # print("item %d in black hole" % each_activity.id)
        for extra_activity in relevant_existing_activities:
            print('removing item %d from database since it doesnt exist on strava'%extra_activity)
            activity.objects.filter(id=extra_activity).delete()
        cum = 0
        # for this_activity in activity.objects.filter(athlete_id = each_athlete).order_by('start_date_local'):
        for each_day in range(1,(date_end.astimezone(pst)-date_start.astimezone(pst)).days+1):
            print(each_athlete, each_day)
            this_day = activity.objects.filter(athlete_id = each_athlete).filter(start_date_local__lte=before).filter(start_date_local__gte=after).filter(day=each_day).aggregate(daily_sum = Sum('total_elevation_gain'))
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
        month.objects.filter(day__gt=datetime.now().day).delete()

def type_update(before, after):
    # update the info for the types pie chart
    # find all the types
    types = activity.objects.values('type').distinct()
    elevation_by_type = activity.objects.filter(start_date_local__lte=before).filter(start_date_local__gte=after).values('type').annotate(Sum('total_elevation_gain'))
    distance_by_type = activity.objects.filter(start_date_local__lte=before).filter(start_date_local__gte=after).values('type').annotate(Sum('distance'))
    quantity_by_type = activity.objects.filter(start_date_local__lte=before).filter(start_date_local__gte=after).values('type').annotate(Count('id'))
    # for each type
    for each_value in types:
        each_type = each_value['type']
        # check to see if it already exists
        this_type = activity_type.objects.filter(pk=each_type)
        if not this_type:
            new_type = activity_type(type = each_type)
            new_type.save()
        else:
            clear = this_type[0]
            clear.elevation = 0
            clear.save()
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
    junk_types = activity_type.objects.filter(elevation=0)
    junk_types.delete()

if __name__ == "__main__":
    print("trying to run")
    t0 = time.clock()
    while(time.clock() - t0 > 60 * 60):
        data_scraper(before, after)
        print("activities updated")
        type_update(before, after)
        print("types updated")

