from django.contrib import admin

from models import *


class HolidayAdmin(admin.ModelAdmin):

    list_display = ['title', 'start_date', 'end_date']


class SpecialDayAdmin(admin.ModelAdmin):

    list_display = ['title', 'month', 'day']


class WeeklyActivityAdmin(admin.ModelAdmin):

    list_display = ['title', 'day_of_the_week', 'start_time', 'end_time', 'except_holidays']


class OneTimeEventAdmin(admin.ModelAdmin):

    list_display = ['title', 'start_date', 'end_date']


admin.site.register(Holiday, HolidayAdmin)
admin.site.register(SpecialDay, SpecialDayAdmin)
admin.site.register(WeeklyActivity, WeeklyActivityAdmin)
admin.site.register(OneTimeEvent, OneTimeEventAdmin)
admin.site.register(Occurrence)
