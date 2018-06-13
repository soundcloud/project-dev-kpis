import os

from flask import Flask, request
from company_jira import jira
from multiprocessing import Process
from gevent.pywsgi import WSGIServer
import project_issue_transition
import shlex
import requests
import threading

JIRA_CONTROL_SECRET = os.environ.get('JIRA_CONTROL_SECRET')
JIRA_CONTROL_PATH = os.environ.get('JIRA_CONTROL_PATH')
JIRA_API_SERVER = os.getenv('JIRA_API_SERVER')

flask_app = Flask(__name__)

help_message = '\n'.join([
    'jira-ctl help:',
    '\t`/jira-ctl help`',
    '\t`/jira-ctl create-issue <project_id> <assignee_username> "<issue_type>" "<summary>" "<description>"`',
    '\t`/jira-ctl transition-issue <issue_key> "<goal_status>"`',
    '\t`/jira-ctl delete-issue <issue_key>`',
    '\t`/jira-ctl assigned-issues <assignee_username>`',
    'examples (don\'t run these):',
    '\t`/jira-ctl create-issue PDK weiden "Story" "This is the summary" "This is the description"`',
    '\t`/jira-ctl transition-issue PDK-40 "In Progress"`',
    '\t`/jira-ctl delete-issue PDK-40`',
    '\t`/jira-ctl assigned-issues weiden`'
])


def parse_command(command_str):
    try:
        return shlex.split(command_str)
    except:
        return None


def create_issue(parsed_params):
    issue = None
    try:
        _, project, assignee, issue_type, summary, description = parsed_params
        issue = jira.create_issue(
            project=project,
            summary=summary,
            description=description.decode('string_escape'),
            issuetype={'name': issue_type},
        )
        jira.assign_issue(issue, assignee)
        return issue
    except Exception as e:
        if issue is not None:
            issue.delete()
        raise e


def transition_issue(parsed_params, conf_map):
    _, issue_key, status = parsed_params
    project = issue_key.split('-')[0]
    issue = jira.issue(issue_key)
    project_issue_transition.transition_to(
        conf=conf_map[project],
        issue=issue,
        goal_status=status
    )
    return issue, status


def delete_issue(parsed_params):
    _, issue_key = parsed_params
    issue = jira.issue(issue_key)
    issue.delete()
    return issue


def assigned_issues(parsed_params):
    _, assignee_username = parsed_params
    issues = jira.search_issues("""
        assignee = %s and statusCategory in ("To Do", "In Progress")
    """ % assignee_username)
    return issues


def render_issue(issue):
    issue_browse_url = JIRA_API_SERVER + '/browse'
    return '<%s/%s|%s> (%s) %s' % (
        issue_browse_url,
        issue.key,
        issue.key,
        issue.fields.status.name,
        "" if issue.fields.summary is None else issue.fields.summary
    )


class AsyncHttpCallback(threading.Thread):

    def __init__(self, task, url):
        super(AsyncHttpCallback, self).__init__()
        self.task = task
        self.url = url

    def run(self):
        try:
            result_text = self.task()
            requests.post(self.url, json={'text': result_text})
        except Exception as e:
            requests.post(self.url, json={'text': str(e)})


@flask_app.route('/-/health', methods=['GET', 'HEAD'])
def check_health():
    return (
        'OK' if ApiServer.healthy else 'NOT OK',
        200 if ApiServer.healthy else 500
    )


@flask_app.route('/' + JIRA_CONTROL_PATH, methods=['POST'])
def jira_ctl():
    actions = ['create-issue', 'transition-issue', 'delete-issue', 'assigned-issues']
    if request.args.get('secret') == JIRA_CONTROL_SECRET:
        try:
            command = parse_command(request.form['text'])

            if command is None or len(command) == 0 or command[0] == 'help':
                return help_message, 200
            elif command[0] not in actions:
                return 'Not a valid action, choose from ' + str(actions), 200

            def task():
                if command[0] == 'create-issue':
                    issue = create_issue(command)
                    return 'Created ' + render_issue(issue)
                elif command[0] == 'transition-issue':
                    issue, status = transition_issue(command, ApiServer.conf_map)
                    return 'Transitioned to "' + status + '": ' + render_issue(issue)
                elif command[0] == 'delete-issue':
                    issue = delete_issue(command)
                    return 'Deleted ' + issue.key
                elif command[0] == 'assigned-issues':
                    issues = sorted(assigned_issues(command), key=lambda i: i.fields.status.name)
                    return 'Issues:\n' + '\n'.join(['\t' + render_issue(i) for i in issues])

            AsyncHttpCallback(task, request.form['response_url']).start()

            return 'Accepted', 202
        except Exception as e:
            flask_app.logger.error('Error! ' + str(e))
            return 'Bad request', 400
    else:
        return 'Not authorized', 401


class ApiServer:

    healthy = True
    conf_map = {}

    def __init__(self, confs, max_sequential_errors, port):
        self.max_sequential_errors = max_sequential_errors
        self.sequential_errors = 0
        self.server = WSGIServer(('0.0.0.0', port), flask_app)
        self.server_proc = Process(target=lambda: self._serve())
        ApiServer.conf_map = dict([(c['project_id'], c) for c in confs])

    def start(self):
        self.server_proc.start()

    def _serve(self):
        try:
            self.server.serve_forever()
        except (KeyboardInterrupt, SystemExit) as e:
            self.server.stop()

    def stop(self):
        self.server_proc.terminate()
        self.server_proc.join()

    def observe_health(self, success):
        if success is True:
            self.sequential_errors = 0
        else:
            self.sequential_errors += 1

        if self.sequential_errors > self.max_sequential_errors:
            self.healthy = False
        else:
            self.healthy = True

