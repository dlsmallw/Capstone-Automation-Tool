import os
import io

import pandas as pd
import openpyxl as opyxl

import configparser
import requests

import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()

class TaigaParsingController:
    config_fp = os.path.join(os.getcwd(), 'config.txt')
    config_parser = None
        
    api = {
        "us_report_url": None,
        "task_report_url": None
    }

    paths = {
        "us_fp": None,
        "task_fp": None
    }

    data = {
        "members": None,
        "sprints": None,
        "raw_us_data": None,
        "raw_task_data": None,
        "formatted_master_data": None
    }
    
    def __init__(self):
        self.__load_config()

    def __load_config(self):
        config = None

        if os.path.exists(self.config_fp):
            config = configparser.RawConfigParser()
            config.read(self.config_fp)
            print(config)

        if config is not None:
            self.config_parser = config     # for future use

            us_report_url = config.get('taiga-config', 'us_report_api_url')
            if us_report_url != "" or us_report_url is not None:
                self.api["us_report_url"] = us_report_url

            task_report_url = config.get('taiga-config', 'task_report_api_url')
            if task_report_url != "" or task_report_url is not None:
                self.api["task_report_url"] = task_report_url

    def set_us_report_url(self, url):
        config = self.config_parser
        
        if url != "" and url is not None:
            self.api['us_report_url'] = url
            config.set('taiga-config', 'us_report_api_url', url)

    def set_task_report_url(self, url):
        config = self.config_parser

        if url != "" and url is not None:
            self.api['task_report_url'] = url
            config.set('taiga-config', 'task_report_api_url', url)
            

    def __file_is_valid(self, filename):
        if filename != "" and filename is not None:
            return True
        else:
            return False

    def set_us_fp(self):
        fp = filedialog.askopenfilename()

        if self.__file_is_valid(fp):
            self.paths["us_fp"] = fp
            return True
    
        return False

    def set_task_fp(self, fp):
        fp = filedialog.askopenfilename()

        if self.__file_is_valid(fp):
            self.paths["task_fp"] = fp
            return True
        
        return False
    
    def __format_us_data(self, raw_df):
        if raw_df is not None:
                self.data["raw_us_data"] = raw_df[['id', 'ref', 'sprint', 'total-points']]
                self.__parse_sprints(raw_df)
                return True
        
        return False

    def __us_data_from_file(self):
        us_fp = self.paths["us_fp"]
        us_url_set = self.__file_is_valid(us_fp)

        if not us_url_set:
            us_url_set = self.set_us_fp()

        if us_url_set:
            raw_data = None

            if us_fp.split(".")[-1] == "csv":
                raw_data = pd.read_csv(us_fp)
            elif us_fp.split(".")[-1] == "xlsx":
                raw_data = pd.read_excel(us_fp)
            
            return self.__format_us_data(raw_data)
            
        return False

    def __us_data_from_api(self):
        us_report_url = self.api["us_report_url"]

        if us_report_url != "" and us_report_url is not None:
            res = requests.get(us_report_url)._content
            raw_data = pd.read_csv(io.StringIO(res.decode('utf-8')))

            return self.__format_us_data(raw_data)
            
        return False
    
    def __format_task_data(self, raw_df):
        if raw_df is not None:
            raw_df = raw_df[['id', 'ref', 'subject', 'user_story', 'sprint', 'assigned_to']]
            raw_df.sort_values(['sprint'], ascending=[True], inplace=True)
            self.data["raw_task_data"] = raw_df
            self.__parse_members(raw_df['assigned_to'])
            return True
        return False

    def __task_data_from_file(self):
        task_fp = self.paths["task_fp"]
        task_url_set = self.__file_is_valid(task_fp)

        if not task_url_set:
            task_url_set = self.set_task_fp()

        if task_url_set:
            raw_data = None

            if task_fp.split(".")[-1] == "csv":
                raw_data = pd.read_csv(task_fp)
            elif task_fp.split(".")[-1] == "xlsx":
                raw_data = pd.read_excel(task_fp)
            
            return self.__format_task_data(raw_data)
        
        return False

    def __task_data_from_api(self):
        task_report_url = self.api["task_report_url"]

        if task_report_url != "" and task_report_url is not None:
            res = requests.get(task_report_url)._content
            raw_data = pd.read_csv(io.StringIO(res.decode('utf-8')))

            return self.__format_task_data(raw_data)
            
        return False

    def __make_hyperlink(self, task_num):
        base_url = 'https://tree.taiga.io/project/dlsmallw-group-8-asu-capstone-natural-language-processing-for-decolonizing-harm-reduction-literature/task/{}'
        return '=HYPERLINK("%s", "Task-%s")' % (base_url.format(task_num), task_num)

    def __parse_members(self, dataframe):
        members = []

        for row in dataframe:
            if pd.notnull(row):
                members.append(row) if row not in members else None

        self.data["members"] = members

    def __parse_sprints(self, df):
        sprints = []

        for row in df:
            if pd.notnull(row):
                sprints.append(row) if row not in sprints else None

        self.data["sprints"] = sprints

    def __format_and_centralize_data(self):
        data_columns = ['subject', 'sprint', 'user_story', 'points', 'task', 'coding']

        members = self.data["members"]
        us_df = self.data["raw_us_data"]
        task_df = self.data["raw_task_data"]

        num_mems = len(members)
        data_columns.extend(members)

        all_data = [0] * len(task_df)

        for index, row in task_df.iterrows():
            assigned = row['assigned_to']

            subject = row['subject']
            sprint = row['sprint']

            us_num = row['user_story']
            us_row = us_df.loc[us_df['ref'] == us_num]

            user_story = row['user_story']
            points = us_row['total-points'].values[0] if pd.notnull(us_num) else 0

            task = row['ref']
            coding = ""

            mem_data = [None] * num_mems

            i = 0
            for mem in members:
                mem_data[i] = "100%" if assigned == mem else None
                i += 1

            data_row = [subject, sprint, user_story, points, task, coding]
            data_row.extend(mem_data)

            all_data[index] = data_row

        self.data["formatted_master_data"] = pd.DataFrame(all_data, columns=data_columns)

    def retrieve_data_by_api(self):
        task_parse_success = self.__task_data_from_api()
        us_parse_success = self.__us_data_from_api()

        if task_parse_success and us_parse_success:
            self.__format_and_centralize_data()
        else:
            print('Error retrieving and parsing data through api')

    def retrieve_data_by_file(self):
        task_parse_success = self.__task_data_from_file()
        us_parse_success = self.__us_data_from_file()

        if task_parse_success and us_parse_success:
            self.__format_and_centralize_data()
        else:
            print('Error retrieving and parsing data from files')

    def __format_df(self, df):
        for i, row in df.iterrows():
            us_num = row['user_story']
            task_num = row['task']
            df.at[i, 'user_story'] = f'US-{int(us_num)}' if pd.notnull(us_num) else "Storyless"
            df.at[i, 'task'] = self.__make_hyperlink(task_num)

        return df

    def __create_new_wb(self, filename):
        if (os.path.exists(filename)):
            os.remove(filename)
        
        wb = opyxl.Workbook()
        wb.create_sheet("All_Data")

        for sprint in self.data["sprints"]:
            wb.create_sheet(sprint)

        for sheet in wb.sheetnames:
            if sheet not in self.data["sprints"] and sheet != "All_Data":
                del wb[sheet]

        wb.save(filename)

    def __parsed_data_to_spreadsheet(self, df, writer, sheet):
        df.to_excel(writer, sheet_name=sheet)

    def write_data(self, filename):
        self.__create_new_wb(filename, self.data["sprints"])

        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            self.__parsed_data_to_spreadsheet(
                self.__format_df(self.data["formatted_master_data"].sort_values(['sprint', 'user_story', 'task'], ascending=[True, True, True])), 
                writer, "All_Data")
            
            for sprint in self.data["sprints"]:
                sprint_df = self.data["formatted_master_data"].loc[self.data["formatted_master_data"]['sprint'] == sprint]
                self.__parsed_data_to_spreadsheet(
                    self.__format_df(sprint_df.sort_values(['sprint', 'user_story', 'task'], ascending=[True, True, True])), 
                    writer, sprint)
                
    def get_master_df(self):
        return self.data["formatted_master_data"]