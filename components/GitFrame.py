import tkinter as tk
from tkinter import ttk, filedialog, StringVar
import tksheet as tks

from typing import Type
import pandas as pd
import numpy as np
import threading

from models import DataManager
from components import DialogWindow
from components.CustomComponents import CustomDateEntry, CustomOptionMenu

class GitFrame(ttk.Frame):
    root = None
    parent_frame = None
    DialogBox = None

    def __init__(self, parent: Type[ttk.Notebook], dc: Type[DataManager.DataController]):
        super().__init__(parent)
        self.dc = dc
        self.parent_frame = parent
        self.root = parent.master

        Dialog = DialogWindow.Dialog
        Dialog.root = parent
        self.DialogBox = Dialog

        self.config_frame = ConfigFrame(self, dc)
        self.data_frame = DataFrame(self, dc)

        self.config_frame.pack(fill='x', anchor='n', pady=(0, 10))
        self.data_frame.pack(fill='both', expand=True, anchor='n')

    def refresh(self):
        self.root.update()
        self.root.after(1000,self.refresh)

    def start_import_thread(self):
        self.refresh()
        threading.Thread(target=self.import_gh_data).start()

    def import_gh_data(self):
        temp_lbl = ttk.Label(self.config_frame, text='Handling GitHub API Call, Please Wait...')
        temp_lbl.pack()

        try:
            if self.dc.validate_gh_auth():
                if self.dc.validate_gh_repo():

                    self.dc.make_gh_api_call()
                    df = self.dc.get_git_master_df()
                    self.data_frame.build_data_display(df)
                    
                else:
                    self.dialog('The specified repo does not exist')
            else:
                self.dialog('The token is invalid')
        except:
            self.dialog('Failed to import data')
        finally:
            temp_lbl.destroy()

    def import_gl_data(self):
        temp_lbl = ttk.Label(self.config_frame, text='Handling GitLab API Call, Please Wait...')
        temp_lbl.pack()

        try:
            if self.dc.validate_gh_auth():
                if self.dc.validate_gh_repo():

                    self.dc.make_gh_api_call()
                    df = self.dc.get_git_master_df()
                    self.data_frame.build_data_display(df)
                    
                else:
                    self.dialog('The specified repo does not exist')
            else:
                self.dialog('The token is invalid')
        except:
            self.dialog('Failed to import data')
        finally:
            temp_lbl.destroy()

        

    def gh_data_ready(self) -> bool:
        return self.data_frame.commit_data_ready()
    
    def get_gh_df(self) -> pd.DataFrame:
        return self.data_frame.get_commit_data()
    
    def get_contributors(self) -> list:
        return self.data_frame.get_contributors()

    def dialog(self, msg):
        self.DialogBox(msg)

    def answer_dialog(self, msg):
        win = self.DialogBox(msg, True)
        self.root.wait_window(win.top)
        return win.result
    
