from typing import Type
import pandas as pd
import numpy as np
import requests
import datetime
import pytz
import re

class GitLabDataServicer:
    base_url = "https://gitlab/api/v4/projects"

    project_id = None
    token = None

    auth_verified = False
    repo_verified = False
    
    def __init__(self, token=None):
        self.base_url = "https://gitlab/api/v4/projects"
        self.token = None
        
        self.auth_and_gl_set = False

        if token: 
            self.set_token(token)
            
    def _init_obj(self):
        pass

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
        pass

    def _get_repo_branches(self, repo) -> dict[str:str]:
        pass
    
    def get_contributors(self, repo) -> list[str]:
        pass
    
    def _get_commit_author(self, contributors, commit) -> str | None:
        pass
    
    def _inv_val_format(self, df: Type[pd.DataFrame]):
        df.replace(['', 'None', 'nan', 'NaN', np.nan, None], pd.NA, inplace=True)

    def _format_commit_data(self, df : pd.DataFrame) -> pd.DataFrame:
        pass
    
    def _get_auth_header(self) -> dict[str:str]:
        return {
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {self.token}',
            'X-GitHub-Api-Version': '2022-11-28'
        }
    
    def _make_api_call(self, header, url) -> requests.Response:
        return requests.get(url, headers=header)
    
    def import_commit_data(self, repo, since=None) -> pd.DataFrame:
        pass