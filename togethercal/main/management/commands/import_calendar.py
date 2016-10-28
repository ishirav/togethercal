from django.core.management.base import BaseCommand, CommandError

from togethercal.main.importer import import_calendar


class Command(BaseCommand):

    help = 'Imports holidays from an ical url'

    def add_arguments(self, parser):
        parser.add_argument('url', help='URL of the ical file to import')
        parser.add_argument('--ignore-past', action='store_true', default=False, help='Do not import past holidays')

    def handle(self, *args, **options):
        import_calendar(options['url'], options['ignore_past'])