class ConfigFrame(ttk.Frame):
    parent_frame = None

    def __init__(self, parent: Type[GitFrame], dc: Type[DataManager.DataController]):
        super().__init__(parent)
        self.dc = dc
        self.parent_frame = parent

        # tabControl = ttk.Notebook(self.parent_frame)

        # github_tab = ttk.Frame(tabControl)
        # gitlab_tab = ttk.Frame(tabControl)


        config_frame = self.__build_config_frame(self)
        config_frame.pack(padx=8, pady=8)

    def __check_all_fields_set(self):
        fields = pd.DataFrame(data=[self.token_field['text'], self.owner_field['text'], self.repo_field['text']], columns=['field'])
        
        fields.replace(to_replace=['', 'Not Set', None], value=[None, None, None], inplace=True)
        for val in fields['field'].tolist():
            if not val:
                return False
        return True

    def __set_field(self, field: Type[tk.Label], val: Type[str]):
        if val is not None and val != '':
            field.config(text=val)
            if self.__check_all_fields_set():
                self.import_gh_data_btn['state'] = 'normal'

    def __update_username(self, field: Type[tk.Label]):
        try:
            username = self.parent_frame.answer_dialog(msg='Enter the GitHub Username').strip()
            if username is not None and username != '':
                success = self.dc.set_gh_username(username)
                if success:
                    self.__set_field(field, username)
                    return
            self.parent_frame.dialog('Invalid Username Entered!')
        except:
            self.parent_frame.dialog('An issue has occurred while trying to set the username!')

    def __update_token(self, field: Type[tk.Label]):
        try:
            token = self.parent_frame.answer_dialog(msg='Enter the GitHub Token').strip()
            if token is not None and token != '':
                success = self.dc.set_gh_token(token)
                if success:
                    self.__set_field(field, token)
                    return
            self.parent_frame.dialog('Invalid Token Entered!')
        except:
            self.parent_frame.dialog('An issue has occurred while trying to set the token!')

    def __update_owner(self, field: Type[tk.Label]):
        try:
            owner = self.parent_frame.answer_dialog(msg='Enter the Repo Owner Username').strip()
            if owner is not None and owner != '':
                success = self.dc.set_gh_owner(owner)
                print(success)
                if success:
                    self.__set_field(field, owner)
                    return
            self.parent_frame.dialog('Invalid Owner Entered!')
        except:
            self.parent_frame.dialog('An issue has occurred while trying to set the repo owner!')

    def __update_repo(self, field: Type[tk.Label]):
        try:
            repo = self.parent_frame.answer_dialog(msg='Enter the Repo Name').strip()
            if repo is not None and repo != '':
                success = self.dc.set_gh_repo(repo)
                if success:
                    self.__set_field(field, repo)
                    return
            self.parent_frame.dialog('Invalid Repo Entered!')
        except:
            self.parent_frame.dialog('An issue has occurred while trying to set the repo!')

    def __generate_field_obj(self, field_frame, row, lbl_str, lbl_width, target_obj, btn_obj=None):
        field_lbl = tk.Label(field_frame, text=lbl_str, width=lbl_width, anchor='e')
        field_lbl.grid(row=row, column=0, padx=(2, 1), pady=(0, 2), sticky='nsew')
        target_obj.grid(row=row, column=1, padx=(1, 2), pady=(0, 2), sticky='nsew')
        if btn_obj is not None:
            btn_obj.grid(row=row, column=2, padx=4, pady=(0, 4))

        return target_obj
    
    def __build_github_tab(self, parent) -> ttk.Frame:
        widget_frame = ttk.Frame(parent)
        options_frame = ttk.Frame(widget_frame)
        btn_frame = ttk.Frame(widget_frame)
        auth_section_frame = ttk.Frame(options_frame, borderwidth=2, relief='ridge')
        repo_section_frame = ttk.Frame(options_frame, borderwidth=2, relief='ridge')

        auth_section_lbl = tk.Label(auth_section_frame, text=f'{' ' * 4}Auth Config Settings{' ' * 4}', font=('Arial', 15), borderwidth=2, relief='ridge')
        auth_section_lbl.grid(row=0, columnspan=3, padx=2, pady=(1, 8), sticky='nsew')
        self.username_field = self.__generate_field_obj(auth_section_frame, 
                                                            1, 
                                                            'Username:', 
                                                            9, 
                                                            tk.Label(auth_section_frame, text='Not Set', anchor='w'), 
                                                            tk.Button(auth_section_frame, text='Edit', command=lambda: self.__update_username(self.username_field), anchor='e', padx=3))
        self.token_field = self.__generate_field_obj(auth_section_frame, 
                                                        2, 
                                                        'Token:', 
                                                        9, 
                                                        tk.Label(auth_section_frame, text='Not Set', anchor='w'), 
                                                        tk.Button(auth_section_frame, text='Edit', command=lambda: self.__update_token(self.token_field), anchor='e', padx=3))
        
        repo_section_lbl = tk.Label(repo_section_frame, text=f'{' ' * 4}Repo Config Settings{' ' * 4}', font=('Arial', 15), borderwidth=2, relief='ridge')
        repo_section_lbl.grid(row=0, columnspan=3, padx=2, pady=(1, 8), sticky='nsew')
        self.owner_field = self.__generate_field_obj(repo_section_frame, 
                                                        1, 
                                                        'Repo Owner:', 
                                                        10, 
                                                        tk.Label(repo_section_frame, text='Not Set', anchor='w'), 
                                                        tk.Button(repo_section_frame, text='Edit', command=lambda: self.__update_owner(self.owner_field), anchor='e', padx=3))
        self.repo_field = self.__generate_field_obj(repo_section_frame, 
                                                        2, 
                                                        'Repo Name:', 
                                                        10, 
                                                        tk.Label(repo_section_frame, text='Not Set', anchor='w'), 
                                                        tk.Button(repo_section_frame, text='Edit', command=lambda: self.__update_repo(self.repo_field), anchor='e', padx=3))
        
        # Buttons for importing and exporting data
        self.import_gh_data_btn = tk.Button(btn_frame, text='Import GitHub Data', state='disabled', command=lambda: self.parent_frame.start_import_thread())
        self.import_gh_data_btn.grid(row=0, column=0, padx=2, sticky='nsew')

        self.__set_field(self.username_field, self.dc.get_gh_username())
        self.__set_field(self.token_field, self.dc.get_gh_token())
        self.__set_field(self.owner_field, self.dc.get_gh_repo_owner())
        self.__set_field(self.repo_field, self.dc.get_gh_repo_name())

        auth_section_frame.grid(row=1, column=0, pady=(0, 8), sticky='nsew')
        repo_section_frame.grid(row=1, column=1, pady=(0, 8), sticky='nsew')
        options_frame.pack(fill='x')
        btn_frame.pack()

        return widget_frame
    
    def __build_gitlab_tab(self, parent) -> ttk.Frame:
        widget_frame = ttk.Frame(parent)
        options_frame = ttk.Frame(widget_frame)
        btn_frame = ttk.Frame(widget_frame)
        auth_section_frame = ttk.Frame(options_frame, borderwidth=2, relief='ridge')
        repo_section_frame = ttk.Frame(options_frame, borderwidth=2, relief='ridge')

        auth_section_lbl = tk.Label(auth_section_frame, text=f'{' ' * 4}Auth Config Settings{' ' * 4}', font=('Arial', 15), borderwidth=2, relief='ridge')
        auth_section_lbl.grid(row=0, columnspan=3, padx=2, pady=(1, 8), sticky='nsew')
        self.username_field = self.__generate_field_obj(auth_section_frame, 
                                                            1, 
                                                            'Username:', 
                                                            9, 
                                                            tk.Label(auth_section_frame, text='Not Set', anchor='w'), 
                                                            tk.Button(auth_section_frame, text='Edit', command=lambda: self.__update_username(self.username_field), anchor='e', padx=3))
        self.token_field = self.__generate_field_obj(auth_section_frame, 
                                                        2, 
                                                        'Token:', 
                                                        9, 
                                                        tk.Label(auth_section_frame, text='Not Set', anchor='w'), 
                                                        tk.Button(auth_section_frame, text='Edit', command=lambda: self.__update_token(self.token_field), anchor='e', padx=3))
        
        repo_section_lbl = tk.Label(repo_section_frame, text=f'{' ' * 4}Repo Config Settings{' ' * 4}', font=('Arial', 15), borderwidth=2, relief='ridge')
        repo_section_lbl.grid(row=0, columnspan=3, padx=2, pady=(1, 8), sticky='nsew')
        self.owner_field = self.__generate_field_obj(repo_section_frame, 
                                                        1, 
                                                        'Repo Owner:', 
                                                        10, 
                                                        tk.Label(repo_section_frame, text='Not Set', anchor='w'), 
                                                        tk.Button(repo_section_frame, text='Edit', command=lambda: self.__update_owner(self.owner_field), anchor='e', padx=3))
        self.repo_field = self.__generate_field_obj(repo_section_frame, 
                                                        2, 
                                                        'Repo Name:', 
                                                        10, 
                                                        tk.Label(repo_section_frame, text='Not Set', anchor='w'), 
                                                        tk.Button(repo_section_frame, text='Edit', command=lambda: self.__update_repo(self.repo_field), anchor='e', padx=3))
        
        # Buttons for importing and exporting data
        self.import_gh_data_btn = tk.Button(btn_frame, text='Import GitHub Data', state='disabled', command=lambda: self.parent_frame.start_import_thread())
        self.import_gh_data_btn.grid(row=0, column=0, padx=2, sticky='nsew')

        self.__set_field(self.username_field, self.dc.get_gh_username())
        self.__set_field(self.token_field, self.dc.get_gh_token())
        self.__set_field(self.owner_field, self.dc.get_gh_repo_owner())
        self.__set_field(self.repo_field, self.dc.get_gh_repo_name())

        auth_section_frame.grid(row=1, column=0, pady=(0, 8), sticky='nsew')
        repo_section_frame.grid(row=1, column=1, pady=(0, 8), sticky='nsew')
        options_frame.pack(fill='x')
        btn_frame.pack()

        return widget_frame

    def __build_config_frame(self, parent) -> ttk.Frame:
        widget_frame = ttk.Frame(parent)
        options_frame = ttk.Frame(widget_frame)
        btn_frame = ttk.Frame(widget_frame)
        auth_section_frame = ttk.Frame(options_frame, borderwidth=2, relief='ridge')
        repo_section_frame = ttk.Frame(options_frame, borderwidth=2, relief='ridge')

        auth_section_lbl = tk.Label(auth_section_frame, text=f'{' ' * 4}Auth Config Settings{' ' * 4}', font=('Arial', 15), borderwidth=2, relief='ridge')
        auth_section_lbl.grid(row=0, columnspan=3, padx=2, pady=(1, 8), sticky='nsew')
        self.token_field = self.__generate_field_obj(auth_section_frame, 
                                                        2, 
                                                        'Token:', 
                                                        9, 
                                                        tk.Label(auth_section_frame, text='Not Set', anchor='w'), 
                                                        tk.Button(auth_section_frame, text='Edit', command=lambda: self.__update_token(self.token_field), anchor='e', padx=3))
        
        repo_section_lbl = tk.Label(repo_section_frame, text=f'{' ' * 4}Repo Config Settings{' ' * 4}', font=('Arial', 15), borderwidth=2, relief='ridge')
        repo_section_lbl.grid(row=0, columnspan=3, padx=2, pady=(1, 8), sticky='nsew')
        self.owner_field = self.__generate_field_obj(repo_section_frame, 
                                                        1, 
                                                        'Repo Owner:', 
                                                        10, 
                                                        tk.Label(repo_section_frame, text='Not Set', anchor='w'), 
                                                        tk.Button(repo_section_frame, text='Edit', command=lambda: self.__update_owner(self.owner_field), anchor='e', padx=3))
        self.repo_field = self.__generate_field_obj(repo_section_frame, 
                                                        2, 
                                                        'Repo Name:', 
                                                        10, 
                                                        tk.Label(repo_section_frame, text='Not Set', anchor='w'), 
                                                        tk.Button(repo_section_frame, text='Edit', command=lambda: self.__update_repo(self.repo_field), anchor='e', padx=3))
        
        # Buttons for importing and exporting data
        self.import_gh_data_btn = tk.Button(btn_frame, text='Import GitHub Data', state='disabled', command=lambda: self.parent_frame.start_import_thread())
        self.import_gh_data_btn.grid(row=0, column=0, padx=2, sticky='nsew')

        self.__set_field(self.token_field, self.dc.get_gh_token())
        self.__set_field(self.owner_field, self.dc.get_gh_repo_owner())
        self.__set_field(self.repo_field, self.dc.get_gh_repo_name())

        auth_section_frame.grid(row=1, column=0, pady=(0, 8), sticky='nsew')
        repo_section_frame.grid(row=1, column=1, pady=(0, 8), sticky='nsew')
        options_frame.pack(fill='x')
        btn_frame.pack()

        return widget_frame

