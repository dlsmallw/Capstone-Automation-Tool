import tkinter as tk
from tkinter import ttk, filedialog, StringVar, messagebox, Tk
import tksheet as tks

from typing import Type
import pandas as pd
import numpy as np
import threading
import requests
import time

from models.DataManager import DataController
from components.CustomComponents import CustomDateEntry, CustomOptionMenu

class TaigaFrame(ttk.Frame):
    def __init__(self, parent: ttk.Notebook, dc: DataController):
        super().__init__(parent)
        self.root : Tk = None
        self.parent_frame = None

        self.dc = dc
        self.parent_frame = parent
        self.root = parent.master

        self.config_frame = ConfigFrame(self, dc)
        self.data_frame = DataFrame(self, dc)

        self.config_frame.pack(fill='x', anchor='n', pady=(0, 10))
        self.data_frame.pack(fill='both', expand=True, anchor='n')
        self.refresh()

    def refresh(self):
        self.root.update()
        self.root.after(1000,self.refresh)

    def start_file_import_thread(self):
        threading.Thread(target=self.import_from_files).start()

    def start_api_import_thread(self):
        threading.Thread(target=self.import_from_api).start()
    
    

    def taiga_data_ready(self) -> bool:
        return self.data_frame.taiga_data_ready()
    
    def get_taiga_df(self) -> pd.DataFrame:
        return self.data_frame.get_taiga_df()
    
    def get_members(self) -> list:
        return self.data_frame.get_members()
    
    def get_sprints(self) -> list:
        return self.data_frame.get_sprints()
    
