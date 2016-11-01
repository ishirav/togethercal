from django.contrib import admin

from models import *


class HolidayAdmin(admin.ModelAdmin):

    list_display = ['title', 'start_date', 'end_date']
    search_fields = ['title']


class SpecialDayAdmin(admin.ModelAdmin):

    list_display = ['title', 'month', 'day']
    search_fields = ['title']


class WeeklyActivityAdmin(admin.ModelAdmin):

    list_display = ['title', 'day_of_the_week', 'start_time', 'end_time', 'include_holidays']
    search_fields = ['title']


class OneTimeEventAdmin(admin.ModelAdmin):

    list_display = ['title', 'start_date', 'end_date']
    search_fields = ['title']


class OccurrenceAdmin(admin.ModelAdmin):

    date_hierarchy = 'date'
    search_fields = ['event__title']


admin.site.register(Holiday, HolidayAdmin)
admin.site.register(SpecialDay, SpecialDayAdmin)
admin.site.register(WeeklyActivity, WeeklyActivityAdmin)
admin.site.register(OneTimeEvent, OneTimeEventAdmin)
admin.site.register(Occurrence, OccurrenceAdmin)
