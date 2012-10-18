import os
import datetime
import pricer


if __name__ == '__main__':
    index_file = os.path.join('..', 'indexes.txt')
    price_dir = os.path.join('..', 'indexes')

    start_date = datetime.date(2001, 1, 1).toordinal()
    end_date = datetime.date.today().toordinal()
    end_date = datetime.date(2003, 1, 1).toordinal()

    month = datetime.date.fromordinal(start_date).month
    for day in range(start_date, end_date):
        dt = datetime.date.fromordinal(day)
        if dt.weekday() >= 5:
            # Never download a Saturday or Sunday
            continue
        if dt.weekday() == 4:
            # Skip Friday if it isn't last Friday of the month
            monday = datetime.date.fromordinal(day + 3)
            if dt.month == monday.month:
                continue
        else:
            # Skip a Monday-Thursday if the next day is same month
            tomorrow = datetime.date.fromordinal(day + 1)
            if dt.month == tomorrow.month:
                continue
        pricer.get_quotes(dt.month, dt.day, dt.year, index_file, price_dir)

