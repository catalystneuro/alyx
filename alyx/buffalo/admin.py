# Register the modules to show up at the admin page https://server/admin
from django.contrib import admin

from .models import BehavioralTask


admin.site.register(BehavioralTask)
