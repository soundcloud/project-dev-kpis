import sys
reload(sys)
sys.setdefaultencoding('utf8')

import os
import json
import time
import argparse

from util import logger
from prometheus_client import start_http_server

import inventory
import project_time_metrics
import project_contributors
import project_composition
import project_issue_transition
from api_server import ApiServer

API_SERVER_PORT = int(os.environ.get('API_SERVER_PORT', '80'))


def configure(configuration_filepath):
    with open(configuration_filepath) as projects_file:
        project_confs = json.load(projects_file)['projects']
    project_synonym_mappings = dict([
        (s, t['project_name'])
        for t in project_confs
        for s in t['project_name_synonyms']
    ])
    assert(project_confs is not None)
    assert(project_synonym_mappings is not {})
    return project_confs, project_synonym_mappings


def schedule(minutes, task, health_check_server):
    while True:
        try:
            tic = time.time()
            task()
            duration = time.time() - tic
            sleep_time = max(60 * minutes - int(duration), 1)
            logger.info("sleeping %d seconds" % sleep_time)
            time.sleep(max(sleep_time, 0))
            health_check_server.observe_health(True)
        except (KeyboardInterrupt, SystemExit) as e:
            raise e
        except Exception as e:
            logger.exception(e)
            health_check_server.observe_health(False)


def main():
    parser = argparse.ArgumentParser(prog='project-dev-kpis', description='Metrics server for project-dev-kpis.')
    parser.add_argument('--projects-config', dest='projects_config', help='projects configuration file')
    args = parser.parse_args(sys.argv[1:])

    project_confs, project_synonym_mappings = configure(args.projects_config)

    def metrics_task():
        for conf in project_confs:
            if conf['transition_parent_issues']:
                project_issue_transition.transition_stories_with_wip_subtasks_to_wip(conf)
                project_issue_transition.transition_epics_with_wip_issues_to_wip(conf)
                project_issue_transition.transition_epics_with_resolved_issues_to_resolved(conf)
            project_time_metrics.monitor_project_time_metrics(conf)
            project_composition.monitor_project_composition(conf)
            project_contributors.monitor_project_contributors(conf)
        inventory.monitor_inventory_metrics(project_synonym_mappings)

    api = ApiServer(
        max_sequential_errors=2,
        confs=project_confs,
        port=API_SERVER_PORT
    )

    try:
        api.start()
        # prometheus server
        start_http_server(8080)
        schedule(minutes=5, task=metrics_task, health_check_server=api)
    except (KeyboardInterrupt, SystemExit) as e:
        api.stop()

if __name__ == "__main__":
    main()
