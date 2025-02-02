import tkinter as tk
from tkinter import ttk, filedialog, StringVar, messagebox, Tk
import tksheet as tks

import pandas as pd
import numpy as np
import threading

from models.DataManager import DataController
from components.CustomComponents import CustomOptionMenu

class TaigaFrame(ttk.Frame):
    def __init__(self, parent: ttk.Notebook, dc: DataController):
        super().__init__(parent)
        self.root : Tk = None
        self.parent_frame = None

        self.dc = dc
        self.parent_frame = parent
        self.root = parent.master

        self.config_panel = ConfigFrame(self, dc)
        self.data_panel = DataFrame(self, dc)

        self.config_panel.pack(fill='x', anchor='n', pady=(0, 10))
        self.data_panel.pack(fill='both', expand=True, anchor='n')
        self.refresh()

        if self.dc.taiga_data_ready():
            self.data_panel.handle_data_to_tables()

    def setup_dataframe(self):
        self.data_panel.handle_data_to_tables()

    def refresh(self):
        self.root.update()
        self.root.after(1000, self.refresh)

    def taiga_data_ready(self):
        return self.data_panel.taiga_data_ready()
    
    def get_taiga_data(self):
        return self.data_panel.get_taiga_data()
    
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
            result, msg = self.dc.taiga_import_by_api()
            if result == 'Success':
                self.parent_frame.setup_dataframe()
            else:
                messagebox.showerror(result, msg)
        except:
            messagebox.showerror('ERROR', 'Failed to import Taiga data by API')
        finally:
            temp_lbl.destroy()

    def import_by_csv_urls(self, us_url, task_url):
        temp_lbl = ttk.Label(self, text='Handling Taiga CSV URL Import Call, Please Wait...')
        temp_lbl.pack()

        try:
            result, msg = self.dc.taiga_import_by_urls(us_url, task_url)

            if result == 'Success':
                self.parent_frame.setup_dataframe()
            else:
                messagebox.showerror(result, msg)
        except:
            messagebox.showerror('ERROR', 'Failed to import Taiga data by csv URLs')
        finally:
            temp_lbl.destroy()

    def import_by_files(self, us_fp, task_fp):
        temp_lbl = ttk.Label(self, text='Handling Taiga File Import Call, Please Wait...')
        temp_lbl.pack()

        try:
            result, msg = self.dc.taiga_import_by_files(us_fp, task_fp)

            if result == 'Success':
                self.parent_frame.setup_dataframe()
            else:
                messagebox.showerror(result, msg)
        except:
            messagebox.showerror('ERROR', 'Failed to import Taiga data by file')
        finally:
            temp_lbl.destroy()

    def ready_for_project_sel(self):
        self.project_link_btn['state'] = 'normal'

    def prompt_for_entry(self, prompt_title, prompt_text, callback, params):
        prompt_window = tk.Toplevel()
        prompt_window.title(prompt_title)
        prompt_window.geometry("300x150")

        # Label for the prompt text
        label = ttk.Label(prompt_window, text=prompt_text)
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

    def _generate_field_obj(self, field_frame, row, lbl_str, target_obj, btn_obj=None):
        field_lbl = ttk.Label(field_frame, text=lbl_str, anchor='e')
        field_lbl.grid(row=row, column=0, padx=(2, 1), sticky='nsew')
        target_obj.grid(row=row, column=1, padx=(1, 2), sticky='nsew')
        if btn_obj is not None:
            btn_obj.grid(row=row, column=2, padx=(4, 4))
        return target_obj
    
    def _build_api_form(self, parent) -> ttk.Frame:

        ## Prompt Methods
        ##====================================================================================================================================================

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
                    auth_not_linked_ui_config(username)
                    th1 = threading.Thread(target=wait_for_projects)
                    th1.start()
                    if threading.currentThread != th1:
                        messagebox.showinfo(result, 'Successfully linked the Taiga account', parent=link_window)
                        link_window.destroy()
                else:
                    messagebox.showerror(result, msg, parent=link_window)

            # Username Label and Entry
            username_label = ttk.Label(link_window, text="Username:")
            username_label.pack(pady=5)
            username_entry = tk.Entry(link_window, width=30)
            username_entry.pack(pady=5)

            # Password Label and Entry
            password_label = ttk.Label(link_window, text="Password:")
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
                    self.project_set = True
                    messagebox.showinfo(result, msg, parent=project_window)
                    auth_and_linked_ui_config(project)
                    project_window.destroy()
                else:
                    messagebox.showerror(result, msg, parent=project_window)
                
            proj_sel_strvar = StringVar(project_window)
            proj_sel_strvar.set('')

            proj_opts = self.dc.get_available_projects()

            # Username Label and Entry
            project_sel_lbl = ttk.Label(project_window, text="Select a Project To Link:")
            project_sel_lbl.pack(pady=5)
            project_opt_sel = CustomOptionMenu(project_window, proj_sel_strvar, *proj_opts)
            project_opt_sel.pack(pady=5)

            # Login Button
            link_project_button = ttk.Button(project_window, text='Submit', command=select_project)
            link_project_button.pack(pady=10)

        ## UI Modification Methods
        ##====================================================================================================================================================

        def initialize_fields():
            default_ui_config()
            username, password = self.dc.load_taiga_credentials()
            if username and password:
                threading.Thread(target=lambda: authenticate_with_credentials(username, password)).start()

        def update_username_field(username_str):
            self.username_strval.set(username_str)

        def update_acct_link_btn(btn_str):
            self.link_btn_strval.set(btn_str)

        def update_auth_status_field(status_str):
            self.link_status_strval.set(status_str)

        def update_proj_sel_btn(btn_str):
            self.project_sel_btn_strval.set(btn_str)

        def update_message_field(msg):
            self.message_strval.set(msg)

        def default_ui_config():
            update_username_field('No Linked User')
            update_acct_link_btn('Link Account')
            update_auth_status_field('No Account Linked')
            update_proj_sel_btn('Link Project')
            update_message_field('A Taiga Account Must Be Linked')
            self.project_link_btn['state'] = 'disabled'
            self.import_from_api_btn['state'] = 'disabled'
            
        def auth_not_linked_ui_config(username):
            update_username_field(username)
            update_acct_link_btn('Update Account Details')
            update_auth_status_field('Account Authenticated')
            update_message_field('Account Authenticated - Waiting for Project List...')
            self.import_from_api_btn['state'] = 'disabled'

        def auth_and_linked_ui_config(project):
            update_proj_sel_btn('Change Project')
            update_message_field(f"Project '{project}' selected - Ready to make Taiga API calls")
            self.import_from_api_btn['state'] = 'normal'

        ## Nested Functionality
        ##====================================================================================================================================================

        def import_from_api():
            threading.Thread(target=self.import_by_api).start()

        def authenticate_with_credentials(username, password):
            result, msg = self.dc.authenticate_with_taiga(username=username, password=password)
            if result == 'Success':
                self.is_linked = True
                auth_not_linked_ui_config(username)
                project = self.dc.get_linked_project()[1]
                projects = self.dc.get_available_projects()
                if project is not None and project in projects:
                    auth_and_linked_ui_config(project)
                    if len(projects) > 1:
                        self.project_set = True
                        self.project_link_btn['state'] = 'normal'
                else:
                    wait_for_projects()
            else:
                update_message_field(msg)

        def wait_for_projects():
            self.dc.wait_for_projects()
            if self.dc.get_num_projects() > 0:
                update_message_field('Account Linked - Project List Ready to Select From...')
                self.project_link_btn['state'] = 'normal'
            else:
                project = self.dc.get_available_projects()[0]
                self.project_set = True
                self.dc.select_taiga_project(project)
                auth_and_linked_ui_config(project)

        ## Frame Building logic
        ##====================================================================================================================================================

        widget_frame = ttk.Frame(parent)

        api_config_frame_lbl = ttk.Label(widget_frame, text=f'{' ' * 4}Import Using API{' ' * 4}', font=('Arial', 15), borderwidth=2, relief='ridge', anchor='center')

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
                                 ttk.Label(status_fields_frame, textvariable=self.link_status_strval))
        self.project_link_btn = ttk.Button(status_frame, textvariable=self.project_sel_btn_strval, style='my.TButton', command=open_project_sel_prompt, state='disabled')
        
        message_field = ttk.Label(details_frame, textvariable=self.message_strval, font=('Arial', 8, 'normal', 'italic'), padding=3, borderwidth=2, relief='ridge', anchor='center')

        self.import_from_api_btn = ttk.Button(widget_frame, text='Import Data from API', command=import_from_api, state='disabled')
        
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
        def set_urls(us_url, task_url):
            if us_url and task_url:
                self.dc.update_taiga_csv_urls(us_url, task_url)
                self.us_csv_url_strvar.set(us_url)
                self.task_csv_url_strvar.set(task_url)
                self.import_from_csv_url_btn['state'] = 'normal'
            else:
                messagebox.showerror('Invalid URLs', 'Invalid URL entered')

        def url_update_prompt():
            prompt_window = tk.Toplevel()
            prompt_window.title('Set/Update CSV Import URLs')
            prompt_window.geometry("300x150")
            curr_us_url, curr_task_url = self.dc.get_taiga_csv_urls()

            # Username Label and Entry
            us_url_lbl = ttk.Label(prompt_window, text="User Story CSV URL:")
            us_url_lbl.pack(pady=5)
            us_url_entry = ttk.Entry(prompt_window, width=30)
            us_url_entry.pack(pady=5)

            # Password Label and Entry
            task_url_lbl = ttk.Label(prompt_window, text="Task CSV URL:")
            task_url_lbl.pack(pady=5)
            task_url_entry = ttk.Entry(prompt_window, show="*", width=30)
            task_url_entry.pack(pady=5)

            if curr_us_url is not None:
                us_url_entry.insert(0, curr_us_url)

            if curr_task_url is not None:
                task_url_entry.insert(0, curr_task_url)

            # Function to handle submission
            def submit_entry():
                us_value = us_url_entry.get().strip()
                task_value = task_url_entry.get().strip()

                if 'https://api.taiga.io/api/v1/userstories/csv?uuid=' not in us_value \
                    and 'https://api.taiga.io/api/v1/tasks/csv?uuid=' not in task_value:
                    messagebox.showerror("Error", "Entries cannot be empty.", parent=prompt_window)
                    return
                
                set_urls(us_value, task_value)
                prompt_window.destroy()

            # Submit button
            submit_button = ttk.Button(prompt_window, text="Submit", command=submit_entry)
            submit_button.pack(pady=10)

        def init_fields():
            us_url, task_url = self.dc.get_taiga_csv_urls()

            if us_url:
                self.us_csv_url_strvar.set(us_url)
            else:
                self.us_csv_url_strvar.set('No URL Specified')

            if task_url:
                self.task_csv_url_strvar.set(task_url)
            else:
                self.task_csv_url_strvar.set('No URL Specified')

            us_url = self.us_csv_url_strvar.get()
            task_url = self.task_csv_url_strvar.get()

            if us_url != 'No URL Specified' and task_url != 'No URL Specified':
                self.import_from_csv_url_btn['state'] = 'normal'

        def import_by_url():
            us_url = self.us_csv_url_strvar.get()
            task_url = self.task_csv_url_strvar.get()

            us_url_ready = us_url and us_url != 'No URL Specified'
            task_url_ready = task_url and task_url != 'No URL Specified'

            if us_url_ready and task_url_ready:
                threading.Thread(target=lambda: self.import_by_csv_urls(us_url, task_url)).start()

        def gen_field(parent, lbl_str, target_obj):
            field_frame = ttk.Frame(parent)
            field_lbl = ttk.Label(field_frame, width=26, text=lbl_str, anchor='e')
            field_obj = ttk.Label(field_frame, textvariable=target_obj, anchor='w')
            field_lbl.grid(row=0, column=0, padx=(2, 1), sticky='nsew')
            field_obj.grid(row=0, column=1, padx=(1, 2), sticky='nsew')
            return field_frame


        ## Function logic
        ##====================================================================================================================================================
        widget_frame = ttk.Frame(parent)

        lbl_frame = ttk.Frame(widget_frame, borderwidth=2, relief='ridge')
        csv_url_config_lbl = ttk.Label(lbl_frame, text=f'{' ' * 4}Import Using CSV URLs{' ' * 4}', font=('Arial', 15))
        csv_url_config_lbl.pack()

        csv_url_config_frame = ttk.Frame(widget_frame)
        csv_url_text_frame = ttk.Frame(csv_url_config_frame)

        self.us_csv_url_strvar = StringVar()
        self.task_csv_url_strvar = StringVar()
        self.url_update_btn_strvar = StringVar(value='Update CSV URLs')

        us_url_field = gen_field(csv_url_text_frame, 
                                    'US Report CSV URL:', 
                                    self.us_csv_url_strvar)
        task_url_field = gen_field(csv_url_text_frame, 
                                    'Task Report CSV URL:', 
                                    self.task_csv_url_strvar)
        self.url_update_btn = ttk.Button(csv_url_config_frame, textvariable=self.url_update_btn_strvar, command=url_update_prompt)
        
        us_url_field.grid(row=0, column=0)
        task_url_field.grid(row=1, column=0)
        csv_url_text_frame.grid(row=0, column=0)
        self.url_update_btn.grid(row=0, column=2, padx=4)

        # Buttons for importing and exporting data
        btn_frame = ttk.Frame(widget_frame)
        self.import_from_csv_url_btn = ttk.Button(btn_frame, text='Import from CSV URL', state='disabled', command=import_by_url)
        self.import_from_csv_url_btn.grid(row=0, column=0, padx=2, sticky='nsew')

        lbl_frame.pack(fill='x', pady=(0, 8))
        csv_url_config_frame.pack(pady=(0, 8))
        btn_frame.pack()

        init_fields()

        return widget_frame

    def _build_file_form(self, parent) -> ttk.Frame:
        ## Nested Methods
        ##====================================================================================================================================================
        def file_select(field: StringVar):
            fp = filedialog.askopenfilename().strip()

            if fp is not None and fp != '':
                field.set(fp)

            if self.us_fp_strval.get() != 'No File Selected' and self.task_fp_strval.get() != 'No File Selected':
                self.import_data_from_file_btn['state'] = 'normal'

        def import_by_file():
            us_fp = self.us_fp_strval.get()
            task_fp = self.task_fp_strval.get()

            if us_fp and task_fp:
                threading.Thread(target= lambda: self.import_by_files(us_fp, task_fp)).start()

        ## Function Logic
        ##====================================================================================================================================================

        widget_frame = ttk.Frame(parent)
        file_sel_lbl = ttk.Label(widget_frame, text=f'{' ' * 4}Import Using CSV Files{' ' * 4}', font=('Arial', 15), borderwidth=2, relief='ridge')
        
        fp_sel_frame = ttk.Frame(widget_frame)

        self.us_fp_strval = StringVar(value='No File Selected')
        self.task_fp_strval = StringVar(value='No File Selected')
        # User Story File Select
        self._generate_field_obj(fp_sel_frame, 
                                    0, 
                                    'US Report Filepath:', 
                                    ttk.Label(fp_sel_frame, textvariable=self.us_fp_strval, anchor='w'), 
                                    ttk.Button(fp_sel_frame, text='Select Report File', command=lambda: file_select(self.us_fp_strval)))

        # Task File Select
        self._generate_field_obj(fp_sel_frame, 
                                    1, 
                                    'Task Report Filepath:', 
                                    ttk.Label(fp_sel_frame, textvariable=self.task_fp_strval, anchor='w'), 
                                    ttk.Button(fp_sel_frame, text='Select Report File', command=lambda: file_select(self.task_fp_strval)))

        # Buttons for importing and exporting data
        btn_frame = ttk.Frame(widget_frame)
        self.import_data_from_file_btn = ttk.Button(btn_frame, text='Import from Files', state='disabled', command=import_by_file)
        self.import_data_from_file_btn.grid(row=0, column=0, padx=2, sticky='nsew')

        file_sel_lbl.pack(fill='x', pady=(0, 8))
        fp_sel_frame.pack(pady=(0, 4))
        btn_frame.pack()

        return widget_frame
    
