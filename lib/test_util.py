import unittest

from util import *
from dateutil.parser import parse as parse_date


class TestUtil(unittest.TestCase):

    def setUp(self):
        pass

    def test_merge_two_dicts(self):
        result = merge_two_dicts({'a': 1}, {'b': 2})
        self.assertEquals(result, {'a': 1, 'b': 2})

    def test_weekdays_between(self):
        noon_friday = parse_date('2017-03-31T12:00:00Z')
        noon_monday = parse_date('2017-04-03T12:00:00Z')
        noon_tuesday = parse_date('2017-04-04T12:00:00Z')
        self.assertEquals(weekdays_between(noon_friday, noon_friday), 0.0)
        self.assertEquals(weekdays_between(noon_friday, noon_monday), 1.0)
        self.assertEquals(weekdays_between(noon_monday, noon_tuesday), 1.0)
        self.assertEquals(
            weekdays_between(parse_date('2017-06-03T00:12:02Z'), parse_date('2017-06-11T00:02:23Z')),
            5.0
        )

    def test_flatten(self):
        self.assertEquals(flatten([[1], [2]]), [1, 2])

    def test_recursive_get(self):
        self.assertEquals(recursive_get(dict([]), ['key']), None)
        self.assertEquals(recursive_get({'a': 1}, ['key']), None)
        self.assertEquals(recursive_get({'key': 1}, ['key']), 1)
        self.assertEquals(recursive_get({'key1': {'key3': 2}}, ['key1', 'key2']), None)
        self.assertEquals(recursive_get({'key1': {'key2': 2}}, ['key1', 'key2']), 2)

    def test_window(self):
        self.assertEquals(list(window([1, 2, 3], 2)), [(1, 2), (2, 3)])

    def test_listify(self):
        self.assertEquals(listify([1, 2, 3]), "\"1\",\"2\",\"3\"")

