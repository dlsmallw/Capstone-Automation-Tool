import configparser
import os

import openpyxl as opyxl
import pandas as pd
import numpy as np
from typing import Type
from models import GitCommitParser, TaigaCSVParser
import requests

class DataController:
    config_fp = os.path.join(os.getcwd(), 'config.txt')
    config_parser = None

    tp = None
    gp = None

    gh_auth_verified = False
    gh_repo_verified = False

    def __init__(self):
        self.__load_config()
        self.__load_raw_data()

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

            self.gp = GitCommitParser.GitParsingController(config, gh_token, repo_owner, repo_name)
        else:
            self.__build_gp_section()

    def __load_taiga_config(self):
        config = self.config_parser

        if config.has_section('taiga-config'):
            us_report_url = config.get('taiga-config', 'us_report_api_url')
            task_report_url = config.get('taiga-config', 'task_report_api_url')

            self.tp = TaigaCSVParser.TaigaParsingController(us_report_url, task_report_url)
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
        self.tp.set_us_report_url(url)
        self.__update_taiga_config_opt('us_report_api_url', url)

    def get_taiga_us_api_url(self):
        return self.tp.get_us_report_url()

    def set_taiga_task_api_url(self, url):
        self.tp.set_task_report_url(url)
        self.__update_taiga_config_opt('task_report_api_url', url)

    def get_taiga_task_api_url(self):
        return self.tp.get_task_report_url()

    def set_us_fp(self, fp):
        self.tp.set_us_fp(fp)

    def get_us_fp(self):
        return self.tp.get_us_fp()

    def set_task_fp(self, fp):
        self.tp.set_task_fp(fp)

    def get_task_fp(self):
        return self.tp.get_task_fp()

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
    
    def taiga_data_ready(self):
        return self.tp.data_is_ready()
    
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
    
    