class DataFrame(ttk.Frame):
    def __init__(self, parent: TaigaFrame, dc: DataController):
        super().__init__(parent)

        self.us_df_master : pd.DataFrame = None         ## Primary DF
        self.curr_us_df : pd.DataFrame = None           ## Current (unsaved) DF
        self.tasks_df_master : pd.DataFrame = None      ## Primary DF
        self.curr_tasks_df : pd.DataFrame = None        ## Current (unsaved) DF

        self.sprints : list[str] = None  
        self.members : list[str] = None  
        self.user_stories : list[str] = None

        self.us_table_sheet : tks.Sheet = None
        self.tasks_table_sheet : tks.Sheet = None

        self.data_frame : ttk.Frame = None
        self.parent_frame = parent
        self.dc = dc

    def taiga_data_ready(self):
        us_data_ready = self.curr_us_df is not None and len(self.curr_us_df) > 0
        task_data_ready = self.curr_tasks_df is not None and len(self.curr_tasks_df) > 0
        return us_data_ready and task_data_ready
    
    def get_taiga_data(self):
        return self.curr_us_df, self.curr_tasks_df

    def handle_data_to_tables(self):
        self.import_data_to_tables()

        if self.data_frame is None:
            self.init_and_display_dataframe()
        else:
            self.update_sheets()

    def update_sheets(self):
        self.us_table_sheet.set_data(data=self.us_df_to_table_format(self.curr_us_df).values.tolist(), redraw=True)
        self.tasks_table_sheet.set_data(data=self.tasks_df_to_table_format(self.curr_tasks_df).values.tolist(), redraw=True)

    def save_data(self):
        print(self.curr_tasks_df)
        self.dc.update_us_df(self.curr_us_df)
        self.dc.update_tasks_df(self.curr_tasks_df, ['task_num', 'us_num', 'is_coding', 'is_complete', 'assignee', 'task_subject'])

    def clear_data(self):
        ans = messagebox.askquestion(title='Delete All Taiga Data', message='Are you sure?')
        if ans == 'yes':
            print('Deleting Taiga Data...')
            self.us_df_master = self.curr_us_df \
                = self.tasks_df_master = self.curr_tasks_df \
                    = self.sprints = self.members = self.user_stories = None
            self.dc.clear_taiga_data()
            if self.data_frame:
                self.data_frame.destroy()
                self.data_frame = None

            messagebox.showinfo('Taiga Data Deletion', 'Taiga Data Cleared')


    def import_data_to_tables(self):
        self.us_df_master = self.dc.update_df(self.us_df_master, self.dc.get_us_df())
        self.tasks_df_master = self.dc.update_df(self.tasks_df_master, self.dc.get_task_df(), 'id', ['task_num', 'us_num', 'is_complete', 'assignee', 'task_subject'])

        self.curr_us_df = self.dc.update_df(self.curr_us_df, self.us_df_master)
        self.curr_tasks_df = self.dc.update_df(self.curr_tasks_df, self.tasks_df_master, 'id', ['task_num', 'us_num', 'is_complete', 'assignee', 'task_subject'])

        self.sprints = self.us_df_master['sprint'].dropna().drop_duplicates().to_list()
        self.user_stories = self.tasks_df_master['us_num'].dropna().drop_duplicates().to_list()
        self.members = self.tasks_df_master['assignee'].dropna().drop_duplicates().to_list()

    def _inv_val_format(self, df: pd.DataFrame):
        df.replace(['', 'None', 'nan', 'NaN', np.nan, None], pd.NA, inplace=True)

    def us_df_to_table_format(self, df : pd.DataFrame) -> pd.DataFrame:
        df_copy = df.copy(deep=True)
        self._inv_val_format(df_copy)
        df_copy['id'] = df_copy['id'].astype(pd.Int64Dtype())
        df_copy['us_num'] = df_copy['us_num'].astype(pd.Int64Dtype())
        df_copy['is_complete'] = df_copy['is_complete'].astype(pd.StringDtype())
        df_copy['is_complete'].replace({'True': 'Complete', 'False': 'In Process'}, inplace=True)
        df_copy['points'] = df_copy['points'].astype(pd.Int64Dtype())
        df_copy['sprint'].replace({pd.NA: 'Not Assigned'}, inplace=True)
        return df_copy

    def us_df_from_table_format(self, df : pd.DataFrame) -> pd.DataFrame:
        df_copy = df.copy(deep=True)
        self._inv_val_format(df_copy)
        df_copy['id'] = df_copy['id'].astype(pd.Int64Dtype())
        df_copy['us_num'] = df_copy['us_num'].astype(pd.Int64Dtype())
        df_copy['points'] = df_copy['points'].astype(pd.Int64Dtype())
        df_copy['is_complete'].replace({'Complete': '1', 'In-process': '0'}, inplace=True)
        df_copy['is_complete'] = df_copy['is_complete'].astype(pd.Int64Dtype())
        df_copy['is_complete'] = df_copy['is_complete'].astype(pd.BooleanDtype())
        return df_copy

    def tasks_df_to_table_format(self, df : pd.DataFrame) -> pd.DataFrame:
        df_copy = df.copy(deep=True)
        self._inv_val_format(df_copy)
        df_copy['id'] = df_copy['id'].astype(pd.Int64Dtype())
        df_copy['task_num'] = df_copy['task_num'].astype(pd.Int64Dtype())
        df_copy['is_coding'] = df_copy['is_coding'].astype(pd.BooleanDtype())
        df_copy['us_num'] = df_copy['us_num'].astype(pd.StringDtype())
        df_copy['us_num'].replace(pd.NA, 'Storyless', inplace=True)
        df_copy['is_complete'] = df_copy['is_complete'].astype(pd.StringDtype())
        df_copy['is_complete'].replace({'True': 'Complete', 'False': 'In-process'}, inplace=True)
        df_copy['assignee'].replace(pd.NA, 'Unassigned', inplace=True)
        return df_copy

    def tasks_df_from_table_format(self, df : pd.DataFrame) -> pd.DataFrame:
        df_copy = df.copy(deep=True)
        self._inv_val_format(df_copy)
        df_copy['id'] = df_copy['id'].astype(pd.Int64Dtype())
        df_copy['us_num'].replace('Storyless', pd.NA, inplace=True)
        df_copy['us_num'] = df_copy['us_num'].astype(pd.Int64Dtype())
        df_copy['task_num'] = df_copy['task_num'].astype(pd.Int64Dtype())
        df_copy['is_coding'] = df_copy['is_coding'].astype(pd.BooleanDtype())
        df_copy['is_complete'].replace({'Complete': '1', 'In-process': '0'}, inplace=True)
        df_copy['is_complete'] = df_copy['is_complete'].astype(pd.Int64Dtype())
        df_copy['is_complete'] = df_copy['is_complete'].astype(pd.BooleanDtype())
        df_copy['assignee'].replace('Unassigned', pd.NA, inplace=True)
        return df_copy

    def init_and_display_dataframe(self):
        def generate_field_obj(parent, lbl_str, target_obj):
            field_lbl = ttk.Label(parent, text=lbl_str, anchor='e')
            field_lbl.grid(row=0, column=0, padx=(2, 1), sticky='nsew')
            target_obj.grid(row=0, column=1, padx=(1, 2), sticky='nsew')

        def build_header_frame(data_frame):
            def build_tab_btn_frame(parent):
                widget_frame = ttk.Frame(parent)
                btn_frame = ttk.Frame(widget_frame)
                save_data_btn = ttk.Button(btn_frame, text='Save Taiga Data', command=self.save_data)
                clear_data_btn = ttk.Button(btn_frame, text='Clear All Taiga Data', command=self.clear_data)
                save_data_btn.grid(row=0, column=0, padx=(2, 1))
                clear_data_btn.grid(row=0, column=1, padx=(2, 1))
                btn_frame.pack(anchor='e')
                return widget_frame

            header_frame = ttk.Frame(data_frame)
            # taiga_data_header_lbl = ttk.Label(header_frame, text=f'{' ' * 4}Taiga Data{' ' * 4}', font=('Arial', 15))
            btn_frame = build_tab_btn_frame(header_frame)
            # taiga_data_header_lbl.pack(pady=2)
            btn_frame.pack(fill='x', pady=2)
            return header_frame

        ## US Tab Creation
        ##=========================================================================================================================================
        def build_us_tab(parent):
            ## Useful Variables
            padx = 3
            sticky = 'nsew'

            sprint_options = [None, 'None', 'Not Assigned'] + self.sprints
            completion_options = [None, 'None', 'Complete', 'In Process']

            sprint_select_strvar = StringVar()
            completion_select_strvar = StringVar()

            def apply_filters(*args):
                sprint = sprint_select_strvar.get()
                compl = completion_select_strvar.get()

                sprint_filter = sprint != 'None'
                completion_filter = compl != 'None'

                if sprint_filter or completion_filter:
                    rows = []
                    for rn, row in enumerate(self.us_table_sheet.data):
                        row_match = True

                        if sprint_filter and row[3] != sprint:
                            row_match = False
                        
                        if completion_filter and row[2] != compl:
                            row_match = False

                        if row_match:
                            rows.append(rn)

                    self.us_table_sheet.display_rows(rows=rows, all_displayed=False, redraw=True)
                    self.us_clear_filters_btn['state'] = 'normal'
                else:
                    self.us_clear_filters_btn['state'] = 'disabled'
                    self.us_table_sheet.display_rows('all', redraw=True)

            def us_table_change(event):
                change_dict = { 'is_complete': {'Complete': True, 'In-process': False } }

                for (row, col), old_value in event.cells.table.items():
                    try:
                        # Convert data type based on original DataFrame column type
                        col_name = self.curr_us_df.columns[col]
                        new_val = not change_dict[col_name][old_value]  # Since the event only returns the old value
                        self.curr_us_df.at[row, col_name] = new_val  # Update DataFrame

                        print(f"Updated US DataFrame: \nRow - {row}, Column Name - {col_name}, New Value - {new_val}\n")  # Debug print
                    except Exception as e:
                        print(f"Error updating DataFrame: {e}")

                self.us_table_sheet.reset_changed_cells()  # Clear change tracker after update

            def build_filter_panel(parent_frame):
                def clear_filters():
                    sprint_opt_sel.reset()
                    completion_opt_sel.reset()
                
                filter_frame = ttk.Frame(parent_frame)
                options_frame = ttk.Frame(filter_frame)

                sprint_filter_frame = ttk.Frame(options_frame)
                complete_filter_frame = ttk.Frame(options_frame)
        
                filter_section_lbl = ttk.Label(options_frame, text='Filters:', font=('Arial', 11, 'bold'))
                sprint_opt_sel = CustomOptionMenu(sprint_filter_frame, sprint_select_strvar, *sprint_options)
                generate_field_obj(sprint_filter_frame, 'Sprint:', sprint_opt_sel)
                completion_opt_sel = CustomOptionMenu(complete_filter_frame, completion_select_strvar, *completion_options)
                generate_field_obj(complete_filter_frame, 'Complete:', completion_opt_sel)
                self.us_clear_filters_btn = ttk.Button(options_frame, text='Clear Filters', state='disabled', command=clear_filters)

                sprint_select_strvar.trace_add(mode='write', callback=apply_filters)
                completion_select_strvar.trace_add(mode='write', callback=apply_filters)

                filter_section_lbl.grid(row=0, column=0, padx=padx, sticky=sticky)
                sprint_filter_frame.grid(row=0, column=1, padx=padx, sticky=sticky)
                complete_filter_frame.grid(row=0, column=3, padx=padx, sticky=sticky)
                self.us_clear_filters_btn.grid(row=0, column=4, padx=padx, sticky=sticky)
                
                options_frame.pack(pady=(4, 4), anchor='w')
                return filter_frame

            def build_table_panel(parent_frame):
                table_frame = ttk.Frame(parent_frame)
                
                df = self.us_df_to_table_format(self.curr_us_df)
                rows = len(df)
                cols = len(df.columns)

                self.us_table_sheet = tks.Sheet(table_frame, data=df.values.tolist(), header=df.columns.tolist(), width=500)

                column_widths = []
                index = 0
                total_width = 0
                for column in df.columns.tolist():
                    text_width = self.us_table_sheet.get_column_text_width(index)
                    # if column == 'task_subject':
                    #     text_width = 500

                    column_widths.append(text_width)
                    total_width += text_width
                    index += 1

                self.us_table_sheet.enable_bindings()
                self.us_table_sheet.disable_bindings('move_columns', 'move_rows', 'edit_cell', 'rc_insert_column', 'rc_delete_column')
                self.us_table_sheet.readonly_columns(columns=[0, 1, 2, 3, 4, 5])
                self.us_table_sheet.pack(fill='y', expand=True)

                self.us_table_sheet.set_sheet_data_and_display_dimensions(total_rows=rows, total_columns=cols)
                self.us_table_sheet.config(width=(total_width * 1.15))
                self.us_table_sheet.set_all_cell_sizes_to_text()
                return table_frame
            
            widget_frame = ttk.Frame(parent)
            hdr_frame = ttk.Frame(widget_frame, borderwidth=2, relief='ridge')
            
            hdr_lbl =  ttk.Label(hdr_frame, text=f'{' ' * 4}User Story Data{' ' * 4}', font=('Arial', 13, 'bold'))
            hdr_lbl.pack()
            filter_panel = build_filter_panel(widget_frame)
            table_panel = build_table_panel(widget_frame)

            hdr_frame.pack(fill='x') 
            filter_panel.pack() 
            table_panel.pack(expand = 1, fill='y') 
            
            return widget_frame
        
        ## Task Tab Creation
        ##=========================================================================================================================================
        def build_task_tab(parent):
            ## Useful Variables
            padx = 3
            sticky = 'nsew'

            us_options = [None, 'None','Storyless'] + self.user_stories
            user_options = [None, 'None' ,'Unassigned'] + self.members
            coding_options = [None, 'None', np.True_, np.False_]

            us_select_strvar = StringVar()
            user_select_strvar = StringVar()
            coding_select_strvar = StringVar()

            def apply_filters(*args):
                us = us_select_strvar.get()
                user = user_select_strvar.get()
                coding_val = coding_select_strvar.get()
                coding = coding_val if coding_val == 'None' else eval(coding_val)

                us_filter = us != 'None'
                user_filter = user != 'None'
                coding_filter = coding != 'None'

                if us_filter or user_filter or coding_filter:
                    rows = []
                    for rn, row in enumerate(self.tasks_table_sheet.data):
                        row_match = True

                        if us_filter and row[2] != us:
                            row_match = False
                        if user_filter and row[5] != user:
                            row_match = False
                        if coding_filter and row[3] != coding:
                            row_match = False

                        if row_match:
                            rows.append(rn)

                    self.tasks_table_sheet.display_rows(rows=rows, all_displayed=False, redraw=True)
                    self.task_clear_filters_btn['state'] = 'normal'
                else:
                    self.task_clear_filters_btn['state'] = 'disabled'
                    self.tasks_table_sheet.display_rows('all', redraw=True)

            def task_table_change(event):
                change_dict = { 'is_coding': { np.True_: True, np.False_: False } }

                for (row, col), old_value in event.cells.table.items():
                    try:
                        # Convert data type based on original DataFrame column type
                        col_name = self.curr_tasks_df.columns[col]
                        new_val = not change_dict[col_name][old_value]  # Since the event only returns the old value
                        self.curr_tasks_df.at[row, col_name] = new_val  # Update DataFrame

                        print(f"Updated Tasks DataFrame: \nRow - {row}, Column Name - {col_name}, New Value - {new_val}\n")  # Debug print
                    except Exception as e:
                        print(f"Error updating DataFrame: {e}")

                self.tasks_table_sheet.reset_changed_cells()  # Clear change tracker after update

            def build_filter_panel(parent_frame):
                def clear_filters():
                    us_opt_sel.reset()
                    user_opt_sel.reset()
                    coding_opt_sel.reset()
                
                filter_frame = ttk.Frame(parent_frame)
                options_frame = ttk.Frame(filter_frame)

                us_filter_frame = ttk.Frame(options_frame)
                user_filter_frame = ttk.Frame(options_frame)
                coding_filter_frame = ttk.Frame(options_frame)
        
                filter_section_lbl = ttk.Label(options_frame, text='Filters:', font=('Arial', 11, 'bold'))
                us_opt_sel = CustomOptionMenu(us_filter_frame, us_select_strvar, *us_options)
                generate_field_obj(us_filter_frame, 'User Story:', us_opt_sel)
                user_opt_sel = CustomOptionMenu(user_filter_frame, user_select_strvar, *user_options)
                generate_field_obj(user_filter_frame, 'Assigned To:', user_opt_sel)
                coding_opt_sel = CustomOptionMenu(coding_filter_frame, coding_select_strvar, *coding_options)
                generate_field_obj(coding_filter_frame, 'Coding Task:', coding_opt_sel)
                self.task_clear_filters_btn = ttk.Button(options_frame, text='Clear Filters', state='disabled', command=clear_filters)

                us_select_strvar.trace_add(mode='write', callback=apply_filters)
                user_select_strvar.trace_add(mode='write', callback=apply_filters)
                coding_select_strvar.trace_add(mode='write', callback=apply_filters)

                filter_section_lbl.grid(row=0, column=0, padx=padx, sticky=sticky)
                us_filter_frame.grid(row=0, column=1, padx=padx, sticky=sticky)
                user_filter_frame.grid(row=0, column=2, padx=padx, sticky=sticky)
                coding_filter_frame.grid(row=0, column=3, padx=padx, sticky=sticky)
                self.task_clear_filters_btn.grid(row=0, column=4, padx=padx, sticky=sticky)
                
                options_frame.pack(pady=(4, 4), anchor='w')
                return filter_frame

            def build_table_panel(parent_frame):
                table_frame = ttk.Frame(parent_frame)
                
                df = self.tasks_df_to_table_format(self.curr_tasks_df)
                rows = len(df)
                cols = len(df.columns)

                self.tasks_table_sheet = tks.Sheet(table_frame, data=df.values.tolist(), header=df.columns.tolist())
                self.tasks_table_sheet.create_dropdown('all', 3, values=[np.True_, np.False_])
                for row, value in enumerate(df['is_coding']):
                    self.tasks_table_sheet.set_cell_data(row, 3, value)

                column_widths = []
                index = 0
                for column in df.columns.tolist():
                    text_width = self.tasks_table_sheet.get_column_text_width(index)
                    if column == 'task_subject':
                        text_width = 500

                    column_widths.append(text_width)
                    index += 1

                self.tasks_table_sheet.enable_bindings()
                self.tasks_table_sheet.extra_bindings("end_edit_cell", task_table_change)  # Call function after edit
                self.tasks_table_sheet.disable_bindings('move_columns', 'move_rows', 'rc_insert_column', 'rc_delete_column')
                self.tasks_table_sheet.readonly_columns(columns=[0, 1, 2, 4, 5, 6])
                self.tasks_table_sheet.pack(fill='both', expand=True, pady=(0, 5))

                self.tasks_table_sheet.set_sheet_data_and_display_dimensions(total_rows=rows, total_columns=cols)
                self.tasks_table_sheet.set_column_widths(column_widths)

                return table_frame

            widget_frame = ttk.Frame(parent)
            hdr_frame = ttk.Frame(widget_frame, borderwidth=2, relief='ridge')
            
            hdr_lbl =  ttk.Label(hdr_frame, text=f'{' ' * 4}Task Data{' ' * 4}', font=('Arial', 13, 'bold'))
            hdr_lbl.pack()
            filter_panel = build_filter_panel(widget_frame)
            table_panel = build_table_panel(widget_frame)

            hdr_frame.pack(fill='x') 
            filter_panel.pack() 
            table_panel.pack(expand = 1, fill ="both") 
            
            return widget_frame

        ## DataFrame build logic
        ##=========================================================================================================================================
        self.data_frame = ttk.Frame(self)
        header_frame = build_header_frame(self.data_frame)

        tabControl = ttk.Notebook(self.data_frame)
        us_data_tab = build_us_tab(tabControl)
        task_data_tab = build_task_tab(tabControl)

        tabControl.add(us_data_tab, text='User Story Data')
        tabControl.add(task_data_tab, text='Task Data')

        header_frame.pack(fill ='x') 
        tabControl.pack(expand = 1, fill ="both") 
        self.data_frame.pack(expand = 1, fill ="both") 
