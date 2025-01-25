import io
import pandas as pd
import numpy as np
import requests

class TaigaProjectServicer:
    base_url = "https://api.taiga.io/api/v1"
    username = None
    password = None
    user_id = None

    token = None
    token_set_and_verified = False
    
    project_id = None
    project_name = None
    project_owner = None
    project_details_set = False

    api_import_ready = False

    def __init__(self, username=None, password=None, project_id=None, project_name=None, project_owner=None):
        if username and password:
            self.init_with_login_credentials(username, password)
            self._extract_user_id()
        if project_id and project_name and project_owner:
            self.init_project_details(project_id, project_name, project_owner)
        if not self.project_details_set:
            self._extract_projects()

    def init_with_login_credentials(self, username, password):
        self.username = username
        self.password = password
        token = self._refresh_token()
        if token:
            self.set_token(token)

    def init_with_comp_credentials(self, username, password, token):
        self.username = username
        self.password = password
        self.set_token(token)
        self._extract_user_id()
        self._extract_projects()

    def set_token(self, token):
        self.token = token
        self.token_set_and_verified = True
        self._validate_project_import_ready()

    def init_project_details(self, project_id, project_name, project_owner):
        self.project_id = project_id
        self.project_name = project_name
        self.project_owner = project_owner
        self.project_details_set = True
        self._validate_project_import_ready()

    def _refresh_token(self):
        url = f'{self.base_url}/auth'  # Change this to your Taiga API URL if self-hosted
        data = {
            "type": "normal",
            "username": self.username,
            "password": self.password
        }

        res = self._make_post_api_req(url, data=data)
        if res.status_code == 200:
            return res.json().get("auth_token")
        else:
            return None
        
    def get_available_projects(self):
        if not self.project_list:
            self._extract_projects()
        return self.project_list
        
    def set_project_by_name(self, project_name):
        for project in self.project_list:
            if project['name'] == project_name:
                self.init_project_details(project['id'], project['name'], project['owner'])
    
    ## API CALL METHODS
    ##==================================================================================================================

    def _api_token_header(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f'Bearer {self.token}'
        }    
        
    def _extract_user_id(self):
        if not self.user_id:
            url = f'{self.base_url}/users/me'
            res = self._make_get_api_req(url, self._api_token_header())
            if res.status_code == 200:
                self.user_id = res.json().get("id")

    def _extract_projects(self):
        project_list = None


        if self.user_id and self.token_set_and_verified:
            url = f'{self.base_url}/users/{self.user_id}/watched'
            res = self._make_get_api_req(url, self._api_token_header())
            if res.status_code == 200:
                project_list = []
                for project in res.json():
                    try:
                        if project.get("type") == 'project':
                            print(project)
                            project_list.append({
                                'id': project.get("id"),
                                'name': project.get("name"),
                                'owner': project.get("slug").split("-")[0]
                            })
                        print('TEST #')
                    except: 
                        print('EXCEPTION')
        else:
            print('ELSE')

        self.project_list = project_list
        

    def _make_post_api_req(self, url, header=None, data=None):
        res = requests.post(url=url, headers=header, json=data)
        if res.status_code == 200:
            return res
        else:
            self.token_set_and_verified = False
            self.api_import_ready = False
            if res.status_code == 401:
                token = self._refresh_token()
                if token:
                    self.set_token(token)
                if self.api_import_ready:
                    return requests.post(url=url, headers=self._api_token_header(), json=data)
    
    def _make_get_api_req(self, url, header, data=None):
        res = requests.get(url=url, headers=header, data=data)
        if res.status_code == 200:
            return res
        else:
            self.token_set_and_verified = False
            self.api_import_ready = False
            if res.status_code == 401:
                token = self._refresh_token()
                if token:
                    self.set_token(token)
                if self.api_import_ready:
                    return requests.get(url=url, headers=self._api_token_header(), json=data)

    def _validate_project_import_ready(self):
        if self.token_set_and_verified and self.project_details_set:
            try:
                url = f'{self.base_url}/projects/{self.project_id}'
                res = self._make_get_api_req(url, self._api_token_header())
                if res.status_code == 200:
                    self.api_import_ready = True
                else:
                    self.api_import_ready = False
            except:
                self.api_import_ready = False
        
    def _format_sprint_df(self, sprints : pd.DataFrame) -> pd.DataFrame:
        if sprints is not None:
            sprints = sprints.set_axis(['id', 'sprint_name', 'sprint_start', 'sprint_end'], axis=1)
            sprints['id'] = sprints['id'].astype(pd.Int64Dtype())
            sprints.sort_values(by='sprint_start', ascending=True, inplace=True)
            sprints['sprint_start'] = pd.to_datetime(sprints['sprint_start']).dt.strftime('%m/%d/%Y')
            sprints['sprint_end'] = pd.to_datetime(sprints['sprint_end']).dt.strftime('%m/%d/%Y')
            self._inv_val_to_none(sprints)
            sprints.dropna(inplace=True, how='all')
            sprints = sprints.drop_duplicates(subset=['id'], keep='first').reset_index(drop=True)
            
        return sprints

    def _format_members_df(self, members : pd.DataFrame) -> pd.DataFrame:
        if members is not None:
            if len(members.columns) != 2:
                members.insert(0, 'id', pd.NA)
            else:
                members['id'] = members['id'].astype(pd.Int64Dtype())

            members = members.set_axis(['id', 'username'], axis=1)
            self._inv_val_to_none(members)
            members.dropna(inplace=True, how='all')
            members = members.drop_duplicates(subset=['username'], keep='first').reset_index(drop=True)
            members.sort_values(by='id', ascending=True, inplace=True)
        return members


    def _format_us_df(self, us_df : pd.DataFrame) -> pd.DataFrame:
        if us_df is not None:
            us_df = us_df.set_axis(['id', 'us_num', 'is_complete', 'sprint_id', 'points'], axis=1)
            self._inv_val_to_none(us_df)
            us_df['sprint_id'] = us_df['sprint_id'].astype(pd.Int64Dtype())
            us_df['points'] = us_df['points'].astype(pd.Int64Dtype())
            us_df['points'].replace(pd.NA, 0, inplace=True)
            us_df.dropna(inplace=True, how='all')
            us_df = us_df.drop_duplicates(subset=['id'], keep='first').reset_index(drop=True)
            us_df.sort_values(by=['sprint_id', 'us_num'], ascending=[True, True], inplace=True)
        return us_df
    
    def _format_task_df(self, tasks_df : pd.DataFrame) -> pd.DataFrame:
        if tasks_df is not None:
            tasks_df = tasks_df.set_axis(['id', 'task_num', 'is_complete', 'us_id', 'assignee', 'task_subject'], axis=1)
            self._inv_val_to_none(tasks_df)
            tasks_df['us_id'] = tasks_df['us_id'].astype(pd.Int64Dtype())
            tasks_df.dropna(inplace=True, how='all')
            tasks_df = tasks_df.drop_duplicates(subset=['id'], keep='first').reset_index(drop=True)
            tasks_df.sort_values(by=['us_id', 'task_num'], ascending=[True, True], inplace=True)
        return tasks_df

    def _inv_val_to_none(self, df: pd.DataFrame):
        df.replace(['', 'None', 'nan', 'NaN', np.nan], [None, None, None, None, None], inplace=True)
    
    def _import_data_by_api(self) -> list[pd.DataFrame]:
        def import_data(url):
            header = {
                "Content-Type": "application/json",
                "Authorization": f'Bearer {self.token}',
                "x-disable-pagination": 'True'
            }
            return self._make_get_api_req(url, header)
        
        def import_sprint_data() -> pd.DataFrame:
            res = import_data(f'{self.base_url}/milestones?project={self.project_id}')
            if res.status_code == 200:
                try:
                    raw_sprints_df = pd.json_normalize(res.json())
                    return self._format_sprint_df(raw_sprints_df[['id', 'name', 'estimated_start', 'estimated_finish']])
                except: pass
            return None

        def import_member_data() -> pd.DataFrame:
            res = import_data(f'{self.base_url}/projects/{self.project_id}')
            if res.status_code == 200:
                try:
                    raw_members_df = pd.json_normalize(res.json().get('members'))
                    updated_raw_df = raw_members_df[raw_members_df['role'] == 9585684]

                    headers = ['id', 'username']
                    data = []

                    for index, row in updated_raw_df.iterrows():
                        mem_id = row['id']
                        uname = row['username']
                        fname = row['full_name']

                        username = uname
                        if pd.notna(uname):
                            if pd.notna(fname) and len(fname) < len(uname):
                                username = fname
                        data.append([mem_id, username])
                    members_df = pd.DataFrame(columns=headers, data=data)
                    return self._format_members_df(members_df)
                except: pass
            return None
            
        def import_us_data() -> pd.DataFrame:
            res = import_data(f'{self.base_url}/userstories?project={self.project_id}')
            if res.status_code == 200:
                try:
                    raw_us_df = pd.json_normalize(res.json())
                    return self._format_us_df(raw_us_df[['id', 'ref', 'is_closed', 'milestone', 'total_points']])
                except: pass
            return None
            
        def import_task_data(member_df) -> pd.DataFrame:
            res = import_data(f'{self.base_url}/tasks?project={self.project_id}')
            if res.status_code == 200:
                try:
                    raw_task_df = pd.json_normalize(res.json())
                    
                    headers = ['id', 'ref', 'is_closed', 'user_story', 'assigned_to', 'subject']
                    data = []

                    for index, row in raw_task_df.iterrows():
                        mem_id = row['assigned_to']
                        
                        task_id = row['id']
                        task = row['ref']
                        closed = row['is_closed']
                        us = row['user_story']
                        try:
                            username = member_df.loc[member_df['id'] == mem_id, 'username'].values[0]
                        except:
                            username = None
                        subject = row['subject']

                        row_data = [task_id, task, closed, us, username, subject]
                        data.append(row_data)
                    tasks_df = pd.DataFrame(columns=headers, data=data)
                    return self._format_task_df(tasks_df)
                except: pass
            return None

        members_df = sprints_df = us_df = task_df = None
        if self.api_import_ready:
            sprints_df = import_sprint_data()
            members_df = import_member_data()
            us_df = import_us_data()
            task_df = import_task_data(members_df)
        return sprints_df, members_df, us_df, task_df
    
    def _import_data_by_urls(self, us_url, task_url):
        def import_csv_by_url(url) -> pd.DataFrame:
            raw_data = None
            if url != "" and url is not None:
                res = requests.get(url)._content
                raw_data = pd.read_csv(io.StringIO(res.decode('utf-8')))
            return raw_data
        
        def parse_sprints(df) -> pd.DataFrame:
            return self._format_sprint_df(df)
        
        def parse_members(df) -> pd.DataFrame:
            headers = ['id', 'username']
            data = []

            for index, row in df.iterrows():
                uname = row['assigned_to']
                fname = row['assigned_to_full_name']

                username = uname
                if pd.notna(uname):
                    if pd.notna(fname) and len(fname) < len(uname):
                        username = fname
                data.append([pd.NA, username])
            members_df = pd.DataFrame(columns=headers, data=data)
            return self._format_members_df(members_df)

        def import_us_csv(url) -> pd.DataFrame:
            raw_us_df = import_csv_by_url(url)
            us_df = self._format_us_df(raw_us_df[['id', 'ref', 'is_closed', 'sprint_id', 'total-points']].copy(deep=True))
            sprint_df = parse_sprints(raw_us_df[['sprint_id', 'sprint', 'sprint_estimated_start', 'sprint_estimated_finish']].copy(deep=True))
            return sprint_df, us_df

        def import_task_csv(url) -> pd.DataFrame:
            raw_tasks_df = import_csv_by_url(url)
            tasks_df = self._format_task_df(raw_tasks_df[['id', 'ref', 'is_closed', 'user_story', 'assigned_to', 'subject']].copy(deep=True))
            members_df = parse_members(raw_tasks_df[['assigned_to', 'assigned_to_full_name']])
            return members_df, tasks_df

        if us_url and task_url:
            sprints_df, us_df = import_us_csv(us_url)
            members_df, task_df = import_task_csv(task_url)
        return sprints_df, members_df, us_df, task_df

    def _import_data_by_files(self, us_fp, task_fp):
        def import_by_file(fp) -> pd.DataFrame:
            raw_data = None
            if fp is not None and fp != '':
                match fp.split(".")[-1]:
                    case 'csv':
                        raw_data = pd.read_csv(fp)
                    case 'xlsx':
                        raw_data = pd.read_excel(fp)
                return raw_data

        def parse_sprints(df) -> pd.DataFrame:
            return self._format_sprint_df(df)
        
        def parse_members(df) -> pd.DataFrame:
            headers = ['id', 'username']
            data = []

            for index, row in df.iterrows():
                uname = row['assigned_to']
                fname = row['assigned_to_full_name']

                username = uname
                if pd.notna(uname):
                    if pd.notna(fname) and len(fname) < len(uname):
                        username = fname
                data.append([pd.NA, username])
            members_df = pd.DataFrame(columns=headers, data=data)
            return self._format_members_df(members_df)

        def import_us_data_by_file(fp) -> pd.DataFrame:
            raw_us_df = import_by_file(fp)
            us_df = self._format_us_df(raw_us_df[['id', 'ref', 'is_closed', 'sprint_id', 'total-points']].copy(deep=True))
            sprint_df = parse_sprints(raw_us_df[['sprint_id', 'sprint', 'sprint_estimated_start', 'sprint_estimated_finish']].copy(deep=True))
            return sprint_df, us_df

        def import_task_data_by_file(fp) -> pd.DataFrame:
            raw_tasks_df = import_by_file(fp)
            tasks_df = self._format_task_df(raw_tasks_df[['id', 'ref', 'is_closed', 'user_story', 'assigned_to', 'subject']].copy(deep=True))
            members_df = parse_members(raw_tasks_df[['assigned_to', 'assigned_to_full_name']])
            return members_df, tasks_df

        if us_fp and task_fp:
            sprints_df, us_df = import_us_data_by_file(us_fp)
            members_df, task_df = import_task_data_by_file(task_fp)
        return sprints_df, members_df, us_df, task_df