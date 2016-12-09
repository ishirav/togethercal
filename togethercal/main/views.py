# -*- coding: utf-8 -*-
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.db import transaction
from django.contrib.auth.decorators import login_required

import dateparser
from datetime import datetime, date, timedelta, time
import logging
import pytz
from dateutil.relativedelta import relativedelta

from models import Occurrence, OneTimeEvent, SpecialDay, WeeklyActivity


@login_required
def main_view(request):
    offset = 0
    dt = _parse(request.GET.get('dt', 'היום')).date()
    offset = (dt - date.today()).days
    days = [day_view(request, offset + i).content for i in range(3)]
    return render(request, 'main.html', locals())


@login_required
def month_view(request, offset=None):
    from month_renderer import MonthRenderer
    offset = offset or int(request.GET.get('offset', 0))
    the_day = date.today().replace(day=1) + relativedelta(months=offset)
    renderer = MonthRenderer()
    month_html = renderer.formatmonth(the_day.year, the_day.month)
    return render(request, 'month.html', locals())


def day_view(request, offset=None):
    offset = offset or int(request.GET.get('offset', 0))
    the_day = date.today() + timedelta(days=offset)
    occurrences = list(Occurrence.objects.filter(date=the_day))
    occurrences.sort(key=lambda o: o.get_sorting_key())
    return render(request, 'day.html', locals())


@login_required
def add_view(request):
    return render(request, 'add.html', locals())


@login_required
@transaction.atomic
def form_view(request, form_type):
    cls = FORM_TYPES[form_type]
    form = cls(request)
    if form.is_valid():
        e = form.save()
        e.create_occurrences()
        return HttpResponseRedirect(reverse('main') + '?' + request.META['QUERY_STRING'])
    return render(request, 'form.html', locals())


@login_required
@transaction.atomic
def edit_view(request, pk):
    occurrence = get_object_or_404(Occurrence, pk=pk)
    event = occurrence.get_event_as_subclass()
    if request.POST.get('action') == 'delete':
        event.delete()
        return HttpResponseRedirect(reverse('main') + '?' + request.META['QUERY_STRING'])
    cls = SpecialDayForm if isinstance(event, SpecialDay) else OneTimeEventForm
    form = cls(request, instance=event)
    if form.is_valid():
        print form.cleaned_data
        e = form.save()
        e.recreate_occurrences()
        return HttpResponseRedirect(reverse('main') + '?' + request.META['QUERY_STRING'])
    return render(request, 'form.html', locals())


def ical_view(request):
    from icalendar import Calendar, Event, Alarm
    start = date.today().replace(day=1)
    end = start + timedelta(days=365)
    cal = Calendar()
    cal.add('prodid', '-//TogetherCal//%s//HE' % request.META['HTTP_HOST'])
    cal.add('version', '1.0')
    cal['dtstart'] = start
    cal['dtend'] = end
    for occurrence in Occurrence.objects.filter(date__range=(start, end)).iterator():
        e = occurrence.get_event_as_subclass()
        if not isinstance(e, WeeklyActivity):
            event = Event()
            event.add('uid', '%d@%s' % (occurrence.pk, request.META['HTTP_HOST']))
            event.add('summary', e.title)
            event.add('dtstamp', occurrence.date)
            event.add('class', 'PRIVATE')
            event.add('categories', occurrence.event_class_name())
            alarm = Alarm()
            alarm.add('action', 'DISPLAY')
            alarm.add('description', e.title)
            alarm.add('trigger', timedelta(hours=-1))
            event.add_component(alarm)
            cal.add_component(event)
    response = HttpResponse(cal.to_ical(), content_type='text/calendar')
    response['Content-Disposition'] = 'filename="family.ics"'
    return response


@csrf_exempt
@transaction.atomic
def inbound_mail_view(request):
    data       = request.POST or request.GET
    sender     = data['from']
    recipient  = data['to']
    subject    = data['subject']
    text       = data['text']
    parts      = text.split(u' עד ')
    start_date = parts[0]
    end_date   = parts[1] if len(parts) > 1 else None
    form       = InboundMailForm(dict(title=subject, start_date=start_date, end_date=end_date))
    if form.is_valid():
        e = form.save()
        e.create_occurrences()
    msg = render_to_string('inbound_mail_reply.html', dict(form=form))
    if request.GET: # for debugging
        return HttpResponse(msg)
    else:
        send_mail(u'Re: %s' % subject, '', recipient, [sender], html_message=msg, fail_silently=False)
        return HttpResponse('OK')


