# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.shortcuts import render
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

import dateparser
from datetime import datetime, date, timedelta

from models import Occurrence, OneTimeEvent, SpecialDay, WeeklyActivity


def main_view(request):
    today = date.today()
    today_html = day_view(request, 0).content
    return render(request, 'main.html', locals())


def day_view(request, offset=None):
    offset = offset or int(request.GET.get('offset', 0))
    the_day = date.today() + timedelta(days=offset)
    occurrences = list(Occurrence.objects.filter(date=the_day))
    occurrences.sort(key=lambda o: o.get_sorting_key())
    return render(request, 'day.html', locals())


def add_view(request):
    return render(request, 'add.html', locals())


def form_view(request, form_type):
    cls = FORM_TYPES[form_type]
    form = cls(request)
    if form.is_valid():
        print form.cleaned_data
        e = form.save()
        e.create_occurrences()
    return render(request, 'form.html', locals())


def inbound_mail_view(request):
    import logging
    logging.info(request.GET)
    logging.info(request.POST)
    return HttpResponse('OK')


def _parse(date_str, base=None):
    base = base or timezone.now()
    return dateparser.parse(
        date_str, 
        languages=[settings.LANGUAGE_CODE],
        settings=dict(PREFER_DATES_FROM='future', RETURN_AS_TIMEZONE_AWARE=True, RELATIVE_BASE=base)
    )


class OneTimeEventForm(forms.ModelForm):

    heading = 'אירוע חד פעמי'

    start_date = forms.CharField(label=u'התחלה', max_length=200)
    end_date = forms.CharField(label=u'סיום', max_length=200, required=False)

    class Meta:
        model = OneTimeEvent
        fields = ('title', 'start_date', 'end_date')

    def __init__(self, request):
        initial = dict(start_date=request.GET.get('dt'), end_date=request.GET.get('dt'))
        super(OneTimeEventForm, self).__init__(request.POST or None, initial=initial)

    def _parse_start(self):
        start = self.cleaned_data.get('start_date', '')
        if isinstance(start, datetime):
            return start
        return _parse(start)

    def clean_start_date(self):
        if self.cleaned_data['start_date']:
            start = self._parse_start()
            print start
            if not start:
                raise ValidationError(u'לא ניתן לפרש את התאריך או השעה')
            return start

    def clean_end_date(self):
        end = self.cleaned_data['end_date']
        if end:
            start = self._parse_start()
            end = _parse(end, start)
            if not end:
                raise ValidationError(u'לא ניתן לפרש את התאריך או השעה')
            return end


class SpecialDayForm(forms.ModelForm):

    heading = 'תאריך מיוחד'

    class Meta:
        model = SpecialDay
        fields = ('title', 'month', 'day')

    def __init__(self, request):
        dt = _parse(request.GET.get('dt', 'היום'))
        initial = dict(month=dt.month, day=dt.day)
        super(SpecialDayForm, self).__init__(request.POST or None, initial=initial)


class WeeklyActivityForm(forms.ModelForm):

    heading = 'פעילות שבועית'

    start_date = forms.CharField(label=u'התחלה', max_length=200, initial='1/9/%s' % datetime.now().year)
    end_date = forms.CharField(label=u'סיום', max_length=200, required=False, initial='31/8/%s' % (datetime.now().year + 1))

    class Meta:
        model = WeeklyActivity
        exclude = ('icon',)

    def __init__(self, request):
        super(WeeklyActivityForm, self).__init__(request.POST or None)


FORM_TYPES = dict(
    O = OneTimeEventForm,
    S = SpecialDayForm,
    W = WeeklyActivityForm
)
