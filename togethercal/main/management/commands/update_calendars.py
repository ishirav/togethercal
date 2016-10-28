from django.core.management.base import BaseCommand, CommandError

from infi.django_holiday_calendar.importer import import_calendar
from infi.django_holiday_calendar.models import HolidayCalendar

import logging


class Command(BaseCommand):

    help = 'Updates all existing holiday calendars that have a source url'

    def add_arguments(self, parser):
        parser.add_argument('--ignore-past', action='store_true', default=False, help='Do not import past holidays')

    def handle(self, *args, **options):
        for hc in HolidayCalendar.objects.exclude(source_url=None):
            logging.info("Updating %s (%s)" % (hc, hc.source_url))
            try:
                import_calendar(hc.source_url, hc.country, options['ignore_past'])
            except:
                logging.exception("Failed updating %s (%s)" % (hc, hc.source_url))
