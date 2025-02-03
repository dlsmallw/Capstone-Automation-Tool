import io
import pandas as pd
import numpy as np
import requests
import traceback

class TaigaDataServicer:
    def __init__(self, username=None, password=None):
        self.base_url = "https://api.taiga.io/api/v1"
        self.username = None
        self.password = None
        self.user_id = None

        self.token = None
        self.token_set_and_verified = False

        if username and password:
            self.username = username
            self.password = password
            token = self._refresh_token()
            if token:
                self.set_token(token)
                self._extract_user_id()

    def update_user_credentials(self, username, password, token):
        self.username = username
        self.password = password
        self.set_token(token)
        self._extract_user_id()

    def set_token(self, token):
        self.token = token
        self.token_set_and_verified = True

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
    
    def get_credentials(self):
        return self.username, self.password
    
    def token_set(self):
        return self.token_set_and_verified
    
    def clear_linked_data(self):
        self.username = None
        self.password = None
        self.user_id = None
        self.token = None
        self.token_set_and_verified = False
    
    ## API CALL METHODS
    ##==================================================================================================================

    def _api_token_header(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f'Bearer {self.token}',
            "x-disable-pagination": 'True'
        }    
        
    def _extract_user_id(self):
        if not self.user_id:
            url = f'{self.base_url}/users/me'
            res = self._make_get_api_req(url, self._api_token_header())
            if res.status_code == 200:
                self.user_id = res.json().get("id")

    def get_watched_projects(self):
        if self.user_id and self.token_set_and_verified:
            url = f'{self.base_url}/users/{self.user_id}/watched'
            res = self._make_get_api_req(url, self._api_token_header())
            if res.status_code == 200:
                projects_data = []
                project_ids = []
                for project in res.json():
                    if project.get("type") == 'project':
                        p_id = project.get("id")
                        p_name = project.get("name")
                        p_owner = project.get("slug").split("-")[0]
                    else:
                        try:
                            p_slug = project.get("project_slug")
                            p_id = project.get("project")
                            p_owner, p_name = p_slug.split("-")
                        except Exception as e:
                            print(e)

                    if p_id and p_name and p_owner:
                        print(p_id)
                        if p_id not in project_ids:
                            print('Not Exists Already')
                            p_data = {
                                'id': p_id,
                                'project_name': p_name,
                                'project_owner': p_owner,
                                'is_selected': 0
                            }
                            projects_data.append(p_data)
                            project_ids.append(p_id)
        else:
            print('ELSE')
        return pd.DataFrame(data=projects_data, columns=['id', 'project_name', 'project_owner', 'is_selected'])
        
    def _make_post_api_req(self, url, header=None, data=None):
        res = requests.post(url=url, headers=header, json=data)
        if res.status_code == 200:
            return res
        else:
            self.token_set_and_verified = False
            if res.status_code == 401:
                token = self._refresh_token()
                if token:
                    self.set_token(token)
                    return requests.post(url=url, headers=self._api_token_header(), json=data)
                else: 
                    return res
    
    def _make_get_api_req(self, url, header, data=None):
        res = requests.get(url=url, headers=header, data=data)
        if res.status_code == 200:
            return res
        else:
            self.token_set_and_verified = False
            if res.status_code == 401:
                token = self._refresh_token()
                if token:
                    self.set_token(token)
                    return requests.get(url=url, headers=self._api_token_header(), json=data)
                else:
                    return res
                
    def _format_sprint_df(self, sprints : pd.DataFrame) -> pd.DataFrame:
        if sprints is not None:
            sprints = sprints.set_axis(['id', 'sprint_name', 'sprint_start', 'sprint_end'], axis=1)
        return sprints

    def _format_members_df(self, members : pd.DataFrame) -> pd.DataFrame:
        if members is not None:
            if len(members.columns) != 2:
                members.insert(0, 'id', pd.NA)
            members = members.set_axis(['id', 'username'], axis=1)
        return members

    def _format_us_df(self, us_df : pd.DataFrame) -> pd.DataFrame:
        if us_df is not None:
            us_df = us_df.set_axis(['id', 'us_num', 'is_complete', 'sprint', 'points'], axis=1)
        return us_df
    
    def _format_task_df(self, tasks_df : pd.DataFrame) -> pd.DataFrame:
        if tasks_df is not None:
            tasks_df = tasks_df.set_axis(['id', 'task_num', 'us_num', 'is_complete', 'assignee', 'task_subject'], axis=1)
            tasks_df.insert(3, 'is_coding', False)
        return tasks_df

    def _inv_val_to_none(self, df: pd.DataFrame):
        df.replace(['', 'None', 'nan', 'NaN', np.nan, None], pd.NA, inplace=True)
    
    def import_data_by_api(self, project_id) -> list[pd.DataFrame]:
        def import_data(url):
            header = {
                "Content-Type": "application/json",
                "Authorization": f'Bearer {self.token}',
                "x-disable-pagination": 'True'
            }
            return self._make_get_api_req(url, header)
        
        def import_sprint_data() -> pd.DataFrame:
            res = import_data(f'{self.base_url}/milestones?project={project_id}')
            if res.status_code == 200:
                raw_sprints_df = pd.json_normalize(res.json())
                return self._format_sprint_df(raw_sprints_df[['id', 'name', 'estimated_start', 'estimated_finish']])
            return None

        def import_member_data() -> pd.DataFrame:
            res = import_data(f'{self.base_url}/projects/{project_id}')
            if res.status_code == 200:
                raw_members_df = pd.json_normalize(res.json().get('members'))
                print(raw_members_df)
                updated_raw_df = raw_members_df[raw_members_df['role_name'] == 'Product Owner']

                headers = ['id', 'username']
                data = []

                for index, row in updated_raw_df.iterrows():
                    mem_id = row['id']
                    uname = row['username']
                    fname = row['full_name_display']

                    uname_valid = pd.notna(uname) and uname != ''
                    fname_valid = pd.notna(fname) and fname != ''

                    username = pd.NA
                    if uname_valid:
                        username = uname
                    if fname_valid and len(fname) < len(uname):
                        if not uname_valid or len(fname) < len(uname):
                            username = fname

                    data.append([mem_id, username])
                members_df = pd.DataFrame(columns=headers, data=data)
                return self._format_members_df(members_df)
            return None
            
        def import_us_data() -> pd.DataFrame:
            res = import_data(f'{self.base_url}/userstories?project={project_id}')
            if res.status_code == 200:
                raw_us_df = pd.json_normalize(res.json())
                return self._format_us_df(raw_us_df[['id', 'ref', 'is_closed', 'milestone_name', 'total_points']])
            return None
            
        def import_task_data(member_df : pd.DataFrame, us_df : pd.DataFrame) -> pd.DataFrame:
            res = import_data(f'{self.base_url}/tasks?project={project_id}')
            if res.status_code == 200:
                raw_task_df = pd.json_normalize(res.json())
                
                headers = ['id', 'ref', 'us_num', 'is_closed', 'assigned_to', 'subject']
                data = []

                for index, row in raw_task_df.iterrows():
                    task_id = row['id']
                    task = row['ref']
                    closed = row['is_closed']

                    try:
                        us_id = row['user_story']
                        us = us_df.loc[us_df['id'] == us_id, 'us_num'].iloc[0]
                    except:
                        us = pd.NA

                    try:
                        mem_id = row['assigned_to']
                        username = member_df.loc[member_df['id'] == mem_id, 'username'].iloc[0]
                    except:
                        username = pd.NA

                    subject = row['subject']

                    row_data = [task_id, task, us, closed, username, subject]
                    data.append(row_data)
                tasks_df = pd.DataFrame(columns=headers, data=data)
                return self._format_task_df(tasks_df)
            return None

        sprints_df = import_sprint_data()
        members_df = import_member_data()
        us_df = import_us_data()
        task_df = import_task_data(members_df, us_df)

        return sprints_df, members_df, us_df, task_df
    
    def _import_data_by_urls(self, us_url, task_url):
        def import_csv_by_url(url) -> pd.DataFrame:
            raw_data = None
            if url != "" and url is not None:
                res = requests.get(url)._content
                raw_data = pd.read_csv(io.StringIO(res.decode('utf-8')))
            return raw_data
        
        def parse_sprints(df : pd.DataFrame) -> pd.DataFrame:
            return self._format_sprint_df(df)
        
        def parse_members(df : pd.DataFrame, tasks_df : pd.DataFrame) -> pd.DataFrame:
            headers = ['id', 'username']
            data = []

            for index, row in df.iterrows():
                uname = row['assigned_to']
                fname = row['assigned_to_full_name']

                uname_valid = pd.notna(uname) and uname != ''
                fname_valid = pd.notna(fname) and fname != ''

                username = pd.NA
                if uname_valid:
                    username = uname
                if fname_valid and len(fname) < len(uname):
                    if not uname_valid or len(fname) < len(uname):
                        username = fname

                tasks_df.loc[tasks_df['assignee'] == uname, 'assignee'] = username

                data.append([pd.NA, username])
            members_df = pd.DataFrame(columns=headers, data=data)
            return self._format_members_df(members_df)

        def import_us_csv(url) -> pd.DataFrame:
            raw_us_df = import_csv_by_url(url)
            us_df = self._format_us_df(raw_us_df[['id', 'ref', 'is_closed', 'sprint', 'total-points']].copy(deep=True))
            sprint_df = parse_sprints(raw_us_df[['sprint_id', 'sprint', 'sprint_estimated_start', 'sprint_estimated_finish']].copy(deep=True))
            return sprint_df, us_df

        def import_task_csv(url) -> pd.DataFrame:
            raw_tasks_df = import_csv_by_url(url)
            tasks_df = self._format_task_df(raw_tasks_df[['id', 'ref', 'user_story', 'is_closed', 'assigned_to', 'subject']].copy(deep=True))
            members_df = parse_members(raw_tasks_df[['assigned_to', 'assigned_to_full_name']], tasks_df)
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

        def parse_sprints(df : pd.DataFrame) -> pd.DataFrame:
            return self._format_sprint_df(df)
        
        def parse_members(df : pd.DataFrame, tasks_df : pd.DataFrame) -> pd.DataFrame:
            headers = ['id', 'username']
            data = []

            for index, row in df.iterrows():
                uname = row['assigned_to']
                fname = row['assigned_to_full_name']

                uname_valid = pd.notna(uname) and uname != ''
                fname_valid = pd.notna(fname) and fname != ''

                username = pd.NA
                if uname_valid:
                    username = uname
                if fname_valid and len(fname) < len(uname):
                    if not uname_valid or len(fname) < len(uname):
                        username = fname

                tasks_df.loc[tasks_df['assignee'] == uname, 'assignee'] = username

                data.append([pd.NA, username])
            members_df = pd.DataFrame(columns=headers, data=data)
            return self._format_members_df(members_df)

        def import_us_data_by_file(fp) -> pd.DataFrame:
            raw_us_df = import_by_file(fp)
            us_df = self._format_us_df(raw_us_df[['id', 'ref', 'is_closed', 'sprint', 'total-points']].copy(deep=True))
            sprint_df = parse_sprints(raw_us_df[['sprint_id', 'sprint', 'sprint_estimated_start', 'sprint_estimated_finish']].copy(deep=True))
            return sprint_df, us_df

        def import_task_data_by_file(fp) -> pd.DataFrame:
            raw_tasks_df = import_by_file(fp)
            tasks_df = self._format_task_df(raw_tasks_df[['id', 'ref', 'user_story', 'is_closed', 'assigned_to', 'subject']].copy(deep=True))
            members_df = parse_members(raw_tasks_df[['assigned_to', 'assigned_to_full_name']], tasks_df)
            return members_df, tasks_df

        if us_fp and task_fp:
            sprints_df, us_df = import_us_data_by_file(us_fp)
            members_df, task_df = import_task_data_by_file(task_fp)
        return sprints_df, members_df, us_df, task_df