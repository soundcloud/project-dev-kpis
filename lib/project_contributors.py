from prometheus_client import Gauge

from jira_util import *
from company_jira import jira
from util import *


PROJECT_CONTRIBUTORS = Gauge(
    'project_contributors',
    'Number of contributors to the project currently active.',
    ['project']
)


def monitor_project_contributors(conf):
    """
    number of contributors
    """
    issues = jira.search_issues(
        """
        project = "%s"
        and (
            status in (%s)
            or (status = %s and updatedDate >= "-3d")
        )
        """ % (
            conf['project_id'],
            listify(conf['wip_workflow_statuses']),
            conf['completed_status'],
        ),
        maxResults=500
    )
    unique_contributors = set([
        i.fields.assignee.key
        for i in issues
        if i.fields.assignee is not None
        and i.fields.assignee.key is not None
        and i.fields.assignee.key != conf['project_name']
        and i.fields.assignee.key not in conf['project_name_synonyms']
    ])
    PROJECT_CONTRIBUTORS.labels(
            conf['project_name']
    ).set(len(unique_contributors))
    logger.info('Observed for %s (%s), contributors: %s' % (
        conf['project_name'],
        conf['project_id'],
        '[' + ', '.join(['"' + c + '"' for c in unique_contributors]) + ']'
    ))
