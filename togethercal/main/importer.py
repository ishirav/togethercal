import requests
from icalendar import Calendar
from datetime import date, timedelta

from models import Holiday


ONE_DAY = timedelta(days=1)


def import_calendar(url, ignore_past=False):
	r = requests.get(url)
	r.raise_for_status()
	r.encoding = 'UTF-8'
	cal = Calendar.from_ical(r.text)
	for event in cal.walk('vevent'):
		if ignore_past and event.get('dtend').dt < date.today():
			continue
		h, _ = Holiday.objects.update_or_create(
			source_url=url,
			uid=event.get('uid'),
			defaults=dict(
				title=event.get('summary').encode('UTF-8'),
				start_date=event.get('dtstart').dt,
				end_date=event.get('dtend').dt - ONE_DAY
			)
		)
		h.full_clean()
		h.save()
		h.create_occurrences()
