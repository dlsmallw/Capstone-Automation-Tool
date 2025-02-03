from typing import Type
from github import Auth, Github, Repository, Branch, Commit
import pandas as pd
import numpy as np
import requests
import datetime
import pytz
import re

class GitHubDataServicer:
    def __init__(self, token=None):
        self.base_url = "https://api.github.com"
        self.gh : Github  = None
        self.gh_auth : Auth = None

        self.token = None
        self.token_verified = False

        if token and self.set_token(token):
            self.init_github_obj()
            
    def init_github_obj(self):
        self.gh_auth = Auth.Token(self.token)
        self.gh = Github(auth=self.gh_auth)

    def set_token(self, token):
        self.token = token
        return self.validate_auth()

    def validate_auth(self):
        if self.token:
            try:
                res = self._make_gh_api_call(f'{self.base_url}/user')
                self.token_verified = res.status_code >= 200 and res.status_code < 300
            except Exception as e:
                print(e)
        return self.token_verified
    
    def auth_validated(self):
        return self.token_verified
    
    def get_repo_list(self):
        pass
    
    def _inv_val_format(self, df: Type[pd.DataFrame]):
        df.replace(['', 'None', 'nan', 'NaN', np.nan, None], pd.NA, inplace=True)
    
    def _get_auth_header(self):
        return {
            'Authorization': f'token {self.token}' 
        }
    
    def _make_gh_api_call(self, url):
        header = self._get_auth_header()
        return requests.get(url, headers=header)
    
    def _parse_repo_branches(self) -> dict:
        owner = self.repo_owner
        repo = self.repo
        url = f'{self.base_url}/repos/{owner}/{repo}/branches?per_page=100'
        return self.__get_paginated_branch_data(url)
    
    def __parse_repo_contributors(self) -> list:
        owner = self.repo_owner
        repo = self.repo
        url = f'{self.base_url}/repos/{owner}/{repo}/contributors'

        res = self._make_gh_api_call(url).json()
        contrbutor_df = pd.json_normalize(res)['login']
        contributors = contrbutor_df.tolist()
        contributors.append('Unknown')
        return contributors
    
    def __get_commit_author(self, contributors, commit):
        author_name = commit["author"]["login"]
        author_email = commit["commit"]["author"]["email"]

        if author_name is not None and author_name != 'unknown':
            if author_name in contributors:
                return author_name
        else:
            if author_email is not None and author_email != 'unknown':
                suspected_name = author_email[0:author_email.index('@')]

                if suspected_name in contributors:
                    return suspected_name
        return 'Unknown'
    
    def __get_paginated_branch_data(self, url):
        pagesRemaining = True
        branches = dict()
        next_url = url

        while pagesRemaining:
            res = self._make_gh_api_call(next_url)
            links = res.links
            data = res.json()

            for entry in data:
                name = entry['name']
                last_commit_sha = entry['commit']['sha']
                branches[name] = last_commit_sha
            
            try:
                next_url = links.get('next').get('url')
            except:
                pagesRemaining = False
        return branches
    
    def pull_commit_data(self, since=None):
        owner = self.repo_owner
        repo = self.repo

        contributors = self.__parse_repo_contributors()
        branch_dict = self._parse_repo_branches()
        branch_list = list(branch_dict.keys())

        all_data = None

        for branch in branch_list:
            branch_sha = branch_dict[branch]
            if since is not None:
                url = f'{self.base_url}/repos/{owner}/{repo}/commits?since={since}&per_page=100&sha={branch_sha}'
            else:
                url = f'{self.base_url}/repos/{owner}/{repo}/commits?per_page=100&sha={branch_sha}'

            pagesRemaining = True
            commits = []
            next_url = url

            while pagesRemaining:
                res = self._make_gh_api_call(next_url)
                links = res.links
                data = res.json()
                pattern = r'task[^a-zA-Z\d\s]?\d+'

                for commit_entry in data:
                    commit_obj = commit_entry["commit"]

                    # Author Details used to assign the commit
                    committer = self.__get_commit_author(contributors, commit_entry)
                    # Commit date and title
                    commit_msg = commit_obj['message']
                    match = re.search(pattern, commit_msg, re.IGNORECASE)

                    if match:
                        task_num = int(re.search(r'\d+', match.group()).group())
                    else:
                        task_num = None
                
                    # Takes the commit timezone (UTC) and converts to AZ timezone
                    utc_dt = datetime.datetime.strptime(commit_obj['committer']['date'], '%Y-%m-%dT%H:%M:%SZ')
                    az_dt = utc_dt.astimezone(pytz.timezone('US/Arizona'))
                    
                    # Used for identifying and filtering commits
                    id = commit_entry['sha']
                    url = commit_entry['html_url']

                    commits.append({
                        "az_date": f'{az_dt.strftime('%m/%d/%Y')}',
                        "message": commit_msg,
                        "task": task_num,
                        "committer": committer,
                        "id": id,
                        "utc_datetime": f'{utc_dt}',
                        "url": url
                    })

                try:
                    next_url = links.get('next').get('url')
                except:
                    pagesRemaining = False
            
            branch_commits = pd.json_normalize(commits)

            if all_data is None:
                all_data = branch_commits
            else:
                all_data = pd.concat([all_data, branch_commits]).drop_duplicates(subset=['id'], keep='last').reset_index(drop=True)

        return all_data

# auth = github.Auth.Token()
# gh = github.Github(auth=auth)
# user = gh.get_user()
# github.PaginatedList
# repos_pages = user.get_repos()
# count = repos_pages.totalCount

# for i in range(count):
#     for repo in repos_pages.get_page(i):
#         print(repo)