class ConfigFrame(ttk.Frame):
    

    def __init__(self, parent: TaigaFrame, dc: DataController):
        super().__init__(parent)
        self.is_linked = False
        self.project_set = False

        self.dc = dc
        self.parent_frame = parent
        self.notebook = ttk.Notebook(self)

        api_tab = ttk.Frame(self.notebook)
        api_tab_widget = self._build_api_form(api_tab)
        api_tab_widget.pack(fill='x', padx=8, pady=8)

        csv_links_tab = ttk.Frame(self.notebook)
        csv_links_widget = self._build_csv_links_form(csv_links_tab)
        csv_links_widget.pack(fill='x', padx=8, pady=8)

        file_tab = ttk.Frame(self.notebook)
        file_sel_widget = self._build_file_form(file_tab)
        file_sel_widget.pack(fill='x', padx=8, pady=8)

        self.notebook.add(api_tab, text='By API')
        self.notebook.add(csv_links_tab, text='By CSV URLs')
        self.notebook.add(file_tab, text='By CSV Files')
        self.notebook.pack()

    def import_by_api(self):
        temp_lbl = ttk.Label(self, text='Handling Taiga API Import Call, Please Wait...')
        temp_lbl.pack()

        try:
            self.dc.taiga_import_by_api()
        except:
            messagebox.showerror('ERROR', 'Failed to import Taiga data by API')
        finally:
            temp_lbl.destroy()

    def import_by_files(self, us_fp, task_fp):
        temp_lbl = ttk.Label(self.config_frame, text='Handling Taiga File Import Call, Please Wait...')
        temp_lbl.pack()

        try:
            self.dc.taiga_import_by_files(us_fp, task_fp)
            df = self.dc.get_taiga_master_df()
            self.data_frame.build_data_display(df)
        except:
            messagebox.showerror('ERROR', 'Failed to import Taiga data by file')
        finally:
            temp_lbl.destroy()

    def import_by_csv_urls(self, us_url, task_url):
        temp_lbl = ttk.Label(self.config_frame, text='Handling Taiga API Import Call, Please Wait...')
        temp_lbl.pack()

        try:
            self.dc.taiga_import_by_urls(us_url, task_url)
            df = self.dc.get_taiga_master_df()
            self.data_frame.build_data_display(df)
        except:
            messagebox.showerror('ERROR', 'Failed to import Taiga data by csv URLs')
        finally:
            temp_lbl.destroy()


    def ready_for_project_sel(self):
        self.project_link_btn['state'] = 'normal'

    def prompt_for_entry(self, prompt_title, prompt_text, callback, params):
        prompt_window = tk.Toplevel()
        prompt_window.title(prompt_title)
        prompt_window.geometry("300x150")

        # Label for the prompt text
        label = tk.Label(prompt_window, text=prompt_text)
        label.pack(pady=10)

        # Entry widget for user input
        entry = tk.Entry(prompt_window, width=30)
        entry.pack(pady=5)

        # Function to handle submission
        def submit_entry():
            value = entry.get()
            if value.strip() == "":
                messagebox.showerror("Error", "Entry cannot be empty.", parent=prompt_window)
                return
            
            callback(*params, value)
            prompt_window.destroy()

        # Submit button
        submit_button = ttk.Button(prompt_window, text="Submit", command=submit_entry)
        submit_button.pack(pady=10)

    def _generate_field_obj(self, field_frame, row, lbl_str, lbl_width, target_obj, btn_obj=None):
        field_lbl = tk.Label(field_frame, text=lbl_str, anchor='e')
        field_lbl.grid(row=row, column=0, padx=(2, 1), sticky='nsew')
        target_obj.grid(row=row, column=1, padx=(1, 2), sticky='nsew')
        if btn_obj is not None:
            btn_obj.grid(row=row, column=2, padx=(4, 4))
        return target_obj
    
    def _build_api_form(self, parent) -> ttk.Frame:
        ## Nested Methods
        ##====================================================================================================================================================
        def update_acct_fields(username_str, btn_str):
            self.username_strval.set(username_str)
            self.link_btn_strval.set(btn_str)

        def update_status_fields(link_status_str):
            self.link_status_strval.set(link_status_str)

        def update_message_field(msg):
            self.message_strval.set(msg)

        def not_authed_or_linked():
            update_acct_fields('No Linked User', 'Link Account')
            update_status_fields('Not Linked')
            update_message_field('A Taiga Account Must Be Linked')

        def authed_waiting_for_proj_sel():
            update_status_fields('Success')
            self.project_sel_btn_strval.set('Link Project')
            update_message_field('Account Linked - Waiting for Project List...')

        def authed_and_linked(project):
            update_status_fields('Success')
            self.project_sel_btn_strval.set('Change Linked Project')
            self.project_link_btn['state'] = 'normal'
            self.import_from_api_btn['state'] = 'normal'
            update_message_field(f"Project '{project}' selected - Ready to make Taiga API calls")

        def authenticate_with_credentials(username, password):
            result, msg = self.dc.authenticate_with_taiga(username=username, password=password)
            if result == 'Success':
                project = self.dc.get_linked_project()[1]
                if project is not None:
                    authed_and_linked(project)
                else:
                    th1 = threading.Thread(target=wait_for_projects)
                    authed_waiting_for_proj_sel()
                    th1.start()
            else:
                update_message_field(msg)

        def initialize_fields():
            username, password = self.dc.load_taiga_credentials()

            if username and password:
                update_acct_fields(username, 'Update Credentials')
                authenticate_with_credentials(username, password)
            else:
                not_authed_or_linked()

        def wait_for_projects():
            self.dc.wait_for_projects()
            update_message_field('Account Linked - Project List Ready to Select From...')
            self.project_link_btn['state'] = 'normal'

        def open_taiga_link_window(btn_lbl='Link'):
            # Create a new Toplevel window for the login form
            link_window = tk.Toplevel()
            link_window.title("Taiga Login")
            link_window.geometry("300x200")
            link_window.wm_protocol("WM_DELETE_WINDOW", link_window.quit)

            curr_uname, curr_pwd = self.dc.load_taiga_credentials()

            # Function to authenticate with Taiga API
            def authenticate_with_taiga():
                username = username_entry.get()
                password = password_entry.get()

                result, msg = self.dc.authenticate_with_taiga(username, password)
                if result == 'Success':
                    th1 = threading.Thread(target=wait_for_projects)
                    authed_waiting_for_proj_sel()
                    update_acct_fields(username, 'Update Credentials')
                    update_status_fields('Success')
                    update_message_field('Account Linked - Waiting for Project List...')
                    th1.start()
                    if threading.currentThread != th1:
                        messagebox.showinfo(result, 'Successfully linked the Taiga account', parent=link_window)
                        link_window.destroy()
                    
                else:
                    messagebox.showerror(result, msg, parent=link_window)

            # Username Label and Entry
            username_label = tk.Label(link_window, text="Username:")
            username_label.pack(pady=5)
            username_entry = tk.Entry(link_window, width=30)
            username_entry.pack(pady=5)

            # Password Label and Entry
            password_label = tk.Label(link_window, text="Password:")
            password_label.pack(pady=5)
            password_entry = tk.Entry(link_window, show="*", width=30)
            password_entry.pack(pady=5)

            if curr_uname is not None:
                username_entry.insert(0, curr_uname)

            if curr_pwd is not None:
                password_entry.insert(0, curr_pwd)

            # Login Button
            link_button = ttk.Button(link_window, text=btn_lbl, command=authenticate_with_taiga)
            link_button.pack(pady=10)

        def import_from_api():
            threading.Thread(target=self.import_by_api).start()

        def open_project_sel_prompt():
            # Create a new Toplevel window for the login form
            project_window = tk.Toplevel()
            project_window.title("Taiga Project Select")
            project_window.geometry("300x200")
            project_window.wm_protocol("WM_DELETE_WINDOW", project_window.quit)

            def select_project():
                project = proj_sel_strvar.get()
                result, msg = self.dc.select_taiga_project(project)
                
                if result == 'Success':
                    messagebox.showinfo(result, msg, parent=project_window)
                    authed_and_linked(project)
                    project_window.destroy()
                else:
                    messagebox.showerror(result, msg, parent=project_window)
                
            proj_sel_strvar = StringVar(project_window)
            proj_sel_strvar.set('')

            proj_opts = self.dc.get_available_projects()

            # Username Label and Entry
            project_sel_lbl = tk.Label(project_window, text="Select a Project To Link:")
            project_sel_lbl.pack(pady=5)
            project_opt_sel = CustomOptionMenu(project_window, proj_sel_strvar, *proj_opts)
            project_opt_sel.pack(pady=5)

            # Login Button
            link_project_button = ttk.Button(project_window, text='Submit', command=select_project)
            link_project_button.pack(pady=10)

        ## Function logic
        ##====================================================================================================================================================
        widget_frame = ttk.Frame(parent)

        api_config_frame_lbl = ttk.Label(widget_frame, text=f'{' ' * 4}Import Using API{' ' * 4}', font=('Arial', 15), borderwidth=2, relief='ridge', anchor='center')
        import_from_api_btn = ttk.Button(widget_frame, text='Import Data from API', command=import_from_api)

        details_frame = ttk.Frame(widget_frame)
        acct_frame = ttk.Frame(details_frame, borderwidth=2, relief='ridge')
        status_frame = ttk.Frame(details_frame, borderwidth=2, relief='ridge')

        self.username_strval = StringVar(value='No Profile Linked')
        self.link_btn_strval = StringVar(value='Link Taiga Account')

        self.link_status_strval = StringVar(value='Not Linked')
        self.project_sel_btn_strval = StringVar(value='Set Linked Project')
        self.message_strval = StringVar(value='An account must be linked for using the API')

        ## Account details info
        acct_frame_lbl = ttk.Label(acct_frame, text=f'{' ' * 6}Authentication Details{' ' * 6}', font=('Arial', 12), borderwidth=2, relief='ridge', anchor='center')
        acct_fields_frame = ttk.Frame(acct_frame)
        self._generate_field_obj(acct_fields_frame, 
                                 0, 
                                 'Username:', 
                                 12, 
                                 ttk.Label(acct_fields_frame, textvariable=self.username_strval))
        btn_style = ttk.Style()
        btn_style.configure('my.TButton', font=('Arial', 8))
        link_acct_btn = ttk.Button(acct_frame, textvariable=self.link_btn_strval, style='my.TButton', command=open_taiga_link_window)

        ## Link Status details info
        link_status_lbl = ttk.Label(status_frame, text=f'{' ' * 6}Authentication Status{' ' * 6}', font=('Arial', 12), borderwidth=2, relief='ridge', anchor='center')
        status_fields_frame = ttk.Frame(status_frame)
        self._generate_field_obj(status_fields_frame,
                                 0,
                                 'Link Status:',
                                 12,
                                 ttk.Label(status_fields_frame, textvariable=self.link_status_strval))
        self.project_link_btn = ttk.Button(status_frame, textvariable=self.project_sel_btn_strval, style='my.TButton', command=open_project_sel_prompt, state='disabled')
        
        message_field = ttk.Label(details_frame, textvariable=self.message_strval, font=('Arial', 8, 'normal', 'italic'), padding=3, borderwidth=2, relief='ridge', anchor='center')

        self.import_from_api_btn = ttk.Button(widget_frame, text='Import by API', command=import_from_api, state='disabled')
        
        ## Configure Acct Details Frame
        acct_frame_lbl.pack(fill='x', pady=(0, 6))
        acct_fields_frame.pack()
        link_acct_btn.pack(pady=(2, 6))
        ## Configure Link Status Frame
        link_status_lbl.pack(fill='x', pady=(0, 6))
        status_fields_frame.pack(pady=(0, 6))
        self.project_link_btn.pack(padx=(4, 4))

        ## Set Placement of Acct and Status frames
        acct_frame.grid(row=0, column=0, sticky='nsew')
        status_frame.grid(row=0, column=1, sticky='nsew')
        message_field.grid(row=1, columnspan=2, sticky='nsew')

        ## Build Whole Frame
        api_config_frame_lbl.pack(fill='x', pady=(0, 8))
        details_frame.pack(pady=(0,8))
        self.import_from_api_btn.pack()

        initialize_fields()

        return widget_frame

    def _build_csv_links_form(self, parent) -> ttk.Frame:
        ## Nested Methods
        ##====================================================================================================================================================
        def set_url(field: StringVar, type: str, url: str):
            if url is not None and url != '':
                if type == 'us':
                    if 'https://api.taiga.io/api/v1/userstories/csv?uuid=' in url:
                        self.dc.set_taiga_us_api_url(url)
                        field.set(url)
                elif type == 'task':
                    if 'https://api.taiga.io/api/v1/tasks/csv?uuid=' in url:
                        self.dc.set_taiga_task_api_url(url)
                        field.set(url)
                else:
                    return
                
                if self.us_csv_url_strvar != 'No URL Specified' and self.task_csv_url_strvar.get() != 'No URL Specified':
                    self.import_from_csv_url_btn['state'] = 'normal'
            else:
                messagebox.showerror('Invalid URL', 'Invalid URL entered')

        def url_update_dialog(field: StringVar, type: str):
            prompt_title = f'Set/Update {'User Story' if type == 'us' else 'Task'} CSV Import URL'
            self.prompt_for_entry(prompt_title, 'Enter the URL:', set_url, [field, type])

        ## Function logic
        ##====================================================================================================================================================
        widget_frame = ttk.Frame(parent)

        csv_url_config_lbl = tk.Label(widget_frame, text=f'{' ' * 4}Import Using CSV URLs{' ' * 4}', font=('Arial', 15), borderwidth=2, relief='ridge')
        csv_url_config_frame = ttk.Frame(widget_frame)

        self.us_csv_url_strvar = StringVar(value='No URL Specified')
        self.task_csv_url_strvar = StringVar(value='No URL Specified')

        self._generate_field_obj(csv_url_config_frame, 
                                    0, 
                                    'US Report CSV URL:', 
                                    16, 
                                    tk.Label(csv_url_config_frame, textvariable=self.us_csv_url_strvar, anchor='w'), 
                                    ttk.Button(csv_url_config_frame, text='Set CSV URL', command=lambda: url_update_dialog(self.us_csv_url_strvar, 'us')))
        
        self._generate_field_obj(csv_url_config_frame, 
                                    1, 
                                    'Task Report CSV URL:', 
                                    16, 
                                    tk.Label(csv_url_config_frame, textvariable=self.task_csv_url_strvar, anchor='w'), 
                                    ttk.Button(csv_url_config_frame, text='Set CSV URL', command=lambda: url_update_dialog(self.task_csv_url_strvar, 'task')))
        

        # Buttons for importing and exporting data
        btn_frame = ttk.Frame(widget_frame)
        self.import_from_csv_url_btn = ttk.Button(btn_frame, text='Import from CSV URL', state='disabled', command=lambda: self.parent_frame.start_api_import_thread())
        self.import_from_csv_url_btn.grid(row=0, column=0, padx=2, sticky='nsew')

        csv_url_config_lbl.pack(fill='x', pady=(0, 8))
        csv_url_config_frame.pack(pady=(0, 4))
        btn_frame.pack()

        us_url = self.dc.get_taiga_us_csv_url()
        task_url = self.dc.get_taiga_task_csv_url()

        if us_url is not None:
            self.us_csv_url_strvar.set(us_url)
        if task_url is not None:
            self.task_csv_url_strvar.set(task_url)

        return widget_frame

    def _build_file_form(self, parent) -> ttk.Frame:
        ## Nested Methods
        ##====================================================================================================================================================
        def file_select(self, field: StringVar, type: str):
            fp = filedialog.askopenfilename().strip()

            if fp is not None and fp != '':
                if type == 'us':
                    field.set(fp)
                    self.dc.set_us_fp(fp)
                elif type == 'task':
                    field.set(fp)
                    self.dc.set_task_fp(fp)
                else:
                    return

                if self.us_fp_strval.get() != 'No File Selected' and self.task_fp_strval.get() != 'No File Selected':
                    self.import_data_from_file_btn['state'] = 'normal'

        ## Function Logic
        ##====================================================================================================================================================

        widget_frame = ttk.Frame(parent)
        file_sel_lbl = tk.Label(widget_frame, text=f'{' ' * 4}Import Using CSV Files{' ' * 4}', font=('Arial', 15), borderwidth=2, relief='ridge')
        
        fp_sel_frame = ttk.Frame(widget_frame)

        self.us_fp_strval = StringVar(value='No File Selected')
        self.task_fp_strval = StringVar(value='No File Selected')
        # User Story File Select
        self._generate_field_obj(fp_sel_frame, 
                                    0, 
                                    'US Report Filepath:', 
                                    16, 
                                    tk.Label(fp_sel_frame, textvariable=self.us_fp_strval, anchor='w'), 
                                    ttk.Button(fp_sel_frame, text='Select Report File', command=lambda: file_select(self.us_fp_strval, 'us')))

        # Task File Select
        self._generate_field_obj(fp_sel_frame, 
                                    1, 
                                    'Task Report Filepath:', 
                                    16, 
                                    tk.Label(fp_sel_frame, textvariable=self.task_fp_strval, anchor='w'), 
                                    ttk.Button(fp_sel_frame, text='Select Report File', command=lambda: file_select(self.task_fp_strval, 'task')))

        # Buttons for importing and exporting data
        btn_frame = ttk.Frame(widget_frame)
        self.import_data_from_file_btn = ttk.Button(btn_frame, text='Import from Files', state='disabled', command=lambda: self.parent_frame.start_file_import_thread())
        self.import_data_from_file_btn.grid(row=0, column=0, padx=2, sticky='nsew')

        file_sel_lbl.pack(fill='x', pady=(0, 8))
        fp_sel_frame.pack(pady=(0, 4))
        btn_frame.pack()

        return widget_frame
    
    
    
