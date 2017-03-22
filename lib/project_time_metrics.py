from dateutil.rrule import *
from prometheus_client import Histogram

from company_jira import jira
from util import *
from jira_util import *


PROJECT_TIME_HISTOGRAM = Histogram(
    'project_time_days',
    'Lead time in days.',
    ['project', 'metric'],
    buckets=[
        0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18,
        20, 25, 30, 35, 40, 50, 60, 70, 80, 90, 100, 365, float("inf")
    ]
)


def get_recent_changelogs(conf, num_issues, all_issues=False):
    last_issues = jira.search_issues(
         """project = "%s" and %s
            status in ("Resolved", "Done", "Closed")
            order by updatedDate DESC""" % (
             conf['project_id'],
             "" if all_issues else "issuetype = \"%s\" and" % conf['product_granularity']
         ),
         expand='changelog',
         maxResults=num_issues
    )
    return [
        issue_to_changelog(issue)['changelog']
        for issue in last_issues
    ]


def calculate_time_metric(conf, metric_name, changelogs):
    delta_days = None

    rev_statuses_until_start = [conf['wip_workflow_statuses'][0]] + list(
        reversed(conf['planning_workflow_statuses'])
    ) + ['Created']

    if metric_name == 'lead-time':
        delta_days = [
            weekdays_between(
                    get_or_else(changelog, ['Created']),
                    get_or_else(changelog, ['Resolved', 'Done', 'Closed'])
            ) for changelog in changelogs
        ]
    elif metric_name == 'cycle-time':
        delta_days = [
            weekdays_between(
                    get_or_else(changelog, rev_statuses_until_start),
                    get_or_else(changelog, ['Resolved', 'Done', 'Closed'])
            ) for changelog in changelogs
        ]
    return delta_days


def observe_metric(project_name, project_id, metric, value):
    PROJECT_TIME_HISTOGRAM.labels(
            project_name,
            metric
    ).observe(value)

    logger.info('Observed for %s (%s), metric %s: %.02f days' % (
        project_name,
        project_id,
        metric,
        value
    ))


def monitor_project_time_metrics(conf):
    recent_changelogs = get_recent_changelogs(conf, 5)
    delta_days = calculate_time_metric(conf, 'lead-time', recent_changelogs)
    for delta in delta_days:
        observe_metric(
            conf['project_name'],
            conf['project_id'],
            'lead-time',
            delta
        )
    delta_days = calculate_time_metric(conf, 'cycle-time', recent_changelogs)
    for delta in delta_days:
        observe_metric(
            conf['project_name'],
            conf['project_id'],
            'cycle-time',
            delta
        )
