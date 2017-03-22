import unittest
from mock import Mock, MagicMock

from jira_util import *


class TestJiraUtil(unittest.TestCase):

    def setUp(self):
        pass

    def test_flatten_issue_no_expand(self):
        get_issue = Mock()
        issue = Mock()
        issue.fields = Mock()
        issue.fields.subtasks = ['issue2', 'issue3']
        self.assertEquals(
            flatten_issue(get_issue, issue),
            [issue, 'issue2', 'issue3']
        )
        get_issue.assert_not_called()

    def test_flatten_issue_with_expand(self):
        issue = Mock()
        issue.fields = Mock()
        issue1 = Mock()
        issue1.key = 'issue1'
        issue.fields.subtasks = [issue1]
        get_issue = Mock(return_value='expanded_issue1')
        self.assertEquals(
            flatten_issue(get_issue, issue, expand_subtasks=True),
            [issue, 'expanded_issue1']
        )
        get_issue.assert_called_with('issue1', expand='changelog')

    def test_is_parent_issue(self):
        issue = Mock()
        issue.fields = MagicMock()
        issue.fields.issuetype = Mock()
        issue.fields.issuetype.name = 'Epic'
        self.assertTrue(is_parent_issue(issue))
        issue.fields.issuetype.name = 'Story'
        self.assertFalse(is_parent_issue(issue))
        issue.fields.subtasks = [1, 2, 3]
        self.assertTrue(is_parent_issue(issue))

    def test_issue_to_changelog(self):
        issue = Mock()
        issue.key = 'some key'
        issue.fields = Mock()
        issue.fields.created = '1986-07-21T00:00:00Z'

        issue.changelog = Mock()

        item1 = Mock()
        item1.field = 'status'
        item1.toString = 'To Do'
        history1 = Mock()
        history1.created = '2017-01-01T00:00:00Z'
        history1.items = [item1]

        item2 = Mock()
        item2.field = 'something else'
        item3 = Mock()
        item3.field = 'status'
        item3.toString = 'In Progress'
        history2 = Mock()
        history2.created = '2017-02-02T00:00:00Z'
        history2.items = [item2, item3]

        issue.changelog.histories = [history1, history2]
        self.assertEquals(
            issue_to_changelog(issue),
            {
                'key': 'some key',
                'changelog': [
                    (u'Created', parse_date('1986-07-21T00:00:00Z')),
                    (u'To Do', parse_date('2017-01-01T00:00:00Z')),
                    (u'In Progress', parse_date('2017-02-02T00:00:00Z'))
                ]
            }
        )

    def test_get_or_else(self):
        changelog = [
            (u'Created', parse_date('1986-07-21T00:00:00Z')),
            (u'To Do', parse_date('2017-01-01T00:00:00Z')),
            (u'In Progress', parse_date('2017-02-02T00:00:00Z'))
        ]
        self.assertEquals(
            get_or_else(changelog, ['Groomed']),
            None
        )
        self.assertEquals(
                get_or_else(changelog, ['Groomed', 'To Do']),
                parse_date('2017-01-01T00:00:00Z')
        )

