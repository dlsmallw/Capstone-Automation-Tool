import configparser
import os


from backend import GitHubCommitParser, TaigaCSVParser

class DataController:
    config_fp = os.path.join(os.getcwd(), 'config.txt')
    config_parser = None

    tp = None
    ghp = None

    gh_auth_verified = False
    gh_repo_verified = False

    def __init__(self):
        self.__load_config()

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
            self.__build_config_section(config)

    def __load_config(self):
        config = configparser.RawConfigParser()

        if not os.path.exists(self.config_fp):
            open(self.config_fp, 'w').close()
            self.__build_config_file()            
        config.read(self.config_fp)
        self.config_parser = config  # for future use
        self.__load_gh_config()
        self.__load_taiga_config()

    def __build_gh_section(self):
        config = self.config_parser
        config.add_section('github-config')
        self.__update_option_in_config('gh_username', None)
        self.__update_option_in_config('gh_token', None)
        self.__update_option_in_config('gh_repo_owner', None)
        self.__update_option_in_config('gh_repo_name', None)

    def __build_taiga_section(self):
        config = self.config_parser
        config.add_section('taiga-config')
        self.__update_option_in_config('us_report_api_url', None)
        self.__update_option_in_config('task_report_api_url', None)

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

    def get_repo_owner(self):
        return self.ghp.get_repo_owner()
    
    def set_gh_repo(self, repo):
        success = self.ghp.set_repo_name(repo)
        if success:
            self.__update_gh_config_opt('gh_repo_name', repo)
            self.gh_repo_verified = self.ghp.validate_repo_exists()


    def get_repo_name(self):
        return self.ghp.get_repo_name()
    
    def set_taiga_us_api_url(self, url):
        self.tp.set_us_report_url(url)
        self.__update_taiga_config_opt('us_report_api_url', url)

    def get_taiga_us_api_url(self):
        return self.tp.get_us_report_url()

    def set_taiga_task_url(self, url):
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
    
    ## Dataframe retrieval
    ##=============================================================================

    def get_taiga_master_df(self):
        return self.tp.get_master_df()
    
    def get_gh_master_df(self):
        return self.ghp.get_all_commit_data()