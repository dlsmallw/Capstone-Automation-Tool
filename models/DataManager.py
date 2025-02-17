import configparser
import os

import openpyxl as opyxl
import pandas as pd
import numpy as np
from typing import Type
from models.Taiga import TaigaDataServicer
from models.GitServicerInterface import GitServicer
from models.database.RecordDatabase import RecDB
import requests
import http.client as hc

TAIGA = 'Taiga'
GITHUB = 'GitHub'
GITLAB = 'GitLab'

class DataController:
    config_fp = os.path.join(os.getcwd(), 'config.txt')
    config_parser = None

    gh_auth_verified = False
    gh_repo_verified = False

    def __init__(self, db: RecDB):
        ## Class object defaults
        self.db : RecDB = None

        ## Data Servicers
        self.ts : TaigaDataServicer = None
        self.gs : GitServicer = None

        ## Taiga-related variables
        #### Projects
        self.taiga_projects_df : pd.DataFrame = None
        self.sel_pid = None
        self.sel_project_name = None
        self.sel_project_owner = None
        self.project_selected = False
        #### Dataframes
        self.sprints_df : pd.DataFrame = None
        self.members_df : pd.DataFrame = None
        self.us_df : pd.DataFrame = None
        self.tasks_df : pd.DataFrame = None
        #### CSV URLs
        self.us_report_url = None
        self.task_report_url = None
        #### Status Vars
        self.taiga_data_available = False

        ## Git-related variables
        self.git_accts : dict = dict()
        self.repos : pd.DataFrame = None
        self.contributors : list[str] = None
        self.commits_df : pd.DataFrame = None
        
        self.commit_data_available = False

        ## Instance initializations and data loading
        self.db = db
        self.ts = self.init_taiga_servicer()
        self.gs = self.init_git_servicer()

    ## Initialization Functions
    ##=============================================================================

    def init_taiga_servicer(self) -> TaigaDataServicer | None:
        def load_taiga_projects():
            projects = self.db.table_to_df('taiga_projects')
            if projects is not None and len(projects) > 0:
                self.taiga_projects_df = projects
                row = projects.loc[projects['is_selected'] == 1]

                if len(row) > 0:
                    self.set_linked_taiga_project(row['id'], row['project_name'], row['project_owner'])

        def load_saved_taiga_data():
            self.update_sprints_df(self.db.table_to_df('sprints'))
            self.update_members_df(self.db.table_to_df('members'))
            self.update_us_df(self.db.table_to_df('userstories'))
            self.update_tasks_df(self.db.table_to_df('tasks'))

        load_taiga_projects()
        load_saved_taiga_data()
        return TaigaDataServicer(self.load_taiga_credentials())
    
    def init_git_servicer(self) -> GitServicer:
        def load_accts():
            accts = self.db.table_to_df('sites')
            repo_accts = accts[accts['nickname'] != 'Taiga']
            for index, row in repo_accts.iterrows():
                user, token = self.db.decrypt([row['username'], row['site_token']])
                repo_accts.iloc[index - 1]['username'] = user
                repo_accts.iloc[index - 1]['site_token'] = token
            
            if repo_accts is not None and len(repo_accts) > 0:
                self.git_accts = dict()

                for index, row in repo_accts.iterrows():
                    site = row['site_name']
                    nickname = row['nickname']
                    user = row['username']
                    token = row['site_token']

                    res, msg = self.validate_token(site, token)

                    if res == 'Success':
                        details = "Ready to make API calls"
                    else:
                        details = msg

                    self.git_accts[nickname] = {
                        'site': site,
                        'user': user,
                        'token': token,
                        'details': details
                    }
        
        def load_repos():
            repos = self.db.table_to_df('repos')
            if repos is not None and len(repos) > 0:
                self.repos = repos
        
        def load_commit_data():
            self.update_commit_df(self.db.table_to_df('commits'))

        gs = GitServicer()
        load_repos()
        load_accts()
        load_commit_data()
        return gs
    

    ## Util Functions
    ##=============================================================================

    def validate_token(self, site, token):
        def gh_request(token):
            base_url = "https://api.github.com/user"
            header = {
                'Accept': 'application/vnd.github+json',
                'Authorization': f'Bearer {token}',
                'X-GitHub-Api-Version': '2022-11-28'
            }

            return base_url, header
        
        def gl_request(token):
            base_url = None
            header = None

            return base_url, header

        if site == GITHUB:
            url, headers = gh_request(token)
        else:
            url, headers = gl_request(token)

        try:
            res = requests.get(url=url, headers=headers)
            sc = res.status_code

            if sc >= 200 and sc <= 200:
                return 'Success', res.json()['login']
            else:
                return 'Error', f'{sc} - [{hc.responses[sc]}]'
        except Exception as e:
            return 'Error', f'Exception - {e}'

    def get_site_credentials_from_db(self, site_name):
        return self.db.decrypt(tuple(self.db.select('sites', ['username', 'user_pwd', 'site_token'], {'site_name': site_name})[0]))
    
    def update_user_credentials(self, site_name, username=None, pwd=None, token=None):
        return self.db.update('sites', dict(zip(['username', 'user_pwd', 'site_token'], self.db.encrypt([username, pwd, token]))), {'site_name': site_name})
    
    def check_if_nickname_exists(self, nickname):
        result = self.db.select('sites', conditions={'nickname': nickname})
        return len(result) > 0
    
    def check_if_token_exists(self, token):
        for acct in self.git_accts.keys():
            if token == self.git_accts[acct]['token']:
                return True
        return False
    
    def update_git_acct(self, site, nickname, token):
        res, msg = self.validate_token(site, token)
        if res == 'Error':
            return res, msg
        
        if self.check_if_token_exists(token):
            return 'Error', 'Account associated with this token already exists'
        
        username = msg
        enc_uname, enc_token = self.db.encrypt([msg, token])
        data = {
            'site_name': site,
            'username': enc_uname,
            'nickname': nickname,
            'site_token': enc_token
        }

        cond = {'nickname': nickname}
        self.db.insert('sites', data, cond)

        if nickname in self.git_accts.keys():
            self.git_accts[nickname]['user'] = username
            self.git_accts[nickname]['token'] = token
            self.git_accts[nickname]['details'] = "Ready to make API calls"
        else:
            self.git_accts[nickname] = {
                'site': site,
                'user': username,
                'token': token,
                'details': "Ready to make API calls"
            }

        return res, msg
    
    def add_git_acct(self, site, nickname, token):
        res, msg = self.update_git_acct(site, nickname, token)
        if res == 'Success':
            self.gs.init_git_servicer(site, nickname, token)
        return res, msg
    
    def remove_git_acct(self, nickname):
        self.gs.remove_servicer(nickname)
        self.git_accts.pop(nickname)
        self.db.delete('sites', conditions={'nickname': nickname})
        self.db.delete('repos', conditions={'site_nickname': nickname} )
        return 
    
    def get_git_accts(self):
        accts = []
        if self.git_accts is not None and len(self.git_accts) > 0:
            for nname in self.git_accts:
                site = self.git_accts[nname]['site']
                user = self.git_accts[nname]['user']
                details = self.git_accts[nname]['details']
                accts.append([site, nname, user, details])
        return accts
    
    def get_acct_repos(self, nickname):
        self.pull_repos(nickname)
        return self.get_avail_repos()
    
    def link_repo(self, repo):
        repos = self.repos.copy(deep=True)
        repos.loc[repos['repo_name'] == repo, 'is_linked'] = 1
        self.update_repos(repos, cols=['is_linked'])

    def unlink_repo(self, repo):
        repos = self.repos.copy(deep=True)
        repos.loc[repos['repo_name'] == repo, 'is_linked'] = 0
        self.update_repos(repos, cols=['is_linked'])

    def repos_available(self) -> bool:
        return self.repos is not None and len(self.repos) > 0
    
    def repos_linked(self) -> bool:
        return len(self.get_linked_repos()) > 0
    
    def api_call_ready(self) -> bool:
        if self.repos_linked:
            for acct in self.git_accts.keys():
                if self.git_accts[acct]['details'] == "Ready to make API calls":
                    return True
        return False
        
    
    #### Taiga
    ####===========================================================================

    def get_us_df(self) -> pd.DataFrame:
        return self.us_df
    
    def get_task_df(self) -> pd.DataFrame:
        return self.tasks_df
    
    def get_members_df(self) -> pd.DataFrame:
        return self.members_df
    
    def get_sprints_df(self) -> pd.DataFrame:
        return self.sprints_df

    def get_num_projects(self):
        if self.taiga_projects_df is not None and not self.taiga_projects_df.empty:
            return len(self.taiga_projects_df)
        else:
            return 0
        
    def get_available_projects(self):
        projects = []
        
        for index, row in self.taiga_projects_df.iterrows():
            projects.append(row['project_name'])
        return projects
    
    def get_linked_taiga_project(self):
        return self.sel_pid, self.sel_project_name, self.sel_project_owner

    def set_linked_taiga_project(self, pid, name, owner):
        if pid and name and owner:
            self.sel_pid = pid
            self.sel_project_name = name
            self.sel_project_owner = owner
            self.project_selected = True

    # Function to authenticate with Taiga API
    def authenticate_with_taiga(self, username, password):
        if not username or not password:
            return "Error", "Please enter both username and password."
            
        url = "https://api.taiga.io/api/v1/auth"  # Change this to your Taiga API URL if self-hosted
        data = {
            "type": "normal",
            "username": username,
            "password": password
        }

        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                auth_token = response.json().get("auth_token")
                self.ts.update_user_credentials(username, password, auth_token)
                self.update_user_credentials('Taiga', username, password, auth_token)

                return "Success", f"Login successful! Token: {auth_token}"
            else:
                return "Error", f"Login failed: {response.json().get('non_field_errors', 'Unknown error')}"
        except Exception as e:
            return "Error", f"An error occurred: {e}"

    def select_taiga_project(self, project):
        sel_row = self.taiga_projects_df.loc[self.taiga_projects_df['project_name'] == project]
        selected_exists = not sel_row.empty
        curr_sel_exists = not self.taiga_projects_df.loc[self.taiga_projects_df['is_selected'] == 1].empty

        if selected_exists:
            if curr_sel_exists:
                self.taiga_projects_df.loc[self.taiga_projects_df['is_selected'] == 1, 'is_selected'] = 0 

            self.taiga_projects_df.loc[self.taiga_projects_df['project_name'] == project, 'is_selected'] = 1
            self.db.df_to_table('taiga_projects', self.taiga_projects_df)
            self.set_linked_taiga_project(sel_row['id'].iloc[0], sel_row['project_name'].iloc[0], sel_row['project_owner'].iloc[0])
            return "Success", f"Successfully linked project '{project}'"
        else:
            return "ERROR", f"No project by name '{project}' exists"

    def taiga_data_ready(self):
        return self.taiga_data_available

    def load_taiga_credentials(self):
        return self.get_site_credentials_from_db(TAIGA)[0:2]
    
    def get_taiga_credentials(self):
        return self.ts.get_credentials()
    
    def update_taiga_credentials(self, uname=None, pwd=None):
        is_success = self.update_user_credentials(TAIGA, username=uname, pwd=pwd)
        return is_success
    
    def update_taiga_csv_urls(self, us_url='NULL', task_url='NULL'):
        self.us_report_url = us_url if us_url != 'NULL' else None
        self.task_report_url = task_url if task_url != 'NULL' else None

        return self.db.update('taiga_csv_urls', {'durl': us_url}, {'dname': 'user_story'}) \
            and self.db.update('taiga_csv_urls', {'durl': task_url}, {'dname': 'task'})
    
    def get_taiga_csv_urls(self):
        us_url = task_url = None
        results = self.db.select('taiga_csv_urls')
        for entry in results:
            if entry:
                dname = entry[0]
                if dname == 'user_story':
                    us_url = entry[1]
                elif dname == 'task':
                    task_url = entry[1]
            
        return us_url, task_url
    
    def clear_taiga_data(self):
        tables = ['members', 'sprints', 'userstories', 'tasks']
        for name in tables:
            self.db.clear_table(name)

        self.sprints_df = self.members_df = self.us_df \
            = self.tasks_df = None
        self.taiga_data_available = False

    def clear_taiga_link(self):
        self.clear_taiga_data()
        self.db.clear_table('taiga_projects')
        self.update_taiga_credentials()
        self.update_taiga_csv_urls()
        self.ts.clear_linked_data()

        self.taiga_projects_df = self.sel_pid = self.sel_project_name \
            = self.sel_project_owner = None
        self.project_selected = False
    
    #### Git
    ####===========================================================================

    def commit_data_ready(self) -> bool:
        return self.commits_df is not None and len(self.commits_df) > 0
    
    def pull_all_repos(self):
        for acct in self.git_accts.keys():
            self.pull_repos(acct)
    
    def pull_repos(self, nickname):
        self.update_repos(self.gs.get_repos(nickname))

    def get_avail_repos(self):
        repos = []
        if self.repos is not None:
            repos_df = self.repos.loc[self.repos['is_linked'] == 0]
            for index, row in repos_df.iterrows():
                repos.append([row['site_nickname'], row['repo_name']])
        return repos
    
    def get_linked_repos(self):
        linked = []
        if self.repos is not None:
            linked_df = self.repos.loc[self.repos['is_linked'] == 1]
            for index, row in linked_df.iterrows():
                linked.append([row['site_nickname'], row['repo_name']])
        return linked
    
    def ready_for_api_calls(self, nickname):
        return self.gs.ready_for_api_calls(nickname)
    
    def pull_contributors(self):
        contributors = []
        for nickname, repo_name in self.get_linked_repos():
            contributors += self.gs.get_contributors(nickname, repo_name)

        if len(contributors) > 0:
            self.contributors = contributors

    def get_contributors(self):
        return self.contributors
    
    ## Data Manipulation
    ##=============================================================================

    def _inv_val_format(self, df: pd.DataFrame):
        df.replace(['', 'None', 'nan', 'NaN', np.nan, None], pd.NA, inplace=True)

    def get_cell_val_from_df(self, df : pd.DataFrame, desired_field, cond_field, cond_val):
        try:
            return df.loc[df[cond_field] == cond_val, desired_field].iloc[0]
        except:
            return None
        
    def update_df(self, curr_df: pd.DataFrame, new_df: pd.DataFrame, col_to_index='id', cols=None):
        try:
            if curr_df is not None and not curr_df.empty:
                curr_df_copy = curr_df.copy(deep=True)
                new_df_copy = new_df.copy(deep=True)

                curr_df_copy = pd.concat([curr_df_copy, new_df_copy]).drop_duplicates([col_to_index], keep='first')

                curr_df_copy.set_index(col_to_index, inplace=True)
                new_df_copy.set_index(col_to_index, inplace=True)

                if cols is not None:
                    curr_df_copy.update(new_df_copy[cols])
                else:
                    curr_df_copy.update(new_df_copy)
                curr_df_copy.reset_index(inplace=True)
                return curr_df_copy
            else:
                curr_df = new_df
                return curr_df
        except Exception as e:
            print(e)
            # exc_type = type(e),__name__
            # exc_cause = 'No Cause/Context Provided'
            # cause = e.__cause__ or e.__context__
            # if cause:
            #     exc_cause = str(cause)

            # print(f'{exc_type}: {exc_cause}')
            return curr_df
        
    #### Taiga
    ####===========================================================================
    
    def update_projects_df(self, new_df):
        def format_df(df: pd.DataFrame) -> pd.DataFrame:
            self._inv_val_format(df)
            df['id'] = df['id'].astype(pd.Int64Dtype())
            
            df.dropna(inplace=True, how='all')
            df = df.drop_duplicates(subset=['id'], keep='first').reset_index(drop=True)
            df.sort_values(by='id', ascending=True, inplace=True)
            return df

        if new_df is not None and len(new_df) > 0:
            self.taiga_projects_df = self.update_df(self.taiga_projects_df, format_df(new_df))
            self.db.df_to_table('taiga_projects', self.taiga_projects_df)
            self.taiga_projects_df = format_df(self.db.table_to_df('taiga_projects'))

    def update_sprints_df(self, new_df: pd.DataFrame):
        def to_table_format(df: pd.DataFrame) -> pd.DataFrame:
            df['sprint_start'] = pd.to_datetime(df['sprint_start']).dt.strftime('%m/%d/%Y')
            df['sprint_end'] = pd.to_datetime(df['sprint_end']).dt.strftime('%m/%d/%Y')
            return df

        def format_df(df: pd.DataFrame) -> pd.DataFrame:
            self._inv_val_format(df)
            df['id'] = df['id'].astype(pd.Int64Dtype())
            df['sprint_start'] = pd.to_datetime(df['sprint_start'])
            df['sprint_end'] = pd.to_datetime(df['sprint_end'])
            
            df.dropna(inplace=True, how='all')
            df = df.drop_duplicates(subset=['id'], keep='first').reset_index(drop=True)
            df.sort_values(by='sprint_start', ascending=True, inplace=True)
            return df

        if new_df is not None and len(new_df) > 0:
            self.sprints_df = self.update_df(self.sprints_df, format_df(new_df))
            self.db.df_to_table('sprints', to_table_format(self.sprints_df))
            self.sprints_df = format_df(self.db.table_to_df('sprints'))


    def update_members_df(self, new_df: pd.DataFrame):
        def format_df(df: pd.DataFrame) -> pd.DataFrame:
            self._inv_val_format(df)
            df['id'] = df['id'].astype(pd.Int64Dtype())
            
            df.dropna(inplace=True, how='all')
            df = df.drop_duplicates(subset=['username'], keep='first').reset_index(drop=True)
            df.sort_values(by='id', ascending=True, inplace=True)
            return df
        
        if new_df is not None and len(new_df) > 0:
            self.members_df = self.update_df(self.members_df, format_df(new_df), 'username')
            self.db.df_to_table('members', self.members_df)
            self.members_df = format_df(self.db.table_to_df('members'))
    
    def update_us_df(self, new_df: pd.DataFrame, cols=None):
        def format_df(df: pd.DataFrame) -> pd.DataFrame:
            self._inv_val_format(df)
            df['id'] = df['id'].astype(pd.Int64Dtype())
            df['us_num'] = df['us_num'].astype(pd.Int64Dtype())
            df['points'] = df['points'].astype(pd.Int64Dtype())
            df['is_complete'] = df['is_complete'].astype(pd.BooleanDtype())
            df['points'].replace(pd.NA, 0, inplace=True)
            
            df.dropna(inplace=True, how='all')
            df = df.drop_duplicates(subset=['id'], keep='first').reset_index(drop=True)
            df.sort_values(by=['sprint', 'us_num'], ascending=True, na_position='last', inplace=True)
            return df
        
        if new_df is not None and len(new_df) > 0:
            self.us_df = self.update_df(self.us_df, format_df(new_df))
            self.db.df_to_table('userstories', self.us_df)
            self.us_df = format_df(self.db.table_to_df('userstories'))

        self.taiga_data_available = self.us_df is not None and len(self.us_df) > 0 and self.tasks_df is not None and len(self.tasks_df) > 0

    def update_tasks_df(self, new_df: pd.DataFrame, cols=['task_num', 'is_complete', 'us_num', 'assignee', 'task_subject']):
        def format_df(df: pd.DataFrame) -> pd.DataFrame:
            df['id'] = df['id'].astype(pd.Int64Dtype())
            df['task_num'] = df['task_num'].astype(pd.Int64Dtype())
            df['us_num'] = df['us_num'].astype(pd.Int64Dtype())
            df['is_coding'] = df['is_coding'].astype(pd.BooleanDtype())
            df['is_complete'] = df['is_complete'].astype(pd.BooleanDtype())

            self._inv_val_format(df)
            df.dropna(inplace=True, how='all')
            df = df.drop_duplicates(subset=['id'], keep='first').reset_index(drop=True)
            df.sort_values(by=['us_num', 'task_num'], ascending=[True, True], inplace=True)
            return df
        
        if new_df is not None and len(new_df) > 0:
            self.tasks_df = self.update_df(self.tasks_df, format_df(new_df), cols=cols)
            self.db.df_to_table('tasks', self.tasks_df)
            self.tasks_df = format_df(self.db.table_to_df('tasks'))

        self.taiga_data_available = self.us_df is not None and len(self.us_df) > 0 and self.tasks_df is not None and len(self.tasks_df) > 0

    def __format_and_centralize_taiga_data(self):
        sprints_df = self.sprints_df
        members_df = self.members_df
        tasks_df = self.tasks_df
        us_df = self.us_df


        data_columns = ['task_num', 'us_num', 'points', 'assignee', 'is_coding', 'sprint_name', 'sprint_start', 'sprint_end', 'task_subject']
        all_data = [0] * len(tasks_df)

        for index, row in tasks_df.iterrows():
            us_num = row['user_story']
            us_row = us_df.loc[us_df['ref'] == us_num]

            
            sprint = row['sprint']
            sprint_start, sprint_end = self.__get_sprint_date(sprint)

            user_story = int(us_num) if pd.notnull(us_num) else None
            points = int(us_row['total-points'].values[0] if pd.notnull(us_num) else 0)
            task = int(row['ref'])
            assigned = row['assigned_to'] if pd.notnull(row['assigned_to']) else 'Unassigned'
            coding = ""
            subject = row['subject']
            
            data_row = [sprint, sprint_start, sprint_end, user_story, points, task, assigned, coding, subject]
            all_data[index] = data_row

    #### Git
    ####===========================================================================
    
    
    

    ## Data Importing
    ##=============================================================================
    #### Taiga
    ####===========================================================================

    def pull_taiga_projects(self):
        projects = self.ts.get_watched_projects()
        if projects is not None and not projects.empty:
             self.update_projects_df(projects)

    def wait_for_projects(self):
        self.pull_taiga_projects()
        return True
    
    def process_taiga_data(self, sprint_df, member_df, us_df, tasks_df):
        self.update_sprints_df(sprint_df)
        self.update_members_df(member_df)
        self.update_us_df(us_df)
        self.update_tasks_df(tasks_df)

    def taiga_import_by_api(self):
        if self.project_selected and self.ts.token_set():
            try:
                sprints_df, members_df, us_df, task_df = self.ts.import_data_by_api(self.sel_pid)
                self.process_taiga_data(sprints_df, members_df, us_df, task_df)
                return 'Success', f'Successfully imported Taiga data by API'
            except Exception as e:
                return 'Error', f'Failed to import Taiga data by API - {e}'

    def taiga_import_by_urls(self, us_url, tasks_url):
        if us_url and tasks_url:
            try:
                sprints_df, members_df, us_df, task_df = self.ts._import_data_by_urls(us_url, tasks_url)
                self.process_taiga_data(sprints_df, members_df, us_df, task_df)
                return 'Success', f'Successfully imported Taiga data by URLs'
            except Exception as e:
                return 'Error', f'Failed to import Taiga data by URLs - {e}'

    def taiga_import_by_files(self, us_fp, tasks_fp):
        if us_fp and tasks_fp:
            try:   
                sprints_df, members_df, us_df, task_df = self.ts._import_data_by_files(us_fp, tasks_fp)
                self.process_taiga_data(sprints_df, members_df, us_df, task_df)
                return 'Success', f'Successfully imported Taiga data by File'
            except Exception as e:
                return 'Error', f'Failed to import Taiga data by File - {e}'
            
    #### Git
    ####===========================================================================

    def update_latest_commit_date(self, repo, date):
        self.gh_repos.loc[self.repos['repo_name'] == repo, 'last_commit_dt'] = date
        self.update_repos(self.gh_repos, cols=['last_commit_dt'])

    def update_commit_df(self, new_df : pd.DataFrame):
        def to_table_format(df) -> pd.DataFrame:
            df['utc_datetime'] = pd.to_datetime(df['utc_datetime']).dt.strftime('%Y-%m-%dT%H:%M:%SZ')
            return df

        def format_df(df: pd.DataFrame) -> pd.DataFrame:
            self._inv_val_format(df)
            df['id'] = df['id'].astype(pd.Int64Dtype())
            df['task_num'] = df['task_num'].astype(pd.Int64Dtype())
            df['utc_datetime'] = pd.to_datetime(df['utc_datetime'])

            df.dropna(inplace=True, how='all')
            df = df.drop_duplicates(subset=['id'], keep='first').reset_index(drop=True)
            df.sort_values(by='utc_datetime', ascending=True, inplace=True)

            latest_commit_date = df['utc_datetime'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
            repository = df.loc[0, 'repo_name']
            self.update_latest_commit_date(repository, latest_commit_date)
            return df

        if new_df is not None and len(new_df) > 0:
            self.commits_df = self.update_df(self.commits_df, format_df(new_df))
            self.db.df_to_table('commits', to_table_format(self.commits_df))
            self.commits_df = format_df(self.db.table_to_df('commits'))
        self.commit_data_available = self.commits_df is not None and len(self.commits_df) > 0

    def update_repos(self, new_df: pd.DataFrame, cols=['repo_name', 'owner_name']):
        def format_df(df: pd.DataFrame) -> pd.DataFrame:
            self._inv_val_format(df)
            df['id'] = df['id'].astype(pd.Int64Dtype())

            df.dropna(inplace=True, how='all')
            df = df.drop_duplicates(subset=['id', 'site_nickname'], keep='first').reset_index(drop=True)
            df.sort_values(by=['site_nickname'], ascending=True, inplace=True)
            return df

        if new_df is not None and len(new_df) > 0:
            self.repos = self.update_df(self.repos, format_df(new_df), cols=cols)
            self.db.df_to_table('repos', self.repos)
            self.repos = format_df(self.db.table_to_df('repos'))
        
    ## Data File reading/writing
    ##=============================================================================

    def __create_new_wb(self, filename, sheets=None):
        if os.path.exists(filename):
            os.remove(filename)
        
        wb = opyxl.Workbook()
        wb.create_sheet("Master")

        if sheets is not None:
            for sheet in sheets:
                wb.create_sheet(sheets)

        for sheet in wb.sheetnames:
            if sheets is not None:
                if sheet not in sheets and sheet != 'Master':
                    del wb[sheet]
            else:
                if sheet != 'Master':
                    del wb[sheet]
            
        wb.save(filename)
        wb.close()

    def __parsed_data_to_spreadsheet(self, df, writer, sheet):
        df.to_excel(writer, sheet_name=sheet, index=False)

    def write_to_csv(self, filepath: Type[str], df: Type[pd.DataFrame]):
        subdirectories = filepath.replace('.', '').split('/')
        curr_dir_level = '.'
        for i in range(len(subdirectories) - 1):
            dir = subdirectories[i]
            curr_dir_level += f'/{dir}'

            if not os.path.exists(curr_dir_level):
                os.makedirs(curr_dir_level)

        df.to_csv(filepath, index=False)

    def write_to_excel(self, filepath, df, header_filter=None, sheets=None, sheet_headers=None):
        self.__create_new_wb(filepath, sheets)
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            self.__parsed_data_to_spreadsheet(df, writer, 'Master')

            if sheets is not None:
                for sheet in sheets:
                    sheet_df = df[df[header_filter == sheet]][sheet_headers]
                    self.__parsed_data_to_spreadsheet(sheet_df, writer, sheet)

    def __load_from_csv(self, filepath) -> pd.DataFrame | None:
        df = None
        if os.path.exists(filepath):
            print(f' > Loading data from {filepath}')
            df = pd.read_csv(filepath)
            df.replace(['', 'None', 'nan', 'NaN'], [None, None, None, None], inplace=True)
        else:
            print(f' > File {filepath} does not exist')
        return df
    
    def remove_file(self, filepath):
        if os.path.exists(filepath):
            os.remove(filepath)

    ## GitHub Controller Management
    ##=============================================================================

    def validate_gh_auth(self):
        return self.gp.gh_auth_validated()
    
    def validate_gh_repo(self):
        return self.gp.gh_repo_validated()

    def set_gh_auth(self, username, token):
        if self.gp.set_gh_auth(username, token):
            self.gh_auth_verified = self.gp.auth_validated()
            self.__update_gh_config_opt('gh_username', username)
            self.__update_gh_config_opt('gh_token', token)
    
    

    def set_gh_owner(self, owner):
        success = self.gp.set_gh_repo_owner(owner)
        if success:
            self.__update_gh_config_opt('gh_repo_owner', owner)
            self.gh_repo_verified = self.gp.gh_repo_validated()
        return success
            
    def get_gh_repo_owner(self):
        return self.gp.get_gh_repo_owner()
    
    def set_gh_repo(self, repo):
        success = self.gp.set_gh_repo_name(repo)
        if success:
            self.__update_gh_config_opt('gh_repo_name', repo)
            self.gh_repo_verified = self.gp.gh_repo_validated()
        return success

    def get_gh_repo_name(self):
        return self.gp.get_gh_repo_name()
    
    

    ## API calling
    ##=============================================================================

    def make_gh_api_call(self):
        self.gp.retrieve_gh_commit_data()

    def taiga_retrieve_from_api(self):
        self.tp.retrieve_data_by_api()

    def taiga_retrieve_from_files(self):
        self.tp.retrieve_data_by_file()
    
    ## Data retrieval/setting
    ##=============================================================================

    
    
    def get_git_master_df(self) -> pd.DataFrame:
        return self.gp.get_current_commit_data()
    
    def get_tasks_from_git_data(self):
        return self.gp.get_tasks()
    
    def get_git_contributors(self):
        return self.gp.get_contributors()
    
    def set_git_master_df(self, df):
        self.gp.set_commit_data(df)
    
    def git_data_ready(self):
        return self.gp.data_is_ready()

    def check_url_exists(self, url):
        try:
            res = requests.get(url)
            if res.status_code >= 200 and res.status_code < 300:
                return True
            return False
        except:
            return False
    
    def convert_hyperlinks(self, filepath):
        if not os.path.exists(filepath):
            return
        
        try:
            wb = opyxl.load_workbook(filepath)
            for sheet in wb.worksheets:  # Iterate over all sheets
                for row in sheet.iter_rows():
                    for cell in row:
                        if isinstance(cell.value, str) and cell.value.startswith('=HYPERLINK('):
                            try:
                                # Extract URL from the formula
                                url_start = cell.value.find('"') + 1
                                url_end = cell.value.find('"', url_start)
                                url = cell.value[url_start:url_end] if url_start > 0 and url_end > url_start else ""

                                url = self.__conv_inv_val_to_none(url)

                                if url is not None and url != None:
                                    # Extract Friendly Text (if available)
                                    text_start = cell.value.find('"', url_end + 1) + 1
                                    text_end = cell.value.find('"', text_start)
                                    friendly_text = cell.value[text_start:text_end] if text_start > 0 and text_end > text_start else url

                                    # Set the hyperlink in the cell
                                    cell.value = friendly_text  # Display text
                                    cell.hyperlink = url  # Set hyperlink
                                    cell.style = "Hyperlink"  # Apply Excel hyperlink style

                            except Exception as e:
                                print(f"Error processing cell {cell.coordinate}: {e}")
                # Save changes
                wb.save(filepath)
        except:
            pass
    
    ## Data Formatting for Reports
    ##=============================================================================
    
    def __generate_hyperlink(self, url, text):
        return f'=HYPERLINK("{url}", "{text}")' if url is not None else None
    
    def generate_task_excel_entry(self, base_url, task_num, text_to_use=None):
        if task_num is not None:
            if text_to_use is not None:
                text = text_to_use
            else:
                text = f'Task-{int(task_num)}'
            if base_url is not None and base_url != '':
                url = f'{base_url}/task/{int(task_num)}'
                return self.__generate_hyperlink(url, text)      
            return text
        return None
    
    def generate_us_entry(self, us_num):
        if not pd.isna(us_num):
            return f'US-{int(us_num)}'
        return 'Storyless'
    
    def format_wsr_excel(self, df: Type[pd.DataFrame]):
        base_url = self.get_taiga_project_url()
        df['task'] = df['task'].apply(lambda x: self.generate_task_excel_entry(base_url, x))
        df['user_story'] = df['user_story'].apply(lambda x: self.generate_us_entry(x))
        return df
    
    def format_wsr_non_excel(self, df: Type[pd.DataFrame]):
        members_df = df['assigned_to'].copy(deep=True)
        members_df.dropna(how='all', inplace=True)
        members_df = members_df.drop_duplicates(keep='first').reset_index(drop=True)
        members = members_df.tolist()

        num_mems = len(members)

        data_columns = ['sprint', 'user_story', 'points', 'task', 'coding']
        data_columns.extend(members)

        data = [None] * len(df)
        for index, row in df.iterrows():
            us_num = row['user_story']
            task_num = row['task']
            assigned = row['assigned_to']

            sprint = row['sprint']
            user_story = int(us_num) if not pd.isna(us_num) else None
            points = int(row['points'])
            task = int(task_num) if task_num is not None else None
            coding = row['coding']

            mem_data = [None] * num_mems
            i = 0
            for mem in members:
                mem_data[i] = "100%" if assigned == mem else None
                i += 1

            row_data = [sprint, user_story, points, task, coding]
            row_data.extend(mem_data)
            data[index] = row_data
            
        result_df = pd.DataFrame(data, columns=data_columns)
        return result_df
    
    def format_icr_df_non_excel(self, commit_df: Type[pd.DataFrame], taiga_df: Type[pd.DataFrame] = None) -> pd.DataFrame:
        base_url = self.get_taiga_project_url()
        raw_task_df = self.tp.get_raw_task_data()

        data_columns = ['committer', 'task_url', 'task', 'task_status', 'coding', 'commit_url', 'commit_date', 'Percent_contributed']
        data = [None] * len(commit_df)
        for index, row in commit_df.iterrows():
            
            committer = row['committer']
            task_num = row['task']
            if not pd.isna(task_num):
                task_url = f'{base_url}/task/{int(task_num)}' if base_url is not None else None
                task = int(task_num) 
                is_complete = raw_task_df.loc[raw_task_df['ref'] == task_num, 'is_closed'].iloc[0] if raw_task_df is not None else None
                task_status = 'Complete' if is_complete else 'In-Process' if raw_task_df is not None else None
                coding = taiga_df.loc[taiga_df['task'] == task_num, 'coding'].iloc[0] if taiga_df is not None else None
            else:
                task_url = None
                task = None
                coding = None
                task_status = None

            commit_url = row['url']
            commit_date = row['az_date']

            row_data = [committer, task_url, task, task_status, coding, commit_url, commit_date, None]
            data[index] = row_data
            
        result_df = pd.DataFrame(data, columns=data_columns)
        return result_df
    
    def format_icr_excel(self, df: Type[pd.DataFrame]):
        df['task_url'] = df['task_url'].apply(lambda url: self.__generate_hyperlink(url, 'Taiga Task Link'))
        df['commit_url'] = df['commit_url'].apply(lambda url: self.__generate_hyperlink(url, 'Link to Commit'))
        return df
    
    