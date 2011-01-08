from datetime import timedelta, date

from django.http import Http404

ONE_DAY = timedelta(days=1)
ONE_WEEK = timedelta(days=7)

SECONDS_PER_DAY = 24 * 60 * 60

def timedelta_seconds(delta):
    return delta.seconds + SECONDS_PER_DAY * delta.days

def timedelta_div(a, b):
    return timedelta_seconds(a) / float(timedelta_seconds(b))

def get_first_day_of_week():
    return 0

def get_week_number(dt):
    fdow = get_first_day_of_week()
    if fdow == 1:
        format = "%U"
    elif fdow == 0:
        format = "%W"
    return int(dt.strftime(format))
    
def get_date(obj):
    if isinstance(obj, date):
        return obj
    elif hasattr(obj, 'date'):
        return obj.date()
    else:
        raise ValueError

def get_week_range(dt):
    first_day = get_date(dt) - timedelta(days=dt.weekday())
    last_day = first_day + ONE_WEEK
    return first_day, last_day

def get_month_range(dt):
    first_day = date(dt.year, dt.month, 1)
    last_day = (first_day + timedelta(days=32)).replace(day=1) - ONE_DAY
    return first_day, last_day

def get_date_or_404(year, month, day):
    try:
        year = int(year)
        month = int(month)
        day = int(day)
        return date(year, month, day)
    except ValueError:
        raise Http404
    
    