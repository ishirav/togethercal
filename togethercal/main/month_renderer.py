# -*- coding: utf-8 -*-
from django.utils.html import escape
from django.conf import settings

from calendar import HTMLCalendar, month_name
import datetime
from itertools import chain

from models import Occurrence, OneTimeEvent, Holiday, SpecialDay


class MonthRenderer(HTMLCalendar):

    def __init__(self):
        super(MonthRenderer, self).__init__(6)

    def formatmonthname(self, theyear, themonth, withyear=True):
        return ''

    def formatmonth(self, theyear, themonth, withyear=True):
        self.year = theyear
        self.month = themonth
        self.occurrences = list(Occurrence.objects.filter(date__year=theyear, date__month=themonth))
        self.occurrences.sort(key=lambda o: o.get_sorting_key())
        return super(MonthRenderer, self).formatmonth(theyear, themonth, withyear)

    def formatweekday(self, day):
        return '<th class="%s">%s</th>' % (self.cssclasses[day], u'בגדהושא'[day])

    def formatday(self, day, weekday):
        if day != 0:
            curdate = datetime.date(self.year, self.month, day)
            classes = set()
            classes.add(self.cssclasses[weekday])
            if datetime.date.today() == curdate:
                classes.add('today')
            content = []
            for occurrence in self.occurrences:
                if occurrence.date == curdate:
                    event = occurrence.get_event_as_subclass()
                    if isinstance(event, Holiday):
                        classes.add('holiday')
                        content.append(escape(event.title) + '<br>')
                    elif isinstance(event, (SpecialDay, OneTimeEvent)):
                        if not content:
                            content.append('<br>')
                        icon = event.icon.image.url if event.icon else '/static/bell.png'
                        content.append('<img src="%s", title="%s">' % (icon, escape(event.title)))
            cssclass = ' '.join(classes)
            return self.day_cell(curdate.strftime(settings.DATE_INPUT_FORMATS[0]), cssclass, day, ''.join(content))
        return self.day_cell('noday', 'noday', '', '')

    def day_cell(self, curdate, cssclass, day, text):
        if day:
            text = '<b>' + str(day) + '</b> ' + text
        return '<td data-day="%s" class="%s">%s</td>' % (curdate, cssclass, text)

