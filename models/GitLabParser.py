from typing import Type
import pandas as pd
import numpy as np
import requests
import datetime
import pytz
import re

class GitLabParser:
    base_url = "https://gitlab/api/v4/projects"

    project_id = None
    token = None

    auth_verified = False
    repo_verified = False

    def __init__(self, token=None, proj_id=None):
        self.set_token(token)
        self.set_project_id(proj_id)

    def validate_auth(self):
        if self.validate_token(self.token):
            url = f'{self.base_url}'
            header = self.__get_auth_header()
            res = requests.get(url, headers=header)
            if res.status_code >= 200 and res.status_code < 300:
                self.auth_verified = True
                return
        self.auth_verified = False
        return

    def validate_repo_exists(self):
        token = self.get_token()
        project_id = self.get_project_id()
        if token is not None:
            url = f'{self.base_url}/{project_id}/repository/tree'
            header = self.__get_auth_header()
            res = requests.get(url, headers=header)
            if res.status_code >= 200 and res.status_code < 300:
                self.repo_verified = True
                return
        self.repo_verified = False
        return
    
    def repo_validated(self) -> bool:
        return self.repo_verified
    
    def validate_token(self, token):
        return token is not None and token != ''

    def set_token(self, token):
        if self.validate_token(token):
            self.token = token
            self.validate_auth()
            return True
        return False

    def get_token(self):
        return self.token
    
    def set_project_id(self, proj_id):
        if proj_id is not None and proj_id > 0:
            self.project_id = proj_id
            self.validate_repo_exists()
            return True
        return False

    def get_project_id(self):
        return self.project_id
    
    def __inv_val_to_none(self, df: Type[pd.DataFrame]):
        df.replace(['', 'None', 'nan', 'NaN', np.nan], [None, None, None, None, None], inplace=True)
    
    def __get_auth_header(self):
        return {
            'Authorization': f'Bearer {self.token}' 
        }