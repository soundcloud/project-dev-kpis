import os
from jira import JIRA

JIRA_API_SERVER = os.getenv('JIRA_API_SERVER')
JIRA_API_USER = os.getenv('JIRA_API_USER')
JIRA_API_PASSWORD = os.getenv('JIRA_API_PASSWORD')

jira = JIRA(
    server=JIRA_API_SERVER,
    basic_auth=(JIRA_API_USER, JIRA_API_PASSWORD)
) if JIRA_API_SERVER != 'https://localhost/' else None
