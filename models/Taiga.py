import io
import pandas as pd
import numpy as np
import requests
import traceback

class TaigaProjectServicer:
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

    def get_watched_projects(self):
        if self.user_id and self.token_set_and_verified:
            url = f'{self.base_url}/users/{self.user_id}/watched'
            res = self._make_get_api_req(url, self._api_token_header())
            if res.status_code == 200:
                projects_data = []
                for project in res.json():
                    try:
                        if project.get("type") == 'project':
                            p_id = project.get("id")
                            p_name = project.get("name")
                            p_owner = project.get("slug").split("-")[0]
                            p_data = {
                                'id': p_id,
                                'project_name': p_name,
                                'project_owner': p_owner,
                                'is_selected': 0
                            }
                            projects_data.append(p_data)
                    except Exception as e:
                        exc_type = type(e),__name__
                        exc_cause = 'No Cause/Context Provided'
                        cause = e.__cause__ or e.__context__
                        if cause:
                            exc_cause = str(cause)

                        print(f'{exc_type}: {exc_cause}')
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
            tasks_df.insert(2, 'is_coding', False)
            self._inv_val_to_none(tasks_df)
            tasks_df['us_id'] = tasks_df['us_id'].astype(pd.Int64Dtype())
            tasks_df.dropna(inplace=True, how='all')
            tasks_df = tasks_df.drop_duplicates(subset=['id'], keep='first').reset_index(drop=True)
            tasks_df.sort_values(by=['us_id', 'task_num'], ascending=[True, True], inplace=True)
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
                try:
                    raw_sprints_df = pd.json_normalize(res.json())
                    return self._format_sprint_df(raw_sprints_df[['id', 'name', 'estimated_start', 'estimated_finish']])
                except Exception as e:
                    exc_type = type(e),__name__
                    exc_cause = 'No Cause/Context Provided'
                    cause = e.__cause__ or e.__context__
                    if cause:
                        exc_cause = str(cause)

                    print(f'{exc_type}: {exc_cause}')
            return None

        def import_member_data() -> pd.DataFrame:
            res = import_data(f'{self.base_url}/projects/{project_id}')
            if res.status_code == 200:
                try:
                    raw_members_df = pd.json_normalize(res.json().get('members'))
                    updated_raw_df = raw_members_df[raw_members_df['role'] == 9585684]

                    headers = ['id', 'username']
                    data = []

                    print(updated_raw_df)

                    for index, row in updated_raw_df.iterrows():
                        print(row.values)
                        mem_id = row['id']
                        uname = row['username']
                        fname = row['full_name_display']

                        username = uname
                        if pd.notna(uname):
                            if pd.notna(fname) and len(fname) < len(uname):
                                username = fname
                        data.append([mem_id, username])
                    members_df = pd.DataFrame(columns=headers, data=data)
                    return self._format_members_df(members_df)
                except Exception as e:
                    exc_type = type(e),__name__
                    exc_cause = 'No Cause/Context Provided'
                    cause = e.__cause__ or e.__context__
                    if cause:
                        exc_cause = str(cause)

                    print(f'{exc_type}: {exc_cause}')
            return None
            
        def import_us_data() -> pd.DataFrame:
            res = import_data(f'{self.base_url}/userstories?project={project_id}')
            if res.status_code == 200:
                try:
                    raw_us_df = pd.json_normalize(res.json())
                    return self._format_us_df(raw_us_df[['id', 'ref', 'is_closed', 'milestone', 'total_points']])
                except Exception as e:
                    exc_type = type(e),__name__
                    exc_cause = 'No Cause/Context Provided'
                    cause = e.__cause__ or e.__context__
                    if cause:
                        exc_cause = str(cause)
                    
                    print(f'{exc_type}: {exc_cause}')
            return None
            
        def import_task_data(member_df) -> pd.DataFrame:
            res = import_data(f'{self.base_url}/tasks?project={project_id}')
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
                        except Exception as e:
                            exc_type = type(e),__name__
                            exc_cause = 'No Cause/Context Provided'
                            cause = e.__cause__ or e.__context__
                            if cause:
                                exc_cause = str(cause)

                            print(f'{exc_type}: {exc_cause}')
                            username = None
                        subject = row['subject']

                        row_data = [task_id, task, closed, us, username, subject]
                        data.append(row_data)
                    tasks_df = pd.DataFrame(columns=headers, data=data)
                    return self._format_task_df(tasks_df)
                except Exception as e:
                    exc_type = type(e),__name__
                    exc_cause = 'No Cause/Context Provided'
                    cause = e.__cause__ or e.__context__
                    if cause:
                        exc_cause = str(cause)

                    print(f'{exc_type}: {exc_cause}')
            return None

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