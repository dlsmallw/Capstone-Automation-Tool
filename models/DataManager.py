import configparser
import os
import openpyxl as opyxl
import pandas as pd
from typing import Type
from models import TaigaCSVParser, GitHubCommitParser
import requests

class DataController:
    config_fp = os.path.join(os.getcwd(), 'config.txt')
    config_parser = None

    tp = None
    ghp = None

    gh_auth_verified = False
    gh_repo_verified = False

    def __init__(self):
        self.__load_config()
        self.__load_raw_data()

    ## Config Management
    ##=============================================================================

    def __load_gh_config(self):
        config = self.config_parser

        if config.has_section('github-config'):
            gh_username = config.get('github-config', 'gh_username')
            gh_token = config.get('github-config', 'gh_token')
            repo_owner = config.get('github-config', 'gh_repo_owner')
            repo_name = config.get('github-config', 'gh_repo_name')

            self.ghp = GitHubCommitParser.GitHubParsingController(gh_username, gh_token, repo_owner, repo_name)
        else:
            self.__build_gh_section()

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
        self.__load_gh_config()
        self.__load_taiga_config()

    def __get_config_opt_val(self, section, opt):
        config = self.config_parser
        return config.get(section, opt)

    def __build_gh_section(self):
        config = self.config_parser
        config.add_section('github-config')
        self.__update_gh_config_opt('gh_username', None)
        self.__update_gh_config_opt('gh_token', None)
        self.__update_gh_config_opt('gh_repo_owner', None)
        self.__update_gh_config_opt('gh_repo_name', None)

    def __build_taiga_section(self):
        config = self.config_parser
        config.add_section('taiga-config')
        self.__update_taiga_config_opt('us_report_api_url', None)
        self.__update_taiga_config_opt('task_report_api_url', None)
        self.__update_taiga_config_opt('taiga_project_url', None)

    def __build_config_file(self):
        self.__build_taiga_section()
        self.__build_gh_section()

    def __update_gh_config_opt(self, option, value):
        self.__update_option_in_config('github-config', option, value)

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
        self.__update_gh_config_opt('gh_username', None)
        self.__update_gh_config_opt('gh_token', None)
        self.__update_gh_config_opt('gh_repo_owner', None)
        self.__update_gh_config_opt('gh_repo_name', None)

    ## GH/Taiga Controller Management
    ##=============================================================================

    def set_gh_auth(self, username, token):
        if self.ghp.set_gh_auth(username, token):
            self.gh_auth_verified = self.ghp.auth_validated()
            self.__update_gh_config_opt('gh_username', username)
            self.__update_gh_config_opt('gh_token', token)
    
    def set_gh_username(self, username):
        success = self.ghp.set_gh_username(username)
        if success:
            self.__update_gh_config_opt('gh_username', username)
            token = self.ghp.get_token()
            if self.ghp.validate_token(token):
                self.gh_auth_verified = self.ghp.set_gh_auth(username, token)
        return success

    def get_gh_username(self):
        return self.ghp.get_username()
    
    def set_gh_token(self, token):
        success = self.ghp.set_gh_token(token)
        if success:
            self.__update_gh_config_opt('gh_token', token)
            username = self.ghp.get_username()
            if self.ghp.validate_username(username):
                self.gh_auth_verified = self.ghp.set_gh_auth(username, token)
        return success
    
    def get_gh_token(self):
        return self.ghp.get_token()
    
    def set_gh_repo_details(self, owner, repo):
        if self.ghp.set_repo_details(owner, repo):
            self.gh_repo_verified = self.ghp.repo_validated()
            self.__update_gh_config_opt('gh_repo_owner', owner)
            self.__update_gh_config_opt('gh_repo_name', repo)

    def set_gh_owner(self, owner):
        success = self.ghp.set_repo_owner_username(owner)
        if success:
            self.__update_gh_config_opt('gh_repo_owner', owner)
            self.gh_repo_verified = self.ghp.validate_repo_exists()
        return success
            

    def get_repo_owner(self):
        return self.ghp.get_repo_owner()
    
    def set_gh_repo(self, repo):
        success = self.ghp.set_repo_name(repo)
        if success:
            self.__update_gh_config_opt('gh_repo_name', repo)
            self.gh_repo_verified = self.ghp.validate_repo_exists()
        return success

    def get_repo_name(self):
        return self.ghp.get_repo_name()
    
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

    def github_retrieve_and_parse(self):
        self.ghp.retrieve_and_parse_commit_data()

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
    
    def get_gh_master_df(self) -> pd.DataFrame:
        return self.ghp.get_all_commit_data()
    
    def get_tasks(self):
        return self.ghp.get_tasks_list()
    
    def get_contributors(self):
        return self.ghp.get_contributors()
    
    def set_gh_master_df(self, df):
        self.ghp.set_commit_data(df)
    
    def set_taiga_master_df(self, df):
        self.tp.set_master_df(df)

    def clear_gh_data(self):
        self.ghp.clear_data()
        self.remove_file('./raw_data/raw_github_master_data.csv')

    def clear_taiga_data(self):
        self.tp.clear_data()
        self.remove_file('./raw_data/raw_taiga_master_data.csv')
        self.remove_file('./raw_data/raw_taiga_us_data.csv')
        self.remove_file('./raw_data/raw_taiga_task_data.csv')
    
    def taiga_data_ready(self):
        return self.tp.data_is_ready()
    
    def github_data_ready(self):
        return self.ghp.data_is_ready()
    
    def __generate_hyperlink(self, url, text):
        return f'=HYPERLINK("{url}", "{text}")'
    
    def generate_task_excel_entry(self, base_url, task_num):
        if task_num is not None:
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
    
    
    
    def get_taiga_project_url(self):
        return self.__get_config_opt_val('taiga-config', 'taiga_project_url')
    
    def set_taiga_project_url(self, project_url):
        self.__update_taiga_config_opt('taiga_project_url', project_url)

    def check_url_exists(self, url):
        res = requests.get(url)

        if res.status_code >= 200 and res.status_code < 300:
            return True
        return False
    
    ## Raw Data Storage/Loading
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
    
    def __load_raw_data(self):
        self.tp.load_raw_data(self.__load_from_csv('./raw_data/raw_taiga_master_data.csv'), 
                              self.__load_from_csv('./raw_data/raw_taiga_us_data.csv'), 
                              self.__load_from_csv('./raw_data/raw_taiga_task_data.csv'))

        self.ghp.load_raw_data(self.__load_from_csv('./raw_data/raw_github_master_data.csv'))

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

    def store_raw_github_data(self, df):
        self.write_to_csv('./raw_data/raw_github_master_data.csv', df)

    def remove_file(self, filepath):
        if os.path.exists(filepath):
            os.remove(filepath)

