
import os
from typing import Type
import pandas as pd
import numpy as np

from models import GitHubParser

class GitParsingController:
    config_fp = os.path.join(os.getcwd(), 'config.txt')
    config_parser = None

    raw_commit_df = None
    data_ready = False

    gh_parser = None
    gh_latest_commit_date = None

    gl_latest_commit_date = None

    def __init__(self, config_parser, gh_token=None, gh_repo=None, gh_owner=None, gh_latest_commit_date=None):
        self.config_parser = config_parser
        self.gh_parser = GitHubParser.GitHubParser(gh_token, gh_repo, gh_owner)

    def load_raw_data(self, raw_df):
        if raw_df is not None:
            self.set_commit_data(raw_df)

    def data_is_ready(self) -> bool:
        return self.data_ready
    
    def set_commit_data(self, all_data):
        all_data['utc_datetime'] = pd.to_datetime(all_data['utc_datetime'])
        all_data.sort_values(by='utc_datetime', inplace=True)
        latest = all_data['utc_datetime'].max().date()
        self.raw_commit_df = all_data
        self.latest_commit_date = f'{latest.isoformat()}T00:00:00Z'
        self.data_ready = True
    
    def get_contributors(self) -> list:
        return sorted(self.raw_commit_df['committer'].unique()) if self.raw_commit_df is not None else None
    
    def __inv_val_to_none(self, df: Type[pd.DataFrame]):
        df.replace(['', 'None', 'nan', 'NaN', np.nan], [None, None, None, None, None], inplace=True)
    
    def get_tasks(self) -> list:
        df_to_use = self.raw_commit_df['task'].copy(deep=True)
        self.__inv_val_to_none(df_to_use)
        df_to_use.dropna(inplace=True)
        df_to_use = df_to_use.drop_duplicates(keep='first').reset_index(drop=True)
        df_to_use = df_to_use.astype(int)
        task_list = df_to_use.tolist()
        return task_list
    
    def get_current_commit_data(self) -> pd.DataFrame:
        return self.raw_commit_df
    
    def __parse_commits_by_committer(self):
        commit_data = self.get_current_commit_data()
        contributors = self.get_contributors()
        commits_by_committer = dict()

        for contributor in contributors:
            commiter_df = commit_data.loc[commit_data['committer'] == contributor]
            commits_by_committer[contributor] = commiter_df

        self.commits_by_committer_df = commits_by_committer

    def get_commits_by_committer_data(self):
        return self.__parse_commits_by_committer()
    
    def __merge_dataframes(self, master_df, new_df):
        self.__inv_val_to_none(master_df)
        self.__inv_val_to_none(new_df)
        master_df.set_index('id', inplace=True)
        master_df.update(new_df.set_index('id'))
        master_df.reset_index(inplace=True)
        master_df.sort_values(by='utc_datetime', ascending=True, inplace=True)
        return master_df[['az_date', 'message', 'task', 'committer', 'id', 'utc_datetime', 'url']]
    
    def set_gh_latest_date(self, df: Type[pd.DataFrame]):
        if df is not None:
            latest = df['utc_datetime'].max().date()
            self.gh_latest_commit_date = f'{latest.isoformat()}T00:00:00Z'

            config = self.config_parser
            config.set('github-config', 'gh_latest_commit_date', self.gh_latest_commit_date)
            with open(self.config_fp, 'w') as configfile:
                config.write(configfile)
                configfile.close()
    
    def retrieve_gh_commit_data(self):
        curr_commit_data = self.get_current_commit_data()
        gh_commit_data = self.gh_parser.pull_commit_data(self.gh_latest_commit_date)
        gh_commit_data['utc_datetime'] = pd.to_datetime(gh_commit_data['utc_datetime'])

        if gh_commit_data is not None:
            self.set_gh_latest_date(gh_commit_data)
            new_commit_df = self.__merge_dataframes(curr_commit_data, gh_commit_data) if curr_commit_data is not None else gh_commit_data
            self.set_commit_data(new_commit_df)
            
            

    def clear_data(self):
        self.raw_commit_df = None
        self.gh_latest_commit_date = None
        self.gl_latest_commit_date = None
        self.data_ready = False

    ## GitHub
    ##=============================================================================

    def set_gh_token(self, token):
        return self.gh_parser.set_gh_token(token)
    
    def get_gh_token(self):
        return self.gh_parser.get_token()
    
    def gh_auth_validated(self) -> bool:
        return self.gh_parser.auth_validated()
    
    def set_gh_repo_owner(self, owner):
        return self.gh_parser.set_repo_owner_username(owner)

    def get_gh_repo_owner(self):
        return self.gh_parser.get_repo_owner()
    
    def gh_repo_validated(self):
        return self.gh_parser.repo_validated()
    
    def set_gh_repo_name(self, repo):
        return self.gh_parser.set_repo_name(repo)

    def get_gh_repo_name(self):
        return self.gh_parser.get_repo_name()

    
    