def _parse(date_str, base=None):
    base = base or datetime.now()
    return dateparser.parse(
        date_str, 
        languages=[settings.LANGUAGE_CODE],
        settings=dict(PREFER_DATES_FROM='future', RETURN_AS_TIMEZONE_AWARE=False, RELATIVE_BASE=base)
    )


class InboundMailForm(forms.ModelForm):

    start_date = forms.CharField(label=u'התחלה', max_length=200)
    end_date = forms.CharField(label=u'סיום', max_length=200, required=False)

    class Meta:
        model = OneTimeEvent
        fields = ('title', 'start_date', 'end_date')

    def _parse_start(self):
        start = self.cleaned_data.get('start_date', '')
        if isinstance(start, datetime):
            return start
        return _parse(start)

    def clean_start_date(self):
        if self.cleaned_data['start_date']:
            start = self._parse_start()
            if not start:
                raise ValidationError(u'לא ניתן לפרש את התאריך או השעה')
            start = start.replace(tzinfo=pytz.UTC)
            return start

    def clean_end_date(self):
        end = self.cleaned_data['end_date']
        if end:
            start = self._parse_start()
            end = _parse(end, start)
            if not end:
                raise ValidationError(u'לא ניתן לפרש את התאריך או השעה')
            end = start.replace(tzinfo=pytz.UTC)
            return end


class OneTimeEventForm(forms.ModelForm):

    heading = 'אירוע חד פעמי'

    start_date = forms.DateField(label=u'תאריך התחלה', widget=forms.SelectDateWidget)
    end_date = forms.DateField(label=u'תאריך סיום', required=False, widget=forms.SelectDateWidget)
    start_time = forms.TimeField(label=u'שעת התחלה (לא חובה)', required=False)
    end_time = forms.TimeField(label=u'שעת סיום (לא חובה)', required=False)
    action = forms.CharField(widget=forms.HiddenInput, required=False)

    class Meta:
        model = OneTimeEvent
        fields = ('title', 'start_date', 'end_date')

    def __init__(self, request, instance=None):
        if instance:
            initial = dict(
                start_date=instance.start_date.strftime(settings.DATE_INPUT_FORMATS[0]),
                end_date=instance.end_date.strftime(settings.DATE_INPUT_FORMATS[0]) if instance.end_date else None,
                start_time=instance.start_date.strftime(settings.TIME_INPUT_FORMATS[0]),
                end_time=instance.end_date.strftime(settings.TIME_INPUT_FORMATS[0]) if instance.end_date else None
            )
        else:
            initial = dict(start_date=request.GET.get('dt'))
        super(OneTimeEventForm, self).__init__(request.POST or None, initial=initial, instance=instance)

    def clean(self):
        cleaned_data = super(OneTimeEventForm, self).clean()
        st = cleaned_data.get('start_time') or time(0, 0)
        if cleaned_data['start_date']:
            start = cleaned_data['start_date']
            cleaned_data['start_date'] = datetime.combine(start, st)
        if cleaned_data['end_date']:
            end = cleaned_data['end_date']
            et = cleaned_data.get('end_time') or st
            cleaned_data['end_date'] = datetime.combine(end, et)


class SpecialDayForm(forms.ModelForm):

    heading = 'תאריך מיוחד'

    action = forms.CharField(widget=forms.HiddenInput, required=False)

    class Meta:
        model = SpecialDay
        fields = ('title', 'month', 'day')

    def __init__(self, request, instance=None):
        dt = _parse(request.GET.get('dt', 'היום'))
        initial = None if instance else dict(month=dt.month, day=dt.day)
        super(SpecialDayForm, self).__init__(request.POST or None, initial=initial, instance=instance)


class WeeklyActivityForm(forms.ModelForm):

    heading = 'פעילות שבועית'

    start_date = forms.DateField(label=u'התחלה', widget=forms.SelectDateWidget)
    end_date = forms.DateField(label=u'סיום', widget=forms.SelectDateWidget)
    action = forms.CharField(widget=forms.HiddenInput, required=False)

    class Meta:
        model = WeeklyActivity
        exclude = ('icon',)

    def __init__(self, request, instance=None):
        dt = _parse(request.GET.get('dt', 'היום'))
        initial = None if instance else dict(
            start_date=date(date.today().year, 9, 1), 
            end_date=date(date.today().year + 1, 8, 31),
            day_of_the_week=dt.weekday()
        )
        super(WeeklyActivityForm, self).__init__(request.POST or None, initial=initial, instance=instance)


FORM_TYPES = dict(
    O = OneTimeEventForm,
    S = SpecialDayForm,
    W = WeeklyActivityForm
)
