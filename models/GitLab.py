import pandas as pd
import numpy as np
import requests
import datetime
import pytz
import re
import gitlab
from gitlab import Gitlab
import json

class GitLabDataServicer:
    base_url = "https://gitlab/api/v4/projects"

    project_id = None
    token = None

    auth_verified = False
    repo_verified = False
    
    def __init__(self, token=None):
        self.base_url = "https://gitlab/api/v4/projects"
        self.token = None
        self.gl : Gitlab = None
        self.auth_and_gl_set = False

        if token: 
            self.set_token(token)
            
    def _init_obj(self):
        self.gl = Gitlab(private_token=self.token)

    def set_token(self, token) -> bool:
        self.token = token

        if self.token:
            try:
                self._init_obj()
                self.auth_and_gl_set = True
            except:
                self.auth_and_gl_set = False
        return self.auth_and_gl_set
    
    def get_token(self) -> str:
        return self.token
    
    def ready_for_api_calls(self) -> bool:
        return self.auth_and_gl_set
    
    def get_repos(self) -> pd.DataFrame:
        repo_list = []
        for item in self.gl.projects.list(membership=True):
            id = item.id
            name = item.name
            owner_id = self.gl.projects.get(id).creator_id
            owner = self.gl.users.get(owner_id).attributes['username']

            repo_list.append({ 
                'id': id,
                'repo_name': name, 
                'owner_name': owner,
                'is_linked': False,
                'last_commit_dt': None
            })
        repos = pd.json_normalize(repo_list)
        return repos

    def _get_repo_branches(self, repo) -> list[str]:
        branch_list = []
        if repo:
            for branch in repo.branches.list(get_all=True):
                branch_list.append(branch.name)
        return branch_list
    
    def get_contributors(self, repo_name) -> list[str]:
        repo = self.get_repo(repo_name)
        return self._get_contributors(repo)
    
    def _get_contributors(self, repo) -> list[str]:
        contributors = []
        if repo is not None:
            for item in repo.members.list(get_all=True):
                if item.state == 'active':
                    contributors.append(item.name)

        return contributors
    
    def _get_commit_author(self, contributors, commit) -> str | None:
        pass
    
    def _inv_val_format(self, df: pd.DataFrame):
        df = df.replace(['', 'None', 'nan', 'NaN', np.nan, None], pd.NA)

    def _format_commit_data(self, df : pd.DataFrame) -> pd.DataFrame:
        pass
    
    def get_repo_by_id(self, repo_id):
        return self.gl.projects.get(repo_id)

    def get_repo(self, repo_name):
        return self.gl.projects.get(repo_name)
    
    def _make_api_call(self, header, url) -> requests.Response:
        return requests.get(url, headers=header)
    
    def import_commit_data(self, repo_name, repo_id, since=None):
        auth_header = {
            'PRIVATE-TOKEN': f'{self.token}'
        }
    
        repo_obj = self.get_repo(repo_id)

        since_param = f'&since={since}' if since is not None else ''
        url = f'https://gitlab.com/api/v4/projects/{repo_obj.get_id()}/repository/commits?{since_param}all=True&per_page=100'
        commit_ids = []

        pagesRemaining = True
        commits = []
        commits_json = []
        next_url = url

        yield 'In Progress', f'Importing GitLab commit data from repository {repo_name}...'

        while pagesRemaining:
            res = self._make_api_call(header=auth_header, url=next_url)
            pattern = r'task[^a-zA-Z\d\s]?\d+'

            for item in res.json():
                if item['id'] not in commit_ids:
                    commit_ids.append(item['id'])
                    commits_json.append(item)

            try:
                next_url = res.links.get('next').get('url')
            except:
                pagesRemaining = False

        commit_cnt = len(commits_json)
        curr_num = 1
        
        for commit in commits_json:
            yield 'In Progress', f'Processing GitLab commit data (Commit {curr_num} of {commit_cnt})...'
            curr_num += 1

            id = commit['id']
            url = commit['web_url']
            committer = commit['committer_name']
            commit_msg = commit['title'] 
            match = re.search(pattern, commit_msg, re.IGNORECASE)
            task_num = int(re.search(r'\d+', match.group()).group()) if match else None
        
            # Takes the commit timezone (UTC) and converts to AZ timezone
            utc_dt = pd.to_datetime(commit['created_at'], format='ISO8601', utc=True)
            az_dt = utc_dt.astimezone(pytz.timezone('US/Arizona'))
            
            commits.append({
                "id": id,
                "repo_name": repo_name,
                "host_site": "GitLab",
                "task_num": task_num,
                "committer": committer,
                "az_date": az_dt.strftime('%m/%d/%Y'),
                "utc_datetime": utc_dt,
                "commit_message": commit_msg,
                "commit_url": url
            })
            
        all_data = pd.json_normalize(commits)                
        yield 'Complete', [f'Completed importing GitLab commit data from repository {repo_name}...', all_data]