class DataFrame(ttk.Frame):
    def __init__(self, parent: TaigaFrame, dc: DataController):
        super().__init__(parent)

        self.parent_frame : TaigaFrame = None
        self.filter_panel : ttk.Frame = None
        self.btn_frame : ttk.Frame = None
        self.sheet : tks.Sheet = None
        self.master_df : pd.DataFrame = None
        self.sheet_master_df : pd.DataFrame = None
        self.col_widths = None

        self.dc = dc
        self.parent_frame = parent

    def taiga_data_ready(self) -> bool:
        return self.sheet_master_df is not None
    
    def get_taiga_df(self) -> pd.DataFrame:
        return self.sheet_master_df.copy(deep=True)
    
    def sheet_df_col_to_list(self, col_lbl) -> list:
        df = self.sheet_master_df[col_lbl].copy(deep=True)
        self.__inv_val_to_none(df)
        df.dropna(inplace=True)
        df = df.drop_duplicates(keep='first').reset_index(drop=True)
        return df.tolist()
    
    def get_members(self) -> list:
        return self.sheet_df_col_to_list('assigned_to')
    
    def get_sprints(self) -> list:
        return self.sheet_df_col_to_list('sprint')

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
        if val == -1 or pd.isna(val):
            return 'Storyless'
        else:
            return f'{int(val)}'
    
    def __convert_from_str(self, str_val):
        if str_val == 'Storyless' or str_val == '' or pd.isna(str_val):
            return None
        else:
            return int(str_val)
        
    def __inv_val_to_none(self, df: Type[pd.DataFrame]):
        df.replace(['', 'None', 'nan', 'NaN', np.nan], [None, None, None, None, None], inplace=True)
    
    def __dataframe_to_table_format(self, df_to_format: Type[pd.DataFrame]):
        df = df_to_format.copy(deep=True)
        self.__inv_val_to_none(df)
        df['user_story'] = df['user_story'].apply(lambda x: self.__convert_to_str(x))
        return df

    def __table_to_dataframe_format(self, df_to_format: Type[pd.DataFrame]):
        df = df_to_format.copy(deep=True)
        df['user_story'] = df['user_story'].apply(lambda x: self.__convert_from_str(x))
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
            df.replace('', None, inplace=True)
            df.dropna(how='all', inplace=True)

            formatted_df = self.__table_to_dataframe_format(df)
        else:
            formatted_df = self.sheet_master_df
        
        return formatted_df
    
    def __merge_dataframes(self, master_df, new_df):
        self.__inv_val_to_none(master_df)
        self.__inv_val_to_none(new_df)
        master_df.set_index('task', inplace=True)
        master_df.update(new_df.set_index('task'))
        master_df.reset_index(inplace=True)
        master_df.sort_values(['sprint', 'user_story', 'task'], ascending=[True, True, True])
        return master_df[['sprint', 'sprint_start', 'sprint_end', 'user_story', 'points', 'task', 'assigned_to', 'coding', 'subject']]

    def __update_sheet_df(self, new_df):
        if self.sheet_master_df is not None:
            master_copy = self.sheet_master_df.copy(deep=True)
            new_df_copy = new_df.copy(deep=True)
            master_copy = self.__merge_dataframes(master_copy, new_df_copy)
            self.sheet_master_df = master_copy.sort_values(['sprint', 'user_story', 'task'], ascending=[True, True, True])
        else:
            self.master_df = new_df
            self.sheet_master_df = new_df

    def __apply_filters(self, 
                        from_date_field: Type[CustomDateEntry], 
                        to_date_field: Type[CustomDateEntry], 
                        us_field: Type[CustomOptionMenu], 
                        sprint_field: Type[CustomOptionMenu], 
                        user_field: Type[CustomOptionMenu]
                        ):
        old_df = self.__parse_table_data_to_df()
        self.__update_sheet_df(old_df)
        df = self.sheet_master_df

        filter_applied = False

        if from_date_field.date_selected():
            filter_applied = True
            from_date = from_date_field.get_date()
            df = df[pd.to_datetime(df['sprint_end']) >= pd.to_datetime(from_date)]
        if to_date_field.date_selected():
            filter_applied = True
            to_date = to_date_field.get_date()
            df = df[pd.to_datetime(df['sprint_start']) <= pd.to_datetime(to_date)]
        if us_field.selection_made():
            filter_applied = True
            us = us_field.get_selection()
            if us != 'Storyless':
                df = df[df['user_story'] == int(us)]
            else:
                df = df[df['user_story'] == -1]
        if sprint_field.selection_made():
            filter_applied = True
            sprint = sprint_field.get_selection()
            df = df[df['sprint'] == sprint]
        if user_field.selection_made():
            filter_applied = True
            user = user_field.get_selection()
            df = df[df['assigned_to'] == user]

        if filter_applied:
            self.clear_filters_btn['state'] = 'normal'

        self.change_table(df)

    def __clear_filters(self, 
                        from_date_field: Type[CustomDateEntry], 
                        to_date_field: Type[CustomDateEntry], 
                        us_field: Type[CustomOptionMenu], 
                        sprint_field: Type[CustomOptionMenu], 
                        user_field: Type[CustomOptionMenu]
                        ):
        df = self.__parse_table_data_to_df()
        self.__update_sheet_df(df)

        from_date_field.clear_date()
        to_date_field.clear_date()
        us_field.reset()
        sprint_field.reset()
        user_field.reset()

        self.clear_filters_btn['state'] = 'disabled'
        self.change_table(self.sheet_master_df)

    def __save_table_data(self):
        df = self.__parse_table_data_to_df()
        self.sheet_master_df = df
        self.master_df = self.sheet_master_df
        self.dc.set_taiga_master_df(df)
        self.dc.store_raw_taiga_data()

    def __clear_data(self):
        self.dc.clear_taiga_data()
        self.master_df = None
        self.sheet_master_df = None
        self.__destroy_frames()

    def __build_filter_panel(self) -> ttk.Frame: 
        widget_frame = ttk.Frame(self, borderwidth=2, relief='ridge')

        filters_lbl = tk.Label(widget_frame, text=f'{' ' * 4}Filter Options{' ' * 4}', font=('Arial', 15), borderwidth=2, relief='ridge')
        
        filters_frame = ttk.Frame(widget_frame)
        date_frame = ttk.Frame(filters_frame)
        opt_frame = ttk.Frame(filters_frame)
        btn_frame = ttk.Frame(filters_frame)

        us_select_def = StringVar(opt_frame)
        us_options = ['', 'Storyless'] + self.dc.get_user_stories()
        us_select_def.set(us_options[0])

        sprint_select_def = StringVar(opt_frame)
        sprint_options = [''] + self.dc.get_sprints()
        sprint_select_def.set(sprint_options[0])

        user_select_def = StringVar(opt_frame)
        user_options = ['', 'Unassigned'] + self.dc.get_members()
        user_select_def.set(user_options[0])

        # Date Filters
        from_frame = ttk.Frame(date_frame)
        to_frame = ttk.Frame(date_frame)

        from_date_entry = self.__generate_field_obj(from_frame, 'From Date:', CustomDateEntry(from_frame, width=8))
        to_date_entry = self.__generate_field_obj(to_frame, 'To Date:', CustomDateEntry(to_frame, width=8))
        from_frame.grid(row=0, column=0)
        to_frame.grid(row=0, column=1)

        # Field Filters
        us_frame = ttk.Frame(opt_frame)
        sprint_frame = ttk.Frame(opt_frame)
        user_frame = ttk.Frame(opt_frame)

        us_filter = self.__generate_field_obj(us_frame, 'User Story:', CustomOptionMenu(us_frame, us_select_def, *us_options))
        sprint_filter = self.__generate_field_obj(sprint_frame, 'Sprint:', CustomOptionMenu(sprint_frame, sprint_select_def, *sprint_options))
        user_filter = self.__generate_field_obj(user_frame, 'User:', CustomOptionMenu(user_frame, user_select_def, *user_options))
        us_frame.grid(row=0, column=0, sticky='nsew')
        sprint_frame.grid(row=0, column=1, sticky='nsew')
        user_frame.grid(row=0, column=2, sticky='nsew')

        # Buttons
        apply_filters_btn = ttk.Button(btn_frame, 
                                      text='Apply Filters', 
                                      command=lambda: self.__apply_filters(from_date_entry, to_date_entry, us_filter, sprint_filter, user_filter))
        self.clear_filters_btn = ttk.Button(btn_frame, 
                                      text='Clear Filters', 
                                      state='disabled',
                                      command=lambda: self.__clear_filters(from_date_entry, to_date_entry, us_filter, sprint_filter, user_filter))
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
        save_data_btn = ttk.Button(btn_frame, text='Save Current Table', command=lambda: self.__save_table_data())
        clear_data_btn = ttk.Button(btn_frame, text='Clear All Taiga Data', command=lambda: self.__clear_data())
        save_data_btn.grid(row=0, column=0, sticky='nsew', padx=2)
        clear_data_btn.grid(row=0, column=1, sticky='nsew', padx=2)
        return btn_frame
    
    def __build_table(self, df) -> tks.Sheet:
        formatted_df = self.__dataframe_to_table_format(df)
        formatted_df.sort_values(by='sprint_start', ascending=True, inplace=True)
        sheet = tks.Sheet(self, header=list(formatted_df.columns), data=formatted_df.values.tolist())
        sheet.enable_bindings('all')
        # sheet.height_and_width(height=300, width=1000)

        if self.col_widths is None:
            column_widths = []
            index = 0
            for column in formatted_df.columns:
                text_width = sheet.get_column_text_width(index)
                if column == 'subject':
                    text_width = 285

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