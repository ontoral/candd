import os
import datetime
import pricer


if __name__ == '__main__':
	index_file = 'indexes.txt'

	start_date = datetime.date(2001, 1, 1).toordinal()
	end_date = datetime.date.today().toordinal()

	for day in range(start_date, end_date):
		dt = datetime.date.fromordinal(day)
		if dt.weekday() >= 5:
			continue
		pricer.get_quotes(dt.month, dt.day, dt.year, 'indexes.txt', 'indexes')

