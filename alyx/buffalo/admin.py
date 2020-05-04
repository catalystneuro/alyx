# Register the modules to show up at the admin page https://server/admin
from django.contrib import admin

from .models import BehavioralTask, TurningRecord, UnitsTracking


admin.site.register(BehavioralTask)
admin.site.register(TurningRecord)
admin.site.register(UnitsTracking)
