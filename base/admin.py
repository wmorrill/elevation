from django.contrib import admin
from .models import athlete
from .models import activity
from .models import data_update
from .models import picture
from .models import club
from .models import activity_type

admin.site.register(athlete)
admin.site.register(activity)
admin.site.register(data_update)
admin.site.register(picture)
admin.site.register(club)
admin.site.register(activity_type)