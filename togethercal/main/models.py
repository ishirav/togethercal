# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import Q

import datetime
from model_utils.managers import InheritanceManager

from togethercal.icons.models import Icon, icon_for_text


class CalendarEvent(models.Model):

    title = models.CharField(max_length=200)
    icon  = models.ForeignKey(Icon, blank=True, null=True)

    objects = InheritanceManager()

    def __unicode__(self):
        return self.title

    def clean(self):
        if not self.icon:
            self.icon = icon_for_text(self.title)

    def create_occurrences(self, *args, **kwargs):
        raise NotImplementedError


class Holiday(CalendarEvent):

    source_url  = models.URLField('Source URL', blank=True, null=True)
    uid         = models.CharField('UID', max_length=200, blank=True, null=True)
    start_date  = models.DateField()
    end_date    = models.DateField()

    class Meta:
        ordering = ('start_date', 'title')
        unique_together = ('source_url', 'uid')
        verbose_name = u'חג'
        verbose_name_plural = u'חגים'

    def clean(self):
        super(Holiday, self).clean()
        # Check date range validity
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError('Start date cannot be later than end date.')
        # Prevent problems with unique_together when UID is empty
        if self.uid == '':
            self.uid = None

    def create_occurrences(self, *args, **kwargs):
        d = self.start_date
        while d <= self.end_date:
            Occurrence.objects.get_or_create(event=self, date=d)
            d += datetime.timedelta(days=1)


class SpecialDay(CalendarEvent):
    # TODO validate day+month combo

    month   = models.PositiveSmallIntegerField(choices=zip(range(1, 13), range(1, 13)))
    day     = models.PositiveSmallIntegerField(choices=zip(range(1, 32), range(1, 32)))

    class Meta:
        ordering = ('month', 'day')
        verbose_name = u'יום מיוחד'
        verbose_name_plural = u'ימים מיוחדים'

    def create_occurrences(self, *args, **kwargs):
        year = datetime.date.today().year
        for y in range(year, year + 10):
            try:
                d = datetime.date(y, self.month, self.day)
            except ValueError:
                # February 29th changes to 28th
                d = datetime.date(y, self.month, self.day - 1)
            Occurrence.objects.get_or_create(event=self, date=d)


DAYS_OF_THE_WEEK = (
    (6, u'ראשון'),
    (0, u'שני'),
    (1, u'שלישי'),
    (2, u'רביעי'),
    (3, u'חמישי'),
    (4, u'שישי'),
    (5, u'שבת'),
)


class WeeklyActivity(CalendarEvent):

    start_date      = models.DateField()
    end_date        = models.DateField()
    day_of_the_week = models.PositiveSmallIntegerField(choices=DAYS_OF_THE_WEEK)
    start_time      = models.TimeField()
    end_time        = models.TimeField()
    except_holidays = models.BooleanField(default=True)

    class Meta:
        ordering = ('day_of_the_week', 'title')
        verbose_name = u'פעילות שבועית'
        verbose_name_plural = u'פעילויות שבועיות'

    def clean(self):
        super(WeeklyActivity, self).clean()
        # Check date range validity
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError('Start date cannot be later than end date.')

    def create_occurrences(self, *args, **kwargs):
        # Determine which dates to skip (holidays)
        skipped_dates = set()
        if self.except_holidays:
            qs = Occurrence.objects.in_range(self.start_date, self.end_date, Holiday)
            skipped_dates.update(qs.values_list('date', flat=True))
        # Find the first date with the correct weekday
        d = self.start_date
        while d.weekday() != self.day_of_the_week:
            d += datetime.timedelta(days=1)
        # Create one occurrence per week
        while d <= self.end_date:
            if d not in skipped_dates:
                Occurrence.objects.get_or_create(event=self, date=d)
            d += datetime.timedelta(days=7) 


class OneTimeEvent(CalendarEvent):

    start_date  = models.DateTimeField()
    end_date    = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ('start_date', 'title')
        verbose_name = u'אירוע חד פעמי'
        verbose_name_plural = u'אירועים חד פעמיים'

    def clean(self):
        super(OneTimeEvent, self).clean()
        # Check date range validity
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError('Start date cannot be later than end date.')

    def create_occurrences(self, *args, **kwargs):
        d = self.start_date
        while d <= self.end_date:
            Occurrence.objects.get_or_create(event=self, date=d.date())
            d += datetime.timedelta(days=1)


class OccurrenceManager(models.Manager):

    def in_range(self, start_date, end_date, event_class=None):
        qs = self.filter(date__range=(start_date, end_date))
        if event_class:
            qs = qs.filter(event__in=event_class.objects.all())
        return qs


class Occurrence(models.Model):

    event = models.ForeignKey(CalendarEvent)
    date  = models.DateField(db_index=True)

    objects = OccurrenceManager()

    class Meta:
        ordering = ('date',)
        unique_together = ('event', 'date')
        verbose_name = u'היקרות'
        verbose_name_plural = u'היקרויות'

    def __unicode__(self):
        return self.date.isoformat() + ' ' + self.event.title

    def get_event_as_subclass(self):
        return CalendarEvent.objects.get_subclass(pk=self.event_id)

    def event_class_name(self):
        return self.get_event_as_subclass().__class__.__name__
        
    def get_sorting_key(self):
        event = self.get_event_as_subclass()
        if isinstance(event, Holiday):
            return -30
        if isinstance(event, SpecialDay):
            return -20
        if isinstance(event, OneTimeEvent):
            return -10
        return event.start_time.hour * 60 + event.start_time.minute

