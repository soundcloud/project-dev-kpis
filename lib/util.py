import logging
import sys
import time
import urllib
import json
from itertools import islice

from dateutil.rrule import *
from datetime import tzinfo, timedelta, datetime
from dateutil.parser import parse as parse_date
from dateutil import tz
import pytz
import re

##
# logging
#
logging.Formatter.converter = time.gmtime
logging.basicConfig(
        stream=sys.stdout,
        format='%(asctime)s %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%SZ',
        level=logging.INFO
)

logger = logging.getLogger()


##
# language
#
def merge_two_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z


def flatten(l):
    return [item for sublist in l for item in sublist]


def recursive_get(d, keys):
    if len(keys) > 0 and d is not None:
        next = keys[0]
        rest = keys[1:]
        return recursive_get(d[next], rest) if next in d else None
    else:
        return d


def json_pprint(js):
    print(json.dumps(js, sort_keys=True, indent=4, separators=(',', ': ')))


def window(seq, n):
    """
    Returns a sliding window (of width n) over data from the iterable
    s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...
    """
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result


##
# time
#
local_tz = pytz.timezone('UTC')


def to_utc(d):
    if d.tzinfo is not None and d.tzinfo.utcoffset(d) == timedelta(0):
        dutc = d
    elif d.tzinfo is None:
        dutc = local_tz.localize(d)
    else:
        dutc = d.astimezone(tz.gettz('UTC'))
    return dutc


def to_epoch(dt):
    return (
        to_utc(dt) - parse_date('1970-01-01T00:00:00Z')
    ).total_seconds()


def closest_biz_day(dt, forward=True):
    adjust = -1 * timedelta(seconds=to_epoch(dt) % 86400)
    if forward:
        delta = timedelta(days=1)
    else:
        delta = timedelta(days=-1)
    new_dt = dt
    while new_dt.weekday() in [5, 6]:
        new_dt = new_dt + delta
    if new_dt != dt:
        return new_dt + adjust
    else:
        return new_dt


def weekdays_between(d1, d2):
    seconds_in_a_day = 86400

    if d1 > d2:
        return weekdays_between(d2, d1)
    start = closest_biz_day(d1)
    end = closest_biz_day(d2)

    num_weekend_days = rrule(
            WEEKLY,
            byweekday=(SA, SU),
            dtstart=start,
            until=end
    ).count()
    return (
               (end - start).total_seconds() -
               num_weekend_days * seconds_in_a_day
           ) / float(seconds_in_a_day)


##
# format
#
def percent_encode(s):
    return urllib.quote(str(s), safe='')


def listify(lst):
    return ','.join(['"' + str(s) + '"' for s in lst])

