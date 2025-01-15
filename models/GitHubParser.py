from typing import Type
import pandas as pd
import numpy as np
import requests
import datetime
import pytz
import re

class GitHubParser:
    base_url = "https://api.github.com"

    token = None
    repo_owner = None
    repo = None

    auth_verified = False
    repo_verified = False

    def __init__(self, token=None, owner=None, repo=None):
        self.set_gh_token(token)
        self.set_repo_owner_username(owner)
        self.set_repo_name(repo)

    def validate_username(self, username):
        return username is not None and username != ""
    
    def validate_token(self, token):
        return token is not None and token != ''

    def validate_auth(self):
        if self.validate_token(self.token):
            res = self.__make_gh_api_call(f'{self.base_url}/user')
            if res.status_code >= 200 and res.status_code < 300:
                self.auth_verified = True
                return
            
        self.auth_verified = False
        return
    
    def auth_validated(self):
        return self.auth_verified
    
    def set_gh_token(self, token):
        if self.validate_token(token):
            self.token = token
            self.validate_auth()
            return True
        return False
    
    def get_token(self):
        return self.token

    def validate_repo_exists(self):
        owner = self.repo_owner
        repo = self.repo

        if owner is not None and repo is not None:
            url = f'{self.base_url}/repos/{owner}/{repo}'
            header = self.__get_auth_header()

            res = requests.get(url, headers=header)

            if res.status_code >= 200 and res.status_code < 300:
                self.repo_verified = True
                return
        self.repo_verified = False
        return
    
    def repo_validated(self) -> bool:
        return self.repo_verified

    def set_repo_owner_username(self, owner):
        if self.validate_username(owner):
            self.repo_owner = owner
            self.validate_repo_exists()
            return True
        return False
    
    def get_repo_owner(self):
        return self.repo_owner
    
    def set_repo_name(self, repo):
        if repo is not None and repo != "":
            self.repo = repo
            self.validate_repo_exists()
            return True
        return False
    
    def get_repo_name(self):
        return self.repo
    
    def __inv_val_to_none(self, df: Type[pd.DataFrame]):
        df.replace(['', 'None', 'nan', 'NaN', np.nan], [None, None, None, None, None], inplace=True)

    def get_tasks_list(self, df: Type[pd.DataFrame]):
        df_to_use = self.df['task'].copy(deep=True)
        self.__inv_val_to_none(df_to_use)
        df_to_use.dropna(inplace=True)
        df_to_use = df_to_use.drop_duplicates(keep='first').reset_index(drop=True)
        df_to_use = df_to_use.astype(int)
        task_list = df_to_use.tolist()
        return task_list
    
    def __get_auth_header(self):
        return {
            'Authorization': f'token {self.token}' 
        }
    
    def __make_gh_api_call(self, url):
        header = self.__get_auth_header()
        return requests.get(url, headers=header)
    
    def __parse_repo_branches(self) -> dict:
        owner = self.repo_owner
        repo = self.repo
        url = f'{self.base_url}/repos/{owner}/{repo}/branches?per_page=100'
        return self.__get_paginated_branch_data(url)
    
    def __parse_repo_contributors(self) -> list:
        owner = self.repo_owner
        repo = self.repo
        url = f'{self.base_url}/repos/{owner}/{repo}/contributors'

        res = self.__make_gh_api_call(url).json()
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
            res = self.__make_gh_api_call(next_url)
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
        branch_dict = self.__parse_repo_branches()
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
                res = self.__make_gh_api_call(next_url)
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