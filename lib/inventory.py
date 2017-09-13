import datetime
import time
import json
import os
from retrying import retry
from github import Github, GithubException
from prometheus_client import Gauge, Histogram

from util import *

GITHUB_ACCESS_TOKENS = os.getenv('GITHUB_ACCESS_TOKENS').split(',')

GITHUB_ACCESS_TOKENS_SELECTOR = 0

CODE_INVENTORY = Gauge(
    'code_inventory', 'Amount of unmerged work in a repository.',
    ['owner', 'repo', 'metric']
)

FEATURES = Gauge(
    'features',
    'Counts of features in org repositories, based on number of manifest files.',
    ['owner', 'repo']
)

CODE_INVENTORY_AGE = Histogram(
    'code_inventory_age',
    'Code inventory age in days.',
    ['owner', 'repo'],
    buckets=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20, 25, 30, 35, 40, 50, 60, 70, 80, 90,
        100, 150, 200, 250, 300, 365, float("inf")]
)

REPO_SCRAPE_TIMES = {}


def get_access_token():
    global GITHUB_ACCESS_TOKENS_SELECTOR
    token = GITHUB_ACCESS_TOKENS[GITHUB_ACCESS_TOKENS_SELECTOR % 2]
    GITHUB_ACCESS_TOKENS_SELECTOR += 1
    return token


def observe_inventory(owner, repo_name, pulls):
    for metric in ['additions', 'commits', 'deletions']:
        metric_sum = None
        if len(pulls) > 0:
            metric_sum = sum([getattr(p, metric) for p in pulls])
        else:
            metric_sum = 0

        logger.info(
            'Observed for owner "%s", repo "%s", %d %s' % (owner, repo_name, metric_sum, metric))

        CODE_INVENTORY.labels(owner, repo_name, metric).set(metric_sum)

    for pull in pulls:
        days_old = weekdays_between(pull.created_at, datetime.now())
        logger.info(
            'Observed for owner "%s", repo "%s", %.2f days old PR' % (owner, repo_name, days_old))
        CODE_INVENTORY_AGE.labels(owner, repo_name).observe(days_old)


def observe_features(owner, repo_name, manifests):
    FEATURES.labels(owner, repo_name).set(len(manifests))


def get_owner(synonyms, repo):
    try:
        raw_owner = json.loads(repo.get_contents('/manifest.json').decoded_content)['owner']
        return synonyms[raw_owner] if raw_owner in synonyms else raw_owner
    except Exception as e:
        return None


@retry(wait_fixed=5000, stop_max_attempt_number=2)
def monitor_inventory_metrics(synonym_mappings):
    global REPO_SCRAPE_TIMES

    minus_three_months = (datetime.now() - timedelta(3 * 365 / 12)).isoformat().split('.')[0]

    git = Github(get_access_token())

    for repo in git.search_repositories('org:soundcloud pushed:>' + minus_three_months):
        owner = get_owner(synonym_mappings, repo)

        REPO_SCRAPE_TIMES[(owner, repo.name)] = time.time()

        pulls = list(repo.get_pulls())

        observe_inventory(owner, repo.name, pulls)

        manifests = [None]

        try:
            manifests = list(git.search_code(
                'repo:soundcloud/%s language:json filename:*manifest*.json' % repo.name))
        except GithubException:
            logger.error('Could not search repo %s!' % repo.name)

        observe_features(owner, repo.name, manifests)

    # zero-out deleted repos
    dead_repos = {tup: last_time for tup, last_time in REPO_SCRAPE_TIMES.iteritems() if
                  last_time < time.time() - 60 * 60}

    for owner, repo_name in dead_repos.keys():
        del REPO_SCRAPE_TIMES[(owner, repo_name)]
        observe_inventory(owner, repo_name, [])
