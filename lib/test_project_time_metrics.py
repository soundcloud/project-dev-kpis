import unittest
from dateutil.parser import parse as parse_date

from project_time_metrics import calculate_time_metric


class TestProjectTimeMetrics(unittest.TestCase):

    def setUp(self):
        self.changelogs = [
            [
                (u'Created',     parse_date('2017-01-01T00:00:00Z')),
                (u'To Do',       parse_date('2017-01-02T00:00:00Z')),
                (u'In Progress', parse_date('2017-01-03T00:00:00Z')),
                (u'In Review',   parse_date('2017-01-04T00:00:00Z')),
                (u'Resolved',    parse_date('2017-01-07T00:00:00Z'))
            ],
            [
                (u'Created',     parse_date('2017-02-01T00:00:00Z')),
                (u'To Do',       parse_date('2017-02-03T00:00:00Z')),
                (u'In Progress', parse_date('2017-02-05T00:00:00Z')),
                (u'In Review',   parse_date('2017-03-06T00:00:00Z')),
                (u'Resolved',    parse_date('2017-02-09T00:00:00Z'))
            ],
            [
                (u'Created',     parse_date('2017-03-01T00:00:00Z')),
                (u'To Do',       parse_date('2017-03-05T00:00:00Z')),
                (u'In Progress', parse_date('2017-03-07T00:00:00Z')),
                (u'In Review',   parse_date('2017-03-08T00:00:00Z')),
                (u'Resolved',    parse_date('2017-03-11T00:00:00Z'))
            ]
        ]
        self.conf = {
            'planning_workflow_statuses': ['To Do'],
            'wip_workflow_statuses': ['In Progress', 'In Review'],
            'completed_status': 'Resolved'
        }

    def test_calculate_time_metric_lead_time(self):
        self.assertEquals(
            calculate_time_metric(self.conf, 'lead-time', self.changelogs),
            [5.0, 6.0, 8.0]
        )

    def test_calculate_time_metric_cycle_time(self):
        self.assertEquals(
            calculate_time_metric(self.conf, 'cycle-time', self.changelogs),
            [4.0, 3.0, 4.0]
        )

