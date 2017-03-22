from collections import Counter
from prometheus_client import Gauge

from jira_util import *
from company_jira import jira
from util import listify, logger

PROJECT_UNRESOLVED_ISSUES = Gauge(
    'project_unresolved_issues',
    'Number of issues in the project by type.',
    ['project', 'issue_type', 'status', 'status_ordinal', 'wip', 'parent', 'product_granularity']
)


def monitor_project_composition(conf):
    """
    issuetype and status composition
    """
    statuses = conf['planning_workflow_statuses'] + conf['wip_workflow_statuses']
    status_ordinal_map = dict(
        zip(
            statuses,
            [chr(i) for i in reversed(range(ord('z') - len(statuses) + 1, ord('z') + 1))]
        )
    )
    issues = jira.search_issues(
        'project = "%s" and status in (%s)' % (
            conf['project_id'],
            listify(statuses)
        ),
        maxResults=500
    )
    issue_type_status_counts = Counter([
        (
            i.fields.issuetype.name,
            i.fields.status.name,
            is_parent_issue(i)
        ) for i in issues if i.fields.status.name in statuses
    ])
    for (issue_type, status, is_parent), count in issue_type_status_counts.iteritems():
        PROJECT_UNRESOLVED_ISSUES.labels(
                conf['project_name'],
                issue_type,
                status,
                status_ordinal_map[status] + '_' + status.replace(' ', '_').lower(),
                str(status in conf['wip_workflow_statuses']),
                is_parent,
                conf['product_granularity'] == issue_type
        ).set(count)
        logger.info('Observed for %s (%s), number of %s %s issues in status "%s": %d' % (
            conf['project_name'],
            conf['project_id'],
            'parent' if is_parent else 'child',
            issue_type,
            status,
            count
        ))
