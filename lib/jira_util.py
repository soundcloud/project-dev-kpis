from dateutil.parser import parse as parse_date
from util import flatten


def flatten_issue(get_issue, issue, expand_subtasks=False):
    """
    story is broken down into subtasks
    """
    issues = [issue]
    if is_parent_issue(issue):
        if expand_subtasks:
            issues += [
                get_issue(s.key, expand='changelog')
                for s in issue.fields.subtasks
            ]
        else:
            issues += issue.fields.subtasks
    return issues


def is_parent_issue(issue):
    return issue.fields.issuetype.name == 'Epic' or (
        len(issue.fields.subtasks) > 0
    )


def issue_to_changelog(issue):
    return dict(
        [
            ('key', issue.key),
            (
                'changelog',
                [
                    (u'Created', parse_date(issue.fields.created))
                ] + flatten([
                    [
                        (i.toString, parse_date(h.created))
                        for i in h.items if i.field == 'status'
                    ] for h in issue.changelog.histories
                ])
            )
        ]
    )


def get_or_else(log, get_by_priority):
    if len(get_by_priority) > 0:
        in_progress = next(
                (t[1] for t in log if t[0] == get_by_priority[0]),
                None
        )
        if in_progress is None:
            return get_or_else(log, get_by_priority[1:])
        else:
            return in_progress
    else:
        return None
