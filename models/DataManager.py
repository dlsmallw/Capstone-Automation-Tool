import configparser
import os

import openpyxl as opyxl
import pandas as pd
import numpy as np
from typing import Type
from models.GitCommitParser import GitParsingController
from models.Taiga import TaigaProjectServicer
from models.database.RecordDatabase import RecDB
import requests
import threading
import time

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
        self.ts : TaigaProjectServicer = None
        self.gp : GitParsingController = None

        ## Taiga-related variables
        #### Projects
        self.taiga_projects_df = None
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

        ## GitHub-related variables
        ## TODO
        ## GitLab-related variables
        ## TODO

        ## Instance initializations and data loading
        self.db = db
        self.ts = self.init_taiga_servicer()

        self.__load_config()

    ## Initialization Functions
    ##=============================================================================

    def get_linked_project(self):
        return self.sel_pid, self.sel_project_name, self.sel_project_owner

    def set_linked_taiga_project(self, pid, name, owner):
        if pid and name and owner:
            self.sel_pid = pid
            self.sel_project_name = name
            self.sel_project_owner = owner
            self.project_selected = True

    def load_taiga_projects(self):
        projects = self.db.select('taiga_projects')
        if len(projects) > 0:
            self.taiga_projects_df = pd.DataFrame(data=projects, columns=['id', 'project_name', 'project_owner', 'is_selected'])
            result = self.db.select('taiga_projects', ['id', 'project_name', 'project_owner'], {'is_selected': 1})
            if result and len(result) > 0:
                self.set_linked_taiga_project(result[0][0], result[0][1], result[0][2])

    def init_taiga_servicer(self):
        self.load_taiga_projects()
        self.load_saved_taiga_data()
        return TaigaProjectServicer(self.load_taiga_credentials())
    
    def load_saved_taiga_data(self):
        self.update_sprints_df(self.db.table_to_df('sprints'))
        self.update_members_df(self.db.table_to_df('members'))
        self.update_us_df(self.db.table_to_df('userstories'))
        self.update_tasks_df(self.db.table_to_df('tasks'))

    def init_git_servicer(self):
        pass

    def get_site_credentials_from_db(self, site_name):
        return self.db.decrypt(tuple(self.db.select('sites', ['username', 'user_pwd', 'site_token'], {'site_name': site_name})[0]))
    
    def load_taiga_credentials(self):
        return self.get_site_credentials_from_db(TAIGA)[0:2]
    
    def load_gh_credential(self):
        return self.get_site_credentials_from_db(GITHUB)[-1]
    
    def load_gl_credential(self):
        return self.get_site_credentials_from_db(GITLAB)[-1]
    
    def get_taiga_credentials(self):
        return self.ts.get_credentials()

    def get_gh_credentials(self):
        pass

    def get_gl_credentials(self):
        pass
    
    def update_user_credentials(self, site_name, username='NULL', pwd='NULL', token='NULL'):
        return self.db.update('sites', dict(zip(['username', 'user_pwd', 'site_token'], self.db.encrypt([username, pwd, token]))), {'site_name': site_name})
    
    def update_taiga_credentials(self, uname, pwd):
        is_success = self.update_user_credentials(TAIGA, username=uname, pwd=pwd)
        return is_success
    
    def update_gh_credentials(self, token):
        is_success = self.update_user_credentials(GITHUB, token=token)
        return is_success
    
    def update_gl_credentials(self, token):
        is_success = self.update_user_credentials(GITLAB, token=token)
        return is_success

    ## Util Functions
    ##=============================================================================

    def taiga_data_ready(self):
        return self.taiga_data_available

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

    def update_projects_df(self, new_df):
        def format_df(df: pd.DataFrame) -> pd.DataFrame:
            df['id'] = df['id'].astype(pd.Int64Dtype())
            self._inv_val_format(df)
            df.dropna(inplace=True, how='all')
            df = df.drop_duplicates(subset=['id'], keep='first').reset_index(drop=True)
            df.sort_values(by='id', ascending=True, inplace=True)
            return df

        if new_df is not None and len(new_df) > 0:
            self.taiga_projects_df = self.update_df(self.taiga_projects_df, format_df(new_df))
            self.db.df_to_table('taiga_projects', self.taiga_projects_df)
            self.taiga_projects_df = format_df(self.db.table_to_df('taiga_projects'))

    def pull_taiga_projects(self):
        projects = self.ts.get_watched_projects()
        if projects is not None and not projects.empty:
             self.update_projects_df(projects)
        
    def wait_for_projects(self):
        self.pull_taiga_projects()
        self.db.df_to_table('taiga_projects', self.taiga_projects_df)
        return True
    
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
        
    

    ## Taiga Data Importing
    ##=============================================================================

    def _inv_val_format(self, df: pd.DataFrame):
        df.replace(['', 'None', 'nan', 'NaN', np.nan, None], pd.NA, inplace=True)

    def get_us_num_by_id(self, us_id):
        return self.get_cell_val_from_df(self.us_df, 'us_num', 'id', us_id)

    def update_sprints_df(self, new_df: pd.DataFrame):
        def to_table_format(df: pd.DataFrame) -> pd.DataFrame:
            df['sprint_start'] = pd.to_datetime(df['sprint_start']).dt.strftime('%m/%d/%Y')
            df['sprint_end'] = pd.to_datetime(df['sprint_end']).dt.strftime('%m/%d/%Y')
            return df

        def format_df(df: pd.DataFrame) -> pd.DataFrame:
            df['id'] = df['id'].astype(pd.Int64Dtype())
            df['sprint_start'] = pd.to_datetime(df['sprint_start'])
            df['sprint_end'] = pd.to_datetime(df['sprint_end'])
            self._inv_val_format(df)
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
            df['id'] = df['id'].astype(pd.Int64Dtype())
            self._inv_val_format(df)
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
            df['id'] = df['id'].astype(pd.Int64Dtype())
            df['us_num'] = df['us_num'].astype(pd.Int64Dtype())
            df['points'] = df['points'].astype(pd.Int64Dtype())
            df['is_complete'] = df['is_complete'].astype(pd.BooleanDtype())
            df['points'].replace(pd.NA, 0, inplace=True)
            
            self._inv_val_format(df)
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
            # print(f'Sprints DF Length: {len(sprints_df)}')
            # print(sprints_df)
            # print(f'Members DF Length: {len(members_df)}')
            # print(members_df)
            # print(f'US DF Length: {len(us_df)}')
            # print(us_df)
            # print(f'Tasks DF Length: {len(task_df)}')
            # print(task_df)

    def get_us_df(self) -> pd.DataFrame:
        return self.us_df
    
    def get_task_df(self) -> pd.DataFrame:
        return self.tasks_df
    
    def get_members_df(self) -> pd.DataFrame:
        return self.members_df
    
    def get_sprints_df(self) -> pd.DataFrame:
        return self.sprints_df

    ## Config Management
    ##=============================================================================

    def __conv_inv_val_to_none(self, val):
        invalid_values = ['', 'None', 'none', 'NaN', 'nan', np.nan, None]

        if val in invalid_values:
            return None
        return val

    def __load_gp_config(self):
        config = self.config_parser

        if config.has_section('github-config'):
            gh_token = config.get('github-config', 'gh_token')
            repo_owner = config.get('github-config', 'gh_repo_owner')
            repo_name = config.get('github-config', 'gh_repo_name')

            self.gp = GitParsingController(config, gh_token, repo_owner, repo_name)
        else:
            self.__build_gp_section()

    def __load_taiga_config(self):
        config = self.config_parser

        if config.has_section('taiga-config'):
            self.us_report_url = config.get('taiga-config', 'us_report_api_url')
            self.task_report_url = config.get('taiga-config', 'task_report_api_url')
        else:
            self.__build_taiga_section()

    def __load_config(self):
        self.config_parser = configparser.RawConfigParser()

        if not os.path.exists(self.config_fp):
            open(self.config_fp, 'w').close()
            self.__build_config_file()
            
        self.config_parser.read(self.config_fp)         
        self.__load_gp_config()
        self.__load_taiga_config()

    def __get_config_opt_val(self, section, opt):
        config = self.config_parser
        return config.get(section, opt, fallback=None)

    def __build_gp_section(self):
        config = self.config_parser

        config.add_section('github-config')
        self.__update_gh_config_opt('gh_token', None)
        self.__update_gh_config_opt('gh_repo_owner', None)
        self.__update_gh_config_opt('gh_repo_name', None)
        self.__update_gh_config_opt('gh_latest_commit_date', None)

        config.add_section('gitlab-config')
        self.__update_gl_config_opt('gl_token', None)
        self.__update_gl_config_opt('gl_project_id', None)
        self.__update_gl_config_opt('gl_latest_commit_date', None)

    def __build_taiga_section(self):
        config = self.config_parser
        config.add_section('taiga-config')
        self.__update_taiga_config_opt('us_report_api_url', None)
        self.__update_taiga_config_opt('task_report_api_url', None)
        self.__update_taiga_config_opt('taiga_project_url', None)

    def __build_config_file(self):
        self.__build_taiga_section()
        self.__build_gp_section()

    def __update_gh_config_opt(self, option, value):
        self.__update_option_in_config('github-config', option, value)

    def __update_gl_config_opt(self, option, value):
        self.__update_option_in_config('gitlab-config', option, value)

    def __update_taiga_config_opt(self, option, value):
        self.__update_option_in_config('taiga-config', option, value)

    def __update_option_in_config(self, section, option, value):
        config = self.config_parser
        config.set(section, option, value)
        with open(self.config_fp, 'w') as configfile:
            config.write(configfile)
            configfile.close()

    def clear_config(self):
        self.__update_taiga_config_opt('us_report_api_url', None)
        self.__update_taiga_config_opt('task_report_api_url', None)

        self.__update_gh_config_opt('gh_token', None)
        self.__update_gh_config_opt('gh_repo_owner', None)
        self.__update_gh_config_opt('gh_repo_name', None)
        self.__update_gh_config_opt('gh_latest_commit_date', None)

        self.__update_gl_config_opt('gl_token', None)
        self.__update_gl_config_opt('gl_project_id', None)
        self.__update_gl_config_opt('gl_latest_commit_date', None)

    ## GH/Taiga Raw Data saving/loading
    ##=============================================================================

    def __load_raw_data(self):
        self.tp.load_raw_data(self.__load_from_csv('./raw_data/raw_taiga_master_data.csv'), 
                              self.__load_from_csv('./raw_data/raw_taiga_us_data.csv'), 
                              self.__load_from_csv('./raw_data/raw_taiga_task_data.csv'))

        self.gp.load_raw_data(self.__load_from_csv('./raw_data/raw_git_master_data.csv'))

    def store_raw_taiga_data(self):
        raw_master_df = self.tp.get_master_df()
        raw_us_df = self.tp.get_raw_us_data()
        raw_task_df = self.tp.get_raw_task_data()

        if raw_master_df is not None:
            self.write_to_csv('./raw_data/raw_taiga_master_data.csv', raw_master_df)

        if raw_us_df is not None:
            self.write_to_csv('./raw_data/raw_taiga_us_data.csv', raw_us_df)

        if raw_task_df is not None:
            self.write_to_csv('./raw_data/raw_taiga_task_data.csv', raw_task_df)

    def store_raw_git_data(self, df):
        self.write_to_csv('./raw_data/raw_git_master_data.csv', df)

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
    
    def set_gh_token(self, token):
        success = self.gp.set_gh_token(token)
        if success:
            self.__update_gh_config_opt('gh_token', token)
            self.gh_auth_verified = self.gp.gh_auth_validated()
        return success
    
    def get_gh_token(self):
        return self.gp.get_gh_token()

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
    
    ## Taiga Controller Management
    ##=============================================================================

    def set_taiga_us_api_url(self, url):
        self.__update_taiga_config_opt('us_report_api_url', url)

    def get_taiga_us_csv_url(self):
        return self.us_report_url

    def set_taiga_task_api_url(self, url):
        self.__update_taiga_config_opt('task_report_api_url', url)

    def get_taiga_task_csv_url(self):
        return self.task_report_url

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

    def get_members(self) -> list:
        return self.tp.get_members()
    
    def get_sprints(self) -> list:
        return self.tp.get_sprints()
    
    def get_user_stories(self) -> list:
        return self.tp.get_user_stories()

    def get_taiga_master_df(self):
        return self.tp.get_master_df()
    
    def get_git_master_df(self) -> pd.DataFrame:
        return self.gp.get_current_commit_data()
    
    def get_tasks_from_git_data(self):
        return self.gp.get_tasks()
    
    def get_git_contributors(self):
        return self.gp.get_contributors()
    
    def set_git_master_df(self, df):
        self.gp.set_commit_data(df)
    
    def set_taiga_master_df(self, df):
        self.tp.set_master_df(df)

    def clear_git_commit_data(self):
        self.gp.clear_data()
        self.remove_file('./raw_data/raw_git_master_data.csv')

    def clear_taiga_data(self):
        self.tp.clear_data()
        self.remove_file('./raw_data/raw_taiga_master_data.csv')
        self.remove_file('./raw_data/raw_taiga_us_data.csv')
        self.remove_file('./raw_data/raw_taiga_task_data.csv')
    
    
    
    def git_data_ready(self):
        return self.gp.data_is_ready()
    
    def get_taiga_project_url(self):
        return self.__get_config_opt_val('taiga-config', 'taiga_project_url')
    
    def set_taiga_project_url(self, project_url):
        self.__update_taiga_config_opt('taiga_project_url', project_url)

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
    
    