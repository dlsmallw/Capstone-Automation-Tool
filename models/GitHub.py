from github import Auth, Github
from github.AuthenticatedUser import AuthenticatedUser
from github.NamedUser import NamedUser
from github.Repository import Repository

import pandas as pd
import numpy as np
import requests
import datetime
import pytz
import re

class GitHubDataServicer:
    def __init__(self, token=None):
        self.base_url = "https://api.github.com"
        self.token = None
        self.gh_auth : Auth = None
        self.gh : Github = None
        self.user : AuthenticatedUser | NamedUser = None
        self.auth_and_gh_set = False

        if token: 
            self.set_token(token)
            
    def _init_obj(self):
        self.gh_auth = Auth.Token(self.token)
        self.gh = Github(auth=self.gh_auth)
        self.user = self.gh.get_user()

    def set_token(self, token) -> bool:
        self.token = token

        if self.token:
            try:
                self._init_obj()
                self.auth_and_gh_set = True
            except:
                self.auth_and_gh_set = False
        return self.auth_and_gh_set
    
    def get_token(self) -> str:
        return self.token
    
    def ready_for_api_calls(self) -> bool:
        return self.auth_and_gh_set
    
    def get_repos(self) -> pd.DataFrame:
        repo_list = []
        for repo in self.user.get_repos():
            repo_list.append({ 
                'id': repo.id,
                'repo_name': repo.name, 
                'owner_name': repo.raw_data['owner']['login'],
                'is_linked': False,
                'last_commit_dt': None
            })
        repos = pd.json_normalize(repo_list)
        return repos
    
    def is_auth_user(self) -> bool:
        return isinstance(self.user, AuthenticatedUser) if self.user else False

    def _get_repo_branches(self, repo : Repository) -> dict[str:str]:
        branch_dict = dict()
        if repo:
            for branch in repo.get_branches():
                branch_name = branch.name
                branch_sha = branch.commit.sha

                if branch_name and branch_sha:
                    branch_dict[branch_name] = branch_sha

        return branch_dict

    def get_repo_by_name(self, repo_name):
        for repo in self.user.get_repos():
            if repo.name == repo_name:
                return repo
    
    def get_contributors(self, repo_name) -> list[str]:
        repo = self.get_repo_by_name(repo_name)
        return self._get_contributors(repo)
    
    def _get_contributors(self, repo : Repository) -> list[str]:
        contributor_list = []
        if repo:
            contributors = repo.get_contributors()
            if contributors.totalCount > 0:
                for contributor in contributors:
                    contributor_list.append(contributor.login)    
        return contributor_list
    
    def _get_commit_author(self, contributors, commit) -> str | None:
        author_name = commit["author"]["login"]
        author_email = commit["commit"]["author"]["email"]

        committer = None
        if author_name and author_name != 'unknown':
            if author_name in contributors:
                committer = author_name
        else:
            if author_email and author_email != 'unknown':
                suspected_name = author_email[0:author_email.index('@')]

                if suspected_name in contributors:
                    committer = suspected_name
        return committer
    
    def _inv_val_format(self, df: pd.DataFrame):
        df = df.replace(['', 'None', 'nan', 'NaN', np.nan, None], pd.NA)

    def _format_commit_data(self, df : pd.DataFrame) -> pd.DataFrame:
        return df
    
    def _get_auth_header(self) -> dict[str:str]:
        return {
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {self.token}',
            'X-GitHub-Api-Version': '2022-11-28'
        }
    
    def _make_api_call(self, header, url) -> requests.Response:
        return requests.get(url, headers=header)
    
    def import_commit_data(self, repo, since=None):
        auth_header = self._get_auth_header()
        
        {
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {self.token}',
            'X-GitHub-Api-Version': '2022-11-28'
        }
    
        repo_obj = self.get_repo_by_name(repo)

        contributors = self._get_contributors(repo_obj)
        branch_dict = self._get_repo_branches(repo_obj)

        base_url = repo_obj.url
        all_data = pd.DataFrame(data=[], columns=['id', 'repo_name', 'task_num', 'committer', 'az_date', 'utc_datetime', 'commit_message', 'commit_url'])
        commit_ids = []

        since_param = f'since={since}&' if since is not None else ''

        for branch in branch_dict.keys():
            yield 'In Progress', branch

            url = f'{base_url}/commits?{since_param}per_page=100&sha={branch_dict[branch]}'

            pagesRemaining = True
            commits = []
            next_url = url

            while pagesRemaining:
                res = self._make_api_call(header=auth_header, url=next_url)
                pattern = r'task[^a-zA-Z\d\s]?\d+'

                for commit_entry in res.json():
                    id = commit_entry['sha']    # Used for identifying and filtering commits
                    if id not in commit_ids:
                        url = commit_entry['html_url']
                        commit_obj = commit_entry["commit"]
                        committer = self._get_commit_author(contributors, commit_entry) # Author Details used to assign the commit
                        commit_msg = commit_obj['message']  # Commit date and title
                        match = re.search(pattern, commit_msg, re.IGNORECASE)
                        task_num = int(re.search(r'\d+', match.group()).group()) if match else None
                    
                        # Takes the commit timezone (UTC) and converts to AZ timezone
                        utc_dt = pd.to_datetime(commit_obj['committer']['date'], format='%Y-%m-%dT%H:%M:%SZ', utc=True)
                        az_dt = utc_dt.astimezone(pytz.timezone('US/Arizona'))
                        
                        commits.append({
                            "id": id,
                            "repo_name": repo,
                            "host_site": "GitHub",
                            "task_num": task_num,
                            "committer": committer,
                            "az_date": az_dt.strftime('%m/%d/%Y'),
                            "utc_datetime": utc_dt,
                            "commit_message": commit_msg,
                            "commit_url": url
                        })

                try:
                    next_url = res.links.get('next').get('url')
                except:
                    pagesRemaining = False
            
            branch_commits = pd.json_normalize(commits)

            if branch_commits is not None and len(branch_commits) > 0:
                if all_data is None or len(all_data) < 1:
                    all_data = branch_commits
                else:
                    all_data = pd.concat([all_data, branch_commits]).drop_duplicates(subset='id', keep='first')
                    
        yield 'Complete', self._format_commit_data(all_data)