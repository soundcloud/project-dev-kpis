from company_jira import jira
from util import logger, listify


def transition_to(conf, issue, goal_status):
    start_status = issue.fields.status.name
    transition_statuses = \
        conf['planning_workflow_statuses'] + \
        conf['wip_workflow_statuses'] + \
        [conf['completed_status']]
    transition_statuses = transition_statuses[
        transition_statuses.index(start_status):
        transition_statuses.index(goal_status)+1
    ]
    status = issue.fields.status.name
    current_ind = transition_statuses.index(status)

    while status != goal_status:
        possible_transitions = [
            (t['name'], t['to']['name'])
            for t in jira.transitions(issue)
        ]
        # find the transition that will get us the furthest to the goal
        max_ind = float("-inf")
        selected_transition = None
        selected_status_name = None
        for transition_name, status_name in possible_transitions:
            if status_name in transition_statuses:
                t_ind = transition_statuses.index(status_name)
                if t_ind > max_ind:
                    max_ind = t_ind
                    selected_transition = transition_name
                    selected_status_name = status_name
        # break if we're not getting anywhere
        if max_ind < current_ind:
            logger.error("Could not find transition for issue %s to status %s!" % (issue.key, goal_status))
            break
        # perform that transition
        jira.transition_issue(issue, selected_transition)
        logger.info(
            'Requested transition %s %s to "%s" via "%s"' % (
                issue.fields.issuetype.name,
                issue.key,
                selected_status_name,
                selected_transition
            )
        )
        # update status and ind
        issue = jira.issue(issue.key)
        # break if the transition failed
        if issue.fields.status.name == status:
            logger.error("Transition failed for issue %s to status %s!" % (issue.key, selected_status_name))
            break
        status = issue.fields.status.name
        current_ind = transition_statuses.index(status)


def transition_stories_with_wip_subtasks_to_wip(conf):
    stories = jira.search_issues(
        """
        project = "%s" and
        issuetype = "Story" and
        status in (%s)
        """ % (
            conf['project_id'],
            listify(conf['planning_workflow_statuses'])
        )
    )
    for story in stories:
        subtask_statuses = set(
                [sub.fields.status.name for sub in story.fields.subtasks]
        )
        if subtask_statuses & set(conf['wip_workflow_statuses']):
            transition_to(conf, story, u'In Progress')


def transition_epics_with_wip_issues_to_wip(conf):
    epics = jira.search_issues(
        """
        project = "%s" and
        issuetype = "Epic" and
        status in (%s) and
        labels not in ("container")
        """ % (
            conf['project_id'],
            listify(conf['planning_workflow_statuses'])
        )
    )
    for epic in epics:
        subissues = jira.search_issues(
            'project = "%s" and "Epic Link" = "%s"' % (
                conf['project_id'],
                epic.key
            )
        )
        subissue_statuses = set([
            sub.fields.status.name
            for sub in (subissues + epic.fields.subtasks)
        ])
        if subissue_statuses and \
           subissue_statuses & set(conf['wip_workflow_statuses']):
            transition_to(conf, epic, u'In Progress')


def transition_epics_with_resolved_issues_to_resolved(conf):
    epics = jira.search_issues(
        """
        project = "%s" and
        issuetype = "Epic" and
        status in (%s)
        """ % (
            conf['project_id'],
            listify(
                conf['planning_workflow_statuses'] +
                conf['wip_workflow_statuses']
            )
        )
    )
    for epic in epics:
        subissues = jira.search_issues(
            '"Epic Link" = "%s"' % epic.key
        )
        subissue_statuses = set([
            sub.fields.status.name
            for sub in (subissues + epic.fields.subtasks)
        ])
        if subissue_statuses and \
           len(subissue_statuses & set(
                conf['planning_workflow_statuses'] +
                conf['wip_workflow_statuses']
           )) == 0:
            transition_to(conf, epic, conf['completed_status'])
