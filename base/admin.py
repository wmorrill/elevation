from django.contrib import admin
from .models import athlete
from .models import activity
from .models import data_update

admin.site.register(athlete)
admin.site.register(activity)
admin.site.register(data_update)