class DataFrame(ttk.Frame):
    parent_frame : Type[GitFrame] = None
    filter_panel : Type[ttk.Frame] = None
    btn_frame : Type[ttk.Frame] = None
    sheet : Type[tks.Sheet] = None
    master_df : Type[pd.DataFrame] = None
    sheet_master_df : Type[pd.DataFrame] = None

    col_widths = None

    def __init__(self, parent: Type[GitFrame], dc: Type[DataManager.DataController]):
        super().__init__(parent)
        self.dc = dc
        self.parent_frame = parent

        data_ready = self.dc.git_data_ready()
        if data_ready:
            self.master_df = self.dc.get_git_master_df()
            self.build_data_display(self.master_df)

    def commit_data_ready(self) -> bool:
        return self.sheet_master_df is not None
    
    def get_commit_data(self) -> pd.DataFrame:
        return self.sheet_master_df.copy(deep=True)
    
    def sheet_df_col_to_list(self, col_lbl) -> list:
        df = self.sheet_master_df[col_lbl].copy(deep=True)
        self.__inv_val_to_none(df)
        df.dropna(inplace=True)
        df = df.drop_duplicates(keep='first').reset_index(drop=True)
        return df.tolist()
    
    def get_contributors(self) -> list:
        return self.sheet_df_col_to_list('committer')

    def __destroy_frames(self):
        if self.filter_panel is not None:
            self.filter_panel.destroy()
        if self.btn_frame is not None:
            self.btn_frame.destroy()
        if self.sheet is not None:
            self.sheet.destroy()

    def __generate_field_obj(self, field_frame, lbl_str, target_obj):
        field_lbl = tk.Label(field_frame, text=lbl_str, anchor='e')

        field_lbl.grid(row=0, column=0, padx=(2, 1), sticky='nsew')
        target_obj.grid(row=0, column=1, padx=(1, 2), sticky='nsew')

        return target_obj
    
    def __convert_to_str(self, val):
        if pd.isna(val):
            return None
        else:
            return f'{int(val)}'
    
    def __convert_from_str(self, str_val):
        if pd.isna(str_val):
            return None
        else:
            return int(str_val)
        
    def __inv_val_to_none(self, df: Type[pd.DataFrame]):
        df.replace(['', 'None', 'nan', 'NaN', np.nan], [None, None, None, None, None], inplace=True)
    
    def __dataframe_to_table_format(self, df_to_format: Type[pd.DataFrame], field='task'):
        df = df_to_format.copy(deep=True)
        self.__inv_val_to_none(df)
        df[field] = df[field].apply(lambda x: self.__convert_to_str(x))
        return df

    def __table_to_dataframe_format(self, df_to_format: Type[pd.DataFrame], field='task'):
        df = df_to_format.copy(deep=True)
        df[field] = df[field].apply(lambda x: self.__convert_from_str(x))
        return df
    
    def __parse_table_data_to_df(self):
        headers = self.sheet.headers()
        num_rows = self.sheet.get_total_rows()

        if num_rows > 0:
            if self.sheet.get_total_rows() == 1:
                data = []
                data.append(self.sheet.get_data())
            else:
                data = self.sheet.get_data()

            df = pd.DataFrame(data, columns=headers)
            self.__inv_val_to_none(df)
            df.dropna(how='all', inplace=True)

            formatted_df = self.__table_to_dataframe_format(df, 'task')
        else:
            formatted_df = self.sheet_master_df
        
        return formatted_df
    
    def __merge_dataframes(self, master_df, new_df):
        self.__inv_val_to_none(master_df)
        self.__inv_val_to_none(new_df)
        master_df.set_index('id', inplace=True)
        master_df.update(new_df.set_index('id'))
        master_df.reset_index(inplace=True)
        master_df.sort_values(by='utc_datetime', ascending=True, inplace=True)
        return master_df[['az_date', 'message', 'task', 'committer', 'id', 'utc_datetime', 'url']]
    
    def __update_sheet_df(self, new_df):
        if self.sheet_master_df is not None:
            master_copy = self.sheet_master_df.copy(deep=True)
            new_df_copy = new_df.copy(deep=True)
            master_copy = self.__merge_dataframes(master_copy, new_df_copy)
            self.sheet_master_df = master_copy.sort_values(by='utc_datetime', ascending=True)
        else:
            self.master_df = new_df.sort_values(by='utc_datetime', ascending=True)
            self.sheet_master_df = self.master_df

    def __save_table_data(self):
        df = self.__parse_table_data_to_df()
        self.sheet_master_df = df.sort_values(by='utc_datetime', ascending=True)
        self.master_df = self.sheet_master_df
        self.dc.set_git_master_df(self.master_df)
        self.dc.store_raw_git_data(self.master_df)

    def __clear_data(self):
        self.dc.clear_git_commit_data()
        self.master_df = None
        self.sheet_master_df = None
        self.__destroy_frames()

    def __apply_filters(self, 
                        from_date_field: Type[CustomDateEntry], 
                        to_date_field: Type[CustomDateEntry], 
                        task_field: Type[CustomOptionMenu],  
                        committer_field: Type[CustomOptionMenu]
                        ):
        old_df = self.__parse_table_data_to_df()
        self.__update_sheet_df(old_df)
        df = self.sheet_master_df

        filter_applied = False
        if from_date_field.date_selected():
            filter_applied = True
            from_date = from_date_field.get_date()
            df = df[pd.to_datetime(df['az_date']) >= pd.to_datetime(from_date)]
        if to_date_field.date_selected():
            filter_applied = True
            to_date = to_date_field.get_date()
            df = df[pd.to_datetime(df['az_date']) <= pd.to_datetime(to_date)]
        if task_field.selection_made():
            filter_applied = True
            us = task_field.get_selection()
            if us != 'Unknown':
                df = df[df['task'] == int(us)]
            else:
                df = df[pd.isna(df['task'])]
        if committer_field.selection_made():
            filter_applied = True
            user = committer_field.get_selection()
            if user != 'Unknown':
                df = df[df['committer'] == user]
            else:
                df = df[df['committer'] == '']
            

        if filter_applied:
            self.clear_filters_btn['state'] = 'normal'

        self.change_table(df)

    def __clear_filters(self, 
                        from_date_field: Type[CustomDateEntry], 
                        to_date_field: Type[CustomDateEntry], 
                        task_field: Type[CustomOptionMenu], 
                        committer_field: Type[CustomOptionMenu]
                        ):
        df = self.__parse_table_data_to_df()
        self.__update_sheet_df(df)

        from_date_field.clear_date()
        to_date_field.clear_date()
        task_field.reset()
        committer_field.reset()

        self.clear_filters_btn['state'] = 'disabled'
        self.change_table(self.sheet_master_df)

    def __build_filter_panel(self) -> ttk.Frame: 
        widget_frame = ttk.Frame(self, borderwidth=2, relief='ridge')

        filters_lbl = tk.Label(widget_frame, text=f'{' ' * 4}Filter Options{' ' * 4}', font=('Arial', 15), borderwidth=2, relief='ridge')
        
        filters_frame = ttk.Frame(widget_frame)
        date_frame = ttk.Frame(filters_frame)
        opt_frame = ttk.Frame(filters_frame)
        btn_frame = ttk.Frame(filters_frame)

        task_select_def = StringVar(opt_frame)
        task_options = ['', 'Unknown'] + self.dc.get_tasks_from_git_data()
        task_select_def.set(task_options[0])

        committer_select_def = StringVar(opt_frame)
        committer_options = ['', 'Unknown'] + self.dc.get_git_contributors()
        committer_select_def.set(committer_options[0])

        # Date Filters
        from_frame = ttk.Frame(date_frame)
        to_frame = ttk.Frame(date_frame)

        from_date_entry = self.__generate_field_obj(from_frame, 'From Date:', CustomDateEntry(from_frame, width=8))
        to_date_entry = self.__generate_field_obj(to_frame, 'To Date:', CustomDateEntry(to_frame, width=8))
        from_frame.grid(row=0, column=0)
        to_frame.grid(row=0, column=1)

        # Field Filters
        task_frame = ttk.Frame(opt_frame)
        committer_frame = ttk.Frame(opt_frame)

        task_filter = self.__generate_field_obj(task_frame, 'Task:', CustomOptionMenu(task_frame, task_select_def, *task_options))
        committer_filter = self.__generate_field_obj(committer_frame, 'Committer:', CustomOptionMenu(committer_frame, committer_select_def, *committer_options))
        task_frame.grid(row=0, column=0, sticky='nsew')
        committer_frame.grid(row=0, column=1, sticky='nsew')

        # Buttons
        apply_filters_btn = tk.Button(btn_frame, 
                                      text='Apply Filters', 
                                      command=lambda: self.__apply_filters(from_date_entry, to_date_entry, task_filter, committer_filter))
        self.clear_filters_btn = tk.Button(btn_frame, 
                                      text='Clear Filters', 
                                      state='disabled',
                                      command=lambda: self.__clear_filters(from_date_entry, to_date_entry, task_filter, committer_filter))
        apply_filters_btn.grid(row=0, column=0, padx=2, sticky='nsew')
        self.clear_filters_btn.grid(row=0, column=1, padx=2, sticky='nsew')

        filters_lbl.pack(fill='x', pady=(0, 5))
        date_frame.pack(fill='x', expand=True)
        opt_frame.pack(pady=2)
        btn_frame.pack(pady=2)
        filters_frame.pack()

        return widget_frame
        
    def __build_table_btn_frame(self) -> ttk.Frame:
        btn_frame = ttk.Frame(self)
        save_data_btn = tk.Button(btn_frame, text='Save Current Table', command=lambda: self.__save_table_data(), padx=1)
        clear_data_btn = tk.Button(btn_frame, text='Clear All GitHub Data', command=lambda: self.__clear_data(), padx=1)
        save_data_btn.grid(row=0, column=0, sticky='nsew', padx=2)
        clear_data_btn.grid(row=0, column=1, sticky='nsew', padx=2)
        return btn_frame
    
    def __build_table(self, df) -> tks.Sheet:
        formatted_df = self.__dataframe_to_table_format(df)
        formatted_df.sort_values(by='utc_datetime', inplace=True)
        sheet = tks.Sheet(self, header=list(formatted_df.columns), data=formatted_df.values.tolist())
        sheet.enable_bindings('all')
        # sheet.height_and_width(height=300, width=1000)

        if self.col_widths is None:
            column_widths = []
            index = 0
            for column in formatted_df.columns:
                text_width = sheet.get_column_text_width(index)
                if column == 'message':
                    text_width = 350
                elif column == 'id':
                    text_width = 80
                elif column == 'url':
                    text_width = 210

                column_widths.append(text_width)
                index += 1

            self.col_widths = column_widths

        sheet.set_column_widths(self.col_widths)

        return sheet

    def build_data_display(self, df):
        self.__destroy_frames()
        self.__update_sheet_df(df)

        self.filter_panel = self.__build_filter_panel()
        self.btn_frame = self.__build_table_btn_frame()
        self.sheet = self.__build_table(self.sheet_master_df)

        self.filter_panel.pack(fill='x', pady=(0, 5))
        self.btn_frame.pack(fill='x', pady=(0, 5), anchor='e')
        self.sheet.pack(fill='both', expand=True, pady=(0, 5))

    def change_table(self, df):
        self.sheet.destroy()
        self.sheet = self.__build_table(df)
        self.sheet.pack(fill='both', expand=True)