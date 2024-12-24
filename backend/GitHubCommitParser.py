import os
import configparser
import requests
import pandas as pd
import re
import json


class GitHubParsingController:
    config_fp = os.path.join(os.getcwd(), 'config.txt')
    config_parser = None

    gh_base_url = "https://api.github.com"

    github_auth = {
        "username": None,
        "token": None
    }

    github_repo_info = {
        "owner": None,
        "repo": None
    }

    github_data = {
        "contributors": None,
        "commit_data": []
    }

    def __init__(self):
        self.__load_config()

    ## Config Initialization and Management
    ##=============================================================================

    def __build_config_section(self, config):
        config.add_section('github-config')
        self.__update_option_in_config('gh_username', None)
        self.__update_option_in_config('gh_token', None)
        self.__update_option_in_config('gh_repo_owner', None)
        self.__update_option_in_config('gh_repo_name', None)

    def __load_config(self):
        config = configparser.RawConfigParser()

        if not os.path.exists(self.config_fp):
            open(self.config_fp, 'w').close()
            
        config.read(self.config_fp)
        self.config_parser = config  # for future use

        if config.has_section('github-config'):
            gh_username = config.get('github-config', 'gh_username')
            gh_token = config.get('github-config', 'gh_token')
            repo_owner = config.get('github-config', 'gh_repo_owner')
            repo_name = config.get('github-config', 'gh_repo_name')

            if self.__validate_username(gh_username):
                self.github_auth["username"] = gh_username
            if self.__validate_token(gh_token):
                self.github_auth["token"] = gh_token
            if self.__validate_username(gh_username):
                self.github_repo_info["owner"] = repo_owner
            if repo_name != "" and repo_name is not None:
                self.github_repo_info["repo"] = repo_name
        else:
            self.__build_config_section(config)

    def clear_config(self):
        config = self.config_parser
        config.set('github-config', 'gh_username', None)
        config.set('github-config', 'gh_token', None)
        config.set('github-config', 'gh_repo_owner', None)
        config.set('github-config', 'gh_repo_name', None)

        with open(self.config_fp, 'w') as configfile:
            config.write(configfile)
            configfile.close()

    def __update_option_in_config(self, option, value):
        config = self.config_parser
        config.set('github-config', option, value)
        with open(self.config_fp, 'w') as configfile:
            config.write(configfile)
            configfile.close()

    ## Auth Management
    ##=============================================================================
    
    def __validate_username(self, username):
        return username != "" and username is not None
    
    def __validate_token(self, token):
        return token != "" and token is not None

    def validate_auth(self, username, token):
        if self.__validate_username(username) and self.__validate_token(token):
            res = self.__make_gh_api_call(f'{self.gh_base_url}/user')
            return res.status_code >= 200 and res.status_code < 300
        return False

    def set_gh_username(self, username):
        if self.__validate_username(username):
            self.github_auth["username"] = username
            self.__update_option_in_config('gh_username', username)
            return True
        
        return False

    def set_gh_token(self, token):
        if self.__validate_token(token):
            self.github_auth["token"] = token
            self.__update_option_in_config('gh_token', token)
            return True
        
        return False

    def set_gh_auth(self, username, token):
        auth_set_success = True

        if not self.set_gh_username(username):
            print('Invalid username provided')
            auth_set_success = False

        if not self.set_gh_token(token):
            print('Invalid token provided')
            auth_set_success = False

        if auth_set_success:
            return self.validate_auth(username, token)
        else:
            return auth_set_success
        
    ## Target Repository Management
    ##=============================================================================
        
    def set_repo_owner_username(self, owner):
        if self.__validate_username(owner):
            self.github_repo_info["owner"] = owner
            self.__update_option_in_config('gh_repo_owner', owner)
            return True
        
        return False
    
    def set_repo_name(self, repo):
        if repo != "" and repo is not None:
            self.github_repo_info["repo"] = repo
            self.__update_option_in_config('gh_repo_name', repo)
            return True
        
        return False
    
    def validate_repo_exists(self):
        owner = self.github_repo_info["owner"]
        repo = self.github_repo_info["repo"]

        url = f'{self.gh_base_url}/repos/{owner}/{repo}'
        header = self.__get_auth_header()

        res = requests.get(url, headers=header)

        if res.status_code >= 200 and res.status_code < 300:
            return True
        
        return False
    
    def set_repo_details(self, owner, repo):
        repo_details_success = True

        if not self.set_repo_owner_username(owner):
            print('Invalid repo owner username')
            repo_details_success = False

        if not self.set_repo_name(repo):
            print('Invalid repo name')
            repo_details_success = False

        if repo_details_success:
            return self.validate_repo_exists()
        else:
            return repo_details_success
        
    ## API Call Management
    ##=============================================================================
        
    def __get_auth_header(self):
        return {
            'Authorization': f'token {self.github_auth["token"]}' 
        }
    
    def __make_gh_api_call(self, url):
        header = self.__get_auth_header()
        return requests.get(url, headers=header)
    
    def __get_paginated_data(self, url):
        pagesRemaining = True
        commits = []

        next_url = url
        
        while pagesRemaining:
            res = self.__make_gh_api_call(next_url)
            links = res.links
            data = res.json()

            for commit_entry in data:
                commit_obj = commit_entry["commit"]
                id = commit_entry['sha']
                url = commit_entry['html_url']
                commit_msg = commit_obj['message']
                commit_date = commit_obj['committer']['date']

                commits.append({
                    "id": id,
                    "url": url,
                    "message": commit_msg,
                    "date": commit_date
                })

            try:
                next_url = links.get('next').get('url')
            except:
                pagesRemaining = False
        
        return pd.json_normalize(commits)
    
    def get_repo_contributors(self):
        owner = self.github_repo_info["owner"]
        repo = self.github_repo_info["repo"]

        url = f'{self.gh_base_url}/repos/{owner}/{repo}/contributors'

        res = self.__make_gh_api_call(url).json()

        contributors = []

        for entry in res:
            contributors.append(entry['login'])

        self.github_data["contributors"] = contributors
    
    def get_commits_by_committer(self, committer):
        owner = self.github_repo_info["owner"]
        repo = self.github_repo_info["repo"]
        url = f'{self.gh_base_url}/repos/{owner}/{repo}/commits?committer={committer}&per_page=100'
        
        commits_df = self.__get_paginated_data(url)
        print(commits_df)

        return commits_df
    
    def parse_commit_data(self):
        self.get_repo_contributors()
        contributors = self.github_data['contributors']
        commits_data = []

        for commiter in contributors:
            print(f'{commiter}:')
            commits_data.append({
                    f'{commiter}': self.get_commits_by_committer(commiter)
                })

        self.github_data['commit_data'] = commits_data
        return commits_data
            
