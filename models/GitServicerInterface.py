
import os
from typing import Type
import pandas as pd
import numpy as np

from models.GitHub import GitHubDataServicer
from models.GitLab import GitLabDataServicer

class GitServicer:
    def __init__(self):
        self.servicers : dict[str:GitHubDataServicer|GitLabDataServicer] = dict()

    def init_git_servicer(self, host, nickname, token) -> bool:
        match host:
            case 'GitHub':
                self.servicers[nickname] = GitHubDataServicer(token)
                return self.ready_for_api_calls(nickname)
            case 'GitLab':
                self.servicers[nickname] = GitLabDataServicer(token)
                return self.ready_for_api_calls(nickname)
            case _:
                return False
    
    def remove_servicer(self, nickname) -> bool:
        if nickname in self.servicers.keys():
            self.servicers.pop(nickname)
        return True
    
    def set_token(self, nickname, token) -> bool:
        servicer : GitHubDataServicer | GitLabDataServicer = self.servicers[nickname]
        return servicer.set_token(token)
    
    def get_token(self, nickname) -> str:
        servicer : GitHubDataServicer | GitLabDataServicer = self.servicers[nickname]
        return servicer.get_token()

    def ready_for_api_calls(self, nickname) -> bool:
        servicer : GitHubDataServicer | GitLabDataServicer = self.servicers[nickname]
        return servicer.ready_for_api_calls()
    
    def get_repos(self, nickname) -> pd.DataFrame:
        servicer : GitHubDataServicer | GitLabDataServicer = self.servicers[nickname]
        repos = servicer.get_repos()
        repos.insert(3, 'site_nickname', nickname)
        return repos
    
    def get_contributors(self, nickname, repo) -> list[str]:
        servicer : GitHubDataServicer | GitLabDataServicer = self.servicers[nickname]
        return servicer.get_contributors(repo)
    
    def import_commit_data(self, nickname, repo, since=None):
        servicer : GitHubDataServicer | GitLabDataServicer = self.servicers[nickname]
        for res, data in servicer.import_commit_data(repo, since):
            yield res, data
